import socket
from decimal import Decimal
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from django.core.management import call_command
from rest_framework.test import APIRequestFactory

from core.services.demo_reset_service import (
    _drop_legacy_asistente_fk_if_exists,
    get_snapshot_path,
    reset_regularidad_database,
    seed_presentation_mocks,
    split_sql_statements,
)
from expedientes.models import (
    AsientoLibroMayor,
    AsistenciaEvento,
    AtencionFelicitacion,
    ComposicionTribunal,
    ConceptoExpedienteEnum,
    DecisionCausalDescargo,
    DecisionCausalEnum,
    DescargoExpediente,
    EstadoAsistenciaEventoEnum,
    EstadoEventoEnum,
    EstadoExpedienteEnum,
    EstadoResolucionEnum,
    EventoConvocado,
    EventoInstitucional,
    Expediente,
    ExpedienteNumberSequence,
    Resolucion,
    TipoDescargoEnum,
)
from expedientes.serializers import ExpedienteListSerializer
from expedientes.services.attendance_processing_service import AttendanceProcessingService
from expedientes.services.ledger_service import LedgerService
from expedientes.services.meeting_compliance_service import MeetingComplianceService
from expedientes.services.resolution_service import registrar_firma_resolucion
from ranking.models import PuntajeAplicado
from socios.models import Role, Socio


def test_split_sql_statements_maneja_binarios_escapes_y_comentarios():
    raw = (
        b"-- Comentario con ; punto y coma\n"
        b"/*!40101 SET NAMES utf8mb4 */;\n"
        b"INSERT INTO docs VALUES ('texto; con \\'escape\\'; y \\\\', "
        b"_binary '%PDF-1.5\\r\\n%\xb5\xb5');\n"
        b"/* comentario bloque ; */\n"
        b"UNLOCK TABLES;\n"
        b"-- Dump completed\n"
    )
    stmts = split_sql_statements(raw)
    assert len(stmts) == 4
    assert stmts[0].endswith(b"/*!40101 SET NAMES utf8mb4 */")
    assert b"_binary '%PDF-1.5\\r\\n%\xb5\xb5'" in stmts[1]
    assert stmts[2] == b"/* comentario bloque ; */\nUNLOCK TABLES"
    assert stmts[3] == b"-- Dump completed"


def test_reset_regularidad_database_falla_si_no_existe_snapshot(tmp_path):
    missing = tmp_path / "inexistente.sql"
    with pytest.raises(FileNotFoundError):
        reset_regularidad_database(snapshot_path=missing)


def test_reset_regularidad_database_omite_use_y_create_database_y_restaura_en_mysql(tmp_path):
    dump_file = tmp_path / "snapshot.sql"
    dump_file.write_bytes(
        b"-- Header\n"
        b"CREATE DATABASE `aveit_tribunal_dev`;\n"
        b"USE `aveit_tribunal_dev`;\n"
        b"DROP TABLE IF EXISTS `t`;\n"
        b"CREATE TABLE `t` (`id` INT PRIMARY KEY);\n"
        b"INSERT INTO `t` VALUES (1);\n"
        b"-- Dump completed\n"
    )

    mock_cursor = MagicMock()
    mock_cm = MagicMock()
    mock_cm.__enter__.return_value = mock_cursor
    mock_cm.__exit__.return_value = False

    with (
        patch("core.services.demo_reset_service.connection") as mock_conn,
        patch("core.services.demo_reset_service.Expediente") as mock_exp,
        patch("core.services.demo_reset_service._drop_legacy_asistente_fk_if_exists") as mock_drop,
        patch(
            "core.services.demo_reset_service.seed_presentation_mocks",
            return_value={
                "mock_expedientes": ["7707/2026", "7708/2026"],
                "evento_id": 10,
                "evento_titulo": "Reunión Ordinaria de Seguimiento - Cómputos y CD",
            },
        ) as mock_seed,
    ):
        mock_conn.vendor = "mysql"
        mock_conn.cursor.return_value = mock_cm
        mock_exp.objects.order_by.return_value.values_list.return_value = [
            "EXP-0001/2026",
            "EXP-0002/2026",
            "7707/2026",
            "7708/2026",
        ]

        result = reset_regularidad_database(snapshot_path=dump_file)

    executed_sqls = [call.args[0] for call in mock_cursor.execute.call_args_list]
    assert executed_sqls == [
        b"DROP TABLE IF EXISTS `t`",
        b"CREATE TABLE `t` (`id` INT PRIMARY KEY)",
        b"INSERT INTO `t` VALUES (1)",
        "SET FOREIGN_KEY_CHECKS = 1;",
    ]
    mock_drop.assert_called_once_with(mock_cursor)
    mock_seed.assert_called_once_with()
    assert result["statements_executed"] == 3
    assert result["expedientes"] == ["EXP-0001/2026", "EXP-0002/2026", "7707/2026", "7708/2026"]
    assert result["mock_expedientes"] == ["7707/2026", "7708/2026"]
    assert result["evento_id"] == 10


