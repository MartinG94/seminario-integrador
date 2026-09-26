"""
Serializadores DRF para validación de contratos de notificación por correo.
"""

import base64
from typing import Any

from rest_framework import serializers

from notifications.models import EmailAttachment, EmailOutbox


class EmailAttachmentSerializer(serializers.ModelSerializer):
    """Serializador para archivos adjuntos codificados en Base64."""

    filename = serializers.CharField(max_length=255)
    content_base64 = serializers.CharField()
    mimetype = serializers.CharField(max_length=100, default="application/octet-stream")

    class Meta:
        model = EmailAttachment
        fields = ("filename", "content_base64", "mimetype")

    def validate_content_base64(self, value: str) -> str:
        """Valida que el contenido sea un string Base64 válido y no exceda 10MB."""
        try:
            decoded = base64.b64decode(value, validate=True)
        except Exception as exc:
            raise serializers.ValidationError(
                "El contenido del adjunto no es Base64 válido."
            ) from exc

        max_bytes = 10 * 1024 * 1024  # 10 MB
        if len(decoded) > max_bytes:
            raise serializers.ValidationError(
                "El archivo adjunto supera el tamaño máximo permitido de 10 MB."
            )
        return value


class SendEmailRequestSerializer(serializers.Serializer):
    """Validador estricto del payload de envío de correo."""

    to = serializers.ListField(
        child=serializers.EmailField(),
        allow_empty=False,
        help_text="Lista de emails destinatarios principales.",
    )
    cc = serializers.ListField(
        child=serializers.EmailField(),
        required=False,
        default=list,
        help_text="Lista de correos en copia.",
    )
    bcc = serializers.ListField(
        child=serializers.EmailField(),
        required=False,
        default=list,
        help_text="Lista de correos en copia oculta.",
    )
    subject = serializers.CharField(max_length=255)
    body_text = serializers.CharField(help_text="Cuerpo en texto plano obligatorio.")
    body_html = serializers.CharField(
        required=False, allow_blank=True, allow_null=True, default=None
    )
    attachments = EmailAttachmentSerializer(many=True, required=False, default=list)
    idempotency_key = serializers.CharField(
        max_length=128, required=False, allow_blank=True, allow_null=True, default=None
    )
    metadata = serializers.DictField(required=False, default=dict)

    def to_internal_value(self, data: Any) -> dict:
        # Si 'to' viene como un único string email, normalizarlo a lista
        if isinstance(data, dict) and isinstance(data.get("to"), str):
            data = data.copy()
            data["to"] = [data["to"]]
        return super().to_internal_value(data)


class EmailOutboxResponseSerializer(serializers.ModelSerializer):
    """Representación pública del registro en cola Outbox."""

    class Meta:
        model = EmailOutbox
        fields = (
            "id",
            "to",
            "cc",
            "bcc",
            "subject",
            "status",
            "retry_count",
            "max_retries",
            "next_retry_at",
            "last_error",
            "idempotency_key",
            "metadata",
            "created_at",
            "sent_at",
        )


class RetryQueueResponseSerializer(serializers.Serializer):
    """Estadísticas de la ejecución del reintento de la cola."""

    processed = serializers.IntegerField()
    sent = serializers.IntegerField()
    failed = serializers.IntegerField()
    pending = serializers.IntegerField()
