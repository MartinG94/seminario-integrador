"""Servicios transaccionales para apertura y transiciones de expedientes."""

from datetime import datetime
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from expedientes.domain.calendar import compute_business_deadline
from expedientes.domain.holiday_provider import Argentina2026HolidayProvider
from expedientes.models import (
    CambioEstadoExpediente,
    EstadoExpedienteEnum,
    Expediente,
    ExpedienteNumberSequence,
    UrgenciaExpedienteEnum,
)
from socios.models import Socio


class ExpedienteWorkflowService:
    """Aplica el ciclo secuencial y auditable del Art. 12."""

    NEXT_STATE = {
        EstadoExpedienteEnum.CREADO: EstadoExpedienteEnum.JUSTIFICANDO,
        EstadoExpedienteEnum.JUSTIFICANDO: EstadoExpedienteEnum.REVISION_RESOLUCION,
        EstadoExpedienteEnum.REVISION_RESOLUCION: EstadoExpedienteEnum.ESPERA_RESOLUCION,
        EstadoExpedienteEnum.ESPERA_RESOLUCION: EstadoExpedienteEnum.PENDIENTE_CORREOS,
        EstadoExpedienteEnum.PENDIENTE_CORREOS: EstadoExpedienteEnum.EMITIDO,
    }

    @staticmethod
    def format_numero(value: int, year: int) -> str:
        return f"EXP-{value:04d}/{year}"

    @classmethod
    @transaction.atomic
    def open_expediente(
        cls,
        *,
        motivo: str,
        socio_ids: list[int],
        actor: str,
        urgencia: str = UrgenciaExpedienteEnum.NORMAL,
        points: Decimal = Decimal("-1.0"),
    ) -> Expediente:
        if not motivo.strip():
            raise ValidationError({"motivo": "El motivo de apertura es obligatorio."})
        if not socio_ids:
            raise ValidationError({"socios": "Debe asociarse al menos un socio."})
        if Socio.objects.filter(pk__in=socio_ids).count() != len(set(socio_ids)):
            raise ValidationError({"socios": "Uno o más socios no existen."})

        year = timezone.localdate().year
        expediente = Expediente.objects.create(
            numero=cls.format_numero(ExpedienteNumberSequence.next_value(year), year),
            socio_id=socio_ids[0],
            motivo=motivo.strip(),
            estado=EstadoExpedienteEnum.CREADO,
            urgencia=urgencia,
            puntos=points,
        )
        expediente.socios.set(socio_ids)
        CambioEstadoExpediente.objects.create(
            expediente=expediente,
            estado_anterior=EstadoExpedienteEnum.CREADO,
            estado_nuevo=EstadoExpedienteEnum.CREADO,
            actor=actor,
            motivo=motivo.strip(),
        )
        return expediente

    @classmethod
    @transaction.atomic
    def transition(
        cls,
        *,
        expediente_id: int,
        estado_nuevo: str,
        actor: str,
        motivo: str,
        ahora: datetime | None = None,
    ) -> Expediente:
        if not motivo.strip():
            raise ValidationError({"motivo": "El motivo de transición es obligatorio."})
        if estado_nuevo not in EstadoExpedienteEnum.values:
            raise ValidationError({"estado": "El estado solicitado no es válido."})

        expediente = Expediente.objects.select_for_update().get(pk=expediente_id)
        estado_esperado = cls.NEXT_STATE.get(expediente.estado)
        if estado_nuevo != estado_esperado:
            raise ValidationError(
                {"estado": "La transición debe avanzar exactamente al siguiente estado."}
            )
        momento = ahora or timezone.now()
        if expediente.estado == EstadoExpedienteEnum.JUSTIFICANDO and (
            not expediente.plazo_limite_at or momento < expediente.plazo_limite_at
        ):
            raise ValidationError(
                {
                    "estado": (
                        "El expediente permanece en período de justificaciones hasta que "
                        "venza el plazo de 5 días hábiles."
                    )
                }
            )

        estado_anterior = expediente.estado
        expediente.estado = estado_nuevo
        fields_to_update = ["estado", "updated_at"]
        if estado_nuevo == EstadoExpedienteEnum.JUSTIFICANDO and not expediente.plazo_limite_at:
            start_at = momento
            expediente.plazo_inicio_at = start_at
            expediente.plazo_limite_at = compute_business_deadline(
                start_at=start_at,
                business_days=5,
                holiday_provider=Argentina2026HolidayProvider(),
            )
            fields_to_update.extend(["plazo_inicio_at", "plazo_limite_at"])
        expediente.save(update_fields=fields_to_update)
        CambioEstadoExpediente.objects.create(
            expediente=expediente,
            estado_anterior=estado_anterior,
            estado_nuevo=estado_nuevo,
            actor=actor,
            motivo=motivo.strip(),
        )
        return expediente
