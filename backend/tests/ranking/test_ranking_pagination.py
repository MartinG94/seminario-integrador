"""Pruebas de integración para la paginación server-side del Ranking (T-87.09 / SCRUM-118).

Verifica:
1. Envolvente canónica de 7 campos en respuestas paginadas.
2. Parámetros page y page_size configurables.
3. Techo estricto max_page_size = 100.
4. Error estructurado RFC 9457 (404) ante páginas fuera de rango.
5. Paginación combinada con filtros (categoría, subcomisión, búsqueda) y ordenamiento.
6. Retrocompatibilidad para consultas sin parámetros de paginación (lista plana).
"""

import pytest
from rest_framework import status

from padron.models import Socio, SocioEstudio, Subcomision
from ranking.models import PuntajeAplicado, PuntajeGeneral
from tests.legacy_schema import create_legacy_record


@pytest.fixture
def seed_many_socios(db) -> list[Socio]:
    """Crea 25 socios para probar paginación de más de una página (page_size=10 o 20)."""
    sub_computos = create_legacy_record(Subcomision, codSubcomision=1, nombre="Cómputos")
    sub_eventos = create_legacy_record(Subcomision, codSubcomision=7, nombre="Eventos")

    socios = []
    for i in range(1, 26):
        sub = sub_computos if i % 2 == 0 else sub_eventos
        ano_social = 5 if i <= 15 else 2  # 15 ACTIVOS, 10 PASIVOS
        saldo = float(100 - i)  # Saldos descendentes

        s = create_legacy_record(
            Socio,
            nroSocio=1000 + i,
            nombre=f"Nombre{i:02d}",
            apellido=f"Apellido{i:02d}",
            anoSocial=ano_social,
            subcomision=sub,
            idTipoSocio=1 if ano_social == 5 else 12,
        )
        create_legacy_record(
            SocioEstudio,
            compositeKey=100000 + i,
            socio=s,
            nroLegajo=50000 + i,
            codEspecialidad=1,
        )
        create_legacy_record(
            PuntajeAplicado,
            idPuntajeAplicado=1000 + i,
            socio=s,
            puntajeAplicado=saldo,
        )
        create_legacy_record(
            PuntajeGeneral,
            idPuntajeGeneral=1000 + i,
            socio=s,
            puntos=saldo,
        )
        socios.append(s)
    return socios


@pytest.mark.django_db
def test_ranking_pagination_default_page_size_and_envelope(api_client, seed_many_socios):
    """Verifica que /api/v1/ranking/?page=1 retorne la envolvente canónica de 7 campos."""
    response = api_client.get("/api/v1/ranking/?page=1")
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert isinstance(data, dict)
    expected_fields = {
        "count",
        "total_pages",
        "current_page",
        "page_size",
        "next",
        "previous",
        "results",
    }
    assert expected_fields.issubset(data.keys())

    assert data["count"] == 25
    assert data["total_pages"] == 2  # 25 registros con page_size=20 -> 2 páginas
    assert data["current_page"] == 1
    assert data["page_size"] == 20
    assert data["next"] is not None
    assert "page=2" in data["next"]
    assert data["previous"] is None
    assert len(data["results"]) == 20


@pytest.mark.django_db
def test_ranking_pagination_custom_page_size(api_client, seed_many_socios):
    """Verifica page_size personalizado y navegación a página 2."""
    response = api_client.get("/api/v1/ranking/?page=2&page_size=10")
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["count"] == 25
    assert data["total_pages"] == 3  # 25 / 10 = 3 páginas
    assert data["current_page"] == 2
    assert data["page_size"] == 10
    assert data["previous"] is not None
    assert "page=1" in data["previous"] or "page_size=10" in data["previous"]
    assert data["next"] is not None
    assert "page=3" in data["next"]
    assert len(data["results"]) == 10


@pytest.mark.django_db
def test_ranking_pagination_max_page_size_ceiling(api_client, seed_many_socios):
    """Verifica que no se permita exceder el techo max_page_size=100."""
    response = api_client.get("/api/v1/ranking/?page=1&page_size=500")
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["page_size"] == 100


@pytest.mark.django_db
def test_ranking_pagination_invalid_page_404_rfc9457(api_client, seed_many_socios):
    """Verifica que solicitar una página fuera de rango retorne 404 estructurado RFC 9457."""
    response = api_client.get("/api/v1/ranking/?page=999")
    assert response.status_code == status.HTTP_404_NOT_FOUND

    data = response.json()
    assert data["type"] == "https://errors.aveit.org.ar/invalid-page"
    assert data["title"] == "Página no encontrada"
    assert data["status"] == 404
    assert "invalid_params" in data
    assert any(param["name"] == "page" for param in data["invalid_params"])


@pytest.mark.django_db
def test_ranking_pagination_combined_with_filters_and_ordering(api_client, seed_many_socios):
    """Verifica que los filtros y el ordenamiento se apliquen en BD previo a la paginación."""
    response = api_client.get("/api/v1/ranking/?categoria=ACTIVO&ordering=saldo&page=1&page_size=5")
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["count"] == 15  # 15 socios activos
    assert data["total_pages"] == 3
    assert len(data["results"]) == 5

    # Con ordering=saldo asc, el primer resultado debe tener el menor saldo entre los activos
    saldos = [item["saldo"] for item in data["results"]]
    assert saldos == sorted(saldos)
    assert all(item["categoria"] == "ACTIVO" for item in data["results"])


