from types import SimpleNamespace

import pytest
from django.core.exceptions import ValidationError
from rest_framework.test import APIClient

from expedientes.models import SolicitudT01
from socios.models import Role


@pytest.fixture
def padron_socio():
    return SimpleNamespace(
        socio_id=9001,
        legajo="9001",
        dni="20123456",
        first_name="Ana",
        last_name="Prueba",
        email="ana@example.test",
        subcomision=SimpleNamespace(id=1, name="Cómputos"),
        social_year=4,
        category=SimpleNamespace(value="ACTIVE"),
        is_active=True,
        membership_status=SimpleNamespace(value="ENABLED"),
    )


@pytest.fixture
def padron_repo(monkeypatch, padron_socio):
    repo = SimpleNamespace(get_by_id=lambda socio_id: padron_socio if socio_id == 9001 else None)
    monkeypatch.setattr("expedientes.serializers.get_padron_repository", lambda: repo)
    return repo


@pytest.fixture
def expediente_client(make_socio, authenticate):
    socio = make_socio(legajo="41001", role=Role.CD)
    return authenticate(socio)


def create_draft(client, **extra):
    payload = {"tipo_accion": "SANCTION", "puntos": "-2.00", "motivo": "Motivo"}
    payload.update(extra)
    response = client.post("/api/v1/expedientes/", payload, format="json")
    assert response.status_code == 201, response.data
    return response


@pytest.mark.django_db
def test_crear_borrador_sin_anexo_no_emite(expediente_client):
    data = create_draft(expediente_client).data
    solicitud = SolicitudT01.objects.get(pk=data["id"])
    assert solicitud.estado == "DRAFT"
    assert solicitud.numero_expediente is None
    assert solicitud.anexo_relato == ""


@pytest.mark.django_db
def test_actualizar_borrador(expediente_client):
    data = create_draft(expediente_client).data
    response = expediente_client.patch(
        f"/api/v1/expedientes/{data['id']}/", {"motivo": "Actualizado"}, format="json"
    )
    assert response.status_code == 200
    assert response.data["motivo"] == "Actualizado"


@pytest.mark.django_db
def test_emitir_sin_anexo_congela_version(padron_repo, expediente_client):
    data = create_draft(expediente_client, destinatario_socio_id=9001).data
    response = expediente_client.post(
        f"/api/v1/expedientes/{data['id']}/emitir/", {}, format="json"
    )
    assert response.status_code == 200, response.data
    solicitud = SolicitudT01.objects.get(pk=data["id"])
    assert solicitud.estado == "ISSUED"
    assert solicitud.numero_expediente.startswith("T01-")
    assert solicitud.issued_at is not None
    assert solicitud.snapshot_destinatario["socio_id"] == 9001
    assert solicitud.snapshot_emitido["puntos"] == "-2.00"
    second = expediente_client.post(f"/api/v1/expedientes/{data['id']}/emitir/", {}, format="json")
    assert second.status_code == 200
    assert second.data["numero_expediente"] == solicitud.numero_expediente
    assert second.data["issued_at"] == response.data["issued_at"]


@pytest.mark.django_db
def test_snapshot_emitido_conserva_todos_los_campos(padron_repo, expediente_client):
    data = create_draft(
        expediente_client,
        destinatario_socio_id=9001,
        causal="Art. 21",
        anexo_fecha="2026-09-30",
        anexo_lugar="Sede central",
        anexo_relato="Relato completo",
        anexo_testigos="Testigo 1",
    ).data
    response = expediente_client.post(
        f"/api/v1/expedientes/{data['id']}/emitir/", {}, format="json"
    )
    assert response.status_code == 200, response.data
    snapshot = response.data["snapshot_emitido"]
    assert snapshot == {
        "id": data["id"],
        "tipo_accion": "SANCTION",
        "titulo": "",
        "causal": "Art. 21",
        "puntos": "-2.00",
        "motivo": "Motivo",
        "razon": "",
        "reglamentos_respaldantes": [],
        "destinatario": response.data["snapshot_destinatario"],
        "anexo_fecha": "2026-09-30",
        "anexo_lugar": "Sede central",
        "anexo_relato": "Relato completo",
        "anexo_testigos": "Testigo 1",
    }


