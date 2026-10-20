"""Pruebas unitarias del dominio de decisión por causal T02 (S4-02, CA1 y CA2)."""

import pytest

from expedientes.domain.causal_resolution import (
    MIN_GROUNDS_LENGTH,
    CausalDecision,
    CausalDecisionError,
    requires_grounds,
    suggested_decision,
    validate_decision,
)

VALID_GROUNDS = "El certificado no acredita la fecha de la inasistencia."


class TestSuggestedDecision:
    def test_suggests_accept_when_descargo_has_current_evidence(self) -> None:
        assert suggested_decision(has_current_evidence=True) == CausalDecision.ACCEPTED

    def test_suggests_reject_without_current_evidence(self) -> None:
        assert suggested_decision(has_current_evidence=False) == CausalDecision.REJECTED


class TestRequiresGrounds:
    def test_accepting_following_rule_does_not_require_grounds(self) -> None:
        assert not requires_grounds(CausalDecision.ACCEPTED, CausalDecision.ACCEPTED)

    def test_rejecting_always_requires_grounds(self) -> None:
        assert requires_grounds(CausalDecision.REJECTED, CausalDecision.REJECTED)
        assert requires_grounds(CausalDecision.REJECTED, CausalDecision.ACCEPTED)

    def test_departing_from_rule_requires_grounds(self) -> None:
        assert requires_grounds(CausalDecision.ACCEPTED, CausalDecision.REJECTED)


class TestValidateDecision:
    def test_accepts_decision_following_rule_without_grounds(self) -> None:
        validate_decision(CausalDecision.ACCEPTED, CausalDecision.ACCEPTED, "")

    @pytest.mark.parametrize("grounds", ["", "   ", "Muy corto"])
    def test_rejection_without_enough_grounds_fails(self, grounds: str) -> None:
        with pytest.raises(CausalDecisionError):
            validate_decision(CausalDecision.REJECTED, CausalDecision.ACCEPTED, grounds)

    def test_departure_without_grounds_fails(self) -> None:
        with pytest.raises(CausalDecisionError):
            validate_decision(CausalDecision.ACCEPTED, CausalDecision.REJECTED, "")

    def test_grounds_length_ignores_surrounding_spaces(self) -> None:
        padded = "  " + "x" * (MIN_GROUNDS_LENGTH - 1) + "  "
        with pytest.raises(CausalDecisionError):
            validate_decision(CausalDecision.REJECTED, CausalDecision.REJECTED, padded)

    def test_rejection_with_grounds_is_valid(self) -> None:
        validate_decision(CausalDecision.REJECTED, CausalDecision.ACCEPTED, VALID_GROUNDS)
