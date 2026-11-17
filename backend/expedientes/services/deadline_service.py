"""Servicio de control y cierre de plazos procesales perentorios (CA4).

Implementa:
- Evaluación transaccional e idempotente de expedientes en estado JUSTIFICANDO.
- Bloqueo pesimista con select_for_update() para evitar condiciones de carrera.
- Transición a REVISION_RESOLUCION (Art. 12 Inc. 2 Reglamento Procesal 2026).
- Auditoría formal registrada en CambioEstadoExpediente.
"""

import logging
from datetime import datetime, timedelta

from django.db import transaction
from django.utils import timezone

from expedientes.models import EstadoExpedienteEnum, Expediente
from expedientes.services.disciplinary_notifications import enqueue_deadline_reminder
from expedientes.services.t01_appeal_service import T01AppealService
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
                    # En los T01 rige el último período de apelación abierto (PB-02).
                    plazo_efectivo = T01AppealService.effective_deadline(expediente)
                    if (
                        expediente.estado != EstadoExpedienteEnum.JUSTIFICANDO
                        or not plazo_efectivo
                        or plazo_efectivo >= momento
                    ):
                        continue

                    ExpedienteWorkflowService.transition(
                        expediente_id=expediente.pk,
                        estado_nuevo=EstadoExpedienteEnum.REVISION_RESOLUCION,
                        actor=self.ACTOR_CRON,
                        motivo=self.MOTIVO_EXPIRACION,
                        ahora=momento,
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

    def send_imminent_deadline_reminders(
        self,
        ahora: datetime | None = None,
        window_hours: int = 24,
    ) -> int:
        """Encola recordatorios preventivos 24h antes del vencimiento del plazo (Evento 7).

        Idempotencia: ``deadline-reminder-{expediente_id}-socio-{socio_id}``.
        """
        momento = ahora or timezone.now()
        limite_ventana = momento + timedelta(hours=window_hours)

        candidate_ids = list(
            Expediente.objects.filter(
                estado=EstadoExpedienteEnum.JUSTIFICANDO,
                plazo_limite_at__isnull=False,
                plazo_limite_at__gt=momento,
            ).values_list("id", flat=True)
        )

        reminded_count = 0
        for exp_id in candidate_ids:
            with transaction.atomic():
                expediente = (
                    Expediente.objects.select_for_update()
                    .select_related("socio")
                    .prefetch_related("socios")
                    .filter(id=exp_id)
                    .first()
                )
                if not expediente or expediente.estado != EstadoExpedienteEnum.JUSTIFICANDO:
                    continue

                plazo_efectivo = T01AppealService.effective_deadline(expediente)
                if not plazo_efectivo or not (momento < plazo_efectivo <= limite_ventana):
                    continue

                socios_map = {expediente.socio.id: expediente.socio} if expediente.socio else {}
                for s in expediente.socios.all():
                    socios_map.setdefault(s.id, s)

                for socio in socios_map.values():
                    outbox = enqueue_deadline_reminder(
                        expediente=expediente,
                        socio=socio,
                        plazo_limite_at=plazo_efectivo,
                    )
                    if outbox is not None:
                        reminded_count += 1

        return reminded_count
