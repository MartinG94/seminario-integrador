"""
Pruebas de API REST para los endpoints de notificaciones (/apiDesign y /backendTesting).
"""

import base64
import socket
from unittest.mock import patch

import pytest
from django.conf import settings
from rest_framework import status
from rest_framework.test import APIClient

from notifications.models import EmailOutbox, EmailOutboxStatus
from socios.models import Role


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture
def service_headers() -> dict[str, str]:
    key = getattr(settings, "INTERNAL_SERVICE_KEY", "aveit-internal-service-secret-2026")
    return {"HTTP_X_INTERNAL_SERVICE_KEY": key}


@pytest.mark.django_db
class TestSendEmailAPI:
    def test_send_email_forbidden_without_auth(self, api_client: APIClient) -> None:
        payload = {
            "to": "socio@aveit.utn.edu.ar",
            "subject": "Aviso",
            "body_text": "Texto",
        }
        response = api_client.post("/api/v1/notifications/email/", payload, format="json")
        assert response.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)

    def test_send_email_forbidden_with_invalid_service_key(self, api_client: APIClient) -> None:
        payload = {
            "to": "socio@aveit.utn.edu.ar",
            "subject": "Aviso",
            "body_text": "Texto",
        }
        response = api_client.post(
            "/api/v1/notifications/email/",
            payload,
            format="json",
            HTTP_X_INTERNAL_SERVICE_KEY="invalid-key-xyz",
        )
        assert response.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)

    def test_send_email_validation_error_missing_fields_400(
        self, api_client: APIClient, service_headers: dict
    ) -> None:
        payload = {"to": "not-an-email"}
        response = api_client.post(
            "/api/v1/notifications/email/", payload, format="json", **service_headers
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "subject" in response.data
        assert "body_text" in response.data
        assert "to" in response.data

    @patch("django.core.mail.message.EmailMultiAlternatives.send")
    def test_send_email_immediate_success_returns_200(
        self, mock_send, api_client: APIClient, service_headers: dict
    ) -> None:
        mock_send.return_value = 1

        payload = {
            "to": "socio@aveit.utn.edu.ar",
            "cc": ["directiva@aveit.utn.edu.ar"],
            "bcc": ["auditoria@aveit.utn.edu.ar"],
            "subject": "Aviso de Apertura",
            "body_text": "Cuerpo plano",
            "body_html": "<p>Cuerpo HTML</p>",
            "metadata": {"tipo": "apertura", "expediente": 10},
        }

        response = api_client.post(
            "/api/v1/notifications/email/", payload, format="json", **service_headers
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == EmailOutboxStatus.SENT
        assert response.data["subject"] == "Aviso de Apertura"
        assert response.data["to"] == ["socio@aveit.utn.edu.ar"]
        assert response.data["cc"] == ["directiva@aveit.utn.edu.ar"]
        assert response.data["bcc"] == ["auditoria@aveit.utn.edu.ar"]
        assert response.data["sent_at"] is not None
        mock_send.assert_called_once()

    @patch("django.core.mail.message.EmailMultiAlternatives.send")
    def test_send_email_smtp_offline_returns_202_accepted(
        self, mock_send, api_client: APIClient, service_headers: dict
    ) -> None:
        # Simulamos falla de conectividad SMTP
        mock_send.side_effect = socket.error("Connection timed out to mail gateway")

        payload = {
            "to": ["socio@aveit.utn.edu.ar"],
            "subject": "Aviso con Caída de Red",
            "body_text": "Se debe encolar en Outbox",
        }

        response = api_client.post(
            "/api/v1/notifications/email/", payload, format="json", **service_headers
        )

        assert response.status_code == status.HTTP_202_ACCEPTED
        assert response.data["status"] == EmailOutboxStatus.PENDING
        assert response.data["retry_count"] == 1
        assert "timed out" in response.data["last_error"]

        # Verificamos persistencia en base de datos
        outbox = EmailOutbox.objects.get(id=response.data["id"])
        assert outbox.status == EmailOutboxStatus.PENDING

    @patch("django.core.mail.message.EmailMultiAlternatives.send")
    def test_send_email_with_base64_attachments(
        self, mock_send, api_client: APIClient, service_headers: dict
    ) -> None:
        mock_send.return_value = 1
        dummy_data = b"Contenido binario de prueba"
        b64 = base64.b64encode(dummy_data).decode("utf-8")

        payload = {
            "to": "socio@aveit.utn.edu.ar",
            "subject": "Aviso con Adjunto",
            "body_text": "Ver archivo adjunto",
            "attachments": [
                {
                    "filename": "formulario_t01.pdf",
                    "content_base64": b64,
                    "mimetype": "application/pdf",
                }
            ],
        }

        response = api_client.post(
            "/api/v1/notifications/email/", payload, format="json", **service_headers
        )

        assert response.status_code == status.HTTP_200_OK
        outbox = EmailOutbox.objects.get(id=response.data["id"])
        assert outbox.attachments.count() == 1
        att = outbox.attachments.first()
        assert att.filename == "formulario_t01.pdf"
        assert att.content_base64 == b64

    @patch("django.core.mail.message.EmailMultiAlternatives.send")
    def test_send_email_idempotency_prevents_duplicate_sending(
        self, mock_send, api_client: APIClient, service_headers: dict
    ) -> None:
        mock_send.return_value = 1

        payload = {
            "to": "socio@aveit.utn.edu.ar",
            "subject": "Idempotent Notice",
            "body_text": "Text",
            "idempotency_key": "idemp-client-12345",
        }

        # Primer request
        res1 = api_client.post(
            "/api/v1/notifications/email/", payload, format="json", **service_headers
        )
        assert res1.status_code == status.HTTP_200_OK
        assert mock_send.call_count == 1

        # Segundo request idéntico
        res2 = api_client.post(
            "/api/v1/notifications/email/", payload, format="json", **service_headers
        )
        assert res2.status_code == status.HTTP_200_OK
        assert res1.data["id"] == res2.data["id"]
        # No se debe haber invocado mock_send nuevamente
        assert mock_send.call_count == 1
        assert EmailOutbox.objects.filter(idempotency_key="idemp-client-12345").count() == 1

    @patch("django.core.mail.message.EmailMultiAlternatives.send")
    def test_send_email_authorized_with_admin_user_jwt(
        self, mock_send, authenticate, make_socio
    ) -> None:
        mock_send.return_value = 1
        admin_socio = make_socio(legajo="99999", role=Role.ADMIN)
        authed_client = authenticate(admin_socio)

        payload = {
            "to": "socio@aveit.utn.edu.ar",
            "subject": "Enviado por Admin",
            "body_text": "Contenido",
        }

        response = authed_client.post("/api/v1/notifications/email/", payload, format="json")
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestRetryQueueAPI:
    @patch("django.core.mail.message.EmailMultiAlternatives.send")
    def test_retry_queue_endpoint_authorized(
        self, mock_send, api_client: APIClient, service_headers: dict
    ) -> None:
        mock_send.return_value = 1

        EmailOutbox.objects.create(
            to=["socio@aveit.utn.edu.ar"],
            subject="Pendiente para retry",
            body_text="Texto",
            status=EmailOutboxStatus.PENDING,
        )

        response = api_client.post(
            "/api/v1/notifications/email/retry/?force=true", **service_headers
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["processed"] >= 1
        assert response.data["sent"] >= 1
