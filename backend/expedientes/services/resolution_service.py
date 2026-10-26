"""Casos de uso transaccionales de resolución oficial."""
import hashlib
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from expedientes.domain.closed_decision import ClosedDecisionProvider
from expedientes.models import EstadoResolucionEnum, Resolucion


class DictamenNoCerradoError(Exception):
    pass


class UnavailableClosedDecisionProvider:
    """Implementación temporal hasta integrar el contrato persistente de SCRUM-55."""

    def get_closed_decision(self, expediente_id):
        return None


@transaction.atomic
def emitir_resolucion(
    resolucion: Resolucion, emisor, provider: ClosedDecisionProvider
) -> Resolucion:
    resolucion = (
        Resolucion.objects.select_for_update()
        .select_related("expediente")
        .get(pk=resolucion.pk)
    )
    if resolucion.estado == EstadoResolucionEnum.ISSUED:
        raise ValidationError("La resolución ya fue emitida.")
    decision = provider.get_closed_decision(resolucion.expediente_id)
    if decision is None or decision.estado != "CLOSED":
        raise DictamenNoCerradoError("No existe un dictamen cerrado para el expediente.")
    required_fields = (
        ("vistos", "Los Vistos"),
        ("considerandos", "Los Considerandos"),
        ("articulos_resolutivos", "Los artículos resolutivos"),
    )
    for field, label in required_fields:
        if not getattr(resolucion, field).strip():
            raise ValidationError({field: f"{label} son obligatorios."})
    resolucion.numero_expediente_snapshot = resolucion.expediente.numero
    resolucion.puntos_finales = Decimal(decision.puntos_finales).quantize(Decimal("0.01"))
    resolucion.medidas = list(decision.medidas)
    resolucion.estado = EstadoResolucionEnum.ISSUED
    resolucion.issued_by = emisor
    resolucion.issued_at = timezone.now()
    payload = "|".join(
        (
            resolucion.numero_expediente_snapshot,
            resolucion.vistos,
            resolucion.considerandos,
            resolucion.articulos_resolutivos,
            str(resolucion.puntos_finales),
            repr(resolucion.medidas),
        )
    )
    resolucion.contenido_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    resolucion.save()
    return resolucion
