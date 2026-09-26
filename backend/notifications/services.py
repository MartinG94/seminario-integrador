"""
Servicios de dominio para el encolado, renderizado y despacho de notificaciones por correo.
"""

import base64
import logging
from datetime import timedelta
from typing import Any

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.db import transaction
from django.utils import timezone

from notifications.models import EmailAttachment, EmailOutbox, EmailOutboxStatus

logger = logging.getLogger(__name__)


class EmailDispatcherService:
    """Orquestador de persistencia Outbox y despacho de correos electrónicos."""

    @classmethod
    def create_or_get_outbox(cls, validated_data: dict[str, Any]) -> tuple[EmailOutbox, bool]:
        """
        Persiste atómicamente el mensaje y sus adjuntos en la cola Outbox.
        Respeta la clave de idempotencia: si ya existe un registro con esa clave,
        lo retorna sin duplicar la creación en base de datos.
        """
        data = dict(validated_data)
        idempotency_key = data.get("idempotency_key")

        if idempotency_key:
            existing = EmailOutbox.objects.filter(idempotency_key=idempotency_key).first()
            if existing:
                logger.info(
                    "Idempotencia detectada para clave '%s'. Reutilizando registro %s.",
                    idempotency_key,
                    existing.id,
                )
                return existing, False

        attachments_data = data.pop("attachments", [])

        with transaction.atomic():
            outbox = EmailOutbox.objects.create(
                to=data["to"],
                cc=data.get("cc", []),
                bcc=data.get("bcc", []),
                subject=data["subject"],
                body_text=data["body_text"],
                body_html=data.get("body_html"),
                idempotency_key=idempotency_key,
                metadata=data.get("metadata", {}),
                status=EmailOutboxStatus.PENDING,
            )

            for att in attachments_data:
                EmailAttachment.objects.create(
                    email=outbox,
                    filename=att["filename"],
                    content_base64=att["content_base64"],
                    mimetype=att.get("mimetype", "application/octet-stream"),
                )

        return outbox, True

    @classmethod
    def dispatch(cls, outbox: EmailOutbox) -> bool:
        """
        Intenta el envío inmediato del correo mediante el backend de Django configurado.
        Si la conexión SMTP es exitosa, marca el registro como SENT y fija sent_at.
        Si ocurre una falla de red/conexión, programa el próximo reintento con backoff exponencial.
        """
        if outbox.status == EmailOutboxStatus.SENT:
            return True

        from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "notificaciones@aveit.utn.edu.ar")
        to_list = outbox.to if isinstance(outbox.to, list) else [outbox.to]
        cc_list = outbox.cc if isinstance(outbox.cc, list) else []
        bcc_list = outbox.bcc if isinstance(outbox.bcc, list) else []

        msg = EmailMultiAlternatives(
            subject=outbox.subject,
            body=outbox.body_text,
            from_email=from_email,
            to=to_list,
            cc=cc_list,
            bcc=bcc_list,
        )

        if outbox.body_html:
            msg.attach_alternative(outbox.body_html, "text/html")

        # Adjuntar archivos
        for att in outbox.attachments.all():
            try:
                decoded_content = base64.b64decode(att.content_base64)
                msg.attach(att.filename, decoded_content, att.mimetype)
            except Exception as att_err:
                logger.error("Error al decodificar adjunto %s: %s", att.filename, att_err)

        try:
            msg.send(fail_silently=False)
            outbox.status = EmailOutboxStatus.SENT
            outbox.sent_at = timezone.now()
            outbox.last_error = None
            outbox.save(update_fields=["status", "sent_at", "last_error"])
            logger.info("Correo despachado con éxito: outbox_id=%s, to=%s", outbox.id, to_list)
            return True
        except Exception as exc:
            outbox.retry_count += 1
            error_message = f"{type(exc).__name__}: {str(exc)}"
            outbox.last_error = error_message

            if outbox.retry_count >= outbox.max_retries:
                outbox.status = EmailOutboxStatus.FAILED
                logger.warning(
                    "Correo %s agotó los %s reintentos máximos. Estado: FAILED. Error: %s",
                    outbox.id,
                    outbox.max_retries,
                    error_message,
                )
            else:
                outbox.status = EmailOutboxStatus.PENDING
                # Backoff exponencial: 2 ** retry_count minutos (máx 60 min)
                backoff_seconds = min((2**outbox.retry_count) * 60, 3600)
                outbox.next_retry_at = timezone.now() + timedelta(seconds=backoff_seconds)
                logger.info(
                    "Falla de envío para correo %s (intento %s/%s). "
                    "Reintento programado para %s. Error: %s",
                    outbox.id,
                    outbox.retry_count,
                    outbox.max_retries,
                    outbox.next_retry_at,
                    error_message,
                )

            outbox.save(update_fields=["retry_count", "last_error", "status", "next_retry_at"])
            return False

    @classmethod
    def process_pending_queue(cls, batch_size: int = 50, force: bool = False) -> dict[str, int]:
        """
        Recupera mensajes pendientes de envío o reintento y ejecuta el despacho.
        """
        now = timezone.now()
        qs = EmailOutbox.objects.filter(status=EmailOutboxStatus.PENDING)
        if not force:
            qs = qs.filter(next_retry_at__lte=now)

        eligible_items = list(qs.order_by("created_at")[:batch_size])

        processed_count = 0
        sent_count = 0
        failed_count = 0

        for item in eligible_items:
            processed_count += 1
            success = cls.dispatch(item)
            if success:
                sent_count += 1
            else:
                # Recargar para verificar si pasó a FAILED o sigue PENDING
                item.refresh_from_db(fields=["status"])
                if item.status == EmailOutboxStatus.FAILED:
                    failed_count += 1

        pending_remaining = EmailOutbox.objects.filter(status=EmailOutboxStatus.PENDING).count()

        return {
            "processed": processed_count,
            "sent": sent_count,
            "failed": failed_count,
            "pending": pending_remaining,
        }
