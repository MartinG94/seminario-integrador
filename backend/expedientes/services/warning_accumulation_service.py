"""Servicio de acumulación y consolidación atómica 3:1 de llamados de atención
y felicitaciones (CA4).

Implementa:
- Control de contadores sobre la tabla legacy atencionFelicitacion (PK nroSocio).
- Bloqueo pesimista con select_for_update() sobre el socio y su registro de atencionFelicitacion.
- Regla 3:1 inmutable: cada 3 llamados de atención consolidan en un único expediente
  formal por -1.00 punto neto (Art. 83 / Art. 100 R.I.) y descuentan 3 llamados.
- Regla 3:1 de felicitaciones: cada 3 felicitaciones acreditan +1.00 punto neto y descuentan
  3 felicitaciones.
- Cero alteraciones directas sobre el saldo de puntos del socio (Regla Innegociable 3).
"""

import logging
from decimal import Decimal
from typing import Any

from django.core.exceptions import ValidationError
from django.db import transaction

from expedientes.models import (
    AtencionFelicitacion,
    Expediente,
)
from expedientes.services.workflow_service import ExpedienteWorkflowService
from socios.models import Socio

logger = logging.getLogger(__name__)


class WarningAccumulationService:
    """Motor transaccional de acumulación 3:1 de llamados de atención y felicitaciones."""

    CONSOLIDATION_THRESHOLD: int = 3
    PENALTY_POINTS: Decimal = Decimal("-1.00")
    MERIT_POINTS: Decimal = Decimal("1.00")

    @classmethod
    @transaction.atomic
    def register_warning(
        cls,
        *,
        socio_id: int,
        origen_tipo: str = "LLAMADO_ATENCION",
        motivo: str,
        fecha_hecho: Any = None,
        articulo_reglamento: str = "Art. 83",
        asistencia_id: int | None = None,
        solicitud_t01_id: str | None = None,
        expediente_origen_id: int | None = None,
        actor: str = "SISTEMA",
    ) -> tuple[AtencionFelicitacion, Expediente | None]:
        """
        Registra un llamado de atención en atencionFelicitacion y evalúa la consolidación 3:1.
        """
        if not motivo or not motivo.strip():
            raise ValidationError({"motivo": "El motivo del apercibimiento es obligatorio."})

        try:
            socio = Socio.objects.select_for_update().get(pk=socio_id)
        except Socio.DoesNotExist:
            raise ValidationError({"socio_id": f"El socio con ID {socio_id} no existe."})

        atencion, _ = AtencionFelicitacion.objects.select_for_update().get_or_create(socio=socio)
        atencion.llamadosAtencion += 1

        expediente_generado: Expediente | None = None

        if atencion.llamadosAtencion >= cls.CONSOLIDATION_THRESHOLD:
            atencion.llamadosAtencion -= cls.CONSOLIDATION_THRESHOLD
            motivo_expediente = (
                f"Consolidación reglamentaria de tres (3) apercibimientos conforme a regla 3:1 "
                f"(Arts. 83 y 100 R.I.). Detalle de hechos: {motivo.strip()}"
            )
            expediente_generado = ExpedienteWorkflowService.open_expediente(
                motivo=motivo_expediente,
                socio_ids=[socio.id],
                actor=actor,
                points=cls.PENALTY_POINTS,
            )
            logger.info(
                "Consolidados 3 llamados de atención para socio %s. Exp: %s",
                socio.legajo,
                expediente_generado.numero,
            )

        atencion.save(update_fields=["llamadosAtencion"])
        return atencion, expediente_generado

    @classmethod
    @transaction.atomic
    def register_felicitacion(
        cls,
        *,
        socio_id: int,
        motivo: str,
        actor: str = "SISTEMA",
    ) -> tuple[AtencionFelicitacion, Expediente | None]:
        """
        Registra una felicitación y evalúa la regla 3:1 para acreditación de méritos.
        """
        if not motivo or not motivo.strip():
            raise ValidationError({"motivo": "El motivo de la felicitación es obligatorio."})

        try:
            socio = Socio.objects.select_for_update().get(pk=socio_id)
        except Socio.DoesNotExist:
            raise ValidationError({"socio_id": f"El socio con ID {socio_id} no existe."})

        atencion, _ = AtencionFelicitacion.objects.select_for_update().get_or_create(socio=socio)
        atencion.felicitaciones += 1

        expediente_generado: Expediente | None = None

        if atencion.felicitaciones >= cls.CONSOLIDATION_THRESHOLD:
            atencion.felicitaciones -= cls.CONSOLIDATION_THRESHOLD
            motivo_expediente = (
                f"Acreditación reglamentaria por tres (3) felicitaciones conforme a regla 3:1. "
                f"Detalle: {motivo.strip()}"
            )
            expediente_generado = ExpedienteWorkflowService.open_expediente(
                motivo=motivo_expediente,
                socio_ids=[socio.id],
                actor=actor,
                points=cls.MERIT_POINTS,
            )
            logger.info(
                "Consolidadas 3 felicitaciones para socio %s. Exp: %s",
                socio.legajo,
                expediente_generado.numero,
            )

        atencion.save(update_fields=["felicitaciones"])
        return atencion, expediente_generado

    @classmethod
    def get_pending_count(cls, socio_id: int) -> int:
        """Devuelve la cantidad de llamados de atención acumulados pendientes por el socio."""
        atencion = AtencionFelicitacion.objects.filter(socio_id=socio_id).first()
        return atencion.llamadosAtencion if atencion else 0
