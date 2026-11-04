"""Casos de uso transaccionales de resolución oficial."""

import hashlib
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from expedientes.domain.closed_decision import ClosedDecision, ClosedDecisionProvider
from expedientes.models import (
    EstadoExpedienteEnum,
    EstadoResolucionEnum,
    Expediente,
    Resolucion,
    SolicitudT01,
)
from expedientes.serializers.visor_serializers import cargar_mapa_grupos
from socios.models import Role, Socio


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


FALLBACK_FIRMANTES_TD = {
    4: "11735 - Candela Moreno Migliore - G59",
    5: "11737 - Catalina Cerda Gallego - G58",
    6: "11239 - Giuliano Toselli - G57",
}


def obtener_firmantes_td_por_anio_social() -> list[str]:
    """Selecciona 3 firmantes del Tribunal de Disciplina, uno por cada año social (4, 5 y 6)."""
    socios_td = list(Socio.objects.filter(role=Role.TD, is_enabled=True).order_by("id"))
    mapa_grupos = cargar_mapa_grupos()
    socios_por_anio: dict[int, Socio] = {}
    for s in socios_td:
        if s.social_year in (4, 5, 6) and s.social_year not in socios_por_anio:
            socios_por_anio[s.social_year] = s

    firmantes: list[str] = []
    for anio in (4, 5, 6):
        soc = socios_por_anio.get(anio)
        if soc:
            nro_socio = str(soc.legajo or "").strip()
            nombre = f"{soc.first_name} {soc.last_name}".strip()
            grupo = mapa_grupos.get(nro_socio, "")
            if not grupo and soc.social_year:
                current_year = timezone.localdate().year
                grupo = f"G{(current_year - 1962) - int(soc.social_year)}"
            if not grupo:
                fallback_val = FALLBACK_FIRMANTES_TD[anio]
                grupo = fallback_val.split(" - ")[-1]
            firmantes.append(f"{nro_socio} - {nombre} - {grupo}")
        else:
            firmantes.append(FALLBACK_FIRMANTES_TD[anio])
    return firmantes


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
    return resolucion
