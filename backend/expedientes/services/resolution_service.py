"""Casos de uso transaccionales de resolución oficial."""

import hashlib
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from expedientes.domain.closed_decision import ClosedDecision, ClosedDecisionProvider
from expedientes.models import (
    CambioEstadoExpediente,
    ConceptoExpedienteEnum,
    EstadoExpedienteEnum,
    EstadoResolucionEnum,
    Expediente,
    Resolucion,
    SolicitudT01,
)
from expedientes.serializers.visor_serializers import cargar_mapa_grupos


class DictamenNoCerradoError(Exception):
    pass


class UnavailableClosedDecisionProvider:
    """Implementación temporal hasta integrar el contrato persistente de SCRUM-55."""

    def get_closed_decision(self, expediente_id: int) -> ClosedDecision | None:
        return None


class ExpedienteConsolidatedDecisionProvider:
    """Consolida la decisión de un expediente en etapa de resolución sin votación nominal."""

    def get_closed_decision(self, expediente_id: int) -> ClosedDecision | None:
        try:
            expediente = (
                Expediente.objects.prefetch_related(
                    "descargos__decisiones_causal",
                    "solicitud_t01",
                )
                .filter(pk=expediente_id)
                .first()
            )
        except Exception:
            return None

        if expediente is None:
            return None

        # Si aún no está en etapa de revisión/resolución/firma, retorna None
        if expediente.estado in (EstadoExpedienteEnum.CREADO, EstadoExpedienteEnum.JUSTIFICANDO):
            return None

        puntos = (
            Decimal(str(expediente.puntos)) if expediente.puntos is not None else Decimal("0.00")
        )
        medidas: list[str] = []

        # Revisar solicitud T01 si existe
        solicitud_t01 = getattr(expediente, "solicitud_t01", None)
        if solicitud_t01 and getattr(solicitud_t01, "puntaje_especial", None):
            if solicitud_t01.puntaje_especial == SolicitudT01.PuntajeEspecial.LLAMADO_ATENCION:
                medidas.append("Llamado de atención")
            elif solicitud_t01.puntaje_especial == SolicitudT01.PuntajeEspecial.FELICITACION:
                medidas.append("Felicitación")

        # Revisar descargos y sus decisiones más recientes
        for descargo in expediente.descargos.all():
            ultima_decision = descargo.decisiones_causal.order_by("-version").first()
            if ultima_decision:
                snapshot = ultima_decision.descargo_snapshot or {}
                ptos_val = snapshot.get("puntaje_final")
                if ptos_val == "LLAMADO_ATENCION":
                    if "Llamado de atención" not in medidas:
                        medidas.append("Llamado de atención")
                    puntos = Decimal("-0.25")
                elif ptos_val == "FELICITACION":
                    if "Felicitación" not in medidas:
                        medidas.append("Felicitación")
                    puntos = Decimal("0.25")
                elif ptos_val is not None:
                    try:
                        puntos = Decimal(str(ptos_val))
                    except Exception:
                        pass
                else:
                    if ultima_decision.decision == "ACCEPTED":
                        puntos = Decimal("0.00")
                    elif ultima_decision.decision == "REJECTED":
                        puntos = Decimal(str(expediente.puntos))

        puntos_finales = puntos.quantize(Decimal("0.01"))
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
def registrar_firma_resolucion(resolucion: Resolucion, user) -> Resolucion:
    """Registra la firma real del usuario TD autenticado según su año social."""
    resolucion = (
        Resolucion.objects.select_for_update().select_related("expediente").get(pk=resolucion.pk)
    )
    if resolucion.estado == EstadoResolucionEnum.ISSUED:
        raise ValidationError("Una resolución emitida ya no admite nuevas firmas.")

    socio = getattr(user, "socio", None)
    legajo = str(getattr(socio, "legajo", "") or getattr(user, "username", "")).strip()
    first_name = (getattr(socio, "first_name", "") or getattr(user, "first_name", "")).strip()
    last_name = (getattr(socio, "last_name", "") or getattr(user, "last_name", "")).strip()
    full_name = f"{first_name} {last_name}".strip() or getattr(user, "username", str(user))

    mapa_grupos = cargar_mapa_grupos()
    grupo = mapa_grupos.get(legajo, "")

    firmantes_existentes = list(resolucion.firmantes or [])
    for f in firmantes_existentes:
        if f.get("user_id") == user.id or (f.get("legajo") and f.get("legajo") == legajo):
            raise ValidationError("El usuario ya ha firmado esta resolución.")

    anios_ocupados = {
        int(f.get("social_year") or f.get("anio_social"))
        for f in firmantes_existentes
        if (f.get("social_year") or f.get("anio_social")) is not None
    }

    raw_social_year = getattr(socio, "social_year", None)
    try:
        social_year = int(raw_social_year) if raw_social_year is not None else None
    except (ValueError, TypeError):
        social_year = None

    if social_year not in (4, 5, 6):
        disponibles = [y for y in (4, 5, 6) if y not in anios_ocupados]
        if not disponibles:
            raise ValidationError("La resolución ya cuenta con las firmas de los 3 años sociales.")
        social_year = disponibles[0]

    if social_year in anios_ocupados:
        raise ValidationError(f"El {social_year}.º año social ya se encuentra firmado.")

    if not grupo and social_year:
        current_year = timezone.localdate().year
        grupo = f"G{(current_year - 1962) - int(social_year)}"

    etiqueta = f"{legajo} - {full_name} - {grupo}" if grupo else f"{legajo} - {full_name}"

    ahora_iso = timezone.now().isoformat()
    registro_firma = {
        "user_id": user.id,
        "legajo": legajo,
        "full_name": full_name,
        "social_year": social_year,
        "anio_social": social_year,
        "grupo": grupo,
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
    if {4, 5, 6}.issubset(anios_actualizados) or len(resolucion.firmantes) >= 3:
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
    resolucion.numero_expediente_snapshot = resolucion.expediente.numero
    resolucion.puntos_finales = Decimal(decision.puntos_finales).quantize(Decimal("0.01"))
    resolucion.medidas = list(decision.medidas)
    resolucion.estado = EstadoResolucionEnum.ISSUED
    resolucion.issued_by = emisor
    resolucion.issued_at = timezone.now()
    payload = "|".join(
        (
            resolucion.numero_expediente_snapshot,
            resolucion.vistos,
            resolucion.considerandos,
            resolucion.articulos_resolutivos,
            str(resolucion.puntos_finales),
            repr(resolucion.medidas),
        )
    )
    resolucion.contenido_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    resolucion.save()

    expediente = resolucion.expediente
    if expediente and expediente.estado != EstadoExpedienteEnum.EMITIDO:
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
