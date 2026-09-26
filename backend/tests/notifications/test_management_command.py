"""
Pruebas del comando de gestión process_email_queue.
"""

from io import StringIO
from unittest.mock import patch

import pytest
from django.core.management import call_command

from notifications.models import EmailOutbox, EmailOutboxStatus


@pytest.mark.django_db
class TestProcessEmailQueueCommand:
    @patch("django.core.mail.message.EmailMultiAlternatives.send")
    def test_process_email_queue_command_success(self, mock_send) -> None:
        mock_send.return_value = 1

        EmailOutbox.objects.create(
            to=["socio@aveit.utn.edu.ar"],
            subject="Aviso por comando",
            body_text="Texto",
            status=EmailOutboxStatus.PENDING,
        )

        out = StringIO()
        call_command("process_email_queue", "--force", stdout=out)

        output = out.getvalue()
        assert "Iniciando procesamiento Outbox" in output
        assert "Procesados=1" in output
        assert "Enviados=1" in output
        assert "Fallidos=0" in output
