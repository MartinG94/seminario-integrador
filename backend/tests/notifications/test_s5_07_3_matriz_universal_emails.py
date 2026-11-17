"""Suite integral de verificación y matriz universal de emails EmailOutbox (S5-07.3 / SCRUM-123).

Cubre:
1. Los 13 eventos oficiales: trigger real de negocio, destinatarios, asunto, plantilla y key.
2. Remitente institucional DEFAULT_FROM_EMAIL.
3. Copia oculta institucional automática EMAIL_BCC_INSTITUCIONAL sin exposición en To/CC.
4. Adjuntos PDF probatorios en Base64 (cédula de apertura y resolución final) con EmailAttachment.
5. Atomicidad transaccional ante commits y rollbacks (0 registros/adjuntos parciales).
6. Backoff exponencial exacto, máximo 5 reintentos, transición a FAILED y cero reintentos extra.
7. Idempotencia ante peticiones HTTP repetidas y ausencia de adjuntos duplicados.
"""

from __future__ import annotations

import base64
import socket
from datetime import datetime, timedelta
from datetime import timezone as dt_timezone
from decimal import Decimal
from io import BytesIO
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from django.core import mail
from django.core.management import call_command
from django.db import transaction
from django.test import override_settings
from django.utils import timezone
from pypdf import PdfReader
from rest_framework import status
from rest_framework.test import APIClient

from expedientes.models import (
    CategoriaEventoEnum,
    EstadoEventoEnum,
    EstadoExpedienteEnum,
    EstadoResolucionEnum,
    EventoConvocado,
    EventoInstitucional,
    Expediente,
    ModalidadEventoEnum,
    ModoConvocatoriaEnum,
    Resolucion,
    SolicitudT01,
    SubtipoReunionEnum,
)
from expedientes.services.deadline_service import DeadlineEnforcementService
from expedientes.services.resolution_service import registrar_firma_resolucion
from expedientes.services.t01_appeal_service import T01AppealService
from expedientes.services.tribunal_composition_service import TribunalCompositionService
from notifications.models import EmailAttachment, EmailOutbox, EmailOutboxStatus
from notifications.services import EmailDispatcherService, process_email_outbox
from padron.models import Socio as LegacySocio
from padron.models import SocioEstadoHistorial
from ranking.domain.threshold_alerts import (
    ThresholdAlertEngine,
    TipoAlerta,
    UmbralConfig,
)
from socios.models import Role, Socio, Subcomision
from tests.expedientes.conftest import CARGO_SUPLENTE_TD, CARGO_TITULAR_TD
from tests.legacy_schema import create_legacy_record


@pytest.fixture(autouse=True)
def safe_email_backend(settings) -> None:
    """Garantiza aislamiento total con locmem para evitar envíos reales SMTP."""
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    settings.DEFAULT_FROM_EMAIL = "notificaciones@aveit.utn.edu.ar"
    settings.EMAIL_BCC_INSTITUCIONAL = "secretaria-td@aveit.utn.edu.ar"
    settings.CD_EMAIL = "cd@aveit.test"
    settings.COMISION_DIRECTIVA_EMAIL = "cd@aveit.test"
    settings.TRIBUNAL_EMAIL = "tribunal@aveit.test"
    settings.FRONTEND_URL = "https://tribunal.aveit.utn.edu.ar"
    mail.outbox.clear()


@pytest.fixture
def subcomision_computos(db) -> Subcomision:
    return Subcomision.objects.create(name="Cómputos")


@pytest.fixture
def mock_padron(monkeypatch):
    """Mockea get_padron_repository para validar socios locales al emitir T01."""

    def _get_by_id(socio_id: int):
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