def test_drop_legacy_asistente_fk_if_exists_elimina_fk_solo_cuando_existe():
    cursor_present = MagicMock()
    cursor_present.fetchone.return_value = ("fk_asistente_socio",)
    assert _drop_legacy_asistente_fk_if_exists(cursor_present) is True
    assert cursor_present.execute.call_count == 2
    assert (
        "ALTER TABLE tribunal_asistente DROP FOREIGN KEY fk_asistente_socio;"
        in cursor_present.execute.call_args_list[1].args[0]
    )

    cursor_absent = MagicMock()
    cursor_absent.fetchone.return_value = None
    assert _drop_legacy_asistente_fk_if_exists(cursor_absent) is False
    assert cursor_absent.execute.call_count == 1


@pytest.mark.django_db
def test_endpoint_reset_demo_db_respeta_debug_y_retorna_snapshot_regularidad(api_client, settings):
    settings.DEBUG = False
    resp_forbidden = api_client.post("/api/v1/auth/reset-demo-db/", {}, format="json")
    assert resp_forbidden.status_code == 403

    settings.DEBUG = True
    with patch(
        "accounts.views.reset_regularidad_database",
        return_value={
            "snapshot": "/database/snapshot_regularidad.sql",
            "statements_executed": 944,
            "expedientes": ["EXP-0001/2026", "EXP-0002/2026"],
        },
    ) as mock_reset:
        resp_ok = api_client.post("/api/v1/auth/reset-demo-db/", {}, format="json")

    assert resp_ok.status_code == 200
    assert resp_ok.data["detail"] == "Base de datos restaurada al snapshot inicial de Regularidad."
    assert resp_ok.data["expedientes"] == ["EXP-0001/2026", "EXP-0002/2026"]
    mock_reset.assert_called_once_with()


def test_comando_reset_regularidad_demo(capsys):
    with patch(
        "core.management.commands.reset_regularidad_demo.reset_regularidad_database",
        return_value={
            "snapshot": "/database/snapshot_regularidad.sql",
            "statements_executed": 944,
            "expedientes": ["EXP-0001/2026", "EXP-0002/2026"],
        },
    ):
        call_command("reset_regularidad_demo")

    out = capsys.readouterr().out
    assert "Base de datos restaurada al snapshot de Regularidad." in out
    assert "EXP-0001/2026, EXP-0002/2026" in out


def test_get_snapshot_path_apunta_a_database_snapshot_regularidad(settings):
    path = get_snapshot_path()
    assert path == Path(settings.BASE_DIR).parent / "database" / "snapshot_regularidad.sql"


