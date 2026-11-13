"""Tests de paginación server-side para ExpedienteCollectionView y MisExpedientesView.

Valida:
- Envolvente canónica de 7 campos en GET /api/v1/expedientes/ y /mis-expedientes/.
- Soporte para parámetros page y page_size con límite anti-DoS (max_page_size=100).
- Respuesta 404 estructurada bajo RFC 9457 ante páginas fuera de rango.
- Retrocompatibilidad con all=true y fallback sin paginar cuando no se solicita page/page_size.
"""

import pytest
from rest_framework import status

from expedientes.models import EstadoExpedienteEnum, Expediente
from socios.models import Role


@pytest.fixture
def cd_socio(make_socio):
    """Socio con rol CD facultado para consultar ExpedienteCollectionView."""
    return make_socio(legajo="40001", role=Role.CD)


@pytest.fixture
def regular_socio(make_socio):
    """Socio ordinario con causas asignadas para MisExpedientesView."""
    return make_socio(legajo="40002", role=Role.SOCIO)


@pytest.fixture
def seed_expedientes(cd_socio, regular_socio):
    """Crea 25 expedientes para pruebas de paginación (15 asignados a regular_socio)."""
    expedientes = []
    for i in range(1, 26):
        target_socio = regular_socio if i <= 15 else cd_socio
        exp = Expediente.objects.create(
            numero=f"EXP-{i:04d}/2026",
            titulo=f"Expediente de prueba {i}",
            motivo=f"Motivo procesal número {i}",
            socio=target_socio,
            estado=EstadoExpedienteEnum.CREADO,
        )
        expedientes.append(exp)
    return expedientes


@pytest.mark.django_db
def test_expedientes_pagination_canonical_envelope(
    api_client, authenticate, cd_socio, seed_expedientes
):
    """Verifica que GET /api/v1/expedientes/gestion/?page=1 retorne la envolvente de 7 campos."""
    authenticate(cd_socio)
    response = api_client.get("/api/v1/expedientes/gestion/?page=1&page_size=10")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    assert set(data.keys()) == {
        "count",
        "total_pages",
        "current_page",
        "page_size",
        "next",
        "previous",
        "results",
    }
    assert data["count"] == 25
    assert data["total_pages"] == 3
    assert data["current_page"] == 1
    assert data["page_size"] == 10
    assert len(data["results"]) == 10
    assert data["previous"] is None
    assert data["next"] is not None
    assert "page=2" in data["next"]


@pytest.mark.django_db
def test_expedientes_pagination_page_navigation(
    api_client, authenticate, cd_socio, seed_expedientes
):
    """Verifica la navegación hacia la página 2 y el cálculo de enlaces next y previous."""
    authenticate(cd_socio)
    response = api_client.get("/api/v1/expedientes/gestion/?page=2&page_size=10")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    assert data["current_page"] == 2
    assert len(data["results"]) == 10
    assert data["previous"] is not None
    assert data["next"] is not None
    assert "page=3" in data["next"]


@pytest.mark.django_db
def test_expedientes_pagination_max_page_size_ceiling(
    api_client, authenticate, cd_socio, seed_expedientes
):
    """Verifica que solicitar page_size=500 quede acotado por el techo rígido max_page_size=100."""
    authenticate(cd_socio)
    response = api_client.get("/api/v1/expedientes/gestion/?page=1&page_size=500")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    assert data["page_size"] == 100
    assert len(data["results"]) == 25  # Hay 25 en total, caben en 1 página
    assert data["total_pages"] == 1
    assert data["next"] is None


@pytest.mark.django_db
def test_expedientes_pagination_out_of_range_rfc9457(
    api_client, authenticate, cd_socio, seed_expedientes
):
    """Verifica que solicitar page=999 emita 404 estructurado bajo RFC 9457."""
    authenticate(cd_socio)
    response = api_client.get("/api/v1/expedientes/gestion/?page=999&page_size=10")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()

    assert data["type"] == "https://errors.aveit.org.ar/invalid-page"
    assert data["title"] == "Página no encontrada"
    assert data["status"] == 404
    assert "invalid_params" in data
    assert data["invalid_params"][0]["name"] == "page"


@pytest.mark.django_db
def test_expedientes_pagination_all_fallback(api_client, authenticate, cd_socio, seed_expedientes):
    """Verifica que con all=true o sin parámetros page/page_size se preserve la lista plana."""
    authenticate(cd_socio)

    # all=true
    resp_all = api_client.get("/api/v1/expedientes/gestion/?all=true")
    assert resp_all.status_code == status.HTTP_200_OK
    data_all = resp_all.json()
    assert isinstance(data_all, list)
    assert len(data_all) == 25

    # Fallback sin parámetros
    resp_flat = api_client.get("/api/v1/expedientes/gestion/")
    assert resp_flat.status_code == status.HTTP_200_OK
    data_flat = resp_flat.json()
    assert isinstance(data_flat, list)
    assert len(data_flat) == 25


