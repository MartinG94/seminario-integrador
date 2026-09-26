"""
Modelos de datos para el encolador transaccional de correos electrónicos (Transactional Outbox).

Garantiza la persistencia inmutable de notificaciones procesales y acuses
ante eventuales pérdidas de conexión con el servidor SMTP institucional.
"""

import uuid

from django.db import models
from django.utils import timezone


class EmailOutboxStatus(models.TextChoices):
    PENDING = "PENDING", "Pendiente de envío o reintento"
    SENT = "SENT", "Despachado exitosamente"
    FAILED = "FAILED", "Falló tras agotar reintentos"


class EmailOutbox(models.Model):
    """Registro de mensaje en la cola transaccional de salida (Outbox)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    to = models.JSONField(help_text="Lista de direcciones de correo destinatarias principales.")
    cc = models.JSONField(
        default=list, blank=True, help_text="Lista de direcciones de correo en copia."
    )
    bcc = models.JSONField(
        default=list, blank=True, help_text="Lista de direcciones de correo en copia oculta."
    )
    subject = models.CharField(max_length=255)
    body_text = models.TextField(help_text="Contenido del mensaje en texto plano.")
    body_html = models.TextField(
        blank=True, null=True, help_text="Contenido opcional del mensaje formateado en HTML."
    )
    status = models.CharField(
        max_length=20,
        choices=EmailOutboxStatus.choices,
        default=EmailOutboxStatus.PENDING,
        db_index=True,
    )
    retry_count = models.PositiveIntegerField(default=0)
    max_retries = models.PositiveIntegerField(default=5)
    next_retry_at = models.DateTimeField(default=timezone.now, db_index=True)
    last_error = models.TextField(blank=True, null=True)
    idempotency_key = models.CharField(
        max_length=128, blank=True, null=True, unique=True, db_index=True
    )
    metadata = models.JSONField(
        default=dict, blank=True, help_text="Metadatos contextuales para auditoría y trazabilidad."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = "notifications_email_outbox"
        ordering = ["-created_at"]
        verbose_name = "Mensaje Outbox"
        verbose_name_plural = "Mensajes Outbox"

    def __str__(self) -> str:
        dest = ", ".join(self.to) if isinstance(self.to, list) else str(self.to)
        return f"[{self.status}] {self.subject} -> {dest}"


class EmailAttachment(models.Model):
    """Archivo adjunto asociado a un mensaje Outbox encolado."""

    email = models.ForeignKey(EmailOutbox, on_delete=models.CASCADE, related_name="attachments")
    filename = models.CharField(max_length=255)
    content_base64 = models.TextField(help_text="Contenido binario codificado en Base64.")
    mimetype = models.CharField(max_length=100, default="application/octet-stream")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "notifications_email_attachment"
        verbose_name = "Adjunto de Notificación"
        verbose_name_plural = "Adjuntos de Notificaciones"

    def __str__(self) -> str:
        return f"{self.filename} ({self.mimetype})"
