from decimal import Decimal

import pytest

from expedientes.models import EstadoResolucionEnum, Resolucion
from socios.models import Role


def resolution_url(expediente_id: int) -> str:
    return f"/api/v1/expedientes/{expediente_id}/resolucion/"


def emit_url(expediente_id: int) -> str:
    return f"{resolution_url(expediente_id)}emitir/"


def sign_url(expediente_id: int) -> str:
    return f"{resolution_url(expediente_id)}firmar/"


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
        api_client.post(resolution_url(causal_expediente.pk), {}, format="json").status_code == 401
    )
    assert (
        api_client.patch(resolution_url(causal_expediente.pk), {}, format="json").status_code == 401
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
    response = client.post(resolution_url(causal_expediente.pk), draft_payload(), format="json")

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
    first_response = client.post(resolution_url(causal_expediente.pk), payload, format="json")
    assert first_response.status_code == 201

    second_response = client.post(resolution_url(causal_expediente.pk), payload, format="json")

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
    causal_expediente.estado = "creado"
    causal_expediente.save(update_fields=["estado"])
    Resolucion.objects.create(
        expediente=causal_expediente,
        plantilla_version="v1",
        numero_expediente_snapshot=causal_expediente.numero,
        vistos="Vistos.",
        considerandos="Considerandos.",
        articulos_resolutivos="Artículo 1.",
        created_by=causal_vocal.user,
    )
    response = authenticate(causal_vocal).post(emit_url(causal_expediente.pk), {}, format="json")
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
    response = authenticate(causal_vocal).post(emit_url(causal_expediente.pk), {}, format="json")

    assert response.status_code == 200
    assert selected["id"] == latest.id


@pytest.mark.django_db
def test_resolucion_serializer_campos_identificador_y_firmantes(
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
    response = authenticate(causal_vocal).get(resolution_url(causal_expediente.pk))
    assert response.status_code == 200
    assert (
        response.data["identificador_resolucion"]
        == f"RESOLUCIÓN {causal_expediente.numero.replace('EXP-', '')}"
    )
    assert isinstance(response.data["firmantes_td"], list)
    assert response.data["firmantes_td"] == []


@pytest.mark.django_db
def test_emision_end_to_end_con_consolidated_decision_provider(
    causal_expediente, causal_vocal, authenticate
):
    causal_expediente.estado = "espera_resolucion"
    causal_expediente.puntos = Decimal("-3.00")
    causal_expediente.save()

    Resolucion.objects.create(
        expediente=causal_expediente,
        plantilla_version="v1",
        numero_expediente_snapshot=causal_expediente.numero,
        vistos="Vistos de prueba.",
        considerandos="Considerandos de prueba.",
        articulos_resolutivos="Artículo 1: sanción.",
        created_by=causal_vocal.user,
    )
    response = authenticate(causal_vocal).post(emit_url(causal_expediente.pk), {}, format="json")
    assert response.status_code == 200
    assert response.data["estado"] == "ISSUED"
    assert Decimal(str(response.data["puntos_finales"])) == Decimal("-3.00")
    assert (
        response.data["identificador_resolucion"]
        == f"RESOLUCIÓN {causal_expediente.numero.replace('EXP-', '')}"
    )
    assert response.data["firmantes_td"] == []


@pytest.mark.django_db
def test_creacion_resolucion_persiste_estado_pendiente_correos(
    causal_expediente, causal_vocal, authenticate
):
    causal_expediente.estado = "revision_resolucion"
    causal_expediente.save()

    client = authenticate(causal_vocal)
    payload = draft_payload()
    response = client.post(resolution_url(causal_expediente.pk), payload, format="json")
    assert response.status_code == 201

    causal_expediente.refresh_from_db()
    assert causal_expediente.estado == "pendiente_correos"
    cambio = causal_expediente.cambios_estado.first()
    assert cambio.estado_nuevo == "pendiente_correos"


@pytest.mark.django_db
def test_firmar_resolucion_endpoint_agrega_firma_y_emite_al_completar(
    causal_expediente, make_socio, authenticate
):
    causal_expediente.estado = "pendiente_correos"
    causal_expediente.puntos = Decimal("-2.50")
    causal_expediente.save()

    s4 = make_socio(legajo="40101", role=Role.TD, social_year=4)
    s5 = make_socio(legajo="50101", role=Role.TD, social_year=5)
    s6 = make_socio(legajo="60101", role=Role.TD, social_year=6)

    # Crear resolución borrador
    Resolucion.objects.create(
        expediente=causal_expediente,
        plantilla_version="v1",
        numero_expediente_snapshot=causal_expediente.numero,
        vistos="Vistos de prueba.",
        considerandos="Considerandos de prueba.",
        articulos_resolutivos="Artículo 1: sanción.",
        created_by=s4.user,
    )

    # 1. Firma socio de 4.° año
    client4 = authenticate(s4)
    res4 = client4.post(sign_url(causal_expediente.pk), {}, format="json")
    assert res4.status_code == 200
    assert len(res4.data["firmantes_td"]) == 1
    assert res4.data["estado"] == "DRAFT"

    # Intento de firmar nuevamente con el mismo usuario debe dar 400
    res4_dup = client4.post(sign_url(causal_expediente.pk), {}, format="json")
    assert res4_dup.status_code == 400

    # 2. Firma socio de 5.° año
    client5 = authenticate(s5)
    res5 = client5.post(sign_url(causal_expediente.pk), {}, format="json")
    assert res5.status_code == 200
    assert len(res5.data["firmantes_td"]) == 2
    assert res5.data["estado"] == "DRAFT"

    # 3. Firma socio de 6.° año -> emite automáticamente
    client6 = authenticate(s6)
    res6 = client6.post(sign_url(causal_expediente.pk), {}, format="json")
    assert res6.status_code == 200
    assert len(res6.data["firmantes_td"]) == 3
    assert res6.data["estado"] == "ISSUED"

    causal_expediente.refresh_from_db()
    assert causal_expediente.estado == "emitido"


@pytest.mark.django_db
def test_expediente_list_serializer_expone_datos_resolucion(causal_expediente, causal_vocal):
    from expedientes.serializers import ExpedienteListSerializer

    Resolucion.objects.create(
        expediente=causal_expediente,
        plantilla_version="v1",
        numero_expediente_snapshot=causal_expediente.numero,
        vistos="Vistos serializados.",
        considerandos="Considerandos serializados.",
        articulos_resolutivos="Artículos serializados.",
        firmantes=[{"social_year": 4, "etiqueta": "40001 - Ana Perez - G60"}],
        created_by=causal_vocal.user,
    )

    data = ExpedienteListSerializer(causal_expediente).data
    assert data["resolucion_estado"] == "DRAFT"
    assert len(data["firmantes_td"]) == 1
    assert data["vistos"] == "Vistos serializados."
    assert data["considerandos"] == "Considerandos serializados."
    assert data["articulos_resolutivos"] == "Artículos serializados."


@pytest.mark.django_db
def test_creacion_resolucion_sin_plantilla_version_usa_default(
    causal_expediente, causal_vocal, authenticate
):
    causal_expediente.estado = "revision_resolucion"
    causal_expediente.save()

    client = authenticate(causal_vocal)
    payload = {
        "vistos": "Vistos de prueba.",
        "considerandos": "Considerando de prueba.",
        "articulos_resolutivos": "Artículo 1: medida.",
    }
    response = client.post(resolution_url(causal_expediente.pk), payload, format="json")
    assert response.status_code == 201
    assert response.data["plantilla_version"] == "v1"

    causal_expediente.refresh_from_db()
    assert causal_expediente.estado == "pendiente_correos"

    resp_board = client.get("/api/v1/expedientes/board/")
    assert resp_board.status_code == 200
    pendientes = next(
        col["cases"] for col in resp_board.data["columns"] if col["key"] == "pendiente_correos"
    )
    caso = next(c for c in pendientes if c["id"] == causal_expediente.pk)
    assert caso["resolucion_estado"] == "DRAFT"
    assert caso["vistos"] == "Vistos de prueba."
    assert caso["considerandos"] == "Considerando de prueba."
    assert caso["articulos_resolutivos"] == "Artículo 1: medida."


@pytest.mark.django_db
def test_creacion_resolucion_guarda_reglamentos_respaldantes_y_los_expone(
    causal_expediente, causal_vocal, authenticate
):
    from expedientes.serializers import ExpedienteListSerializer

    causal_expediente.estado = "revision_resolucion"
    causal_expediente.save()

    client = authenticate(causal_vocal)
    reglamentos = [
        "Reglamento Procesal Disciplinario 2026, Art. 12",
        "Estatuto Social A.V.E.I.T. - Art. 15",
    ]
    payload = {
        "vistos": "Vistos con citas.",
        "considerandos": "Considerando específico del TD.",
        "articulos_resolutivos": "Artículo 1: medida.",
        "reglamentos_respaldantes": reglamentos,
    }
    response = client.post(resolution_url(causal_expediente.pk), payload, format="json")
    assert response.status_code == 201
    assert response.data["reglamentos_respaldantes"] == reglamentos

    resolucion = Resolucion.objects.get(expediente=causal_expediente)
    assert resolucion.reglamentos_respaldantes == reglamentos

    # Validar que ExpedienteListSerializer expone los reglamentos de la resolución
    causal_expediente.refresh_from_db()
    data = ExpedienteListSerializer(causal_expediente).data
    assert data["reglamentos_respaldantes"] == reglamentos
    assert data["reglamento_asociado"] == reglamentos[0]
    assert data["considerandos"] == "Considerando específico del TD."