@pytest.mark.django_db
def test_mis_expedientes_pagination_canonical_envelope(
    api_client, authenticate, regular_socio, seed_expedientes
):
    """Verifica que GET /mis-expedientes/?page=1 devuelva envolvente de 7 campos."""
    authenticate(regular_socio)
    response = api_client.get("/api/v1/expedientes/mis-expedientes/?page=1&page_size=5")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    assert set(data.keys()) == {
        "count",
        "total_pages",
        "current_page",
        "page_size",
        "next",
        "previous",
        "results",
    }
    assert data["count"] == 15  # regular_socio tiene 15 causas asignadas
    assert data["total_pages"] == 3
    assert data["current_page"] == 1
    assert data["page_size"] == 5
    assert len(data["results"]) == 5
    assert data["next"] is not None


@pytest.mark.django_db
def test_mis_expedientes_out_of_range_rfc9457(
    api_client, authenticate, regular_socio, seed_expedientes
):
    """Verifica que GET /mis-expedientes/?page=999 responda 404 estructurado RFC 9457."""
    authenticate(regular_socio)
    response = api_client.get("/api/v1/expedientes/mis-expedientes/?page=999")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response["Content-Type"].split(";")[0].strip() == "application/problem+json"
    data = response.json()
    assert data["type"] == "https://errors.aveit.org.ar/invalid-page"
    assert data["status"] == 404


@pytest.mark.django_db
def test_expedientes_gestion_supports_search_estado_and_deterministic_ordering(
    api_client, authenticate, cd_socio, regular_socio
):
    """Verifica filtrado search/estado y desempate determinístico en GET /gestion/ paginado."""
    exp_a = Expediente.objects.create(
        numero="EXP-9001/2026",
        titulo="Causa Alfa especial",
        motivo="Incumplimiento Alfa",
        socio=regular_socio,
        estado=EstadoExpedienteEnum.CREADO,
    )
    exp_b = Expediente.objects.create(
        numero="EXP-9002/2026",
        titulo="Causa Alfa segunda",
        motivo="Incumplimiento Beta",
        socio=cd_socio,
        estado=EstadoExpedienteEnum.JUSTIFICANDO,
    )
    Expediente.objects.create(
        numero="EXP-9003/2026",
        titulo="Otro caso",
        motivo="Sin coincidencia",
        socio=cd_socio,
        estado=EstadoExpedienteEnum.CREADO,
    )

    authenticate(cd_socio)
    res_search = api_client.get(
        "/api/v1/expedientes/gestion/?search=Alfa&ordering=numero&page=1&page_size=10"
    )
    assert res_search.status_code == status.HTTP_200_OK
    data_search = res_search.json()
    assert data_search["count"] == 2
    assert [item["numero"] for item in data_search["results"]] == [exp_a.numero, exp_b.numero]

    res_estado = api_client.get(
        f"/api/v1/expedientes/gestion/?search=Alfa&estado={EstadoExpedienteEnum.JUSTIFICANDO}&page=1&page_size=10"
    )
    assert res_estado.status_code == status.HTTP_200_OK
    data_estado = res_estado.json()
    assert data_estado["count"] == 1
    assert data_estado["results"][0]["id"] == exp_b.id


@pytest.mark.django_db
def test_mis_expedientes_supports_search_estado_and_ordering(
    api_client, authenticate, regular_socio
):
    """Verifica búsqueda, filtro por estado y ordenamiento en GET /mis-expedientes/."""
    e1 = Expediente.objects.create(
        numero="EXP-9101/2026",
        titulo="Descargo pendiente uno",
        motivo="Falta leve",
        socio=regular_socio,
        estado=EstadoExpedienteEnum.JUSTIFICANDO,
    )
    e2 = Expediente.objects.create(
        numero="EXP-9102/2026",
        titulo="Descargo cerrado dos",
        motivo="Falta archivada",
        socio=regular_socio,
        estado=EstadoExpedienteEnum.EMITIDO,
    )

    authenticate(regular_socio)
    res = api_client.get(
        f"/api/v1/expedientes/mis-expedientes/?search=Descargo&estado={EstadoExpedienteEnum.JUSTIFICANDO}&ordering=-numero&page=1&page_size=10"
    )
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert data["count"] == 1
    assert data["results"][0]["id"] == e1.id

    res_all = api_client.get(
        "/api/v1/expedientes/mis-expedientes/?ordering=-numero&page=1&page_size=10"
    )
    assert res_all.status_code == status.HTTP_200_OK
    assert [r["id"] for r in res_all.json()["results"]] == [e2.id, e1.id]
