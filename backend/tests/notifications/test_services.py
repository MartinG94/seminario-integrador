"""
Pruebas unitarias de dominio para EmailDispatcherService y modelos Outbox (/backendTesting).
"""

import base64
import socket
from unittest.mock import patch

import pytest
from django.utils import timezone

from notifications.models import EmailOutbox, EmailOutboxStatus
from notifications.services import EmailDispatcherService


@pytest.mark.django_db
class TestEmailDispatcherService:
    def test_create_outbox_atomic_with_attachments(self) -> None:
        raw_content = b"PDF dummy content for testing"
        b64_content = base64.b64encode(raw_content).decode("utf-8")

        payload = {
            "to": ["socio@aveit.utn.edu.ar"],
            "cc": ["directiva@aveit.utn.edu.ar"],
            "bcc": ["auditoria@aveit.utn.edu.ar"],
            "subject": "Notificación de Apertura de Expediente",
            "body_text": "Estimado socio, se notifica apertura...",
            "body_html": "<p>Estimado socio, se notifica apertura...</p>",
            "idempotency_key": "idemp-001",
            "metadata": {"expediente_id": 42},
            "attachments": [
                {
                    "filename": "resolucion_001.pdf",
                    "content_base64": b64_content,
                    "mimetype": "application/pdf",
                }
            ],
        }

        outbox, created = EmailDispatcherService.create_or_get_outbox(payload)

        assert created is True
        assert outbox.idempotency_key == "idemp-001"
        assert outbox.status == EmailOutboxStatus.PENDING
        assert outbox.to == ["socio@aveit.utn.edu.ar"]
        assert outbox.cc == ["directiva@aveit.utn.edu.ar"]
        assert outbox.bcc == ["auditoria@aveit.utn.edu.ar"]
        assert outbox.attachments.count() == 1

        att = outbox.attachments.first()
        assert att.filename == "resolucion_001.pdf"
        assert att.mimetype == "application/pdf"
        assert att.content_base64 == b64_content

    def test_create_outbox_idempotency_reuses_existing(self) -> None:
        payload = {
            "to": ["socio@aveit.utn.edu.ar"],
            "subject": "Aviso con Idempotencia",
            "body_text": "Contenido",
            "idempotency_key": "unique-token-xyz",
        }

        outbox1, created1 = EmailDispatcherService.create_or_get_outbox(payload)
        assert created1 is True

        outbox2, created2 = EmailDispatcherService.create_or_get_outbox(payload)
        assert created2 is False
        assert outbox1.id == outbox2.id
        assert EmailOutbox.objects.filter(idempotency_key="unique-token-xyz").count() == 1

    @patch("django.core.mail.message.EmailMultiAlternatives.send")
    def test_dispatch_success_marks_sent(self, mock_send) -> None:
        mock_send.return_value = 1

        outbox = EmailOutbox.objects.create(
            to=["socio@aveit.utn.edu.ar"],
            subject="Prueba de Envío Inmediato",
            body_text="Cuerpo en texto plano",
            status=EmailOutboxStatus.PENDING,
        )

        success = EmailDispatcherService.dispatch(outbox)

        assert success is True
        outbox.refresh_from_db()
        assert outbox.status == EmailOutboxStatus.SENT
        assert outbox.sent_at is not None
        assert outbox.last_error is None
        mock_send.assert_called_once()

    @patch("django.core.mail.message.EmailMultiAlternatives.send")
    def test_dispatch_connection_failure_schedules_retry(self, mock_send) -> None:
        mock_send.side_effect = socket.error("Connection refused to SMTP server")

        outbox = EmailOutbox.objects.create(
            to=["socio@aveit.utn.edu.ar"],
            subject="Prueba de Corte de Conexión",
            body_text="Cuerpo",
            status=EmailOutboxStatus.PENDING,
        )

        before_now = timezone.now()
        success = EmailDispatcherService.dispatch(outbox)

        assert success is False
        outbox.refresh_from_db()
        assert outbox.status == EmailOutboxStatus.PENDING
        assert outbox.retry_count == 1
        assert "Connection refused" in outbox.last_error
        assert outbox.next_retry_at > before_now

    @patch("django.core.mail.message.EmailMultiAlternatives.send")
    def test_dispatch_exceeding_max_retries_marks_failed(self, mock_send) -> None:
        mock_send.side_effect = socket.error("Persistent connection failure")

        outbox = EmailOutbox.objects.create(
            to=["socio@aveit.utn.edu.ar"],
            subject="Prueba de Agotamiento de Reintentos",
            body_text="Cuerpo",
            status=EmailOutboxStatus.PENDING,
            retry_count=4,
            max_retries=5,
        )

        success = EmailDispatcherService.dispatch(outbox)

        assert success is False
        outbox.refresh_from_db()
        assert outbox.status == EmailOutboxStatus.FAILED
        assert outbox.retry_count == 5

    @patch("django.core.mail.message.EmailMultiAlternatives.send")
    def test_process_pending_queue_flushes_when_connection_restored(self, mock_send) -> None:
        # Creamos 2 mensajes encolados
        o1 = EmailOutbox.objects.create(
            to=["socio1@aveit.utn.edu.ar"],
            subject="Pendiente 1",
            body_text="Cuerpo 1",
            status=EmailOutboxStatus.PENDING,
            next_retry_at=timezone.now() - timezone.timedelta(minutes=5),
        )
        o2 = EmailOutbox.objects.create(
            to=["socio2@aveit.utn.edu.ar"],
            subject="Pendiente 2",
            body_text="Cuerpo 2",
            status=EmailOutboxStatus.PENDING,
            next_retry_at=timezone.now() - timezone.timedelta(minutes=2),
        )

        # SMTP vuelve a estar disponible
        mock_send.return_value = 1

        result = EmailDispatcherService.process_pending_queue(batch_size=10, force=False)

        assert result["processed"] == 2
        assert result["sent"] == 2
        assert result["failed"] == 0

        o1.refresh_from_db()
        o2.refresh_from_db()
        assert o1.status == EmailOutboxStatus.SENT
        assert o2.status == EmailOutboxStatus.SENT
