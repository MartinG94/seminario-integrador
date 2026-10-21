"""Reglas de dominio para resolver causales tipificadas T02 (S4-02).

Dominio puro sin dependencias de Django:
- Regla sugerida: un T02 con comprobante vigente sugiere aceptar la causal (Spec 005).
- Fundamento obligatorio al rechazar o al apartarse de la regla sugerida (CA2).
"""

from enum import StrEnum

MIN_GROUNDS_LENGTH = 20


class CausalDecision(StrEnum):
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


class CausalDecisionError(ValueError):
    """La decisión no cumple las reglas de fundamentación."""


def suggested_decision(has_current_evidence: bool) -> CausalDecision:
    """Regla orientativa: la causal T02 se acredita con al menos un comprobante vigente."""
    return CausalDecision.ACCEPTED if has_current_evidence else CausalDecision.REJECTED


def requires_grounds(decision: CausalDecision, suggested: CausalDecision) -> bool:
    return decision == CausalDecision.REJECTED or decision != suggested


def validate_decision(decision: CausalDecision, suggested: CausalDecision, grounds: str) -> None:
    if requires_grounds(decision, suggested) and len(grounds.strip()) < MIN_GROUNDS_LENGTH:
        raise CausalDecisionError(
            "Indicá un fundamento de al menos "
            f"{MIN_GROUNDS_LENGTH} caracteres para rechazar la causal "
            "o apartarte de la regla sugerida."
        )