@pytest.fixture
def tribunal_nomina(make_socio) -> dict[str, Socio]:
    """Nómina estatutaria TD completa en SQLite/legacy para pruebas de apartamiento."""
    base = timezone.localdate().year - 1962

    def _make_legacy(nro: int, year: int, cargo: int, grupo: int) -> Socio:
        socio = make_socio(legajo=str(nro), role=Role.TD, social_year=year, is_enabled=True)
        legacy = create_legacy_record(
            LegacySocio,
            nroSocio=nro,
            apellido=socio.last_name,
            nombre=socio.first_name,
            anoSocial=year,
            idTipoSocio=cargo,
            user_id=socio.user_id,
        )
        create_legacy_record(
            SocioEstadoHistorial,
            idGrupo=grupo,
            socio=legacy,
            fechaHora=datetime(2026, 3, 1, tzinfo=dt_timezone.utc),
            codEstadoSocio=1,
            socio_motivoCambioEstado=1,
        )
        return socio

    return {
        "t4": _make_legacy(81004, 4, CARGO_TITULAR_TD, base - 4),
        "s4": _make_legacy(82004, 4, CARGO_SUPLENTE_TD, base - 4),
        "t5": _make_legacy(81005, 5, CARGO_TITULAR_TD, base - 5),
        "s5": _make_legacy(82005, 5, CARGO_SUPLENTE_TD, base - 5),
        "t6": _make_legacy(81006, 6, CARGO_TITULAR_TD, base - 6),
        "s6": _make_legacy(82006, 6, CARGO_SUPLENTE_TD, base - 6),
    }


@pytest.fixture
def t01_involucrados(make_socio) -> list[Socio]:
    return [make_socio(legajo="91071"), make_socio(legajo="91072")]


@pytest.fixture
def t01_expediente(make_socio, t01_involucrados) -> Expediente:
    solicitante = make_socio(legajo="91070", role=Role.REVISORES, social_year=5)
    expediente = Expediente.objects.create(
        numero="EXP-0701/2026",
        socio=t01_involucrados[0],
        motivo="Uso indebido del laboratorio",
        puntos=Decimal("-2.00"),
        estado=EstadoExpedienteEnum.CREADO,
    )
    expediente.socios.set(t01_involucrados)
    SolicitudT01.objects.create(
        estado=SolicitudT01.Estado.ISSUED,
        solicitante=solicitante,
        destinatarios_socios_ids=[s.id for s in t01_involucrados],
        tipo_accion=SolicitudT01.TipoAccion.SANCTION,
        titulo="Uso indebido del laboratorio",
        puntos=Decimal("-2.00"),
        motivo="Uso indebido del laboratorio",
        snapshot_emitido={"puntos": "-2.00", "titulo": "Uso indebido del laboratorio"},
        numero_expediente="T01-2026-EMAILTEST01",
        expediente=expediente,
        issued_at=timezone.now(),
    )
    return expediente


def _decode_pdf_text(attachment: EmailAttachment) -> tuple[bytes, str]:
    raw = base64.b64decode(attachment.content_base64)
    reader = PdfReader(BytesIO(raw))
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    return raw, text


