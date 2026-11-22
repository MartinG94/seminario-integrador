"""Casos de uso transaccionales de resolución oficial."""

import logging
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils import timezone

from expedientes.domain.closed_decision import ClosedDecision, ClosedDecisionProvider
from expedientes.models import (
    CambioEstadoExpediente,
    ComposicionTribunal,
    ConceptoExpedienteEnum,
    CondicionIntegranteEnum,
    DescargoExpediente,
    EstadoExpedienteEnum,
    EstadoResolucionEnum,
    Expediente,
    Resolucion,
)
from expedientes.serializers.visor_serializers import cargar_mapa_grupos
from expedientes.services.publication_service import calcular_hash_resolucion
from notifications.models import EmailOutbox
from notifications.services import EmailDispatcherService
from ranking.domain.threshold_alerts import AlertaSanitizer

logger = logging.getLogger(__name__)


class DictamenNoCerradoError(Exception):
    pass


class UnavailableClosedDecisionProvider:
    """Implementación temporal hasta integrar el contrato persistente de SCRUM-55."""

    def get_closed_decision(self, expediente_id: int) -> ClosedDecision | None:
        return None


class ExpedienteConsolidatedDecisionProvider:
    """Consolida la decisión de un expediente en etapa de resolución sin votación nominal.

    El impacto de cada imputado se calcula con la misma regla que usa el libro mayor
    (`resolver_impacto_socio`): exclusión fundada, puntaje ratificado, decisión causal o
    valoración T03 vigentes y, en su defecto, lo solicitado. Las medidas especiales nunca
    son puntos fraccionarios (regla 3:1 de las Notas del PO).
    """

    def get_closed_decision(self, expediente_id: int) -> ClosedDecision | None:
        from expedientes.services.ledger_service import impactos_dictaminados
        from ranking.domain.ledger import TipoImpacto

        expediente = Expediente.objects.prefetch_related("socios").filter(pk=expediente_id).first()
        if expediente is None:
            return None
        # Si aún no está en etapa de revisión/resolución/firma, no hay dictamen.
        if expediente.estado in (EstadoExpedienteEnum.CREADO, EstadoExpedienteEnum.JUSTIFICANDO):
            return None

        impactos = impactos_dictaminados(expediente)
        puntos_finales = sum(
            (i.puntos for i in impactos.values() if i.tipo == TipoImpacto.PUNTOS),
            Decimal("0.00"),
        ).quantize(Decimal("0.01"))
        medidas: list[str] = []
        if any(i.tipo == TipoImpacto.LLAMADO_ATENCION for i in impactos.values()):
            medidas.append("Llamado de atención")
        if any(i.tipo == TipoImpacto.FELICITACION for i in impactos.values()):
            medidas.append("Felicitación")

        if puntos_finales < Decimal("0.00") or "Llamado de atención" in medidas:
            resultado = "SANCTION"
        elif puntos_finales > Decimal("0.00") or "Felicitación" in medidas:
            resultado = "MERIT"
        else:
            resultado = "NEUTRAL"

        return ClosedDecision(
            id=f"closed-{expediente.id}",
            expediente_id=expediente.id,
            estado="CLOSED",
            resultado=resultado,
            puntos_finales=puntos_finales,
            medidas=medidas,
            considerandos_base=expediente.motivo or "",
            version=1,
            closed_at=timezone.now(),
        )


def obtener_firmantes_resolucion(resolucion: Resolucion) -> list[dict]:
    """Devuelve la lista real de firmantes registrados en la resolución ordenada por año social."""
    firmantes = getattr(resolucion, "firmantes", []) or []
    return sorted(
        firmantes,
        key=lambda f: f.get("social_year") or f.get("anio_social") or 99,
    )


def obtener_firmantes_td_por_anio_social(resolucion: Resolucion | None = None) -> list[str]:
    """Devuelve las firmas reales registradas en la resolución (cero hardcodeos)."""
    if not resolucion:
        return []
    return [
        f.get("etiqueta") or f.get("firma") or str(f)
        for f in obtener_firmantes_resolucion(resolucion)
    ]