@pytest.mark.django_db
def test_emitir_sin_destinatario_falla(padron_repo, expediente_client):
    data = create_draft(expediente_client).data
    response = expediente_client.post(
        f"/api/v1/expedientes/{data['id']}/emitir/", {}, format="json"
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_emitir_sin_puntos_falla_y_conserva_borrador(padron_repo, expediente_client):
    data = create_draft(expediente_client, destinatario_socio_id=9001, puntos=None).data
    response = expediente_client.post(
        f"/api/v1/expedientes/{data['id']}/emitir/", {}, format="json"
    )
    assert response.status_code == 400
    solicitud = SolicitudT01.objects.get(pk=data["id"])
    assert solicitud.estado == SolicitudT01.Estado.DRAFT
    assert solicitud.numero_expediente is None


@pytest.mark.django_db
def test_emitir_con_destinatario_inexistente_falla(padron_repo, expediente_client):
    data = create_draft(expediente_client, destinatario_socio_id=9999).data
    response = expediente_client.post(
        f"/api/v1/expedientes/{data['id']}/emitir/", {}, format="json"
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_issued_no_se_puede_modificar(padron_repo, expediente_client):
    data = create_draft(expediente_client, destinatario_socio_id=9001).data
    expediente_client.post(f"/api/v1/expedientes/{data['id']}/emitir/", {}, format="json")
    response = expediente_client.patch(
        f"/api/v1/expedientes/{data['id']}/", {"motivo": "Cambio"}, format="json"
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_segunda_emision_conserva_snapshot_exacto(padron_repo, expediente_client):
    data = create_draft(expediente_client, destinatario_socio_id=9001).data
    first = expediente_client.post(f"/api/v1/expedientes/{data['id']}/emitir/", {}, format="json")
    second = expediente_client.post(f"/api/v1/expedientes/{data['id']}/emitir/", {}, format="json")
    assert second.data["numero_expediente"] == first.data["numero_expediente"]
    assert second.data["issued_at"] == first.data["issued_at"]
    assert second.data["snapshot_emitido"] == first.data["snapshot_emitido"]


@pytest.mark.django_db
def test_emitir_con_socio_inactivo_falla(monkeypatch, padron_socio, expediente_client):
    inactive = SimpleNamespace(**{**vars(padron_socio), "is_active": False})
    monkeypatch.setattr(
        "expedientes.serializers.get_padron_repository",
        lambda: SimpleNamespace(get_by_id=lambda _socio_id: inactive),
    )
    data = create_draft(expediente_client, destinatario_socio_id=9001).data
    response = expediente_client.post(
        f"/api/v1/expedientes/{data['id']}/emitir/", {}, format="json"
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_usuario_socio_no_puede_crear_t01(make_socio, authenticate):
    client = authenticate(make_socio(legajo="41003", role=Role.SOCIO))
    response = client.post(
        "/api/v1/expedientes/",
        {"tipo_accion": "SANCTION", "puntos": "-1.00", "motivo": "Motivo"},
        format="json",
    )
    assert response.status_code == 403


@pytest.mark.django_db
def test_usuario_admin_no_puede_crear_t01(make_socio, authenticate):
    client = authenticate(make_socio(legajo="41004", role=Role.ADMIN))
    response = client.post(
        "/api/v1/expedientes/",
        {"tipo_accion": "SANCTION", "puntos": "-1.00", "motivo": "Motivo"},
        format="json",
    )
    assert response.status_code == 403


@pytest.mark.django_db
def test_usuario_anonimo_no_puede_crear_t01():
    response = APIClient().post(
        "/api/v1/expedientes/",
        {"tipo_accion": "SANCTION", "puntos": "-1.00", "motivo": "Motivo"},
        format="json",
    )
    assert response.status_code == 401


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("tipo_accion", "puntos"),
    [("SANCTION", "0"), ("SANCTION", "1.00"), ("MERIT", "0"), ("MERIT", "-1.00")],
)
def test_puntos_deben_respetar_signo_de_la_accion(expediente_client, tipo_accion, puntos):
    response = expediente_client.post(
        "/api/v1/expedientes/",
        {"tipo_accion": tipo_accion, "puntos": puntos, "motivo": "Motivo"},
        format="json",
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_solicitante_no_puede_acceder_a_borrador_ajeno(expediente_client, make_socio):
    data = create_draft(expediente_client).data
    otro = make_socio(legajo="41002", role=Role.CD)
    otro_client = APIClient()
    login = otro_client.post(
        "/api/v1/auth/login/",
        {"identifier": otro.legajo, "password": "Aveit-Test-2026!"},
        format="json",
    )
    otro_client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")
    response = otro_client.patch(
        f"/api/v1/expedientes/{data['id']}/", {"motivo": "Cambio"}, format="json"
    )
    assert response.status_code == 404
    response = otro_client.get(f"/api/v1/expedientes/{data['id']}/")
    assert response.status_code == 404
    response = otro_client.post(f"/api/v1/expedientes/{data['id']}/emitir/", {}, format="json")
    assert response.status_code == 404


@pytest.mark.django_db
def test_uuid_inexistente_devuelve_404(expediente_client):
    missing = "00000000-0000-0000-0000-000000000000"
    assert expediente_client.get(f"/api/v1/expedientes/{missing}/").status_code == 404
    assert expediente_client.post(f"/api/v1/expedientes/{missing}/emitir/").status_code == 404


@pytest.mark.django_db
def test_borrador_se_puede_borrar(expediente_client):
    data = create_draft(expediente_client).data
    solicitud = SolicitudT01.objects.get(pk=data["id"])
    solicitud.delete()
    assert not SolicitudT01.objects.filter(pk=data["id"]).exists()


@pytest.mark.django_db
def test_borrador_persiste_titulo_razon_y_reglamentos(expediente_client):
    response = expediente_client.post(
        "/api/v1/expedientes/",
        {
            "tipo_accion": "SANCTION",
            "puntos": "-1.00",
            "titulo": "Título de prueba",
            "razon": "Razón de prueba",
            "reglamentos_respaldantes": ["Estatuto AVEIT Reforma 2026"],
        },
        format="json",
    )
    assert response.status_code == 201
    solicitud = SolicitudT01.objects.get(pk=response.data["id"])
    assert solicitud.titulo == "Título de prueba"
    assert solicitud.razon == "Razón de prueba"
    assert solicitud.reglamentos_respaldantes == ["Estatuto AVEIT Reforma 2026"]


@pytest.mark.django_db
def test_endpoint_reglamentos_vigentes(expediente_client):
    response = expediente_client.get("/api/v1/expedientes/reglamentos/")
    assert response.status_code == 200
    assert response.data["reglamentos"] == [
        "Estatuto AVEIT Reforma 2026",
        "Reglamento Procesal Disciplinario 2026",
        "Reglamento Interno de Disciplina",
    ]


@pytest.mark.django_db
def test_emitida_no_se_puede_borrar(padron_repo, expediente_client):
    data = create_draft(expediente_client, destinatario_socio_id=9001).data
    response = expediente_client.post(
        f"/api/v1/expedientes/{data['id']}/emitir/", {}, format="json"
    )
    assert response.status_code == 200
    solicitud = SolicitudT01.objects.get(pk=data["id"])
    with pytest.raises(ValidationError, match="inmutable"):
        solicitud.delete()