@pytest.mark.django_db
def test_seed_presentation_mocks_preserva_datos_previos_y_solo_actualiza_lucas_y_malena(
    make_socio,
):
    prev_diego = make_socio(
        legajo="87414",
        role=Role.CD,
        social_year=6,
        email="diego.previo@aveit.test",
        numero_socio=11779,
    )
    prev_otro = make_socio(
        legajo="99999",
        role=Role.SOCIO,
        social_year=3,
        email="otro.previo@aveit.test",
        numero_socio=99999,
    )
    AtencionFelicitacion.objects.create(socio=prev_otro, llamadosAtencion=1, felicitaciones=2)

    ExpedienteNumberSequence.objects.update_or_create(year=2026, defaults={"last_value": 7706})
    prev_exp = Expediente.objects.create(
        numero="7706/2026",
        socio=prev_otro,
        motivo="Expediente previo del snapshot",
        titulo="Expediente Previo",
        puntos=Decimal("-1.00"),
        estado=EstadoExpedienteEnum.EMITIDO,
    )
    from django.utils import timezone

    now = timezone.now()
    prev_evento = EventoInstitucional.objects.create(
        titulo="Evento Previo Snapshot",
        convocante=prev_diego,
        fecha_publicacion=now,
        fecha_programada=now,
        estado=EstadoEventoEnum.FINALIZADO,
    )

    result = seed_presentation_mocks()

    prev_diego.refresh_from_db()
    assert prev_diego.email == "diego.previo@aveit.test"
    assert prev_diego.first_name == "Nombre"

    atencion_otro = AtencionFelicitacion.objects.get(socio=prev_otro)
    assert atencion_otro.llamadosAtencion == 1
    assert atencion_otro.felicitaciones == 2

    atencion_malena = AtencionFelicitacion.objects.get(socio__legajo="770013")
    assert atencion_malena.llamadosAtencion == 2
    assert atencion_malena.felicitaciones == 0

    atencion_lucas = AtencionFelicitacion.objects.get(socio__legajo="74907")
    assert atencion_lucas.llamadosAtencion == 0
    assert atencion_lucas.felicitaciones == 0

    assert Expediente.objects.filter(pk=prev_exp.pk, numero="7706/2026").exists()
    assert EventoInstitucional.objects.filter(
        pk=prev_evento.pk, titulo="Evento Previo Snapshot"
    ).exists()
    assert result["mock_expedientes"] == ["7707/2026", "7708/2026"]
    assert Expediente.objects.count() == 5
    assert EventoInstitucional.objects.count() == 2

    malena = Socio.objects.get(legajo="770013")
    assert malena.numero_socio == 770013
    malena_exps = Expediente.objects.filter(socio=malena).order_by("id")
    assert malena_exps.count() == 2
    assert all(e.estado == EstadoExpedienteEnum.EMITIDO for e in malena_exps)
    assert all(e.puntos == Decimal("0.00") and e.es_llamado for e in malena_exps)
    assert AsientoLibroMayor.objects.filter(socio=malena).count() == 2
    assert LedgerService.verificar_cadena(malena).valida is True
    assert LedgerService.calcular_saldo(malena) == Decimal("0.00")


@pytest.mark.django_db
def test_seed_presentation_mocks_expedientes_en_revision_y_pendiente_firma_408917():
    result = seed_presentation_mocks()
    num_rev, num_firma = result["mock_expedientes"]

    exp_rev = Expediente.objects.get(numero=num_rev)
    assert exp_rev.socio.legajo == "74907"
    assert exp_rev.estado == EstadoExpedienteEnum.REVISION_RESOLUCION
    assert exp_rev.concepto == ConceptoExpedienteEnum.GSA
    assert exp_rev.puntos == Decimal("-1.00")

    descargo = DescargoExpediente.objects.get(expediente=exp_rev, es_vigente=True)
    assert descargo.tipo == TipoDescargoEnum.T02_CERTIFICADO
    decision = DecisionCausalDescargo.objects.get(descargo=descargo, version=1)
    assert decision.decision == DecisionCausalEnum.REJECTED
    assert decision.autor.socio.legajo == "85421"

    esteban = Socio.objects.get(legajo="85421")
    req = APIRequestFactory().get("/")
    req.user = esteban.user
    serialized = ExpedienteListSerializer(
        exp_rev,
        context={"request": req},
    ).data
    assert serialized["descargos"][0]["leido"] is True

    exp_firma = Expediente.objects.get(numero=num_firma)
    assert exp_firma.socio.legajo == "74907"
    assert exp_firma.estado == EstadoExpedienteEnum.PENDIENTE_CORREOS
    assert exp_firma.concepto == ConceptoExpedienteEnum.GSA
    assert ComposicionTribunal.objects.filter(expediente=exp_firma).exists()

    resolucion = Resolucion.objects.get(expediente=exp_firma)
    assert resolucion.estado == EstadoResolucionEnum.DRAFT
    assert [f["social_year"] for f in resolucion.firmantes] == [4, 5]

    nicolas_td = Socio.objects.get(legajo="408917")
    with patch(
        "expedientes.services.resolution_service.EmailDispatcherService.dispatch",
        return_value=True,
    ):
        resolucion_emitida = registrar_firma_resolucion(resolucion, nicolas_td.user)

    exp_firma.refresh_from_db()
    assert resolucion_emitida.estado == EstadoResolucionEnum.ISSUED
    assert len(resolucion_emitida.firmantes) == 3
    assert {f["social_year"] for f in resolucion_emitida.firmantes} == {4, 5, 6}
    assert exp_firma.estado == EstadoExpedienteEnum.EMITIDO
    assert AsientoLibroMayor.objects.filter(
        resolucion=resolucion_emitida, socio__legajo="74907"
    ).exists()
    assert PuntajeAplicado.objects.filter(socio_id=74907, puntajeAplicado=Decimal("-1.00")).exists()