@pytest.mark.django_db
class TestCatalogoTreceEventos:
    """Verifica trigger, destinatarios, asunto, plantilla, BCC y adjuntos para los 13 eventos."""

    def test_evento_01_apertura_t01_con_cedula_pdf_y_coimputados(
        self, make_socio, authenticate
    ) -> None:
        td_vocal = make_socio(legajo="91001", role=Role.TD, social_year=5)
        socio_1 = make_socio(legajo="91002", role=Role.SOCIO)
        socio_2 = make_socio(legajo="91003", role=Role.SOCIO)

        exp = Expediente.objects.create(
            numero="EXP-0101/2026",
            socio=socio_1,
            motivo="Incumplimiento operativo",
            estado=EstadoExpedienteEnum.CREADO,
            puntos=Decimal("-1.00"),
        )
        exp.socios.add(socio_1, socio_2)

        client = authenticate(td_vocal)
        resp = client.post(
            f"/api/v1/expedientes/{exp.id}/despachar-notificacion/", {}, format="json"
        )
        assert resp.status_code == status.HTTP_200_OK

        outboxes = EmailOutbox.objects.filter(metadata__tipo_notificacion="APERTURA_EXPEDIENTE")
        assert outboxes.count() == 2
        destinos = {o.to[0] for o in outboxes}
        assert destinos == {socio_1.email, socio_2.email}

        for outbox in outboxes:
            assert "Notificación de Apertura de Causa" in outbox.subject
            assert "secretaria-td@aveit.utn.edu.ar" in outbox.bcc
            assert "secretaria-td@aveit.utn.edu.ar" not in outbox.to
            assert "secretaria-td@aveit.utn.edu.ar" not in outbox.cc
            assert outbox.attachments.count() == 1
            att = outbox.attachments.first()
            assert att.mimetype == "application/pdf"
            assert att.filename.endswith(".pdf")
            raw, text = _decode_pdf_text(att)
            assert raw.startswith(b"%PDF")
            assert "EXP-0101/2026" in text

        # Reintento HTTP no duplica outbox ni adjuntos
        resp2 = client.post(
            f"/api/v1/expedientes/{exp.id}/despachar-notificacion/", {}, format="json"
        )
        assert resp2.status_code == status.HTTP_200_OK
        assert outboxes.count() == 2
        assert EmailAttachment.objects.count() == 2

    def test_evento_02_aviso_apertura_al_solicitante_acuse_formal(
        self, make_socio, authenticate, mock_padron
    ) -> None:
        solicitante = make_socio(legajo="91010", role=Role.REVISORES, social_year=5)
        imputado = make_socio(legajo="91011", role=Role.SOCIO)

        solicitud = SolicitudT01.objects.create(
            solicitante=solicitante,
            destinatario_socio_id=imputado.id,
            destinatarios_socios_ids=[imputado.id],
            tipo_accion=SolicitudT01.TipoAccion.SANCTION,
            titulo="Falta de entrega de inventario",
            motivo="Falta de entrega de inventario en término.",
            puntos=Decimal("-1.00"),
            numero_expediente="9101/2026",
        )

        client = authenticate(solicitante)
        resp = client.post(f"/api/v1/expedientes/{solicitud.id}/emitir/", {}, format="json")
        assert resp.status_code == status.HTTP_200_OK

        ack = EmailOutbox.objects.get(idempotency_key=f"t01-solicitante-ack-{solicitud.id}")
        assert ack.to == [solicitante.email]
        assert ack.bcc == ["secretaria-td@aveit.utn.edu.ar"]
        assert "Acuse de Recibo" in ack.subject
        assert "9101/2026" in ack.body_text
        assert ack.metadata["tipo_notificacion"] == "ACUSE_SOLICITANTE_T01"

        # Repetir HTTP emitir es idempotente
        resp2 = client.post(f"/api/v1/expedientes/{solicitud.id}/emitir/", {}, format="json")
        assert resp2.status_code == status.HTTP_200_OK
        assert EmailOutbox.objects.filter(idempotency_key=ack.idempotency_key).count() == 1

    def test_eventos_03_12_y_13_convocatoria_reunion_evento_y_anulacion(
        self, make_socio, authenticate
    ) -> None:
        autoridad_cd = make_socio(legajo="91020", role=Role.CD, social_year=5)
        socio_citado = make_socio(legajo="91021", role=Role.SOCIO)

        # Evento 3 y 12: Convocatoria formal a Reunión (evento_views /notificar/)
        reunion = EventoInstitucional.objects.create(
            titulo="Reunión Plenaria Mensual",
            categoria=CategoriaEventoEnum.REUNION,
            tipo=SubtipoReunionEnum.ORDINARIA,
            modalidad=ModalidadEventoEnum.PRESENCIAL_SEDE,
            lugar="Sede Central AVEIT",
            fecha_publicacion=timezone.now(),
            fecha_programada=timezone.now() + timedelta(days=5),
            modo_convocatoria=ModoConvocatoriaEnum.PERSONALIZADA,
            es_obligatoria=True,
            es_sancionable=True,
            estado=EstadoEventoEnum.CREADO,
            convocante=autoridad_cd,
        )
        EventoConvocado.objects.create(evento=reunion, socio=socio_citado)

        client = authenticate(autoridad_cd)
        resp_notif = client.post(f"/api/v1/eventos/{reunion.id}/notificar/", {}, format="json")
        assert resp_notif.status_code == status.HTTP_200_OK

        conv = EmailOutbox.objects.get(
            idempotency_key=f"meeting_notice_{reunion.id}_socio_{socio_citado.id}"
        )
        assert conv.to == [socio_citado.email]
        assert "Convocatoria Institucional" in conv.subject
        assert conv.bcc == ["secretaria-td@aveit.utn.edu.ar"]
        assert conv.status == EmailOutboxStatus.SENT

        # Evento 13: Anulación de Evento Institucional (evento_views /anular/)
        resp_anul = client.post(
            f"/api/v1/eventos/{reunion.id}/anular/",
            {"motivo": "Reprogramación por asamblea universitaria."},
            format="json",
        )
        assert resp_anul.status_code == status.HTTP_200_OK

        cancel = EmailOutbox.objects.get(
            idempotency_key=f"meeting_cancellation_{reunion.id}_socio_{socio_citado.id}"
        )
        assert cancel.to == [socio_citado.email]
        assert "Cancelación de Convocatoria" in cancel.subject
        assert "Reprogramación por asamblea universitaria" in cancel.body_text
        assert cancel.bcc == ["secretaria-td@aveit.utn.edu.ar"]
        assert cancel.status == EmailOutboxStatus.SENT

    def test_eventos_04_y_05_alertas_preventiva_menos_7_y_critica_menos_10(self) -> None:
        cfg = UmbralConfig()
        cfg.activar_preventivo()

        # Evento 4: Alerta preventiva (-7) -> Socio y CD
        res_prev = ThresholdAlertEngine.evaluar_cruce(
            socio_id=91030,
            saldo_anterior=Decimal("-6.00"),
            saldo_nuevo=Decimal("-7.00"),
            config=cfg,
            socio_email="socio7@aveit.test",
            socio_nombre="Ana López",
            despachar_outbox=True,
        )
        assert res_prev.alerta_generada is not None
        assert res_prev.alerta_generada.tipo == TipoAlerta.PREVENTIVA
        out_prev = EmailOutbox.objects.get(
            idempotency_key=f"threshold-alert-preventiva-91030-{res_prev.alerta_generada.id}"
        )
        assert out_prev.to == ["socio7@aveit.test", "cd@aveit.test"]
        assert "ALERTA PREVENTIVA" in out_prev.subject
        assert out_prev.bcc == ["secretaria-td@aveit.utn.edu.ar"]
        assert out_prev.status == EmailOutboxStatus.SENT

        # Evento 5: Alerta crítica (-10) -> Socio, CD y TD
        res_crit = ThresholdAlertEngine.evaluar_cruce(
            socio_id=91031,
            saldo_anterior=Decimal("-9.00"),
            saldo_nuevo=Decimal("-10.00"),
            config=cfg,
            socio_email="socio10@aveit.test",
            socio_nombre="Carlos Ruiz",
            despachar_outbox=True,
        )
        assert res_crit.alerta_generada is not None
        assert res_crit.alerta_generada.tipo == TipoAlerta.CRITICA
        out_crit = EmailOutbox.objects.get(
            idempotency_key=f"threshold-alert-critica-91031-{res_crit.alerta_generada.id}"
        )
        assert out_crit.to == ["socio10@aveit.test", "cd@aveit.test", "tribunal@aveit.test"]
        assert "ALERTA CRÍTICA" in out_crit.subject
        assert out_crit.bcc == ["secretaria-td@aveit.utn.edu.ar"]
        assert out_crit.status == EmailOutboxStatus.SENT

    def test_evento_06_presentacion_descargo_notifica_al_td(self, make_socio, authenticate) -> None:
        imputado = make_socio(legajo="91040", role=Role.SOCIO)
        exp = Expediente.objects.create(
            numero="EXP-0106/2026",
            socio=imputado,
            motivo="Falta a jornada",
            estado=EstadoExpedienteEnum.JUSTIFICANDO,
            plazo_inicio_at=timezone.now() - timedelta(days=1),
            plazo_limite_at=timezone.now() + timedelta(days=3),
        )
        exp.socios.add(imputado)

        client = authenticate(imputado)
        resp = client.post(
            f"/api/v1/expedientes/{exp.id}/descargo/",
            {
                "tipo": "T03_EXTRAORDINARIO",
                "causal": "Motivo laboral extraordinario",
                "texto": "Presento justificativo de horario laboral.",
            },
            format="json",
        )
        assert resp.status_code == status.HTTP_201_CREATED

        outbox = EmailOutbox.objects.get(
            idempotency_key=f"descargo-recibido-{exp.id}-socio-{imputado.id}-v1"
        )
        assert outbox.to == ["tribunal@aveit.test"]
        assert outbox.bcc == ["secretaria-td@aveit.utn.edu.ar"]
        assert "Descargo T03_EXTRAORDINARIO recibido" in outbox.subject
        assert "EXP-0106/2026" in outbox.subject

    def test_evento_07_recordatorio_vencimiento_inminente_24h_idempotente(self, make_socio) -> None:
        imputado = make_socio(legajo="91050", role=Role.SOCIO)
        lejos = make_socio(legajo="91051", role=Role.SOCIO)

        ahora = timezone.now()
        exp_inminente = Expediente.objects.create(
            numero="EXP-0107/2026",
            socio=imputado,
            motivo="Causa por vencer en 12h",
            estado=EstadoExpedienteEnum.JUSTIFICANDO,
            plazo_inicio_at=ahora - timedelta(days=4),
            plazo_limite_at=ahora + timedelta(hours=12),
        )
        exp_inminente.socios.add(imputado)

        exp_lejano = Expediente.objects.create(
            numero="EXP-0108/2026",
            socio=lejos,
            motivo="Causa con 72h restantes",
            estado=EstadoExpedienteEnum.JUSTIFICANDO,
            plazo_inicio_at=ahora - timedelta(days=1),
            plazo_limite_at=ahora + timedelta(hours=72),
        )
        exp_lejano.socios.add(lejos)

        call_command("send_deadline_reminders")

        rem = EmailOutbox.objects.get(
            idempotency_key=f"deadline-reminder-{exp_inminente.id}-socio-{imputado.id}"
        )
        assert rem.to == [imputado.email]
        assert rem.bcc == ["secretaria-td@aveit.utn.edu.ar"]
        assert "vencimiento inminente" in rem.subject.lower()
        assert not EmailOutbox.objects.filter(
            idempotency_key=f"deadline-reminder-{exp_lejano.id}-socio-{lejos.id}"
        ).exists()

        # Segunda ejecución mantiene idempotencia sin duplicar
        DeadlineEnforcementService().send_imminent_deadline_reminders(ahora=ahora)
        assert EmailOutbox.objects.filter(idempotency_key=rem.idempotency_key).count() == 1

    def test_evento_08_apartamiento_y_suplencia_notifica_a_miembros_td(
        self, tribunal_nomina
    ) -> None:
        # El titular de 4to año (t4) es parte interesada -> lo reemplaza s4
        exp = Expediente.objects.create(
            numero="EXP-0109/2026",
            socio=tribunal_nomina["t4"],
            motivo="Inasistencia de miembro TD",
            estado=EstadoExpedienteEnum.CREADO,
        )
        exp.socios.add(tribunal_nomina["t4"])

        TribunalCompositionService.notify_if_ad_hoc(exp)

        outbox = EmailOutbox.objects.get(idempotency_key=f"td-suplencia-expediente-{exp.id}")
        assert tribunal_nomina["s4"].email in outbox.to
        assert tribunal_nomina["t5"].email in outbox.to
        assert tribunal_nomina["t6"].email in outbox.to
        assert tribunal_nomina["t4"].email not in outbox.to
        assert outbox.bcc == ["secretaria-td@aveit.utn.edu.ar"]
        assert "Apartamiento e integración de suplente en TD" in outbox.subject

    def test_eventos_09_y_10_emision_resolucion_final_socio_y_cd_con_pdf(self, make_socio) -> None:
        imputado = make_socio(legajo="91060", role=Role.SOCIO)
        td4 = make_socio(legajo="91061", role=Role.TD, social_year=4)
        td5 = make_socio(legajo="91062", role=Role.TD, social_year=5)
        td6 = make_socio(legajo="91063", role=Role.TD, social_year=6)

        exp = Expediente.objects.create(
            numero="EXP-0110/2026",
            socio=imputado,
            motivo="Causa en firma",
            estado=EstadoExpedienteEnum.PENDIENTE_CORREOS,
            puntos=Decimal("-2.00"),
        )
        exp.socios.add(imputado)

        resolucion = Resolucion.objects.create(
            expediente=exp,
            plantilla_version="resolucion-2026.1",
            numero_expediente_snapshot=exp.numero,
            vistos="Vistos los antecedentes de la causa.",
            considerandos="Considerando el descargo presentado.",
            articulos_resolutivos="Artículo 1: Aplicar -2.00 puntos.",
            created_by=td4.user,
        )

        registrar_firma_resolucion(resolucion, td4.user)
        registrar_firma_resolucion(resolucion, td5.user)
        emitida = registrar_firma_resolucion(resolucion, td6.user)
        assert emitida.estado == EstadoResolucionEnum.ISSUED

        # Evento 9: Al socio imputado con dictamen, puntos y PDF oficial adjunto
        out_socio = EmailOutbox.objects.get(
            idempotency_key=f"resolucion-emitida-{emitida.id}-socio-{imputado.id}"
        )
        assert out_socio.to == [imputado.email]
        assert out_socio.bcc == ["secretaria-td@aveit.utn.edu.ar"]
        assert "Resolución Final Emitida" in out_socio.subject
        assert "-2.00" in out_socio.body_text
        assert out_socio.attachments.count() == 1
        raw_s, text_s = _decode_pdf_text(out_socio.attachments.first())
        assert raw_s.startswith(b"%PDF")
        assert "EXP-0110/2026" in text_s
        assert "BORRADOR" not in text_s

        # Evento 10: A Comisión Directiva para conocimiento y archivo con el mismo PDF adjunto
        out_cd = EmailOutbox.objects.get(idempotency_key=f"resolucion-emitida-{emitida.id}-cd")
        assert out_cd.to == ["cd@aveit.test"]
        assert out_cd.bcc == ["secretaria-td@aveit.utn.edu.ar"]
        assert "Notificación de Resolución a CD" in out_cd.subject
        assert out_cd.attachments.count() == 1
        assert (
            out_cd.attachments.first().content_base64
            == out_socio.attachments.first().content_base64
        )

    def test_evento_11_apelacion_t01_socio_y_td_con_bcc(
        self, t01_expediente, t01_involucrados
    ) -> None:
        en_just = Expediente.objects.get(pk=t01_expediente.pk)
        from expedientes.services.workflow_service import ExpedienteWorkflowService

        ExpedienteWorkflowService.transition(
            expediente_id=en_just.pk,
            estado_nuevo=EstadoExpedienteEnum.JUSTIFICANDO,
            actor="tribunal",
            motivo="Apertura de apelación",
        )

        socio = t01_involucrados[0]
        apelacion = T01AppealService.present_appeal(
            expediente_id=en_just.pk,
            user=socio.user,
            texto="Solicito revisión del puntaje aplicado en la solicitud T01.",
        )

        out_socio = EmailOutbox.objects.get(idempotency_key=f"t01-apelacion-{apelacion.pk}-socio")
        out_td = EmailOutbox.objects.get(idempotency_key=f"t01-apelacion-{apelacion.pk}-tribunal")
        assert out_socio.to == [socio.email]
        assert out_td.to == ["tribunal@aveit.test"]
        assert out_socio.bcc == ["secretaria-td@aveit.utn.edu.ar"]
        assert out_td.bcc == ["secretaria-td@aveit.utn.edu.ar"]


