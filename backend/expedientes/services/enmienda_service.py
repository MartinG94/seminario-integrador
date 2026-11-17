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
    TipoDescargoEnum,
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
        articulos_resolutivos: str | None = None,
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
        medidas_finales = list(resolucion_anterior.medidas or [])
        articulos_actualizados_socios: list[str] = []

        if nuevos_puntajes and isinstance(nuevos_puntajes, list):
            suma = Decimal("0.00")
            medidas_enmienda: list[str] = []
            for item in nuevos_puntajes:
                socio_id = item.get("socio_id")
                ptje = item.get("puntaje")
                if not socio_id or ptje is None:
                    continue

                ptje_str = str(ptje).strip()
                descargo, _ = DescargoExpediente.objects.get_or_create(
                    expediente=expediente,
                    socio_id=socio_id,
                    defaults={
                        "tipo": TipoDescargoEnum.T02_CERTIFICADO,
                        "es_vigente": False,
                        "texto": "",
                    },
                )
                if not descargo.esta_excluido:
                    descargo.puntaje_ratificado = ptje_str
                    descargo.save(update_fields=["puntaje_ratificado"])

                if ptje_str == "LLAMADO_ATENCION":
                    if "Llamado de atención" not in medidas_enmienda:
                        medidas_enmienda.append("Llamado de atención")
                    etiqueta_ptje = "Llamado de atención"
                elif ptje_str == "FELICITACION":
                    if "Felicitación" not in medidas_enmienda:
                        medidas_enmienda.append("Felicitación")
                    etiqueta_ptje = "Felicitación"
                else:
                    try:
                        ptje_dec = Decimal(ptje_str)
                        suma += ptje_dec
                        etiqueta_ptje = f"{ptje_dec:+.2f} pts"
                    except Exception:
                        etiqueta_ptje = ptje_str

                socio_obj = getattr(descargo, "socio", None)
                if socio_obj:
                    nombre_soc = f"{socio_obj.first_name} {socio_obj.last_name}".strip()
                    nro_soc = getattr(socio_obj, "numero_socio", None) or socio_obj.legajo
                    articulos_actualizados_socios.append(
                        f"Socio {nro_soc} ({nombre_soc}): {etiqueta_ptje}"
                    )
                else:
                    articulos_actualizados_socios.append(f"Socio #{socio_id}: {etiqueta_ptje}")

            nuevo_puntaje_total = suma.quantize(Decimal("0.01"))
            medidas_finales = medidas_enmienda

        # Crear nueva resolución borrador versionada (EARS-103.2)
        nueva_version = resolucion_anterior.version + 1
        considerandos_finales = (
            considerandos.strip() if considerandos else resolucion_anterior.considerandos
        )
        if articulos_resolutivos and articulos_resolutivos.strip():
            articulos_finales = articulos_resolutivos.strip()
        elif articulos_actualizados_socios:
            resumen_socios = "; ".join(articulos_actualizados_socios)
            base_articulos = (resolucion_anterior.articulos_resolutivos or "").strip()
            if base_articulos:
                articulos_finales = (
                    f"{base_articulos}\n\nRectificación por socio: {resumen_socios}."
                )
            else:
                articulos_finales = f"Artículo 1: Rectificación por socio: {resumen_socios}."
        else:
            articulos_finales = resolucion_anterior.articulos_resolutivos

        nueva_resolucion = Resolucion.objects.create(
            expediente=expediente,
            version=nueva_version,
            plantilla_version=resolucion_anterior.plantilla_version or "v1",
            estado=EstadoResolucionEnum.DRAFT,
            numero_expediente_snapshot=resolucion_anterior.numero_expediente_snapshot,
            vistos=resolucion_anterior.vistos,
            considerandos=considerandos_finales,
            articulos_resolutivos=articulos_finales,
            reglamentos_respaldantes=list(resolucion_anterior.reglamentos_respaldantes or []),
            expedientes_referenciados=list(resolucion_anterior.expedientes_referenciados or []),
            puntos_finales=nuevo_puntaje_total,
            medidas=medidas_finales,
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

        # Consultar socios que ya tenían registros contables previos para este expediente
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT DISTINCT socio_id FROM tribunal_puntajeaplicado WHERE expediente_id = %s",
                [expediente.id],
            )
            existing_ledger_sids = {row[0] for row in cursor.fetchall()}

        # Obtener excluidos y puntajes ratificados individuales (por PK y nroSocio legacy)
        excluidos_ids: set[int] = set()
        ratificados_map: dict[int, str] = {}
        for d in DescargoExpediente.objects.filter(expediente=expediente).select_related("socio"):
            keys = {d.socio_id}
            nro = getattr(d.socio, "numero_socio", None) if d.socio else None
            if nro is not None:
                keys.add(int(nro))
            if d.esta_excluido:
                excluidos_ids.update(keys)
            elif d.puntaje_ratificado is not None:
                for k in keys:
                    ratificados_map[k] = d.puntaje_ratificado

        socio_ids = set(existing_ledger_sids)
        for s in socios:
            nro = getattr(s, "numero_socio", None)
            if s.id in existing_ledger_sids:
                ledger_sid = s.id
            elif nro is not None and int(nro) in existing_ledger_sids:
                ledger_sid = int(nro)
            elif nro is not None and connection.vendor == "mysql":
                ledger_sid = int(nro)
            else:
                ledger_sid = s.id
            socio_ids.add(ledger_sid)

        with connection.cursor() as cursor:
            for sid in socio_ids:
                cursor.execute(
                    "SELECT COALESCE(SUM(puntajeAplicado), 0), COUNT(*) "
                    "FROM tribunal_puntajeaplicado WHERE expediente_id = %s AND socio_id = %s",
                    [expediente.id, sid],
                )
                saldo_prev, count_prev = cursor.fetchone()

                if sid in excluidos_ids:
                    if Decimal(str(saldo_prev)) != Decimal("0"):
                        cursor.execute(
                            "INSERT INTO tribunal_puntajeaplicado "
                            "(puntajeAplicado, socio_id, expediente_id) "
                            "VALUES (%s, %s, %s)",
                            [-float(saldo_prev), sid, expediente.id],
                        )
                    continue

                ptos_ant_socio = Decimal(str(saldo_prev)) if count_prev > 0 else ptos_ant
                ptos_nuevo_socio = ptos_nuevo
                if sid in ratificados_map:
                    rat_val = str(ratificados_map[sid]).strip()
                    if rat_val in ("LLAMADO_ATENCION", "FELICITACION"):
                        ptos_nuevo_socio = Decimal("0.00")
                    else:
                        try:
                            ptos_nuevo_socio = Decimal(rat_val)
                        except Exception:
                            ptos_nuevo_socio = ptos_nuevo

                # 1. Asiento de reversión íntegra (monto opuesto exacto)
                cursor.execute(
                    "INSERT INTO tribunal_puntajeaplicado "
                    "(puntajeAplicado, socio_id, expediente_id) "
                    "VALUES (%s, %s, %s)",
                    [-float(ptos_ant_socio), sid, expediente.id],
                )
                # 2. Asiento nuevo definitivo por el valor rectificado
                cursor.execute(
                    "INSERT INTO tribunal_puntajeaplicado "
                    "(puntajeAplicado, socio_id, expediente_id) "
                    "VALUES (%s, %s, %s)",
                    [float(ptos_nuevo_socio), sid, expediente.id],
                )

        logger.info(
            "Contra-asientos Opción B registrados para expediente %s (Res. %s -> %s)",
            expediente.id,
            resolucion_ant.version,
            resolucion_nueva.version,
        )