@pytest.mark.django_db
def test_seed_presentation_mocks_evento_flujo1_y_cierre_como_87414():
    result = seed_presentation_mocks()
    evento = EventoInstitucional.objects.get(pk=result["evento_id"])

    assert evento.estado == EstadoEventoEnum.NOTIFICADO
    assert evento.es_obligatoria is True
    assert evento.es_sancionable is True
    assert evento.fecha_programada.weekday() < 5
    cumple_preaviso, _ = MeetingComplianceService.validate_notice_period(
        evento.fecha_publicacion, evento.fecha_programada
    )
    assert cumple_preaviso is True

    assert EventoConvocado.objects.filter(evento=evento).count() == 4
    asistencias = {a.socio.legajo: a for a in AsistenciaEvento.objects.filter(evento=evento)}
    assert set(asistencias.keys()) == {"74907", "770013", "770005", "770008"}
    assert all(not a.procesado_disciplinario for a in asistencias.values())
    assert asistencias["74907"].estado_asistencia == EstadoAsistenciaEventoEnum.AUSENTE
    assert asistencias["770013"].estado_asistencia == EstadoAsistenciaEventoEnum.TARDE_LEVE
    assert asistencias["770013"].minutos_tardanza == 22

    diego_cd = Socio.objects.get(legajo="87414")
    marcaciones = [
        {
            "socio_id": a.socio_id,
            "estado_asistencia": a.estado_asistencia,
            "motivo": a.motivo or "Sin motivo circunstanciado",
            "minutos_tardanza": a.minutos_tardanza,
            "minutos_retiro_anticipado": a.minutos_retiro_anticipado,
            "hora_registro": a.hora_registro.isoformat() if a.hora_registro else None,
            "hora_salida": a.hora_salida.isoformat() if a.hora_salida else None,
            "observaciones": a.observaciones,
        }
        for a in AsistenciaEvento.objects.filter(evento=evento)
    ]

    cierre = AttendanceProcessingService.process_event_attendance(
        evento_id=evento.id,
        marcaciones=marcaciones,
        actor=f"{diego_cd.first_name} {diego_cd.last_name}",
        reportado_por_id=diego_cd.id,
        cerrar_evento=True,
    )

    evento.refresh_from_db()
    assert evento.estado == EstadoEventoEnum.FINALIZADO
    assert evento.es_sancionable is True
    assert cierre["expedientes_generados"] == 2
    assert cierre["apercibimientos_generados"] == 1

    asist_lucas = AsistenciaEvento.objects.get(evento=evento, socio__legajo="74907")
    assert asist_lucas.procesado_disciplinario is True
    assert asist_lucas.notificado is True
    assert asist_lucas.expediente_generado is not None
    assert asist_lucas.expediente_generado.estado == EstadoExpedienteEnum.JUSTIFICANDO
    assert asist_lucas.expediente_generado.plazo_inicio_at is not None
    assert asist_lucas.expediente_generado.plazo_limite_at is not None
    assert asist_lucas.expediente_generado.puntos == Decimal("-1.00")

    malena = Socio.objects.get(legajo="770013")
    asist_malena = AsistenciaEvento.objects.get(evento=evento, socio=malena)
    assert asist_malena.procesado_disciplinario is True
    assert asist_malena.notificado is True
    assert asist_malena.expediente_generado is not None
    assert asist_malena.expediente_generado.estado == EstadoExpedienteEnum.JUSTIFICANDO
    assert asist_malena.expediente_generado.plazo_inicio_at is not None
    assert asist_malena.expediente_generado.plazo_limite_at is not None
    assert asist_malena.expediente_generado.puntos == Decimal("0.00")
    assert asist_malena.expediente_generado.es_llamado is True

    assert Expediente.objects.filter(socio=malena, estado=EstadoExpedienteEnum.EMITIDO).count() == 2
    assert (
        Expediente.objects.filter(socio=malena, estado=EstadoExpedienteEnum.JUSTIFICANDO).count()
        == 1
    )
    atencion_malena = AtencionFelicitacion.objects.get(socio=malena)
    assert atencion_malena.llamadosAtencion == 2
    assert LedgerService.calcular_saldo(malena) == Decimal("0.00")


