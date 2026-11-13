"""Tests de paginación server-side para ExpedienteCollectionView y MisExpedientesView.

Valida:
- Envolvente canónica de 7 campos en GET /api/v1/expedientes/ y /mis-expedientes/.
- Soporte para parámetros page y page_size con límite anti-DoS (max_page_size=100).
- Respuesta 404 estructurada bajo RFC 9457 ante páginas fuera de rango.
- Retrocompatibilidad con all=true y fallback sin paginar cuando no se solicita page/page_size.
"""

from decimal import Decimal

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from rest_framework import status

from expedientes.models import EstadoExpedienteEnum, Expediente, SolicitudT01
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


@pytest.mark.django_db
def test_gestion_and_mis_expedientes_exclude_estado_ne_emitido(
    api_client, authenticate, cd_socio, regular_socio
):
    """Verifica exclusión de estado=emitido vía estado_ne en /gestion/ y /mis-expedientes/."""
    e_creado = Expediente.objects.create(
        numero="EXP-9201/2026",
        titulo="Causa abierta uno",
        motivo="Pendiente",
        socio=regular_socio,
        estado=EstadoExpedienteEnum.CREADO,
    )
    e_just = Expediente.objects.create(
        numero="EXP-9202/2026",
        titulo="Causa en descargo",
        motivo="Justificando",
        socio=regular_socio,
        estado=EstadoExpedienteEnum.JUSTIFICANDO,
    )
    e_emitido = Expediente.objects.create(
        numero="EXP-9203/2026",
        titulo="Causa emitida",
        motivo="Resuelta",
        socio=regular_socio,
        estado=EstadoExpedienteEnum.EMITIDO,
    )

    authenticate(regular_socio)
    res_mis = api_client.get(
        "/api/v1/expedientes/mis-expedientes/?estado_ne=emitido&ordering=numero&page=1&page_size=10"
    )
    assert res_mis.status_code == status.HTTP_200_OK
    data_mis = res_mis.json()
    assert data_mis["count"] == 2
    assert [item["id"] for item in data_mis["results"]] == [e_creado.id, e_just.id]
    assert all(item["estado"] != EstadoExpedienteEnum.EMITIDO for item in data_mis["results"])

    authenticate(cd_socio)
    res_gestion = api_client.get(
        "/api/v1/expedientes/gestion/?estado_ne=emitido&ordering=numero&page=1&page_size=10"
    )
    assert res_gestion.status_code == status.HTTP_200_OK
    data_gestion = res_gestion.json()
    assert data_gestion["count"] == 2
    assert [item["id"] for item in data_gestion["results"]] == [e_creado.id, e_just.id]
    assert e_emitido.id not in [item["id"] for item in data_gestion["results"]]


@pytest.mark.django_db
def test_collection_search_combines_with_estado_ne_and_m2m_via_single_filter(
    api_client, authenticate, cd_socio, regular_socio, make_socio
):
    """Valida búsqueda unificada vía ExpedienteFilter (M2M + search + estado_ne)."""
    co_imputado = make_socio(legajo="49999", role=Role.SOCIO)
    exp_activo = Expediente.objects.create(
        numero="EXP-9301/2026",
        titulo="Falta compartida Sigma",
        motivo="Ausencia plenaria",
        socio=cd_socio,
        estado=EstadoExpedienteEnum.JUSTIFICANDO,
    )
    exp_activo.socios.add(regular_socio, co_imputado)

    exp_emitido = Expediente.objects.create(
        numero="EXP-9302/2026",
        titulo="Falta compartida Sigma cerrada",
        motivo="Ausencia plenaria",
        socio=cd_socio,
        estado=EstadoExpedienteEnum.EMITIDO,
    )
    exp_emitido.socios.add(regular_socio, co_imputado)

    authenticate(cd_socio)
    res_gestion = api_client.get(
        "/api/v1/expedientes/gestion/?search=49999&estado_ne=emitido&page=1&page_size=10"
    )
    assert res_gestion.status_code == status.HTTP_200_OK
    assert res_gestion.json()["count"] == 1
    assert res_gestion.json()["results"][0]["id"] == exp_activo.id

    authenticate(regular_socio)
    res_mis = api_client.get(
        "/api/v1/expedientes/mis-expedientes/?search=Sigma&estado_ne=emitido&page=1&page_size=10"
    )
    assert res_mis.status_code == status.HTTP_200_OK
    assert res_mis.json()["count"] == 1
    assert res_mis.json()["results"][0]["id"] == exp_activo.id


