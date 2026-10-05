"""Servicio de aplicación para despacho atómico de notificaciones de apertura de expedientes.

Implementa:
- CA1: Transición atómica condicionada al despacho acordado.
- CA3: Encolado resiliente en Transactional Outbox, idempotencia y reintentos.
- CA5: Inmutabilidad estricta de la fecha base.
- Principio 6: Sanitización de datos sensibles antes de la persistencia.
- Principio 7: Registro de auditoría y excepciones sin fuga de datos privados.
"""

import logging
from typing import Any

from django.conf import settings
from django.db import models, transaction
from django.utils import timezone

from expedientes.domain.opening_policy import OpeningNotificationTemplate
from expedientes.models import EstadoExpedienteEnum, Expediente
from notifications.models import EmailOutbox
from notifications.services import EmailDispatcherService

logger = logging.getLogger(__name__)


class InvalidCaseStatusError(Exception):
    """Lanzada cuando se intenta despachar un expediente en un estado incompatible."""


class MissingSocioEmailError(Exception):
    """Lanzada cuando el socio imputado carece de dirección de correo electrónico en su legajo."""


class OpeningNotificationService:
    """Orquestador transaccional en 2 fases para la apertura formal de sumarios."""

    @classmethod
    def dispatch_opening(
        cls,
        expediente_id: int,
        actor: str = "TD_User",
        frontend_url: str | None = None,
    ) -> tuple[Expediente, EmailOutbox]:
        """Ejecuta la orden formal de apertura en 2 fases:

        Fase 1 (Transacción atómica de BD):
        - Bloqueo pesimista mediante select_for_update().
        - Verificación de estado CREADO e idempotencia si ya fue despachado.
        - Validación de email del socio imputado.
        - Invocación de iniciar_plazo_descargo (congelamiento de fecha base).
        - Generación de plantilla institucional sanitizada.
        - Creación en EmailOutbox con idempotency_key.

        Fase 2 (Despacho de transporte fuera del lock de BD):
        - Invocación a EmailDispatcherService.dispatch(outbox).
        """
        # --- FASE 1: Transacción atómica de BD ---
        with transaction.atomic():
            expediente = (
                Expediente.objects.select_for_update().select_related("socio").get(pk=expediente_id)
            )
            # BAJO-002: Formato canónico alineado con spec.md (RF-NOTIF-03)
            idempotency_key = f"opening-expediente-{expediente.id}-socio-{expediente.socio_id}"

            # Manejo de idempotencia: si ya está en JUSTIFICANDO y tiene outbox registrado
            if expediente.estado == EstadoExpedienteEnum.JUSTIFICANDO:
                legacy_key = f"opening-exp-{expediente.id}-socio-{expediente.socio_id}"
                existing_outbox = EmailOutbox.objects.filter(
                    models.Q(idempotency_key=idempotency_key) | models.Q(idempotency_key=legacy_key)
                ).first()
                if existing_outbox:
                    logger.info(
                        "Despacho redundante para expediente %s. Reutilizando outbox %s.",
                        expediente.id,
                        existing_outbox.id,
                    )
                    return expediente, existing_outbox

            # Rechazo si el estado procesal no es CREADO
            if expediente.estado != EstadoExpedienteEnum.CREADO:
                raise InvalidCaseStatusError(
                    f"No se puede despachar notificación: el expediente se encuentra en "
                    f"estado '{expediente.estado}', pero se requiere estado "
                    f"'{EstadoExpedienteEnum.CREADO}'."
                )

            # Validar correo institucional del socio imputado
            socio_email = (expediente.socio.email or "").strip()
            if not socio_email:
                raise MissingSocioEmailError(
                    f"El socio imputado '{expediente.socio.legajo}' no posee dirección de "
                    f"correo electrónico válida registrada en su legajo."
                )

            # Transicionar a JUSTIFICANDO y congelar plazos procesales
            now = timezone.now()
            expediente.iniciar_plazo_descargo(
                fecha_hora_inicio=now,
                dias_habiles=5,
                actor=actor,
            )

            # Componer plantilla institucional (valida ausencia de datos médicos)
            base_url = frontend_url or getattr(settings, "FRONTEND_URL", "http://localhost:4200")
            socio_nombre = (
                f"{expediente.socio.first_name} {expediente.socio.last_name}".strip()
                or expediente.socio.legajo
            )
            payload = OpeningNotificationTemplate.render(
                expediente_numero=expediente.numero,
                socio_nombre=socio_nombre,
                motivo_caratula=expediente.motivo,
                plazo_inicio_at=expediente.plazo_inicio_at,
                plazo_limite_at=expediente.plazo_limite_at,
                frontend_url=base_url,
                expediente_id=expediente.id,
                socio_id=expediente.socio_id,
            )

            # Encolar en Outbox
            outbox_payload: dict[str, Any] = {
                "to": [socio_email],
                "subject": payload.subject,
                "body_text": payload.body_text,
                "body_html": payload.body_html,
                "idempotency_key": payload.idempotency_key,
                "metadata": payload.metadata,
            }
            outbox, _ = EmailDispatcherService.create_or_get_outbox(outbox_payload)

        # --- FASE 2: Despacho SMTP fuera del lock de BD ---
        try:
            EmailDispatcherService.dispatch(outbox)
        except Exception as exc:
            # Principio 7: Auditoría sin fuga de asunto ni cuerpo del correo
            logger.warning(
                "Fallo al despachar notificación inmediata para expediente %s (outbox_id=%s): %s",
                expediente.id,
                outbox.id,
                type(exc).__name__,
            )

        return expediente, outbox


class CaseNotificationQueryService:
    """Servicio de consulta para la bitácora de entrega de notificaciones del TD."""

    @classmethod
    def get_case_notifications(cls, expediente_id: int) -> models.QuerySet[EmailOutbox]:
        """Retorna el queryset de mensajes outbox vinculados al expediente."""
        return EmailOutbox.objects.filter(
            models.Q(metadata__expediente_id=expediente_id)
            | models.Q(idempotency_key__startswith=f"opening-expediente-{expediente_id}-")
            | models.Q(idempotency_key__startswith=f"opening-exp-{expediente_id}-")
        ).order_by("-created_at")