@pytest.mark.django_db
def test_flujo1_tercer_llamado_malena_confirmado_consolida_menos_1():
    result = seed_presentation_mocks()
    evento = EventoInstitucional.objects.get(pk=result["evento_id"])
    diego_cd = Socio.objects.get(legajo="87414")
    esteban_td = Socio.objects.get(legajo="85421")
    marcaciones = [
        {
            "socio_id": a.socio_id,
            "estado_asistencia": a.estado_asistencia,
            "motivo": a.motivo or "Sin motivo",
            "minutos_tardanza": a.minutos_tardanza,
            "minutos_retiro_anticipado": a.minutos_retiro_anticipado,
            "hora_registro": a.hora_registro.isoformat() if a.hora_registro else None,
            "hora_salida": a.hora_salida.isoformat() if a.hora_salida else None,
            "observaciones": a.observaciones,
        }
        for a in AsistenciaEvento.objects.filter(evento=evento)
    ]
    AttendanceProcessingService.process_event_attendance(
        evento_id=evento.id,
        marcaciones=marcaciones,
        actor=diego_cd.legajo,
        reportado_por_id=diego_cd.id,
        cerrar_evento=True,
    )

    malena = Socio.objects.get(legajo="770013")
    exp_3 = AsistenciaEvento.objects.get(evento=evento, socio=malena).expediente_generado
    exp_3.estado = EstadoExpedienteEnum.EMITIDO
    exp_3.save(update_fields=["estado"])
    res_3 = Resolucion.objects.create(
        expediente=exp_3,
        numero_expediente_snapshot=exp_3.numero,
        vistos="Vistos.",
        considerandos="Considerandos.",
        articulos_resolutivos="Artículo 1.",
        created_by=esteban_td.user,
    )
    LedgerService.registrar_resolucion(res_3, esteban_td.user)

    assert LedgerService.calcular_saldo(malena) == Decimal("-1.00")
    mov = PuntajeAplicado.objects.get(socio_id=770013)
    assert mov.puntajeAplicado == Decimal("-1.00")
    assert mov.expediente_id == exp_3.id
    assert AtencionFelicitacion.objects.get(socio=malena).llamadosAtencion == 0