@pytest.mark.django_db
def test_list_serializers_detect_llamado_and_felicitacion_without_extra_queries(
    api_client, authenticate, cd_socio, regular_socio
):
    """Bug #3 PO: reconoce ±0.25, SolicitudT01.puntaje_especial y ±0.33 históricos sin N+1."""
    exp_llamado_canon = Expediente.objects.create(
        numero="EXP-9401/2026",
        titulo="Llamado canónico",
        motivo="Incumplimiento menor",
        socio=regular_socio,
        puntos=Decimal("-0.25"),
        estado=EstadoExpedienteEnum.JUSTIFICANDO,
    )
    exp_felic_canon = Expediente.objects.create(
        numero="EXP-9402/2026",
        titulo="Felicitación canónica",
        motivo="Colaboración destacada",
        socio=regular_socio,
        puntos=Decimal("0.25"),
        estado=EstadoExpedienteEnum.EMITIDO,
    )
    exp_llamado_t01 = Expediente.objects.create(
        numero="EXP-9403/2026",
        titulo="Llamado desde T01",
        motivo="Apercibimiento T01",
        socio=regular_socio,
        puntos=Decimal("0.00"),
        estado=EstadoExpedienteEnum.CREADO,
    )
    SolicitudT01.objects.create(
        solicitante=cd_socio,
        destinatarios_socios_ids=[regular_socio.id],
        tipo_accion=SolicitudT01.TipoAccion.SANCTION,
        puntaje_especial=SolicitudT01.PuntajeEspecial.LLAMADO_ATENCION,
        puntos=Decimal("-0.25"),
        causal="Art. 14",
        expediente=exp_llamado_t01,
    )
    exp_felic_t01 = Expediente.objects.create(
        numero="EXP-9404/2026",
        titulo="Felicitación desde T01",
        motivo="Reconocimiento T01",
        socio=regular_socio,
        puntos=Decimal("0.00"),
        estado=EstadoExpedienteEnum.CREADO,
    )
    SolicitudT01.objects.create(
        solicitante=cd_socio,
        destinatarios_socios_ids=[regular_socio.id],
        tipo_accion=SolicitudT01.TipoAccion.MERIT,
        puntaje_especial=SolicitudT01.PuntajeEspecial.FELICITACION,
        puntos=Decimal("0.25"),
        causal="Art. 15",
        expediente=exp_felic_t01,
    )
    exp_llamado_legacy = Expediente.objects.create(
        numero="EXP-9405/2026",
        titulo="Llamado histórico",
        motivo="Registro previo",
        socio=regular_socio,
        puntos=Decimal("-0.33"),
        estado=EstadoExpedienteEnum.EMITIDO,
    )
    exp_felic_legacy = Expediente.objects.create(
        numero="EXP-9406/2026",
        titulo="Felicitación histórica",
        motivo="Registro previo",
        socio=regular_socio,
        puntos=Decimal("0.33"),
        estado=EstadoExpedienteEnum.EMITIDO,
    )
    exp_ordinario = Expediente.objects.create(
        numero="EXP-9407/2026",
        titulo="Sanción ordinaria",
        motivo="Falta estándar",
        socio=regular_socio,
        puntos=Decimal("-1.00"),
        estado=EstadoExpedienteEnum.EMITIDO,
    )

    for user, endpoint in (
        (regular_socio, "/api/v1/expedientes/mis-expedientes/?page=1&page_size=20"),
        (cd_socio, "/api/v1/expedientes/gestion/?page=1&page_size=20"),
    ):
        authenticate(user)
        with CaptureQueriesContext(connection) as ctx:
            response = api_client.get(endpoint)
        assert response.status_code == status.HTTP_200_OK
        assert len(ctx) <= 18
        by_id = {item["id"]: item for item in response.json()["results"]}

        assert by_id[exp_llamado_canon.id]["es_llamado"] is True
        assert by_id[exp_llamado_canon.id]["es_felicitacion"] is False
        assert by_id[exp_llamado_canon.id]["puntaje_solicitado"] == "LLAMADO_ATENCION"

        assert by_id[exp_felic_canon.id]["es_felicitacion"] is True
        assert by_id[exp_felic_canon.id]["es_llamado"] is False
        assert by_id[exp_felic_canon.id]["puntaje_solicitado"] == "FELICITACION"

        assert by_id[exp_llamado_t01.id]["es_llamado"] is True
        assert by_id[exp_llamado_t01.id]["es_felicitacion"] is False

        assert by_id[exp_felic_t01.id]["es_felicitacion"] is True
        assert by_id[exp_felic_t01.id]["es_llamado"] is False

        assert by_id[exp_llamado_legacy.id]["es_llamado"] is True
        assert by_id[exp_llamado_legacy.id]["es_felicitacion"] is False

        assert by_id[exp_felic_legacy.id]["es_felicitacion"] is True
        assert by_id[exp_felic_legacy.id]["es_llamado"] is False

        assert by_id[exp_ordinario.id]["es_llamado"] is False
        assert by_id[exp_ordinario.id]["es_felicitacion"] is False
