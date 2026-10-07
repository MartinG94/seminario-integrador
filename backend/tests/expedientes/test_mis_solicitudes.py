"""Pruebas para monitoreo de solicitudes T01 iniciadas (SCRUM-75 / PB-04).

Cubre:
- CA1: Aislamiento estricto de creador/solicitante.
- CA2: Exposición de número, fecha, involucrados, título/motivo, estado procesal y resolución final.
- CA3: Confidencialidad garantizada (cero notas de deliberación, votos nominales
  o borradores del TD).
- CA4: Restricción RBAC mediante CanCreateT01 (CD, TD, Fiscalizadora).
- CA5: Filtrado por estado y búsqueda por texto.
- Vinculación: Creación atómica del Expediente formal al emitir.
"""

from types import SimpleNamespace

import pytest
from rest_framework.test import APIClient

from expedientes.models import EstadoExpedienteEnum, SolicitudT01
from socios.models import Role, Socio


@pytest.fixture
def mock_padron(monkeypatch):
    """Mockea get_padron_repository para validar socios por id en el serializer."""

    def _get_by_id(socio_id):
        socio = Socio.objects.filter(pk=socio_id).first()
        if not socio:
            return None
        return SimpleNamespace(
            socio_id=socio.id,
            legajo=socio.legajo,
            dni="30111222",
            first_name=socio.first_name,
            last_name=socio.last_name,
            email=socio.email,
            subcomision=socio.subcomision,
            social_year=socio.social_year,
            category=socio.category,
            is_active=socio.is_enabled,
            membership_status=SimpleNamespace(value="ENABLED"),
        )

    repo = SimpleNamespace(get_by_id=_get_by_id)
    monkeypatch.setattr("expedientes.serializers.get_padron_repository", lambda: repo)
    return repo


@pytest.mark.django_db
def test_emitir_t01_crea_y_vincula_expediente(make_socio, authenticate, mock_padron):
    autoridad = make_socio(legajo="61001", role=Role.CD)
    imputado = make_socio(legajo="61002", role=Role.SOCIO)
    client = authenticate(autoridad)

    # 1. Crear borrador
    resp_draft = client.post(
        "/api/v1/expedientes/",
        {
            "tipo_accion": "SANCTION",
            "puntos": "-1.50",
            "titulo": "Inconducta en evento",
            "motivo": "Falta reglamentaria durante asamblea",
            "destinatarios_socios_ids": [imputado.id],
        },
        format="json",
    )
    assert resp_draft.status_code == 201
    draft_id = resp_draft.data["id"]

    # 2. Emitir solicitud
    resp_emit = client.post(f"/api/v1/expedientes/{draft_id}/emitir/", {}, format="json")
    assert resp_emit.status_code == 200

    solicitud = SolicitudT01.objects.get(pk=draft_id)
    assert solicitud.estado == SolicitudT01.Estado.ISSUED
    assert solicitud.expediente is not None
    assert solicitud.expediente.estado == EstadoExpedienteEnum.CREADO
    assert solicitud.expediente.numero.startswith("EXP-")
    assert solicitud.expediente.socios.filter(pk=imputado.id).exists()


@pytest.mark.django_db
def test_mis_solicitudes_control_acceso_rbac_ca4(make_socio, authenticate):
    # Anónimo -> 401
    anon_client = APIClient()
    resp_anon = anon_client.get("/api/v1/expedientes/mis-solicitudes/")
    assert resp_anon.status_code == 401

    # Socio ordinario -> 403
    socio_ordinario = make_socio(legajo="62001", role=Role.SOCIO)
    client_socio = authenticate(socio_ordinario)
    resp_socio = client_socio.get("/api/v1/expedientes/mis-solicitudes/")
    assert resp_socio.status_code == 403

    # Admin ordinario no directivo -> 403
    admin_socio = make_socio(legajo="62002", role=Role.ADMIN)
    client_admin = authenticate(admin_socio)
    resp_admin = client_admin.get("/api/v1/expedientes/mis-solicitudes/")
    assert resp_admin.status_code == 403

    # Roles habilitados (CD, TD, FISCALIZADORA) -> 200
    for rol in (Role.CD, Role.TD, Role.FISCALIZADORA):
        auth_socio = make_socio(legajo=f"620{rol[:2]}", role=rol)
        client_auth = authenticate(auth_socio)
        resp_auth = client_auth.get("/api/v1/expedientes/mis-solicitudes/")
        assert resp_auth.status_code == 200
        assert isinstance(resp_auth.data, list)


