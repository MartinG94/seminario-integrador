from decimal import Decimal

from django.utils import timezone
from rest_framework import serializers

from padron.factory import get_padron_repository

from .models import SolicitudT01


class SolicitudT01Serializer(serializers.ModelSerializer):
    class Meta:
        model = SolicitudT01
        fields = "__all__"
        read_only_fields = (
            "id",
            "estado",
            "solicitante",
            "snapshot_destinatario",
            "snapshot_emitido",
            "numero_expediente",
            "created_at",
            "updated_at",
            "issued_at",
        )

    def validate_tipo_accion(self, value):
        if value not in SolicitudT01.TipoAccion.values:
            raise serializers.ValidationError("Tipo de acción inválido.")
        return value

    def validate(self, attrs):
        if self.instance and self.instance.estado == SolicitudT01.Estado.ISSUED:
            raise serializers.ValidationError("Una solicitud emitida es inmutable.")
        puntos = attrs.get("puntos", getattr(self.instance, "puntos", None))
        accion = attrs.get("tipo_accion", getattr(self.instance, "tipo_accion", None))
        if puntos is not None and accion:
            if accion == SolicitudT01.TipoAccion.SANCTION and puntos >= Decimal("0"):
                raise serializers.ValidationError({"puntos": "La sanción debe ser negativa."})
            if accion == SolicitudT01.TipoAccion.MERIT and puntos <= Decimal("0"):
                raise serializers.ValidationError({"puntos": "El mérito debe ser positivo."})
        return attrs


def _snapshot(socio):
    sub = socio.subcomision
    category = getattr(socio.category, "value", socio.category)
    status = getattr(socio.membership_status, "value", socio.membership_status)
    return {
        "socio_id": socio.socio_id,
        "legajo": socio.legajo,
        "dni": socio.dni,
        "first_name": socio.first_name,
        "last_name": socio.last_name,
        "email": socio.email,
        "subcomision": {"id": sub.id, "name": sub.name} if sub else None,
        "social_year": socio.social_year,
        "category": category,
        "is_active": socio.is_active,
        "membership_status": status,
    }


class EmitirT01Serializer(serializers.Serializer):
    def validate(self, attrs):
        solicitud = self.context["solicitud"]
        if solicitud.estado == SolicitudT01.Estado.ISSUED:
            return attrs
        if solicitud.destinatario_socio_id is None:
            raise serializers.ValidationError({"destinatario_socio_id": "Es requerido al emitir."})
        if solicitud.puntos is None:
            raise serializers.ValidationError({"puntos": "Los puntos son requeridos al emitir."})
        if not solicitud.motivo.strip():
            raise serializers.ValidationError({"motivo": "Es requerido al emitir."})
        socio = get_padron_repository().get_by_id(solicitud.destinatario_socio_id)
        if socio is None:
            raise serializers.ValidationError(
                {"destinatario_socio_id": "El socio no existe en el padrón."}
            )
        if not socio.is_active:
            raise serializers.ValidationError({"destinatario_socio_id": "El socio no está activo."})
        return attrs

    def save(self):
        solicitud = self.context["solicitud"]
        if solicitud.estado == SolicitudT01.Estado.ISSUED:
            return solicitud
        socio = get_padron_repository().get_by_id(solicitud.destinatario_socio_id)
        solicitud.snapshot_destinatario = _snapshot(socio)
        solicitud.snapshot_emitido = {
            "id": str(solicitud.id),
            "tipo_accion": solicitud.tipo_accion,
            "causal": solicitud.causal,
            "puntos": str(solicitud.puntos),
            "motivo": solicitud.motivo,
            "destinatario": solicitud.snapshot_destinatario,
            "anexo_fecha": solicitud.anexo_fecha.isoformat() if solicitud.anexo_fecha else None,
            "anexo_lugar": solicitud.anexo_lugar,
            "anexo_relato": solicitud.anexo_relato,
            "anexo_testigos": solicitud.anexo_testigos,
        }
        solicitud.estado = SolicitudT01.Estado.ISSUED
        solicitud.issued_at = timezone.now()
        solicitud.numero_expediente = (
            f"T01-{solicitud.issued_at:%Y}-{solicitud.id.hex[:12].upper()}"
        )
        solicitud.save()
        return solicitud