@pytest.mark.django_db
class TestGarantiasTransversalesOutbox:
    """Verifica remitente, BCC en transporte SMTP/locmem, atomicidad, backoff y FAILED."""

    @override_settings(
        DEFAULT_FROM_EMAIL="notificaciones@aveit.utn.edu.ar",
        EMAIL_BCC_INSTITUCIONAL="bcc-institucional@aveit.utn.edu.ar",
    )
    def test_remitente_y_bcc_en_mensaje_despachado_sin_exponer_en_to_ni_cc(self) -> None:
        outbox, _ = EmailDispatcherService.create_or_get_outbox(
            {
                "to": ["socio@aveit.test"],
                "cc": ["copia@aveit.test"],
                "subject": "Cédula formal",
                "body_text": "Contenido procesal",
                "idempotency_key": "test-from-bcc-001",
                "metadata": {"es_disciplinario": True},
            }
        )

        assert EmailDispatcherService.dispatch(outbox) is True
        assert len(mail.outbox) == 1
        sent_msg = mail.outbox[0]
        assert sent_msg.from_email == "notificaciones@aveit.utn.edu.ar"
        assert sent_msg.to == ["socio@aveit.test"]
        assert sent_msg.cc == ["copia@aveit.test"]
        assert sent_msg.bcc == ["bcc-institucional@aveit.utn.edu.ar"]
        assert "bcc-institucional@aveit.utn.edu.ar" not in sent_msg.to
        assert "bcc-institucional@aveit.utn.edu.ar" not in sent_msg.cc

    def test_atomicidad_ante_rollback_no_deja_outbox_ni_attachments_parciales(self) -> None:
        b64 = base64.b64encode(b"%PDF-1.4 rollback test").decode("utf-8")

        with pytest.raises(RuntimeError, match="Fallo forzado de negocio"):
            with transaction.atomic():
                EmailDispatcherService.create_or_get_outbox(
                    {
                        "to": ["socio@aveit.test"],
                        "subject": "Notificación abortada",
                        "body_text": "No debe persistirse",
                        "idempotency_key": "rollback-atomic-001",
                        "metadata": {"es_disciplinario": True},
                        "attachments": [
                            {
                                "filename": "doc.pdf",
                                "content_base64": b64,
                                "mimetype": "application/pdf",
                            }
                        ],
                    }
                )
                raise RuntimeError("Fallo forzado de negocio")

        assert EmailOutbox.objects.filter(idempotency_key="rollback-atomic-001").count() == 0
        assert EmailAttachment.objects.count() == 0

    @patch("django.core.mail.message.EmailMultiAlternatives.send")
    def test_backoff_exponencial_5_reintentos_y_bloqueo_definitivo_en_failed(
        self, mock_send
    ) -> None:
        mock_send.side_effect = socket.error("SMTP gateway unreachable")

        outbox = EmailOutbox.objects.create(
            to=["socio@aveit.test"],
            subject="Correo con fallos persistentes",
            body_text="Cuerpo",
            status=EmailOutboxStatus.PENDING,
            max_retries=5,
        )

        # Intentos 1 a 4 deben programar backoff exponencial: 2m, 4m, 8m, 16m
        expected_minutes = [2, 4, 8, 16]
        for attempt_idx, mins in enumerate(expected_minutes, start=1):
            before = timezone.now()
            res = process_email_outbox(force=True)
            outbox.refresh_from_db()

            assert res["processed"] == 1
            assert outbox.status == EmailOutboxStatus.PENDING
            assert outbox.retry_count == attempt_idx
            delta_seconds = (outbox.next_retry_at - before).total_seconds()
            assert (mins * 60 - 5) <= delta_seconds <= (mins * 60 + 5)

        # Intento 5 agota max_retries -> pasa a FAILED
        res_final = process_email_outbox(force=True)
        outbox.refresh_from_db()
        assert res_final["processed"] == 1
        assert res_final["failed"] == 1
        assert outbox.status == EmailOutboxStatus.FAILED
        assert outbox.retry_count == 5
        assert "SMTP gateway unreachable" in (outbox.last_error or "")

        # Tras FAILED: ni process_email_outbox ni dispatch directo vuelven a intentar enviar
        calls_before = mock_send.call_count
        assert calls_before == 5
        res_after = process_email_outbox(force=True)
        assert res_after["processed"] == 0
        assert EmailDispatcherService.dispatch(outbox) is False
        assert mock_send.call_count == calls_before

    @patch("django.core.mail.message.EmailMultiAlternatives.send")
    def test_idempotencia_http_con_adjunto_no_duplica_registros(self, mock_send) -> None:
        mock_send.return_value = 1
        client = APIClient()
        b64 = base64.b64encode(b"%PDF-1.4 doc").decode("utf-8")
        payload = {
            "to": ["socio@aveit.test"],
            "subject": "Cédula idempotente",
            "body_text": "Cuerpo",
            "idempotency_key": "http-idemp-pdf-001",
            "metadata": {"es_disciplinario": True},
            "attachments": [
                {
                    "filename": "cedula.pdf",
                    "content_base64": b64,
                    "mimetype": "application/pdf",
                }
            ],
        }
        headers = {"HTTP_X_INTERNAL_SERVICE_KEY": "aveit-internal-service-secret-2026"}

        r1 = client.post("/api/v1/notifications/email/", payload, format="json", **headers)
        r2 = client.post("/api/v1/notifications/email/", payload, format="json", **headers)

        assert r1.status_code == status.HTTP_200_OK
        assert r2.status_code == status.HTTP_200_OK
        assert r1.data["id"] == r2.data["id"]
        assert mock_send.call_count == 1
        assert EmailOutbox.objects.filter(idempotency_key="http-idemp-pdf-001").count() == 1
        assert EmailAttachment.objects.filter(email_id=r1.data["id"]).count() == 1
