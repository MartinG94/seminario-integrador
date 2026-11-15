"""Servicio transaccional de enmienda trazable de resoluciones emitidas (SCRUM-103)."""

import logging
from decimal import Decimal
from typing import Any

from django.core.exceptions import ValidationError
from django.db import connection, transaction

from expedientes.models import (
    CambioEstadoExpediente,
    DescargoExpediente,
    EnmiendaResolucion,
    EstadoExpedienteEnum,
    EstadoResolucionEnum,
    Expediente,
    Resolucion,
)

logger = logging.getLogger(__name__)


class EnmiendaService:
    @classmethod
    @transaction.atomic
    def solicitar_enmienda(
        cls,
        *,
        expediente_id: int,
        user: Any,
        motivo_enmienda: str,
        considerandos: str | None = None,
        nuevos_puntajes: list[dict[str, Any]] | None = None,
    ) -> tuple[EnmiendaResolucion, Resolucion]:
        """Inicia el circuito de enmienda trazable sobre una resolución emitida (EARS-103.1)."""
        motivo_limpio = (motivo_enmienda or "").strip()
        if len(motivo_limpio) < 10:
            raise ValidationError(
                {
                    "motivo_enmienda": (
                        "El motivo de la enmienda debe contener al menos 10 caracteres."
                    )
                }
            )

        expediente = (
            Expediente.objects.select_for_update()
            .prefetch_related("socios", "descargos")
            .filter(pk=expediente_id)
            .first()
        )
        if not expediente:
            raise ValidationError({"expediente": "Expediente no encontrado."})

        # 1. Verificar que no exista ya una enmienda en borrador pendiente
        borrador_existente = Resolucion.objects.filter(
            expediente=expediente, estado=EstadoResolucionEnum.DRAFT
        ).first()
        if borrador_existente:
            raise ValidationError(
                {
                    "enmienda": (
                        "Ya existe una enmienda en borrador pendiente de firma "
                        "para este expediente."
                    )
                }
            )

        # 2. Verificar última resolución emitida y estado del expediente
        resolucion_anterior = (
            Resolucion.objects.select_for_update()
            .filter(expediente=expediente, estado=EstadoResolucionEnum.ISSUED)
            .order_by("-version")
            .first()
        )
        if not resolucion_anterior or expediente.estado != EstadoExpedienteEnum.EMITIDO:
            raise ValidationError(
                {"resolucion": "Solo se pueden enmendar expedientes con una resolución emitida."}
            )

        # Procesar nuevos puntajes si fueron enviados
        nuevo_puntaje_total = resolucion_anterior.puntos_finales
        if nuevos_puntajes and isinstance(nuevos_puntajes, list):
            suma = Decimal("0.00")
            for item in nuevos_puntajes:
                socio_id = item.get("socio_id")
                ptje = item.get("puntaje")
                if socio_id and ptje is not None:
                    try:
                        ptje_dec = Decimal(str(ptje))
                        suma += ptje_dec
                    except Exception:
                        pass
                    descargo = DescargoExpediente.objects.filter(
                        expediente=expediente, socio_id=socio_id
                    ).first()
                    if descargo:
                        descargo.puntaje_ratificado = str(ptje)
                        descargo.save(update_fields=["puntaje_ratificado", "updated_at"])
            nuevo_puntaje_total = suma.quantize(Decimal("0.01"))

        # Crear nueva resolución borrador versionada (EARS-103.2)
        nueva_version = resolucion_anterior.version + 1
        considerandos_finales = (
            considerandos.strip() if considerandos else resolucion_anterior.considerandos
        )

        nueva_resolucion = Resolucion.objects.create(
            expediente=expediente,
            version=nueva_version,
            plantilla_version=resolucion_anterior.plantilla_version or "v1",
            estado=EstadoResolucionEnum.DRAFT,
            numero_expediente_snapshot=resolucion_anterior.numero_expediente_snapshot,
            vistos=resolucion_anterior.vistos,
            considerandos=considerandos_finales,
            articulos_resolutivos=resolucion_anterior.articulos_resolutivos,
            reglamentos_respaldantes=list(resolucion_anterior.reglamentos_respaldantes or []),
            expedientes_referenciados=list(resolucion_anterior.expedientes_referenciados or []),
            puntos_finales=nuevo_puntaje_total,
            medidas=list(resolucion_anterior.medidas or []),
            firmantes=[],
            created_by=user,
        )

        # Crear registro de enmienda
        enmienda = EnmiendaResolucion.objects.create(
            resolucion_anterior=resolucion_anterior,
            resolucion_nueva=nueva_resolucion,
            motivo_enmienda=motivo_limpio,
            solicitado_por=user,
        )

        # Transicionar expediente a PENDIENTE_CORREOS (pendiente de firma)
        estado_ant = expediente.estado
        expediente.estado = EstadoExpedienteEnum.PENDIENTE_CORREOS
        if nuevo_puntaje_total is not None:
            expediente.puntos = nuevo_puntaje_total
        expediente.save(update_fields=["estado", "puntos", "updated_at"])

        actor_name = getattr(user, "username", str(user))
        CambioEstadoExpediente.objects.create(
            expediente=expediente,
            estado_anterior=estado_ant,
            estado_nuevo=EstadoExpedienteEnum.PENDIENTE_CORREOS,
            actor=actor_name,
            motivo=f"Apertura de enmienda trazable (Versión {nueva_version}): {motivo_limpio}",
        )

        return enmienda, nueva_resolucion

    @classmethod
    def aplicar_contra_asientos_opcion_b(cls, enmienda: EnmiendaResolucion) -> None:
        """Registra en libro mayor reversión íntegra y nuevo asiento definitivo (EARS-103.3)."""
        resolucion_ant = enmienda.resolucion_anterior
        resolucion_nueva = enmienda.resolucion_nueva
        expediente = resolucion_nueva.expediente

        ptos_ant = (
            Decimal(str(resolucion_ant.puntos_finales))
            if resolucion_ant.puntos_finales is not None
            else Decimal("0.00")
        )
        ptos_nuevo = (
            Decimal(str(resolucion_nueva.puntos_finales))
            if resolucion_nueva.puntos_finales is not None
            else Decimal("0.00")
        )

        # Determinar socios involucrados
        socios = list(expediente.socios.all())
        if expediente.socio and expediente.socio not in socios:
            socios.append(expediente.socio)

        socio_ids = {s.id for s in socios}
        if expediente.socio_id:
            socio_ids.add(expediente.socio_id)

        # También incluir socios que tenían registros contables previos para este expediente
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT DISTINCT socio_id FROM tribunal_puntajeaplicado WHERE expediente_id = %s",
                [expediente.id],
            )
            for row in cursor.fetchall():
                socio_ids.add(row[0])

        with connection.cursor() as cursor:
            for sid in socio_ids:
                # 1. Asiento de reversión íntegra (monto opuesto exacto)
                cursor.execute(
                    "INSERT INTO tribunal_puntajeaplicado "
                    "(puntajeAplicado, socio_id, expediente_id) "
                    "VALUES (%s, %s, %s)",
                    [-float(ptos_ant), sid, expediente.id],
                )
                # 2. Asiento nuevo definitivo por el valor rectificado
                cursor.execute(
                    "INSERT INTO tribunal_puntajeaplicado "
                    "(puntajeAplicado, socio_id, expediente_id) "
                    "VALUES (%s, %s, %s)",
                    [float(ptos_nuevo), sid, expediente.id],
                )

        logger.info(
            "Contra-asientos Opción B registrados para expediente %s (Res. %s -> %s)",
            expediente.id,
            resolucion_ant.version,
            resolucion_nueva.version,
        )
