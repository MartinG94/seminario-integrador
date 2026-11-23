from decimal import Decimal

import pytest
from django.core.management import call_command

from core.services.demo_reset_service import DEMO_PASSWORD, reset_regularidad_database
from expedientes.models import (
    AsientoLibroMayor,
    EstadoExpedienteEnum,
    EstadoResolucionEnum,
    Expediente,
    Resolucion,
)
from ranking.models import PuntajeAplicado
from socios.models import Socio


@pytest.mark.django_db
def test_reset_regularidad_database_crea_exactamente_2_expedientes_limpios(make_socio):
    otro = make_socio(legajo="99001", numero_socio=99001)
    Expediente.objects.create(
        numero="EXP-9999/2026",
        socio=otro,
        motivo="Expediente previo a limpiar",
        puntos=Decimal("-2.00"),
        estado=EstadoExpedienteEnum.CREADO,
    )

    result = reset_regularidad_database()

    assert result["expedientes"] == ["EXP-0001/2026", "EXP-0002/2026"]
    numeros = list(Expediente.objects.order_by("numero").values_list("numero", flat=True))
    assert numeros == ["EXP-0001/2026", "EXP-0002/2026"]

    exp1 = Expediente.objects.get(numero="EXP-0001/2026")
    assert exp1.estado == EstadoExpedienteEnum.REVISION_RESOLUCION
    assert exp1.concepto == "GSA"
    assert exp1.puntos == Decimal("-1.00")
    assert exp1.socio.legajo == "74907"
    assert exp1.descargos.count() == 1
    assert exp1.decisiones_causal.count() == 1

    exp2 = Expediente.objects.get(numero="EXP-0002/2026")
    assert exp2.estado == EstadoExpedienteEnum.PENDIENTE_CORREOS
    assert exp2.concepto == "GSA"
    assert exp2.puntos == Decimal("-1.00")
    assert exp2.socio.legajo == "74907"
    res2 = exp2.resoluciones.get()
    assert res2.estado == EstadoResolucionEnum.DRAFT
    assert len(res2.firmantes) == 2
    assert {f["social_year"] for f in res2.firmantes} == {4, 5}


@pytest.mark.django_db
def test_exp1_tiene_descargo_leido_y_exp2_emite_al_firmar_408917(
    api_client, authenticate, settings
):
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    reset_regularidad_database()

    td_408917 = Socio.objects.get(legajo="408917")
    exp1 = Expediente.objects.get(numero="EXP-0001/2026")
    exp2 = Expediente.objects.get(numero="EXP-0002/2026")

    client = authenticate(td_408917, password=DEMO_PASSWORD)

    # Verificar que EXP-0001/2026 expone el descargo como leído para TD
    detail_resp = client.get(f"/api/v1/expedientes/{exp1.pk}/")
    assert detail_resp.status_code == 200
    assert detail_resp.data["descargos"][0]["leido"] is True

    # Firmar EXP-0002/2026 como 408917 (3ra firma, año social 6) -> pasa a emitido
    sign_resp = client.post(f"/api/v1/expedientes/{exp2.pk}/resolucion/firmar/", {}, format="json")
    assert sign_resp.status_code == 200, sign_resp.data
    assert sign_resp.data["estado"] == EstadoResolucionEnum.ISSUED
    assert len(sign_resp.data["firmantes_td"]) == 3

    exp2.refresh_from_db()
    assert exp2.estado == EstadoExpedienteEnum.EMITIDO

    res2 = Resolucion.objects.get(expediente=exp2)
    assert res2.estado == EstadoResolucionEnum.ISSUED
    assert AsientoLibroMayor.objects.filter(expediente=exp2, socio__legajo="74907").exists()
    assert PuntajeAplicado.objects.filter(expediente_id=exp2.pk, socio_id=74907).exists()


@pytest.mark.django_db
def test_endpoint_reset_demo_db_respeta_debug_y_es_idempotente(api_client, settings):
    settings.DEBUG = False
    resp_forbidden = api_client.post("/api/v1/auth/reset-demo-db/", {}, format="json")
    assert resp_forbidden.status_code == 403

    settings.DEBUG = True
    resp_ok_1 = api_client.post("/api/v1/auth/reset-demo-db/", {}, format="json")
    assert resp_ok_1.status_code == 200
    assert resp_ok_1.data["expedientes"] == ["EXP-0001/2026", "EXP-0002/2026"]

    # Segundo reset consecutivo (incluso tras emitir EXP-0002/2026) debe funcionar sin errores
    exp2 = Expediente.objects.get(numero="EXP-0002/2026")
    td_408917 = Socio.objects.get(legajo="408917")
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    api_client.post(
        "/api/v1/auth/login/",
        {"identifier": td_408917.legajo},
        format="json",
    )
    from expedientes.services.resolution_service import registrar_firma_resolucion

    registrar_firma_resolucion(exp2.resoluciones.get(), td_408917.user)
    exp2.refresh_from_db()
    assert exp2.estado == EstadoExpedienteEnum.EMITIDO

    resp_ok_2 = api_client.post("/api/v1/auth/reset-demo-db/", {}, format="json")
    assert resp_ok_2.status_code == 200
    assert list(Expediente.objects.order_by("numero").values_list("numero", flat=True)) == [
        "EXP-0001/2026",
        "EXP-0002/2026",
    ]


@pytest.mark.django_db
def test_comando_reset_regularidad_demo(capsys):
    call_command("reset_regularidad_demo")
    assert Expediente.objects.count() == 2