@pytest.mark.django_db
def test_ranking_pagination_backward_compatibility_flat_list(api_client, seed_many_socios):
    """Verifica que sin parámetros page/page_size retorne una lista plana para tests legados."""
    response = api_client.get("/api/v1/ranking/")
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 25


@pytest.mark.django_db
def test_ranking_pagination_all_parameter_forces_flat_list(api_client, seed_many_socios):
    """Verifica que all=true fuerce lista plana incluso si se pasa page_size."""
    response = api_client.get("/api/v1/ranking/?page=1&page_size=5&all=true")
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 25


@pytest.mark.django_db
def test_ranking_pagination_deterministic_tie_breaker_across_pages(api_client, db):
    """Socios con idéntico saldo, apellido y nombre desempatan por nroSocio entre páginas."""
    sub_comp = create_legacy_record(Subcomision, codSubcomision=11, nombre="Cómputos")
    for idx in range(6):
        s = create_legacy_record(
            Socio,
            nroSocio=8000 + idx,
            nombre="Homónimo",
            apellido="Idéntico",
            anoSocial=5,
            subcomision=sub_comp,
            idTipoSocio=1,
        )
        create_legacy_record(
            PuntajeAplicado, idPuntajeAplicado=8000 + idx, socio=s, puntajeAplicado=10.0
        )
        create_legacy_record(PuntajeGeneral, idPuntajeGeneral=8000 + idx, socio=s, puntos=10.0)

    r1 = api_client.get("/api/v1/ranking/?search=Homónimo&ordering=-saldo&page=1&page_size=3")
    r2 = api_client.get("/api/v1/ranking/?search=Homónimo&ordering=-saldo&page=2&page_size=3")
    assert r1.status_code == status.HTTP_200_OK
    assert r2.status_code == status.HTTP_200_OK

    ids1 = [item["id"] for item in r1.json()["results"]]
    ids2 = [item["id"] for item in r2.json()["results"]]
    assert ids1 == ["8000", "8001", "8002"]
    assert ids2 == ["8003", "8004", "8005"]
    assert set(ids1).isdisjoint(set(ids2))


@pytest.mark.django_db
def test_ranking_pagination_filters_grupo_solo_alertas_and_ordering_categoria(api_client, db):
    """Verifica filtros server-side por grupo, solo_alertas (<= -7) y ordering=categoria."""
    from django.utils import timezone

    from padron.models import SocioEstadoHistorial

    sub_comp = create_legacy_record(Subcomision, codSubcomision=12, nombre="Cómputos")
    s1 = create_legacy_record(
        Socio,
        nroSocio=9001,
        nombre="Ana",
        apellido="Alerta",
        anoSocial=5,
        subcomision=sub_comp,
        idTipoSocio=1,
    )
    s2 = create_legacy_record(
        Socio,
        nroSocio=9002,
        nombre="Bruno",
        apellido="Regular",
        anoSocial=2,
        subcomision=sub_comp,
        idTipoSocio=1,
    )
    create_legacy_record(
        SocioEstadoHistorial,
        idEstadoHistorial=9001,
        socio=s1,
        idGrupo=58,
        fechaHora=timezone.now(),
        codEstadoSocio=1,
        socio_motivoCambioEstado=1,
    )
    create_legacy_record(PuntajeAplicado, idPuntajeAplicado=9001, socio=s1, puntajeAplicado=-8.0)
    create_legacy_record(PuntajeGeneral, idPuntajeGeneral=9001, socio=s1, puntos=-8.0)
    create_legacy_record(PuntajeAplicado, idPuntajeAplicado=9002, socio=s2, puntajeAplicado=3.0)
    create_legacy_record(PuntajeGeneral, idPuntajeGeneral=9002, socio=s2, puntos=3.0)

    r_alerta = api_client.get("/api/v1/ranking/?solo_alertas=true&page=1&page_size=10")
    assert r_alerta.status_code == status.HTTP_200_OK
    assert [x["id"] for x in r_alerta.json()["results"]] == ["9001"]

    r_grupo = api_client.get("/api/v1/ranking/?grupo=G58&page=1&page_size=10")
    assert r_grupo.status_code == status.HTTP_200_OK
    assert [x["id"] for x in r_grupo.json()["results"]] == ["9001"]

    r_sin_grupo = api_client.get("/api/v1/ranking/?grupo=SIN_GRUPO&page=1&page_size=10")
    assert r_sin_grupo.status_code == status.HTTP_200_OK
    assert [x["id"] for x in r_sin_grupo.json()["results"]] == ["9002"]

    r_cat_ord = api_client.get("/api/v1/ranking/?ordering=categoria&page=1&page_size=10")
    assert r_cat_ord.status_code == status.HTTP_200_OK
    assert [x["categoria"] for x in r_cat_ord.json()["results"]] == ["ACTIVO", "PASIVO"]
