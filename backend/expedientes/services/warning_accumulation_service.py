"""Servicio de acumulación y consolidación atómica 3:1 de llamados de atención
y felicitaciones (CA4).

Implementa:
- Apertura de expediente con 0.00 puntos y notificación automática al registrar un
  llamado de atención o felicitación (sin alterar contadores hasta emitir resolución).
- Control de contadores sobre la tabla legacy atencionFelicitacion (PK nroSocio).
- Bloqueo pesimista con select_for_update() sobre el socio y su registro de atencionFelicitacion.
- Regla 3:1 inmutable al emitir resolución (`apply_confirmed_measure`): cada 3 llamados
  confirmados aplican -1.00 punto neto en `PuntajeAplicado` y descuentan 3 llamados;
  cada 3 felicitaciones confirmadas acreditan +1.00 punto neto y descuentan 3 felicitaciones.
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
from ranking.models import PuntajeAplicado
from socios.models import Socio

logger = logging.getLogger(__name__)


class WarningAccumulationService:
    """Motor transaccional de acumulación 3:1 de llamados de atención y felicitaciones."""

    CONSOLIDATION_THRESHOLD: int = 3
    PENALTY_POINTS: Decimal = Decimal("-1.00")
    MERIT_POINTS: Decimal = Decimal("1.00")

    @staticmethod
    def _resolve_nro_socio(socio: Socio) -> int:
        if socio.numero_socio is not None:
            return int(socio.numero_socio)
        legajo = (socio.legajo or "").strip()
        return int(legajo) if legajo.isdigit() else int(socio.pk)

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
    ) -> tuple[AtencionFelicitacion, Expediente]:
        """Abre un expediente de llamado de atención (0.00 pts) y dispara su notificación."""
        if not motivo or not motivo.strip():
            raise ValidationError({"motivo": "El motivo del apercibimiento es obligatorio."})

        try:
            socio = Socio.objects.select_for_update().get(pk=socio_id)
        except Socio.DoesNotExist:
            raise ValidationError({"socio_id": f"El socio con ID {socio_id} no existe."})

        atencion, _ = AtencionFelicitacion.objects.select_for_update().get_or_create(socio=socio)

        from expedientes.services.opening_notification_service import OpeningNotificationService
        from expedientes.services.workflow_service import ExpedienteWorkflowService

        motivo_limpio = motivo.strip()
        expediente_generado = ExpedienteWorkflowService.open_expediente(
            motivo=f"Llamado de atención ({articulo_reglamento}): {motivo_limpio}",
            titulo=f"Llamado de atención: {motivo_limpio}"[:255],
            socio_ids=[socio.id],
            actor=actor,
            points=Decimal("0.00"),
        )
        OpeningNotificationService.notify_automatic_expediente(expediente_generado, actor=actor)
        return atencion, expediente_generado

    @classmethod
    @transaction.atomic
    def register_felicitacion(
        cls,
        *,
        socio_id: int,
        motivo: str,
        actor: str = "SISTEMA",
    ) -> tuple[AtencionFelicitacion, Expediente]:
        """Abre un expediente de felicitación institucional (0.00 pts) y dispara su notificación."""
        if not motivo or not motivo.strip():
            raise ValidationError({"motivo": "El motivo de la felicitación es obligatorio."})

        try:
            socio = Socio.objects.select_for_update().get(pk=socio_id)
        except Socio.DoesNotExist:
            raise ValidationError({"socio_id": f"El socio con ID {socio_id} no existe."})

        atencion, _ = AtencionFelicitacion.objects.select_for_update().get_or_create(socio=socio)

        from expedientes.services.opening_notification_service import OpeningNotificationService
        from expedientes.services.workflow_service import ExpedienteWorkflowService

        motivo_limpio = motivo.strip()
        expediente_generado = ExpedienteWorkflowService.open_expediente(
            motivo=f"Felicitación institucional: {motivo_limpio}",
            titulo=f"Felicitación: {motivo_limpio}"[:255],
            socio_ids=[socio.id],
            actor=actor,
            points=Decimal("0.00"),
        )
        OpeningNotificationService.notify_automatic_expediente(expediente_generado, actor=actor)
        return atencion, expediente_generado

    @classmethod
    @transaction.atomic
    def apply_confirmed_measure(
        cls,
        *,
        socio: Socio,
        es_llamado: bool,
        expediente_id: int | None = None,
        nro_socio: int | None = None,
        actor: str = "TRIBUNAL",
    ) -> tuple[int, int | None, Decimal]:
        """Aplica la medida confirmada al emitir resolución y consolida 3:1 si alcanza el umbral."""
        atencion, _ = AtencionFelicitacion.objects.select_for_update().get_or_create(socio=socio)
        field_name = "llamadosAtencion" if es_llamado else "felicitaciones"
        actual = int(getattr(atencion, field_name) or 0) + 1

        if actual >= cls.CONSOLIDATION_THRESHOLD:
            actual -= cls.CONSOLIDATION_THRESHOLD
            setattr(atencion, field_name, actual)
            atencion.save(update_fields=[field_name])

            puntos_aplicados = cls.PENALTY_POINTS if es_llamado else cls.MERIT_POINTS
            target_nro = nro_socio if nro_socio is not None else cls._resolve_nro_socio(socio)
            mov = PuntajeAplicado.registrar_movimiento(
                nro_socio=target_nro,
                puntos=puntos_aplicados,
                expediente_id=expediente_id,
            )
            logger.info(
                "Consolidadas 3 %s para socio %s por %s: %s pts (expediente_id=%s).",
                "llamados de atención" if es_llamado else "felicitaciones",
                socio.legajo,
                actor,
                puntos_aplicados,
                expediente_id,
            )
            return actual, mov.pk, puntos_aplicados

        setattr(atencion, field_name, actual)
        atencion.save(update_fields=[field_name])
        return actual, None, Decimal("0.00")

    @classmethod
    @transaction.atomic
    def _revert_counter(
        cls,
        *,
        socio_id: int,
        field_name: str,
        label: str,
        actor: str,
        restaurar_terna: bool,
    ) -> AtencionFelicitacion:
        try:
            socio = Socio.objects.select_for_update().get(pk=socio_id)
        except Socio.DoesNotExist:
            raise ValidationError({"socio_id": f"El socio con ID {socio_id} no existe."})

        atencion, _ = AtencionFelicitacion.objects.select_for_update().get_or_create(socio=socio)
        valor = int(getattr(atencion, field_name) or 0)
        if valor > 0:
            setattr(atencion, field_name, valor - 1)
            atencion.save(update_fields=[field_name])
            logger.info("Revertido %s para socio %s por %s.", label, socio.legajo, actor)
        elif restaurar_terna:
            setattr(atencion, field_name, cls.CONSOLIDATION_THRESHOLD - 1)
            atencion.save(update_fields=[field_name])
            logger.info(
                "Restaurada terna de %s a %s para socio %s por %s.",
                label,
                cls.CONSOLIDATION_THRESHOLD - 1,
                socio.legajo,
                actor,
            )
        else:
            logger.warning(
                "No se pudo decrementar %s para socio %s (contador en 0).",
                label,
                socio.legajo,
            )
        return atencion

    @classmethod
    @transaction.atomic
    def revert_warning(
        cls,
        *,
        socio_id: int,
        actor: str = "SISTEMA",
        restaurar_terna: bool = False,
    ) -> AtencionFelicitacion:
        """Compensa un llamado de atención (decrementa 1 o restaura terna a 2 por enmienda)."""
        return cls._revert_counter(
            socio_id=socio_id,
            field_name="llamadosAtencion",
            label="llamado de atención",
            actor=actor,
            restaurar_terna=restaurar_terna,
        )

    @classmethod
    @transaction.atomic
    def revert_felicitacion(
        cls,
        *,
        socio_id: int,
        actor: str = "SISTEMA",
        restaurar_terna: bool = False,
    ) -> AtencionFelicitacion:
        """Compensa una felicitación (decrementa 1 o restaura terna a 2 por enmienda)."""
        return cls._revert_counter(
            socio_id=socio_id,
            field_name="felicitaciones",
            label="felicitación",
            actor=actor,
            restaurar_terna=restaurar_terna,
        )

    @classmethod
    def get_pending_count(cls, socio_id: int) -> int:
        """Devuelve la cantidad de llamados de atención acumulados pendientes por el socio."""
        atencion = AtencionFelicitacion.objects.filter(socio_id=socio_id).first()
        return atencion.llamadosAtencion if atencion else 0