@transaction.atomic
def registrar_firma_resolucion(
    resolucion: Resolucion,
    user,
    es_suplente: bool | None = None,
    anio_social: int | None = None,
) -> Resolucion:
    """Registra la firma real del usuario TD autenticado según su año social (EARS-99)."""
    resolucion = (
        Resolucion.objects.select_for_update().select_related("expediente").get(pk=resolucion.pk)
    )
    if resolucion.estado == EstadoResolucionEnum.ISSUED:
        raise ValidationError("Una resolución emitida ya no admite nuevas firmas.")

    socio = getattr(user, "socio", None)
    numero_socio = getattr(socio, "numero_socio", None)
    legajo = str(getattr(socio, "legajo", "") or getattr(user, "username", "")).strip()
    first_name = (getattr(socio, "first_name", "") or getattr(user, "first_name", "")).strip()
    last_name = (getattr(socio, "last_name", "") or getattr(user, "last_name", "")).strip()
    full_name = f"{first_name} {last_name}".strip() or getattr(user, "username", str(user))

    mapa_grupos = cargar_mapa_grupos()
    grupo = mapa_grupos.get(str(numero_socio), "") or mapa_grupos.get(legajo, "")

    firmantes_existentes = list(resolucion.firmantes or [])
    for f in firmantes_existentes:
        if (
            f.get("user_id") == user.id
            or (f.get("numero_socio") and f.get("numero_socio") == numero_socio)
            or (f.get("legajo") and f.get("legajo") == legajo)
        ):
            raise ValidationError("El usuario ya ha firmado esta resolución.")

    anios_ocupados = {
        int(f.get("social_year") or f.get("anio_social"))
        for f in firmantes_existentes
        if (f.get("social_year") or f.get("anio_social")) is not None
    }

    if anio_social is not None:
        try:
            social_year = int(anio_social)
        except (ValueError, TypeError):
            raise ValidationError("El año social debe ser 4, 5 o 6.")
        if social_year not in (4, 5, 6):
            raise ValidationError("El año social debe ser 4, 5 o 6.")
    else:
        raw_social_year = getattr(socio, "social_year", None)
        try:
            social_year = int(raw_social_year) if raw_social_year is not None else None
        except (ValueError, TypeError):
            social_year = None

        if social_year not in (4, 5, 6):
            disponibles = [y for y in (4, 5, 6) if y not in anios_ocupados]
            if not disponibles:
                raise ValidationError(
                    "La resolución ya cuenta con las firmas de los 3 años sociales."
                )
            social_year = disponibles[0]

    if social_year in anios_ocupados:
        raise ValidationError(f"El {social_year}.º año social ya se encuentra firmado.")

    if social_year in (4, 5, 6):
        current_year = timezone.localdate().year
        expected_grupo = f"G{(current_year - 1962) - int(social_year)}"
        if not grupo or grupo != expected_grupo:
            grupo = expected_grupo

    # Inferencia de suplencia si no fue provista explícitamente (EARS-99.2)
    if es_suplente is None:
        # 1. Chequear ComposicionTribunal del expediente
        expediente = getattr(resolucion, "expediente", None)
        if expediente:
            comp = getattr(expediente, "composicion_tribunal", None)
            if comp is None:
                comp = ComposicionTribunal.objects.filter(expediente=expediente).first()
            if comp:
                legajo_int = int(legajo) if legajo.isdigit() else -1
                integrante = comp.integrantes.filter(
                    models.Q(socio__user=user)
                    | models.Q(socio=socio)
                    | models.Q(nro_socio=legajo_int)
                ).first()
                if integrante:
                    es_suplente = integrante.condicion == CondicionIntegranteEnum.SUPLENTE

        # 2. Chequear padrón institucional legacy (socio_lista: 10=Titular, 11=Suplente)
        if es_suplente is None:
            soc_tipo = getattr(socio, "idTipoSocio", None)
            user_tipo = getattr(user, "idTipoSocio", None)
            if soc_tipo == 11 or user_tipo == 11:
                es_suplente = True
            elif soc_tipo == 10 or user_tipo == 10:
                es_suplente = False
            else:
                try:
                    from padron.models import Socio as LegacySocio

                    legacy_socio = LegacySocio.objects.filter(user_id=user.id).first()
                    if not legacy_socio and legajo.isdigit():
                        legacy_socio = LegacySocio.objects.filter(nroSocio=int(legajo)).first()
                    if legacy_socio and getattr(legacy_socio, "idTipoSocio", None) == 11:
                        es_suplente = True
                    elif legacy_socio and getattr(legacy_socio, "idTipoSocio", None) == 10:
                        es_suplente = False
                except Exception:
                    pass

        if es_suplente is None:
            es_suplente = False

    es_suplente = bool(es_suplente)

    identificador = str(numero_socio) if numero_socio is not None else legajo
    etiqueta = (
        f"{identificador} - {full_name} - {grupo}" if grupo else f"{identificador} - {full_name}"
    )
    if es_suplente:
        etiqueta += " (Sup.)"

    ahora_iso = timezone.now().isoformat()
    registro_firma = {
        "user_id": user.id,
        "numero_socio": numero_socio,
        "legajo": legajo,
        "full_name": full_name,
        "social_year": social_year,
        "anio_social": social_year,
        "grupo": grupo,
        "condicion": "SUPLENTE" if es_suplente else "TITULAR",
        "es_suplente": es_suplente,
        "etiqueta": etiqueta,
        "firma": etiqueta,
        "signed_at": ahora_iso,
        "firmado_at": ahora_iso,
    }

    firmantes_existentes.append(registro_firma)
    resolucion.firmantes = firmantes_existentes
    resolucion.save(update_fields=["firmantes", "updated_at"])

    anios_actualizados = {
        int(f.get("social_year") or f.get("anio_social"))
        for f in resolucion.firmantes
        if (f.get("social_year") or f.get("anio_social")) is not None
    }
    if {4, 5, 6}.issubset(anios_actualizados):
        if resolucion.estado == EstadoResolucionEnum.DRAFT:
            resolucion = emitir_resolucion(
                resolucion=resolucion,
                emisor=user,
                provider=ExpedienteConsolidatedDecisionProvider(),
            )

    return resolucion