@pytest.mark.django_db
def test_mis_solicitudes_aislamiento_creador_ca1(make_socio, authenticate, mock_padron):
    autoridad_a = make_socio(legajo="63001", role=Role.CD)
    autoridad_b = make_socio(legajo="63002", role=Role.FISCALIZADORA)
    imputado = make_socio(legajo="63003", role=Role.SOCIO)

    client_a = authenticate(autoridad_a)

    client_b = APIClient()
    login_b = client_b.post(
        "/api/v1/auth/login/",
        {"identifier": autoridad_b.legajo, "password": "Aveit-Test-2026!"},
        format="json",
    )
    client_b.credentials(HTTP_AUTHORIZATION=f"Bearer {login_b.data['access']}")

    # Autoridad A crea un borrador y emite una solicitud
    r_a1 = client_a.post(
        "/api/v1/expedientes/",
        {
            "tipo_accion": "SANCTION",
            "puntos": "-1.00",
            "titulo": "Causa Iniciada por A",
            "motivo": "Motivo A",
            "destinatarios_socios_ids": [imputado.id],
        },
        format="json",
    )
    client_a.post(f"/api/v1/expedientes/{r_a1.data['id']}/emitir/", {}, format="json")

    # Autoridad B crea un borrador propio
    client_b.post(
        "/api/v1/expedientes/",
        {
            "tipo_accion": "MERIT",
            "puntos": "2.00",
            "titulo": "Causa Iniciada por B",
            "motivo": "Motivo B",
            "destinatarios_socios_ids": [imputado.id],
        },
        format="json",
    )

    # Autoridad A consulta sus solicitudes
    resp_a = client_a.get("/api/v1/expedientes/mis-solicitudes/")
    assert resp_a.status_code == 200
    titulos_a = [item["titulo"] for item in resp_a.data]
    assert "Causa Iniciada por A" in titulos_a
    assert "Causa Iniciada por B" not in titulos_a

    # Autoridad B consulta sus solicitudes
    resp_b = client_b.get("/api/v1/expedientes/mis-solicitudes/")
    assert resp_b.status_code == 200
    titulos_b = [item["titulo"] for item in resp_b.data]
    assert "Causa Iniciada por B" in titulos_b
    assert "Causa Iniciada por A" not in titulos_b


@pytest.mark.django_db
def test_mis_solicitudes_confidencialidad_estricta_ca2_ca3(make_socio, authenticate, mock_padron):
    autoridad = make_socio(legajo="64001", role=Role.TD)
    imputado = make_socio(legajo="64002", role=Role.SOCIO)
    client = authenticate(autoridad)

    r_sol = client.post(
        "/api/v1/expedientes/",
        {
            "tipo_accion": "SANCTION",
            "puntos": "-2.00",
            "titulo": "Causa para auditoría de confidencialidad",
            "motivo": "Motivo formal",
            "destinatarios_socios_ids": [imputado.id],
        },
        format="json",
    )
    client.post(f"/api/v1/expedientes/{r_sol.data['id']}/emitir/", {}, format="json")

    resp = client.get("/api/v1/expedientes/mis-solicitudes/")
    assert resp.status_code == 200
    assert len(resp.data) == 1
    item = resp.data[0]

    # Datos visibles CA2
    assert "id" in item
    assert "numero" in item
    assert "fecha" in item
    assert "titulo" in item
    assert "motivo" in item
    assert "estado_procesal" in item
    assert "estado_procesal_display" in item
    assert "involucrados" in item
    assert len(item["involucrados"]) == 1
    assert item["involucrados"][0]["legajo"] == imputado.legajo
    assert "resolucion_final" in item

    # Confidencialidad CA3: NO deben existir campos o notas de deliberación interna ni votos
    for campo_prohibido in (
        "deliberacion",
        "deliberaciones",
        "votos",
        "votos_nominales",
        "votos_en_curso",
        "notas_internas",
        "notas_secretas",
        "borradores_resolucion",
    ):
        assert campo_prohibido not in item


