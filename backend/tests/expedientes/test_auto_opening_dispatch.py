"""Tests de transición automática Creado -> Justificando y despacho de correo al abrir."""

import socket
from datetime import timedelta
from unittest.mock import patch

import pytest
from django.core import mail
from django.test import override_settings
from django.utils import timezone

from expedientes.models import (
    CambioEstadoExpediente,
    CategoriaEventoEnum,
    EstadoAsistenciaEventoEnum,
    EstadoEventoEnum,
    EstadoExpedienteEnum,
    EventoConvocado,
    EventoInstitucional,
    Expediente,
    SubtipoReunionEnum,
)
from expedientes.services.attendance_processing_service import AttendanceProcessingService
from expedientes.services.workflow_service import ExpedienteWorkflowService
from notifications.models import EmailOutbox, EmailOutboxStatus
from socios.models import Socio


@pytest.mark.django_db(transaction=True)
class TestAutoOpeningDispatch:
    """Valida el flujo automático Creado -> Justificando + EmailOutbox controlado por flag."""

    @override_settings(
        AUTO_DISPATCH_OPENING_EMAIL=True,
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    )
    def test_open_expediente_auto_transitions_and_dispatches_to_all_implicated_socios(
        self, make_socio
    ) -> None:
        socio_titular = make_socio(legajo="780001", email="lucas@aveit.test")
        socio_coimputado = make_socio(legajo="780002", email="coimputado@aveit.test")

        expediente = ExpedienteWorkflowService.open_expediente(
            motivo="Inasistencia injustificada a reunión general",
            socio_ids=[socio_titular.id, socio_coimputado.id],
            actor="CD_User",
        )

        expediente.refresh_from_db()
        assert expediente.estado == EstadoExpedienteEnum.JUSTIFICANDO
        assert expediente.plazo_inicio_at is not None
        assert expediente.plazo_limite_at is not None

        cambios = list(
            CambioEstadoExpediente.objects.filter(expediente=expediente)
            .order_by("id")
            .values_list("estado_anterior", "estado_nuevo")
        )
        assert cambios == [
            (EstadoExpedienteEnum.CREADO, EstadoExpedienteEnum.CREADO),
            (EstadoExpedienteEnum.CREADO, EstadoExpedienteEnum.JUSTIFICANDO),
        ]

        outboxes = list(EmailOutbox.objects.order_by("id"))
        assert len(outboxes) == 2
        assert {o.to[0] for o in outboxes} == {"lucas@aveit.test", "coimputado@aveit.test"}
        assert all(o.status == EmailOutboxStatus.SENT for o in outboxes)
        assert len(mail.outbox) == 2

    @override_settings(
        AUTO_DISPATCH_OPENING_EMAIL=False,
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    )
    def test_open_expediente_stays_creado_when_auto_dispatch_disabled(self, make_socio) -> None:
        socio = make_socio(legajo="780003", email="socio3@aveit.test")

        expediente = ExpedienteWorkflowService.open_expediente(
            motivo="Falta leve de prueba",
            socio_ids=[socio.id],
            actor="TD_User",
        )

        expediente.refresh_from_db()
        assert expediente.estado == EstadoExpedienteEnum.CREADO
        assert expediente.plazo_limite_at is None
        assert EmailOutbox.objects.count() == 0

    @override_settings(
        AUTO_DISPATCH_OPENING_EMAIL=True,
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    )
    def test_open_expediente_does_not_fail_when_socio_has_no_email(self, make_socio) -> None:
        socio = make_socio(legajo="780004", email="temp@aveit.test")
        Socio.objects.filter(pk=socio.pk).update(email="")

        expediente = ExpedienteWorkflowService.open_expediente(
            motivo="Inasistencia sin correo en legajo",
            socio_ids=[socio.id],
            actor="CD_User",
        )

        expediente.refresh_from_db()
        assert expediente.estado == EstadoExpedienteEnum.CREADO
        assert EmailOutbox.objects.count() == 0

    @override_settings(
        AUTO_DISPATCH_OPENING_EMAIL=True,
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    )
    @patch("django.core.mail.message.EmailMultiAlternatives.send")
    def test_open_expediente_survives_smtp_failure_and_keeps_outbox_pending(
        self, mock_send, make_socio
    ) -> None:
        mock_send.side_effect = socket.error("SMTP unreachable")
        socio = make_socio(legajo="780005", email="socio5@aveit.test")

        expediente = ExpedienteWorkflowService.open_expediente(
            motivo="Inasistencia con fallo SMTP",
            socio_ids=[socio.id],
            actor="CD_User",
        )

        expediente.refresh_from_db()
        assert expediente.estado == EstadoExpedienteEnum.JUSTIFICANDO
        assert expediente.plazo_limite_at is not None

        outbox = EmailOutbox.objects.get()
        assert outbox.status == EmailOutboxStatus.PENDING
        assert outbox.retry_count == 1

    @override_settings(
        AUTO_DISPATCH_OPENING_EMAIL=True,
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    )
    def test_attendance_absence_auto_transitions_to_justificando_and_sends_email(
        self, make_socio
    ) -> None:
        cd_user = make_socio(legajo="780010", email="cd@aveit.test")
        socio_ausente = make_socio(legajo="780011", email="ausente@aveit.test")
        ahora = timezone.now()
        evento = EventoInstitucional.objects.create(
            titulo="Reunión General Demo",
            categoria=CategoriaEventoEnum.REUNION,
            tipo=SubtipoReunionEnum.ORDINARIA,
            estado=EstadoEventoEnum.NOTIFICADO,
            fecha_programada=ahora - timedelta(hours=2),
            fecha_fin=ahora - timedelta(hours=1),
            fecha_publicacion=ahora - timedelta(days=10),
            responsable=cd_user,
            es_obligatoria=True,
        )
        EventoConvocado.objects.create(evento=evento, socio=socio_ausente)

        result = AttendanceProcessingService.process_event_attendance(
            evento_id=evento.id,
            marcaciones=[
                {
                    "socio_id": socio_ausente.id,
                    "estado_asistencia": EstadoAsistenciaEventoEnum.AUSENTE,
                    "motivo": "Inasistencia en demo",
                }
            ],
            actor=cd_user.legajo,
            reportado_por_id=cd_user.id,
            fecha_reporte=ahora,
            fecha_hora_cierre_efectivo=ahora - timedelta(hours=1),
            cerrar_evento=True,
        )

        assert len(result["expedientes_creados"]) == 1
        expediente = Expediente.objects.get(numero=result["expedientes_creados"][0]["numero"])
        assert expediente.estado == EstadoExpedienteEnum.JUSTIFICANDO
        assert expediente.plazo_inicio_at is not None
        assert expediente.plazo_limite_at is not None

        outbox = EmailOutbox.objects.get()
        assert outbox.to == ["ausente@aveit.test"]
        assert outbox.status == EmailOutboxStatus.SENT
        assert len(mail.outbox) == 1