@transaction.atomic
def emitir_resolucion(
    resolucion: Resolucion, emisor, provider: ClosedDecisionProvider
) -> Resolucion:
    resolucion = (
        Resolucion.objects.select_for_update().select_related("expediente").get(pk=resolucion.pk)
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
    from expedientes.models import EnmiendaResolucion

    es_enmienda = EnmiendaResolucion.objects.filter(resolucion_nueva=resolucion).exists()
    resolucion.numero_expediente_snapshot = resolucion.expediente.numero
    if es_enmienda and resolucion.puntos_finales is not None:
        resolucion.puntos_finales = Decimal(str(resolucion.puntos_finales)).quantize(
            Decimal("0.01")
        )
    else:
        resolucion.puntos_finales = Decimal(decision.puntos_finales).quantize(Decimal("0.01"))
    if not es_enmienda:
        resolucion.medidas = list(decision.medidas)
    resolucion.estado = EstadoResolucionEnum.ISSUED
    resolucion.issued_by = emisor
    resolucion.issued_at = timezone.now()
    resolucion.contenido_hash = calcular_hash_resolucion(resolucion)
    resolucion.save()

    # Libro mayor inmutable en la misma transacción de la emisión (Spec 011, RF-01).
    # Una enmienda registra su contra-asiento (reversión íntegra) y el nuevo impacto
    # (Opción B, SCRUM-103) por el mismo camino: nunca se duplican movimientos.
    from expedientes.services.ledger_service import LedgerService

    enmienda = EnmiendaResolucion.objects.filter(resolucion_nueva=resolucion).first()
    if enmienda:
        LedgerService.registrar_enmienda(enmienda, emisor)
    else:
        LedgerService.registrar_resolucion(resolucion, emisor)

    # Despacho atómico e idempotente de notificaciones (EARS-100.2)
    _, hubo_fallo_correos = despachar_notificaciones_resolucion_emitida_con_estado(resolucion)

    expediente = resolucion.expediente
    if expediente:
        if hubo_fallo_correos:
            if expediente.estado != EstadoExpedienteEnum.PENDIENTE_CORREOS:
                estado_ant = expediente.estado
                if not expediente.concepto:
                    expediente.concepto = ConceptoExpedienteEnum.TD
                expediente.estado = EstadoExpedienteEnum.PENDIENTE_CORREOS
                expediente.save(update_fields=["estado", "concepto", "updated_at"])
                actor_name = getattr(emisor, "username", str(emisor))
                CambioEstadoExpediente.objects.create(
                    expediente=expediente,
                    estado_anterior=estado_ant,
                    estado_nuevo=EstadoExpedienteEnum.PENDIENTE_CORREOS,
                    actor=actor_name,
                    motivo=(
                        "Resolución emitida con fallo en despacho de correos; pendiente de envío."
                    ),
                )
        elif expediente.estado != EstadoExpedienteEnum.EMITIDO:
            estado_ant = expediente.estado
            if not expediente.concepto:
                expediente.concepto = ConceptoExpedienteEnum.TD
            expediente.estado = EstadoExpedienteEnum.EMITIDO
            expediente.save(update_fields=["estado", "concepto", "updated_at"])
            actor_name = getattr(emisor, "username", str(emisor))
            CambioEstadoExpediente.objects.create(
                expediente=expediente,
                estado_anterior=estado_ant,
                estado_nuevo=EstadoExpedienteEnum.EMITIDO,
                actor=actor_name,
                motivo="Resolución emitida con la totalidad de firmas requeridas.",
            )

    return resolucion


def despachar_notificaciones_resolucion_emitida(resolucion: Resolucion) -> list[EmailOutbox]:
    """Despacha notificaciones atómicas en EmailOutbox hacia involucrados, CD y TD (EARS-100)."""
    despachados, _ = despachar_notificaciones_resolucion_emitida_con_estado(resolucion)
    return despachados


def despachar_notificaciones_resolucion_emitida_con_estado(
    resolucion: Resolucion,
) -> tuple[list[EmailOutbox], bool]:
    """Despacha notificaciones de resolución emitida y reporta si hubo fallos de envío."""
    expediente = getattr(resolucion, "expediente", None)
    if not expediente:
        return [], False

    numero_exp = resolucion.numero_expediente_snapshot or expediente.numero
    identificador = f"RESOLUCIÓN {numero_exp.replace('EXP-', '').strip()}"
    puntos_str = (
        f"{resolucion.puntos_finales:+.2f} pts"
        if resolucion.puntos_finales is not None
        else "0.00 pts"
    )
    medidas_str = ", ".join(resolucion.medidas) if resolucion.medidas else "Ninguna"

    despachados: list[EmailOutbox] = []
    hubo_fallo = False

    # 1. Notificar a socios involucrados activos (no excluidos)
    excluidos_ids = set(
        DescargoExpediente.objects.filter(expediente=expediente, esta_excluido=True).values_list(
            "socio_id", flat=True
        )
    )
    socios_destinatarios = list(expediente.socios.all())
    if expediente.socio and expediente.socio not in socios_destinatarios:
        socios_destinatarios.append(expediente.socio)

    for socio in socios_destinatarios:
        if socio.id in excluidos_ids:
            continue

        socio_email = (
            getattr(getattr(socio, "user", None), "email", None)
            or getattr(socio, "email", None)
            or f"socio.{socio.legajo}@aveit.test"
        )
        asunto_socio = f"[AVEIT] Expediente {numero_exp}: Emisión de {identificador}"
        cuerpo_socio = (
            f"Estimado/a {socio.first_name} {socio.last_name}:\n\n"
            f"Se notifica que el Tribunal de Disciplina ha emitido la {identificador} "
            f"correspondiente al expediente {numero_exp}.\n\n"
            "Resumen de lo resuelto:\n"
            f"- Puntaje final: {puntos_str}\n"
            f"- Medidas adoptadas: {medidas_str}\n\n"
            "La resolución se encuentra disponible en la plataforma SGD-AVEIT.\n\n"
            "Atentamente,\nTribunal de Disciplina — A.V.E.I.T."
        )

        AlertaSanitizer.assert_no_sensitive_data(asunto_socio)
        AlertaSanitizer.assert_no_sensitive_data(cuerpo_socio)

        try:
            outbox, _ = EmailDispatcherService.create_or_get_outbox(
                {
                    "to": [socio_email],
                    "subject": asunto_socio,
                    "body_text": cuerpo_socio,
                    "idempotency_key": f"resolucion-emision-{resolucion.id}-{socio_email}",
                    "metadata": {
                        "tipo": "EMISION_RESOLUCION",
                        "resolucion_id": resolucion.id,
                        "expediente_id": expediente.id,
                        "socio_id": socio.id,
                    },
                }
            )
            ok = EmailDispatcherService.dispatch(outbox)
            despachados.append(outbox)
            if ok is False or getattr(outbox, "status", None) == "FAILED":
                hubo_fallo = True
        except Exception as exc:
            logger.warning(
                "Fallo al despachar notificación de resolución a socio %s: %s",
                socio_email,
                exc,
            )
            hubo_fallo = True

    # 2. Notificar a Comisión Directiva
    cd_email = getattr(settings, "COMISION_DIRECTIVA_EMAIL", None) or getattr(
        settings, "CD_EMAIL", "cd@aveit.org"
    )
    asunto_cd = f"[AVEIT] Notificación CD: Emisión de {identificador} ({numero_exp})"
    cuerpo_cd = (
        "Estimados Miembros de la Comisión Directiva:\n\n"
        f"Se notifica formalmente la emisión de la {identificador} del expediente {numero_exp}.\n\n"
        f"- Puntos dictaminados: {puntos_str}\n"
        f"- Medidas: {medidas_str}\n\n"
        "Atentamente,\nTribunal de Disciplina — A.V.E.I.T."
    )
    AlertaSanitizer.assert_no_sensitive_data(asunto_cd)
    AlertaSanitizer.assert_no_sensitive_data(cuerpo_cd)

    try:
        outbox_cd, _ = EmailDispatcherService.create_or_get_outbox(
            {
                "to": [cd_email],
                "subject": asunto_cd,
                "body_text": cuerpo_cd,
                "idempotency_key": f"resolucion-emision-{resolucion.id}-cd",
                "metadata": {
                    "tipo": "EMISION_RESOLUCION_CD",
                    "resolucion_id": resolucion.id,
                    "expediente_id": expediente.id,
                },
            }
        )
        ok_cd = EmailDispatcherService.dispatch(outbox_cd)
        despachados.append(outbox_cd)
        if ok_cd is False or getattr(outbox_cd, "status", None) == "FAILED":
            hubo_fallo = True
    except Exception as exc:
        logger.warning("Fallo al despachar notificación de resolución a CD: %s", exc)
        hubo_fallo = True

    # 3. Notificar a Tribunal de Disciplina
    td_email = getattr(settings, "TRIBUNAL_EMAIL", "td@aveit.org")
    asunto_td = f"[AVEIT] Notificación TD: Perfeccionamiento de {identificador}"
    cuerpo_td = (
        "Estimados Integrantes del Tribunal de Disciplina:\n\n"
        f"Se ha completado la suscripción colegiada y emisión de la {identificador}.\n\n"
        f"- Sello criptográfico SHA-256: {resolucion.contenido_hash}\n"
        f"- Puntos dictaminados: {puntos_str}\n\n"
        "Atentamente,\nSGD-AVEIT — Tribunal de Disciplina"
    )
    AlertaSanitizer.assert_no_sensitive_data(asunto_td)
    AlertaSanitizer.assert_no_sensitive_data(cuerpo_td)

    try:
        outbox_td, _ = EmailDispatcherService.create_or_get_outbox(
            {
                "to": [td_email],
                "subject": asunto_td,
                "body_text": cuerpo_td,
                "idempotency_key": f"resolucion-emision-{resolucion.id}-td",
                "metadata": {
                    "tipo": "EMISION_RESOLUCION_TD",
                    "resolucion_id": resolucion.id,
                    "expediente_id": expediente.id,
                },
            }
        )
        ok_td = EmailDispatcherService.dispatch(outbox_td)
        despachados.append(outbox_td)
        if ok_td is False or getattr(outbox_td, "status", None) == "FAILED":
            hubo_fallo = True
    except Exception as exc:
        logger.warning("Fallo al despachar notificación de resolución a TD: %s", exc)
        hubo_fallo = True

    return despachados, hubo_fallo
