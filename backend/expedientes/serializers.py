"""Serializadores para el módulo de expedientes y descargos."""

from rest_framework import serializers

from expedientes.models import Expediente, TipoDescargoEnum


class ExpedienteListSerializer(serializers.ModelSerializer):
    """Serializador para listado y detalle de expedientes."""

    socio_nombre = serializers.SerializerMethodField()
    socio_legajo = serializers.CharField(source="socio.legajo", read_only=True)
    subcomision = serializers.CharField(source="socio.subcomision.name", default="", read_only=True)
    esta_en_plazo = serializers.SerializerMethodField()
    horas_restantes = serializers.SerializerMethodField()

    class Meta:
        model = Expediente
        fields = [
            "id",
            "numero",
            "motivo",
            "puntos",
            "estado",
            "socio_nombre",
            "socio_legajo",
            "subcomision",
            "plazo_inicio_at",
            "plazo_limite_at",
            "descargo_presentado",
            "descargo_tipo",
            "descargo_causal",
            "descargo_archivo",
            "descargo_texto",
            "descargo_presentado_at",
            "esta_en_plazo",
            "horas_restantes",
            "created_at",
        ]

    def get_socio_nombre(self, obj: Expediente) -> str:
        return f"{obj.socio.first_name} {obj.socio.last_name}"

    def get_esta_en_plazo(self, obj: Expediente) -> bool:
        return obj.esta_en_plazo()

    def get_horas_restantes(self, obj: Expediente) -> int:
        if not obj.plazo_limite_at or obj.estado != "justificando":
            return 0
        from django.utils import timezone

        diff = obj.plazo_limite_at - timezone.now()
        horas = int(diff.total_seconds() // 3600)
        return max(0, horas)


class PresentarDescargoSerializer(serializers.Serializer):
    """Payload para presentación de descargo T02/T03."""

    tipo = serializers.ChoiceField(choices=TipoDescargoEnum.choices)
    causal = serializers.CharField(max_length=255, required=False, allow_blank=True)
    archivo = serializers.CharField(max_length=255, required=False, allow_blank=True)
    texto = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs: dict) -> dict:
        tipo = attrs.get("tipo")
        if tipo == TipoDescargoEnum.T02_CERTIFICADO:
            if not attrs.get("archivo"):
                raise serializers.ValidationError(
                    {"archivo": "Es obligatorio adjuntar comprobante para justificaciones T02."}
                )
        elif tipo == TipoDescargoEnum.T03_EXTRAORDINARIO:
            if not attrs.get("texto", "").strip():
                raise serializers.ValidationError(
                    {"texto": "Es obligatorio incluir la exposición fáctica para descargos T03."}
                )
        return attrs


class DispatchNotificationResponseSerializer(serializers.Serializer):
    """Payload de respuesta tras el despacho formal de la notificación de apertura."""

    expediente_id = serializers.IntegerField()
    numero = serializers.CharField()
    estado = serializers.CharField()
    plazo_inicio_at = serializers.DateTimeField()
    plazo_limite_at = serializers.DateTimeField()
    outbox_id = serializers.UUIDField()
    outbox_status = serializers.CharField()
    idempotency_key = serializers.CharField()
    mensaje = serializers.CharField(
        required=False, default="Notificación de apertura despachada correctamente."
    )


# Backward-compatible alias for existing imports
DespachoNotificacionResponseSerializer = DispatchNotificationResponseSerializer


class CaseNotificationAuditSerializer(serializers.ModelSerializer):
    """Serializador de auditoría y bitácora de entrega para operadores del TD."""

    destinatario = serializers.JSONField(source="to")
    asunto = serializers.CharField(source="subject")
    estado = serializers.CharField(source="status")
    reintentos = serializers.IntegerField(source="retry_count")
    max_reintentos = serializers.IntegerField(source="max_retries")
    proximo_reintento_at = serializers.DateTimeField(source="next_retry_at")
    ultimo_error = serializers.CharField(source="last_error", allow_null=True)
    despachado_at = serializers.DateTimeField(source="sent_at", allow_null=True)

    class Meta:
        from notifications.models import EmailOutbox

        model = EmailOutbox
        fields = [
            "id",
            "destinatario",
            "asunto",
            "estado",
            "reintentos",
            "max_reintentos",
            "proximo_reintento_at",
            "ultimo_error",
            "despachado_at",
            "created_at",
        ]


# Backward-compatible alias for existing imports
ExpedienteNotificationAuditSerializer = CaseNotificationAuditSerializer
