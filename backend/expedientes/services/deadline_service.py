"""Servicio de control y cierre de plazos procesales perentorios (CA4).

Implementa:
- Evaluación transaccional e idempotente de expedientes en estado JUSTIFICANDO.
- Bloqueo pesimista con select_for_update() para evitar condiciones de carrera.
- Transición a REVISION_RESOLUCION (Art. 12 Inc. 2 Reglamento Procesal 2026).
- Auditoría formal registrada en CambioEstadoExpediente.
"""

import logging
from datetime import datetime

from django.db import transaction
from django.utils import timezone

from expedientes.models import EstadoExpedienteEnum, Expediente
from expedientes.services.workflow_service import ExpedienteWorkflowService

logger = logging.getLogger(__name__)


class DeadlineEnforcementService:
    """Servicio de aplicación para la ejecución del cierre de plazos vencidos."""

    ACTOR_CRON: str = "SISTEMA_CRON"
    MOTIVO_EXPIRACION: str = "Expiración de plazo perentorio de 5 días hábiles — Art. 12 Inc. 2"

    def close_expired_deadlines(self, ahora: datetime | None = None) -> int:
        """
        Localiza y cierra todos los expedientes en 'justificando' cuyo deadline expiró.

        Garantías:
        - Totalmente idempotente: si se ejecuta múltiples veces concurrentemente o en serie,
          cada expediente sólo transiciona una única vez.
        - Seguro frente a concurrencia: bloquea pesimistamente cada fila candidata.
        - Retorna la cantidad exacta de expedientes cerrados en la ejecución.
        """
        momento = ahora or timezone.now()

        # Localizamos los IDs candidatos
        candidate_ids = list(
            Expediente.objects.filter(
                estado=EstadoExpedienteEnum.JUSTIFICANDO,
                descargo_presentado=False,
                plazo_limite_at__isnull=False,
                plazo_limite_at__lt=momento,
            ).values_list("id", flat=True)
        )

        if not candidate_ids:
            return 0

        closed_count = 0

        # Procesamos cada expediente dentro de una transacción atómica protegida con lock
        for exp_id in candidate_ids:
            with transaction.atomic():
                try:
                    expediente = Expediente.objects.select_for_update().filter(id=exp_id).first()
                    if not expediente:
                        continue

                    # Doble verificación bajo lock pesimista (Double-Checked Locking Pattern)
                    if (
                        expediente.estado != EstadoExpedienteEnum.JUSTIFICANDO
                        or expediente.descargo_presentado
                        or not expediente.plazo_limite_at
                        or expediente.plazo_limite_at >= momento
                    ):
                        continue

                    ExpedienteWorkflowService.transition(
                        expediente_id=expediente.pk,
                        estado_nuevo=EstadoExpedienteEnum.REVISION_RESOLUCION,
                        actor=self.ACTOR_CRON,
                        motivo=self.MOTIVO_EXPIRACION,
                    )
                    closed_count += 1
                    logger.info(
                        "Expediente %s cerrado por vencimiento de plazo. Estado: %s -> %s",
                        expediente.numero,
                        EstadoExpedienteEnum.JUSTIFICANDO,
                        EstadoExpedienteEnum.REVISION_RESOLUCION,
                    )
                except Exception as exc:
                    logger.error(
                        "Error al procesar el cierre del expediente ID %s: %s",
                        exp_id,
                        exc,
                    )
                    raise

        return closed_count
