"""Serializadores para el módulo de expedientes y descargos."""

from rest_framework import serializers

from expedientes.models import (
    DescargoExpediente,
    Expediente,
    TipoDescargoEnum,
)
from socios.models import Socio


class ExpedienteListSerializer(serializers.ModelSerializer):
    """Serializador para listado y detalle de expedientes."""

    socio_nombre = serializers.SerializerMethodField()
    socio_legajo = serializers.CharField(source="socio.legajo", read_only=True)
    subcomision = serializers.CharField(source="socio.subcomision.name", default="", read_only=True)
    descargo_presentado = serializers.SerializerMethodField()
    descargo_tipo = serializers.SerializerMethodField()
    descargo_causal = serializers.SerializerMethodField()
    descargo_archivo = serializers.SerializerMethodField()
    descargo_texto = serializers.SerializerMethodField()
    descargo_presentado_at = serializers.SerializerMethodField()
    esta_en_plazo = serializers.SerializerMethodField()
    horas_restantes = serializers.SerializerMethodField()
    socios = serializers.SerializerMethodField()
    historial = serializers.SerializerMethodField()

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
            "socios",
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
            "historial",
        ]

    def get_socio_nombre(self, obj: Expediente) -> str:
        return f"{obj.socio.first_name} {obj.socio.last_name}"

    def _descargo_for_requester(self, obj: Expediente) -> DescargoExpediente | None:
        request = self.context.get("request")
        socio = getattr(request.user, "socio", None) if request else None
        if socio is None:
            return None
        # Se recorre la colección precargada para no consultar una vez por campo y fila.
        return next((d for d in obj.descargos.all() if d.socio_id == socio.pk), None)

    def get_descargo_presentado(self, obj: Expediente) -> bool:
        descargo = self._descargo_for_requester(obj)
        if descargo:
            return True
        request = self.context.get("request")
        socio = getattr(request.user, "socio", None) if request else None
        return bool(obj.descargo_presentado and obj.socio_id == getattr(socio, "id", None))

    def get_descargo_tipo(self, obj: Expediente) -> str | None:
        descargo = self._descargo_for_requester(obj)
        if descargo:
            return descargo.tipo
        return obj.descargo_tipo if self._is_primary_socio(obj) else None

    def get_descargo_causal(self, obj: Expediente) -> str | None:
        descargo = self._descargo_for_requester(obj)
        if descargo:
            return descargo.causal
        return obj.descargo_causal if self._is_primary_socio(obj) else None

    def get_descargo_archivo(self, obj: Expediente) -> str | None:
        descargo = self._descargo_for_requester(obj)
        if descargo:
            return descargo.archivo
        return obj.descargo_archivo if self._is_primary_socio(obj) else None

    def get_descargo_texto(self, obj: Expediente) -> str | None:
        descargo = self._descargo_for_requester(obj)
        if descargo:
            return descargo.texto
        return obj.descargo_texto if self._is_primary_socio(obj) else None

    def get_descargo_presentado_at(self, obj: Expediente):
        descargo = self._descargo_for_requester(obj)
        if descargo:
            return descargo.presentado_at
        return obj.descargo_presentado_at if self._is_primary_socio(obj) else None

    def _is_primary_socio(self, obj: Expediente) -> bool:
        request = self.context.get("request")
        socio = getattr(request.user, "socio", None) if request else None
        return bool(socio and obj.socio_id == socio.pk)

    def get_esta_en_plazo(self, obj: Expediente) -> bool:
        return obj.esta_en_plazo()

    def get_horas_restantes(self, obj: Expediente) -> int:
        if not obj.plazo_limite_at or obj.estado != "justificando":
            return 0
        from django.utils import timezone

        diff = obj.plazo_limite_at - timezone.now()
        horas = int(diff.total_seconds() // 3600)
        return max(0, horas)

    def get_socios(self, obj: Expediente) -> list[dict[str, int | str]]:
        return [
            {
                "id": socio.id,
                "legajo": socio.legajo,
                "nombre": f"{socio.first_name} {socio.last_name}",
            }
            for socio in obj.socios.all()
        ]

    def get_historial(self, obj: Expediente) -> list[dict[str, str]]:
        changes = sorted(obj.cambios_estado.all(), key=lambda c: (c.fecha_hora, c.id))
        return [
            {
                "estado_anterior": change.estado_anterior,
                "estado_nuevo": change.estado_nuevo,
                "actor": change.actor,
                "fecha_hora": change.fecha_hora.isoformat(),
                "motivo": change.motivo,
            }
            for change in changes
        ]


class AperturaExpedienteSerializer(serializers.Serializer):
    motivo = serializers.CharField(max_length=5000)
    socios = serializers.ListField(child=serializers.IntegerField(min_value=1), allow_empty=False)

    def validate_socios(self, value: list[int]) -> list[int]:
        if len(set(value)) != len(value):
            raise serializers.ValidationError("No se puede repetir un socio.")
        if set(value) != set(Socio.objects.filter(id__in=value).values_list("id", flat=True)):
            raise serializers.ValidationError("Uno o más socios no existen.")
        return value


class TransicionExpedienteSerializer(serializers.Serializer):
    estado = serializers.ChoiceField(choices=Expediente._meta.get_field("estado").choices)
    motivo = serializers.CharField(max_length=5000)


class DescargoExpedienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = DescargoExpediente
        fields = ["id", "socio", "tipo", "causal", "archivo", "texto", "presentado_at"]


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
