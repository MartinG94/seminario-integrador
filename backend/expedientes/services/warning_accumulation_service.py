"""Servicio de acumulación y consolidación atómica 3:1 de apercibimientos (CA4).

Implementa:
- Registro atómico de apercibimientos y llamados de atención en el libro mayor.
- Bloqueo pesimista con select_for_update() sobre el socio y sus apercibimientos pendientes.
- Regla 3:1 inmutable: cada terna de 3 apercibimientos pendientes genera un único expediente
  formal por -1.00 punto neto (Art. 83 / Art. 100 R.I.).
- Asignación de UUID único por lote_consolidacion.
- Vinculación inmutable al expediente_sancion generado en estado CREADO.
- Cero alteraciones directas sobre el saldo de puntos del socio (Regla Innegociable 3).
"""

import logging
import uuid
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from expedientes.models import (
    EstadoRegistroApercibimientoEnum,
    Expediente,
    RegistroApercibimiento,
)
from expedientes.services.workflow_service import ExpedienteWorkflowService
from socios.models import Socio

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class WarningAccumulationService:
    """Motor transaccional de acumulación 3:1 de apercibimientos y llamados de atención."""

    CONSOLIDATION_THRESHOLD: int = 3
    PENALTY_POINTS: Decimal = Decimal("-1.00")

    @classmethod
    @transaction.atomic
    def register_warning(
        cls,
        *,
        socio_id: int,
        origen_tipo: str,
        motivo: str,
        fecha_hecho: date | None = None,
        articulo_reglamento: str = "Art. 83",
        asistencia_id: int | None = None,
        solicitud_t01_id: str | None = None,
        expediente_origen_id: int | None = None,
        actor: str = "SISTEMA",
    ) -> tuple[RegistroApercibimiento, Expediente | None]:
        """
        Registra un apercibimiento en el libro mayor y evalúa la regla de consolidación 3:1.

        Garantías:
        - Transaccionalidad total (ACID).
        - Bloqueo pesimista sobre el socio para prevenir condiciones de carrera concurrentes.
        - Si el socio acumula 3 pendientes, consolida atómicamente la terna más antigua.
        - Genera un expediente formal por -1.00 punto sin modificar saldos de MySQL directamente.

        Retorna:
            (nuevo_apercibimiento, expediente_generado_o_none)
        """
        if not motivo or not motivo.strip():
            raise ValidationError({"motivo": "El motivo del apercibimiento es obligatorio."})

        # Bloqueo pesimista del socio para serializar registros simultáneos
        try:
            socio = Socio.objects.select_for_update().get(pk=socio_id)
        except Socio.DoesNotExist:
            raise ValidationError({"socio_id": f"El socio con ID {socio_id} no existe."})

        fecha = fecha_hecho or timezone.localdate()

        # 1. Crear el apercibimiento en estado PENDIENTE
        nuevo_apercibimiento = RegistroApercibimiento.objects.create(
            socio=socio,
            origen_tipo=origen_tipo,
            asistencia_id=asistencia_id,
            solicitud_t01_id=solicitud_t01_id,
            expediente_origen_id=expediente_origen_id,
            fecha_hecho=fecha,
            motivo=motivo.strip(),
            articulo_reglamento=articulo_reglamento,
            estado=EstadoRegistroApercibimientoEnum.PENDIENTE,
            actor_registro=actor,
        )

        # 2. Consultar todos los pendientes bajo lock pesimista
        pendientes = list(
            RegistroApercibimiento.objects.select_for_update()
            .filter(socio=socio, estado=EstadoRegistroApercibimientoEnum.PENDIENTE)
            .order_by("created_at", "id")
        )

        expediente_generado: Expediente | None = None

        # 3. Si hay al menos 3 pendientes, consolidar la terna más antigua
        if len(pendientes) >= cls.CONSOLIDATION_THRESHOLD:
            terna = pendientes[: cls.CONSOLIDATION_THRESHOLD]
            lote_uuid = uuid.uuid4()
            ahora = timezone.now()

            detalle_motivos = " | ".join(
                f"[{ap.fecha_hecho.strftime('%d/%m/%Y')}]: {ap.motivo}" for ap in terna
            )
            motivo_expediente = (
                f"Consolidación reglamentaria de tres (3) apercibimientos (Lote {lote_uuid}) "
                f"conforme a regla 3:1 (Arts. 83 y 100 R.I.). Detalle de hechos: {detalle_motivos}"
            )

            # Abrir expediente formal de oficio por -1.00 punto
            expediente_generado = ExpedienteWorkflowService.open_expediente(
                motivo=motivo_expediente,
                socio_ids=[socio.id],
                actor=actor,
                points=cls.PENALTY_POINTS,
            )

            # Marcar la terna como CONSOLIDADO
            for apercibimiento in terna:
                apercibimiento.estado = EstadoRegistroApercibimientoEnum.CONSOLIDADO
                apercibimiento.lote_consolidacion = lote_uuid
                apercibimiento.expediente_sancion = expediente_generado
                apercibimiento.fecha_consolidacion = ahora
                apercibimiento.save(
                    update_fields=[
                        "estado",
                        "lote_consolidacion",
                        "expediente_sancion",
                        "fecha_consolidacion",
                    ]
                )

            logger.info(
                "Consolidada terna de apercibimientos para socio %s. Lote: %s. Exp: %s",
                socio.legajo,
                lote_uuid,
                expediente_generado.numero,
            )

        return nuevo_apercibimiento, expediente_generado

    @classmethod
    def get_pending_count(cls, socio_id: int) -> int:
        """Devuelve la cantidad de apercibimientos pendientes acumulados por el socio."""
        return RegistroApercibimiento.objects.filter(
            socio_id=socio_id,
            estado=EstadoRegistroApercibimientoEnum.PENDIENTE,
        ).count()