@pytest.mark.django_db
def test_flujo1_tercer_llamado_malena_sin_efecto_mantiene_saldo_0_y_contador_2():
    result = seed_presentation_mocks()
    evento = EventoInstitucional.objects.get(pk=result["evento_id"])
    diego_cd = Socio.objects.get(legajo="87414")
    esteban_td = Socio.objects.get(legajo="85421")
    marcaciones = [
        {
            "socio_id": a.socio_id,
            "estado_asistencia": a.estado_asistencia,
            "motivo": a.motivo or "Sin motivo",
            "minutos_tardanza": a.minutos_tardanza,
            "minutos_retiro_anticipado": a.minutos_retiro_anticipado,
            "hora_registro": a.hora_registro.isoformat() if a.hora_registro else None,
            "hora_salida": a.hora_salida.isoformat() if a.hora_salida else None,
            "observaciones": a.observaciones,
        }
        for a in AsistenciaEvento.objects.filter(evento=evento)
    ]
    AttendanceProcessingService.process_event_attendance(
        evento_id=evento.id,
        marcaciones=marcaciones,
        actor=diego_cd.legajo,
        reportado_por_id=diego_cd.id,
        cerrar_evento=True,
    )

    malena = Socio.objects.get(legajo="770013")
    exp_3 = AsistenciaEvento.objects.get(evento=evento, socio=malena).expediente_generado
    descargo = DescargoExpediente.objects.create(
        expediente=exp_3,
        socio=malena,
        tipo=TipoDescargoEnum.T02_CERTIFICADO,
    )
    DecisionCausalDescargo.objects.create(
        expediente=exp_3,
        descargo=descargo,
        version=1,
        decision=DecisionCausalEnum.ACCEPTED,
        regla_sugerida=DecisionCausalEnum.ACCEPTED,
        descargo_snapshot={},
        autor=esteban_td.user,
        autor_legajo=esteban_td.legajo,
        autor_rol=esteban_td.role,
    )
    exp_3.estado = EstadoExpedienteEnum.EMITIDO
    exp_3.save(update_fields=["estado"])
    res_3 = Resolucion.objects.create(
        expediente=exp_3,
        numero_expediente_snapshot=exp_3.numero,
        vistos="Vistos.",
        considerandos="Considerandos.",
        articulos_resolutivos="Artículo 1.",
        created_by=esteban_td.user,
    )
    LedgerService.registrar_resolucion(res_3, esteban_td.user)

    assert LedgerService.calcular_saldo(malena) == Decimal("0.00")
    assert AtencionFelicitacion.objects.get(socio=malena).llamadosAtencion == 2
    assert not PuntajeAplicado.objects.filter(socio_id=770013).exists()


@pytest.mark.django_db
@patch("django.core.mail.message.EmailMultiAlternatives.send")
def test_flujo1_fallo_smtp_cierra_evento_y_deja_expedientes_en_creado_sin_plazo(
    mock_send, settings
):
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    mock_send.side_effect = socket.error("SMTP unreachable")

    result = seed_presentation_mocks()
    evento = EventoInstitucional.objects.get(pk=result["evento_id"])
    diego_cd = Socio.objects.get(legajo="87414")
    marcaciones = [
        {
            "socio_id": a.socio_id,
            "estado_asistencia": a.estado_asistencia,
            "motivo": a.motivo or "Sin motivo",
            "minutos_tardanza": a.minutos_tardanza,
            "minutos_retiro_anticipado": a.minutos_retiro_anticipado,
            "hora_registro": a.hora_registro.isoformat() if a.hora_registro else None,
            "hora_salida": a.hora_salida.isoformat() if a.hora_salida else None,
            "observaciones": a.observaciones,
        }
        for a in AsistenciaEvento.objects.filter(evento=evento)
    ]

    AttendanceProcessingService.process_event_attendance(
        evento_id=evento.id,
        marcaciones=marcaciones,
        actor=diego_cd.legajo,
        reportado_por_id=diego_cd.id,
        cerrar_evento=True,
    )

    evento.refresh_from_db()
    assert evento.estado == EstadoEventoEnum.FINALIZADO

    for legajo in ("74907", "770013"):
        asist = AsistenciaEvento.objects.get(evento=evento, socio__legajo=legajo)
        assert asist.procesado_disciplinario is True
        assert asist.notificado is False
        assert asist.expediente_generado is not None
        assert asist.expediente_generado.estado == EstadoExpedienteEnum.CREADO
        assert asist.expediente_generado.plazo_inicio_at is None
        assert asist.expediente_generado.plazo_limite_at is None


