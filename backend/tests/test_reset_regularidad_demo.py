from datetime import datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

import pytest
from django.core.management import call_command
from django.utils import timezone

from core.services.demo_reset_service import (
    DEMO_PASSWORD,
    _compute_event_dates,
    reset_regularidad_database,
)
from expedientes.domain.calendar import compute_business_deadline
from expedientes.domain.holiday_provider import Argentina2026HolidayProvider
from expedientes.models import (
    AsientoLibroMayor,
    AsistenciaEvento,
    AtencionFelicitacion,
    EstadoAsistenciaEventoEnum,
    EstadoEventoEnum,
    EstadoExpedienteEnum,
    EstadoResolucionEnum,
    EventoConvocado,
    EventoInstitucional,
    Expediente,
    Resolucion,
)
from expedientes.services.meeting_compliance_service import MeetingComplianceService
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


@pytest.mark.django_db
def test_reset_regularidad_database_prepara_flujo_1_y_procesar_cierre_abre_expedientes(
    api_client, authenticate
):
    result = reset_regularidad_database()

    assert result["expedientes"] == ["EXP-0001/2026", "EXP-0002/2026"]
    assert Expediente.objects.count() == 2
    assert EventoInstitucional.objects.count() == 1

    evento = EventoInstitucional.objects.get(pk=result["evento_id"])
    assert evento.titulo == "Reunión Ordinaria de Seguimiento - Cómputos y CD"
    assert evento.responsable.legajo == "87414"
    assert evento.estado == EstadoEventoEnum.NOTIFICADO
    assert evento.es_obligatoria is True
    assert evento.es_sancionable is True

    ahora = timezone.now()
    assert evento.fecha_fin is not None
    assert evento.fecha_fin < ahora
    assert MeetingComplianceService.validate_notice_period(
        fecha_publicacion=evento.fecha_publicacion,
        fecha_programada=evento.fecha_programada,
    ) == (True, None)
    assert MeetingComplianceService.validate_reporting_deadline(
        fecha_reporte=ahora,
        fecha_fin=evento.fecha_fin,
        fecha_programada=evento.fecha_programada,
    ) == (True, None)

    convocados_legajos = set(
        EventoConvocado.objects.filter(evento=evento).values_list("socio__legajo", flat=True)
    )
    assert convocados_legajos == {"74907", "770013", "770005", "770008"}

    asistencias = {
        a.socio.legajo: a
        for a in AsistenciaEvento.objects.filter(evento=evento).select_related("socio")
    }
    assert set(asistencias.keys()) == {"74907", "770013", "770005", "770008"}
    assert all(not a.procesado_disciplinario for a in asistencias.values())
    assert all(a.expediente_generado_id is None for a in asistencias.values())
    assert asistencias["74907"].estado_asistencia == EstadoAsistenciaEventoEnum.AUSENTE
    assert asistencias["770013"].estado_asistencia == EstadoAsistenciaEventoEnum.TARDE_LEVE
    assert asistencias["770013"].minutos_tardanza == 22
    assert asistencias["770005"].estado_asistencia == EstadoAsistenciaEventoEnum.PRESENTE
    assert asistencias["770008"].estado_asistencia == EstadoAsistenciaEventoEnum.PRESENTE

    assert AtencionFelicitacion.objects.get(socio__legajo="770013").llamadosAtencion == 2
    assert AtencionFelicitacion.objects.get(socio__legajo="74907").llamadosAtencion == 0

    cd_user = Socio.objects.get(legajo="87414")
    client = authenticate(cd_user, password=DEMO_PASSWORD)
    resp = client.post(
        f"/api/v1/expedientes/eventos/{evento.id}/procesar-asistencias/",
        {},
        format="json",
    )
    assert resp.status_code == 200, resp.data
    assert resp.data["estado_evento"] == EstadoEventoEnum.FINALIZADO
    assert resp.data["es_sancionable"] is True
    assert resp.data["expedientes_generados"] == 2
    assert resp.data["apercibimientos_generados"] == 1

    evento.refresh_from_db()
    assert evento.estado == EstadoEventoEnum.FINALIZADO

    asist_lucas = AsistenciaEvento.objects.get(evento=evento, socio__legajo="74907")
    asist_malena = AsistenciaEvento.objects.get(evento=evento, socio__legajo="770013")
    asist_elena = AsistenciaEvento.objects.get(evento=evento, socio__legajo="770005")
    asist_hector = AsistenciaEvento.objects.get(evento=evento, socio__legajo="770008")

    assert asist_lucas.procesado_disciplinario is True
    assert asist_malena.procesado_disciplinario is True
    assert asist_elena.procesado_disciplinario is True
    assert asist_hector.procesado_disciplinario is True

    assert asist_lucas.expediente_generado is not None
    assert asist_lucas.expediente_generado.estado == EstadoExpedienteEnum.CREADO
    assert asist_lucas.expediente_generado.puntos == Decimal("-1.00")

    assert asist_malena.expediente_generado is not None
    assert asist_malena.expediente_generado.estado == EstadoExpedienteEnum.CREADO
    assert asist_malena.expediente_generado.puntos == Decimal("-1.00")
    assert "3:1" in asist_malena.expediente_generado.motivo
    assert AtencionFelicitacion.objects.get(socio__legajo="770013").llamadosAtencion == 0

    assert asist_elena.expediente_generado is None
    assert asist_hector.expediente_generado is None


@pytest.mark.parametrize(
    "now_iso",
    [
        "2026-11-23T20:50:00-03:00",  # Feriado lunes 23/11
        "2026-11-22T15:00:00-03:00",  # Domingo
        "2026-02-17T12:00:00-03:00",  # Carnaval martes (después de lunes feriado)
        "2026-11-24T09:00:00-03:00",  # Día hábil siguiente a un feriado
    ],
)
def test_compute_event_dates_cumple_plazos_en_feriados_y_fines_de_semana(now_iso):
    provider = Argentina2026HolidayProvider()
    tz = ZoneInfo("America/Argentina/Buenos_Aires")
    now = datetime.fromisoformat(now_iso).astimezone(tz)

    fecha_pub, fecha_prog, fecha_fin = _compute_event_dates(now=now, holiday_provider=provider)

    assert fecha_pub < fecha_prog < fecha_fin < now
    assert fecha_prog.date().weekday() < 5
    assert not provider.is_holiday(fecha_prog.date())
    assert compute_business_deadline(fecha_pub, 2, provider) <= fecha_prog
    assert compute_business_deadline(fecha_fin, 3, provider) > now
