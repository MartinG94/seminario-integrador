"""Servicio de aplicación para resolver causales T02 con fundamento trazable (S4-02)."""

from collections.abc import Sequence
from uuid import UUID

from django.db import transaction
from django.db.models import Max, Q, QuerySet

from expedientes.domain.causal_resolution import (
    CausalDecision,
    CausalDecisionError,
    suggested_decision,
    validate_decision,
)
from expedientes.models import (
    DecisionCausalDescargo,
    DescargoExpediente,
    EstadoExpedienteEnum,
    EvidenciaDescargo,
    Expediente,
    TipoDescargoEnum,
)

DECIDABLE_STATES = (
    EstadoExpedienteEnum.REVISION_RESOLUCION,
    EstadoExpedienteEnum.ESPERA_RESOLUCION,
)


class CausalResolutionError(Exception):
    """Error base del servicio de decisión por causal."""


class CausalResolutionNotFound(CausalResolutionError):
    pass


class CausalResolutionStateError(CausalResolutionError):
    pass


class CausalResolutionValidationError(CausalResolutionError):
    pass


def current_evidence_for(descargo: DescargoExpediente) -> QuerySet[EvidenciaDescargo]:
    """Comprobantes vigentes del descargo, incluidos los aún no vinculados del mismo socio."""
    return EvidenciaDescargo.objects.filter(
        expediente_id=descargo.expediente_id, es_vigente=True
    ).filter(Q(descargo=descargo) | Q(descargo__isnull=True, socio_id=descargo.socio_id))


def suggested_for(descargo: DescargoExpediente) -> CausalDecision:
    return suggested_decision(has_current_evidence=current_evidence_for(descargo).exists())


def _descargo_snapshot(descargo: DescargoExpediente) -> dict:
    return {
        "socio_id": descargo.socio_id,
        "socio_legajo": descargo.socio.legajo,
        "tipo": descargo.tipo,
        "causal": descargo.causal,
        "texto": descargo.texto,
        "archivo": descargo.archivo,
        "presentado_at": descargo.presentado_at.isoformat() if descargo.presentado_at else None,
    }


class CausalResolutionService:
    @staticmethod
    def get_descargo(expediente_id: int, descargo_id: int) -> DescargoExpediente:
        descargo = (
            DescargoExpediente.objects.select_related("socio")
            .filter(pk=descargo_id, expediente_id=expediente_id)
            .first()
        )
        if descargo is None:
            raise CausalResolutionNotFound("Descargo no encontrado en este expediente.")
        return descargo

    @staticmethod
    @transaction.atomic
    def decide(
        *,
        expediente_id: int,
        descargo_id: int,
        decision: CausalDecision,
        fundamento: str,
        evidencia_ids: Sequence[UUID] | None,
        user,
    ) -> DecisionCausalDescargo:
        expediente = Expediente.objects.select_for_update().filter(pk=expediente_id).first()
        if expediente is None:
            raise CausalResolutionNotFound("Expediente no encontrado.")
        if expediente.estado not in DECIDABLE_STATES:
            raise CausalResolutionStateError(
                f"El expediente está en '{expediente.get_estado_display()}' "
                "y no admite decisiones sobre causales."
            )

        descargo = CausalResolutionService.get_descargo(expediente_id, descargo_id)
        if descargo.tipo != TipoDescargoEnum.T02_CERTIFICADO:
            raise CausalResolutionValidationError(
                "Sólo se resuelven acá las causales tipificadas del Formulario T02."
            )

        current = list(current_evidence_for(descargo))
        if evidencia_ids is None:
            valued = current
        else:
            by_id = {ev.id: ev for ev in current}
            unknown = [str(ev_id) for ev_id in evidencia_ids if ev_id not in by_id]
            if unknown:
                raise CausalResolutionValidationError(
                    "Uno o más comprobantes no pertenecen al descargo o no están vigentes."
                )
            valued = [by_id[ev_id] for ev_id in dict.fromkeys(evidencia_ids)]

        suggested = suggested_decision(has_current_evidence=bool(current))
        fundamento = fundamento.strip()
        try:
            validate_decision(decision, suggested, fundamento)
        except CausalDecisionError as exc:
            raise CausalResolutionValidationError(str(exc)) from exc

        last_version = (
            DecisionCausalDescargo.objects.filter(descargo=descargo).aggregate(last=Max("version"))[
                "last"
            ]
            or 0
        )
        socio = getattr(user, "socio", None)
        return DecisionCausalDescargo.objects.create(
            expediente=expediente,
            descargo=descargo,
            version=last_version + 1,
            decision=decision,
            regla_sugerida=suggested,
            se_aparta_de_regla=decision != suggested,
            fundamento=fundamento,
            evidencias_valoradas=[
                {
                    "id": str(ev.id),
                    "nombre_original": ev.nombre_original,
                    "sha256_hash": ev.sha256_hash,
                }
                for ev in valued
            ],
            descargo_snapshot=_descargo_snapshot(descargo),
            autor=user,
            autor_legajo=socio.legajo if socio else user.get_username(),
            autor_rol=socio.role if socio else "",
        )