@pytest.mark.django_db
def test_flujo_presentacion_7708_firma_emision_enmienda_y_reversion(
    make_socio, authenticate
):
    lucas = make_socio(legajo="74907", role=Role.SOCIO, social_year=2, numero_socio=74907)
    esteban_td = make_socio(legajo="85421", role=Role.TD, social_year=4, numero_socio=1001)
    catalina_td = make_socio(legajo="86361", role=Role.TD, social_year=5, numero_socio=11737)
    nicolas_td = make_socio(legajo="408917", role=Role.TD, social_year=6, numero_socio=408917)
    ExpedienteNumberSequence.objects.update_or_create(year=2026, defaults={"last_value": 7706})

    initial_saldo = LedgerService.calcular_saldo(lucas)

    with patch(
        "expedientes.services.resolution_service.EmailDispatcherService.dispatch",
        return_value=True,
    ):
        result = seed_presentation_mocks()
        assert result["mock_expedientes"] == ["7707/2026", "7708/2026"]

        exp_firma = Expediente.objects.get(numero="7708/2026")
        assert exp_firma.estado == EstadoExpedienteEnum.PENDIENTE_CORREOS

        res_v1 = Resolucion.objects.get(expediente=exp_firma, version=1)
        assert res_v1.estado == EstadoResolucionEnum.DRAFT
        assert [f["legajo"] for f in res_v1.firmantes] == ["85421", "86361"]
        assert [f["social_year"] for f in res_v1.firmantes] == [4, 5]

        sign_url = f"/api/v1/expedientes/{exp_firma.id}/resolucion/firmar/"
        enmendar_url = f"/api/v1/expedientes/{exp_firma.id}/enmendar/"

        # 1. Tercera firma (408917) emite 7708/2026 y descuenta -1.00 a Lucas
        client = authenticate(nicolas_td)
        resp_emision = client.post(sign_url, {}, format="json")
        assert resp_emision.status_code == 200, resp_emision.data

        exp_firma.refresh_from_db()
        res_v1.refresh_from_db()
        assert exp_firma.estado == EstadoExpedienteEnum.EMITIDO
        assert res_v1.estado == EstadoResolucionEnum.ISSUED
        assert len(res_v1.firmantes) == 3
        assert LedgerService.calcular_saldo(lucas) == initial_saldo - Decimal("1.00")

        # 2. Enmienda como 408917 con puntaje 0: vuelve a pendiente_correos sin alterar saldo aún
        resp_enmienda = client.post(
            enmendar_url,
            {
                "motivo_enmienda": "Rectificación formal del Tribunal de Disciplina a 0 puntos.",
                "nuevos_puntajes": [{"socio_id": lucas.id, "puntaje": 0}],
            },
            format="json",
        )
        assert resp_enmienda.status_code == 201, resp_enmienda.data

        exp_firma.refresh_from_db()
        res_v2 = Resolucion.objects.get(expediente=exp_firma, version=2)
        assert exp_firma.estado == EstadoExpedienteEnum.PENDIENTE_CORREOS
        assert res_v2.estado == EstadoResolucionEnum.DRAFT
        assert res_v2.firmantes == []
        assert res_v2.puntos_finales == Decimal("0.00")
        assert LedgerService.calcular_saldo(lucas) == initial_saldo - Decimal("1.00")

        # 3. Tres firmas sobre la enmienda (85421 -> 86361 -> 408917) emiten y revierten saldo
        for firmante, expected_count in ((esteban_td, 1), (catalina_td, 2)):
            client = authenticate(firmante)
            resp_parcial = client.post(sign_url, {}, format="json")
            assert resp_parcial.status_code == 200, resp_parcial.data
            res_v2.refresh_from_db()
            exp_firma.refresh_from_db()
            assert res_v2.estado == EstadoResolucionEnum.DRAFT
            assert len(res_v2.firmantes) == expected_count
            assert exp_firma.estado == EstadoExpedienteEnum.PENDIENTE_CORREOS
            assert LedgerService.calcular_saldo(lucas) == initial_saldo - Decimal("1.00")

        client = authenticate(nicolas_td)
        resp_final = client.post(sign_url, {}, format="json")
        assert resp_final.status_code == 200, resp_final.data

    exp_firma.refresh_from_db()
    res_v2.refresh_from_db()
    assert exp_firma.estado == EstadoExpedienteEnum.EMITIDO
    assert res_v2.estado == EstadoResolucionEnum.ISSUED
    assert {f["legajo"] for f in res_v2.firmantes} == {"85421", "86361", "408917"}
    assert LedgerService.calcular_saldo(lucas) == initial_saldo
    assert LedgerService.verificar_cadena(lucas).valida is True
    movimientos_7708 = [
        Decimal(str(m.puntajeAplicado))
        for m in PuntajeAplicado.objects.filter(expediente_id=exp_firma.id, socio_id=74907)
    ]
    assert sum(movimientos_7708) == Decimal("0.00")



