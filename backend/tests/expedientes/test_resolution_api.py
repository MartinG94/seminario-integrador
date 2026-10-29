from decimal import Decimal

import pytest

from expedientes.models import EstadoResolucionEnum, Resolucion
from socios.models import Role


def resolution_url(expediente_id: int) -> str:
    return f"/api/v1/expedientes/{expediente_id}/resolucion/"


def emit_url(expediente_id: int) -> str:
    return f"{resolution_url(expediente_id)}emitir/"


def draft_payload() -> dict:
    return {
        "expediente": 999999,
        "plantilla_version": "resolucion-2026.1",
        "estado": "ISSUED",
        "numero_expediente_snapshot": "FORZADO",
        "vistos": "Vistos el expediente.",
        "considerandos": "Considerando la prueba.",
        "articulos_resolutivos": "Artículo 1: aplicar la medida.",
        "puntos_finales": "99.99",
        "medidas": ["medida impuesta por cliente"],
        "issued_by": 999999,
        "issued_at": "2026-01-01T00:00:00Z",
        "contenido_hash": "forzado",
    }


@pytest.mark.django_db
def test_resolucion_requiere_autenticacion(api_client, causal_expediente):
    assert api_client.get(resolution_url(causal_expediente.pk)).status_code == 401
    assert (
        api_client.post(resolution_url(causal_expediente.pk), {}, format="json").status_code
        == 401
    )
    assert (
        api_client.patch(resolution_url(causal_expediente.pk), {}, format="json").status_code
        == 401
    )
    assert api_client.post(emit_url(causal_expediente.pk), {}, format="json").status_code == 401


@pytest.mark.django_db
def test_resolucion_rechaza_usuario_sin_permiso(make_socio, authenticate, causal_expediente):
    socio = make_socio(legajo="76099", role=Role.SOCIO)
    client = authenticate(socio)
    for method in (client.get, client.post, client.patch):
        response = method(resolution_url(causal_expediente.pk), {}, format="json")
        assert response.status_code == 403
    assert client.post(emit_url(causal_expediente.pk), {}, format="json").status_code == 403


@pytest.mark.django_db
def test_creacion_toma_expediente_de_la_url_y_no_acepta_campos_derivados(
    causal_expediente, causal_vocal, authenticate
):
    client = authenticate(causal_vocal)
    response = client.post(
        resolution_url(causal_expediente.pk), draft_payload(), format="json"
    )

    assert response.status_code == 201, response.data
    resolucion = Resolucion.objects.get(pk=response.data["id"])
    assert resolucion.expediente_id == causal_expediente.pk
    assert resolucion.estado == EstadoResolucionEnum.DRAFT
    assert resolucion.puntos_finales is None
    assert resolucion.medidas == []
    assert resolucion.issued_by_id is None
    assert resolucion.issued_at is None
    assert resolucion.contenido_hash == ""
    assert resolucion.numero_expediente_snapshot == causal_expediente.numero


@pytest.mark.django_db
def test_creacion_rechaza_segunda_resolucion_para_el_mismo_expediente(
    causal_expediente, causal_vocal, authenticate
):
    client = authenticate(causal_vocal)
    payload = draft_payload()
    first_response = client.post(
        resolution_url(causal_expediente.pk), payload, format="json"
    )
    assert first_response.status_code == 201

    second_response = client.post(
        resolution_url(causal_expediente.pk), payload, format="json"
    )

    assert second_response.status_code == 409
    assert Resolucion.objects.filter(expediente=causal_expediente).count() == 1


@pytest.mark.django_db
def test_get_devuelve_la_version_mas_reciente(causal_expediente, causal_vocal, authenticate):
    Resolucion.objects.create(
        expediente=causal_expediente,
        version=1,
        plantilla_version="v1",
        numero_expediente_snapshot=causal_expediente.numero,
        created_by=causal_vocal.user,
    )
    latest = Resolucion.objects.create(
        expediente=causal_expediente,
        version=2,
        plantilla_version="v2",
        numero_expediente_snapshot=causal_expediente.numero,
        created_by=causal_vocal.user,
    )
    response = authenticate(causal_vocal).get(resolution_url(causal_expediente.pk))
    assert response.status_code == 200
    assert response.data["id"] == latest.id
    assert response.data["version"] == 2


@pytest.mark.django_db
def test_patch_modifica_la_version_mas_reciente(causal_expediente, causal_vocal, authenticate):
    Resolucion.objects.create(
        expediente=causal_expediente,
        version=1,
        plantilla_version="v1",
        numero_expediente_snapshot=causal_expediente.numero,
        created_by=causal_vocal.user,
    )
    latest = Resolucion.objects.create(
        expediente=causal_expediente,
        version=2,
        plantilla_version="v2",
        numero_expediente_snapshot=causal_expediente.numero,
        created_by=causal_vocal.user,
    )
    response = authenticate(causal_vocal).patch(
        resolution_url(causal_expediente.pk), {"vistos": "Vistos actualizados."}, format="json"
    )
    assert response.status_code == 200
    latest.refresh_from_db()
    assert latest.vistos == "Vistos actualizados."


@pytest.mark.django_db
def test_patch_no_modifica_resolucion_emitida(causal_expediente, causal_vocal, authenticate):
    resolucion = Resolucion.objects.create(
        expediente=causal_expediente,
        plantilla_version="v1",
        estado=EstadoResolucionEnum.ISSUED,
        numero_expediente_snapshot=causal_expediente.numero,
        puntos_finales=Decimal("-2.00"),
        created_by=causal_vocal.user,
        issued_by=causal_vocal.user,
    )
    response = authenticate(causal_vocal).patch(
        resolution_url(causal_expediente.pk), {"vistos": "Cambio no permitido."}, format="json"
    )
    assert response.status_code in (400, 409)
    resolucion.refresh_from_db()
    assert resolucion.vistos == ""


@pytest.mark.django_db
def test_emision_sin_dictamen_cerrado_devuelve_error_controlado(
    causal_expediente, causal_vocal, authenticate
):
    Resolucion.objects.create(
        expediente=causal_expediente,
        plantilla_version="v1",
        numero_expediente_snapshot=causal_expediente.numero,
        vistos="Vistos.",
        considerandos="Considerandos.",
        articulos_resolutivos="Artículo 1.",
        created_by=causal_vocal.user,
    )
    response = authenticate(causal_vocal).post(
        emit_url(causal_expediente.pk), {}, format="json"
    )
    assert response.status_code == 400
    assert "dictamen" in response.data


@pytest.mark.django_db
def test_emision_selecciona_la_version_mas_reciente(
    causal_expediente, causal_vocal, authenticate, monkeypatch
):
    Resolucion.objects.create(
        expediente=causal_expediente,
        version=1,
        plantilla_version="v1",
        numero_expediente_snapshot=causal_expediente.numero,
        created_by=causal_vocal.user,
    )
    latest = Resolucion.objects.create(
        expediente=causal_expediente,
        version=2,
        plantilla_version="v2",
        numero_expediente_snapshot=causal_expediente.numero,
        created_by=causal_vocal.user,
    )
    selected = {}

    def fake_emitir(resolucion, emisor, provider):
        selected["id"] = resolucion.id
        return resolucion

    monkeypatch.setattr("expedientes.resolution_views.emitir_resolucion", fake_emitir)
    response = authenticate(causal_vocal).post(
        emit_url(causal_expediente.pk), {}, format="json"
    )

    assert response.status_code == 200
    assert selected["id"] == latest.id