@pytest.mark.django_db
def test_mis_solicitudes_filtro_estado_y_busqueda_ca5(make_socio, authenticate, mock_padron):
    autoridad = make_socio(legajo="65001", role=Role.CD)
    socio1 = make_socio(legajo="65002", role=Role.SOCIO)
    socio1.last_name = "Alvarez"
    socio1.save()

    socio2 = make_socio(legajo="65003", role=Role.SOCIO)
    socio2.last_name = "Zeballos"
    socio2.save()
    client = authenticate(autoridad)

    # 1. Borrador
    client.post(
        "/api/v1/expedientes/",
        {
            "tipo_accion": "SANCTION",
            "puntos": "-1.00",
            "titulo": "Borrador Incompleto",
            "motivo": "Falta leve",
            "destinatarios_socios_ids": [socio1.id],
        },
        format="json",
    )

    # 2. Solicitud emitida
    r2 = client.post(
        "/api/v1/expedientes/",
        {
            "tipo_accion": "MERIT",
            "puntos": "3.00",
            "titulo": "Premio a la innovación tecnológica",
            "motivo": "Aporte destacado al laboratorio",
            "destinatarios_socios_ids": [socio2.id],
        },
        format="json",
    )
    client.post(f"/api/v1/expedientes/{r2.data['id']}/emitir/", {}, format="json")

    # Filtro: solo borradores
    resp_drafts = client.get("/api/v1/expedientes/mis-solicitudes/?estado=DRAFT")
    assert resp_drafts.status_code == 200
    assert len(resp_drafts.data) == 1
    assert resp_drafts.data[0]["titulo"] == "Borrador Incompleto"

    # Filtro: solo emitidos
    resp_issued = client.get("/api/v1/expedientes/mis-solicitudes/?estado=ISSUED")
    assert resp_issued.status_code == 200
    assert len(resp_issued.data) == 1
    assert resp_issued.data[0]["titulo"] == "Premio a la innovación tecnológica"

    # Búsqueda por texto: por apellido del involucrado
    resp_search = client.get("/api/v1/expedientes/mis-solicitudes/?search=Zeballos")
    assert resp_search.status_code == 200
    assert len(resp_search.data) == 1
    assert resp_search.data[0]["titulo"] == "Premio a la innovación tecnológica"

    # Búsqueda por texto: por título
    resp_search_tit = client.get("/api/v1/expedientes/mis-solicitudes/?search=innovación")
    assert resp_search_tit.status_code == 200
    assert len(resp_search_tit.data) == 1


@pytest.mark.django_db
def test_eliminar_borrador_solicitud(make_socio, authenticate):
    autoridad = make_socio(legajo="66001", role=Role.CD)
    client = authenticate(autoridad)

    # Crear borrador
    r = client.post(
        "/api/v1/expedientes/",
        {
            "tipo_accion": "SANCTION",
            "puntos": "-1.00",
            "titulo": "Borrador para eliminar",
            "motivo": "Temporal",
        },
        format="json",
    )
    draft_id = r.data["id"]

    # Eliminar borrador
    resp_del = client.delete(f"/api/v1/expedientes/{draft_id}/")
    assert resp_del.status_code == 204
    assert not SolicitudT01.objects.filter(pk=draft_id).exists()
