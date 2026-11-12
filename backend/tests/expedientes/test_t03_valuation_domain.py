"""Pruebas unitarias del dominio de la valoración extraordinaria T03 (S4-03)."""

import pytest

from expedientes.domain.ports import TribunalConditionPort
from expedientes.domain.t03_valuation import (
    MAX_GROUNDS_LENGTH,
    MIN_GROUNDS_LENGTH,
    T03ValuationError,
    T03ValuationResult,
    TribunalCondition,
    condition_for_position,
    normalize_case_number,
    validate_antecedent_ids,
    validate_valuation,
)

VALID_GROUNDS = "El Tribunal considera acreditada la causa extraordinaria invocada."


class TestValidateValuation:
    """RF-2, RF-3 y RF-4: resultado binario y fundamento siempre obligatorio (S-1)."""

    @pytest.mark.parametrize("result", ["ACCEPTED", "REJECTED"])
    def test_accepts_both_results_with_grounds(self, result: str) -> None:
        assert validate_valuation(result, VALID_GROUNDS) == T03ValuationResult(result)

    @pytest.mark.parametrize("result", ["", "PARTIAL", "accepted", None])
    def test_rejects_invalid_result(self, result: object) -> None:
        with pytest.raises(T03ValuationError, match="resultado"):
            validate_valuation(result, VALID_GROUNDS)  # type: ignore[arg-type]

    @pytest.mark.parametrize("result", ["ACCEPTED", "REJECTED"])
    @pytest.mark.parametrize("grounds", ["", "   ", "\n\t "])
    def test_grounds_are_required_for_any_result(self, result: str, grounds: str) -> None:
        with pytest.raises(T03ValuationError, match="fundamento"):
            validate_valuation(result, grounds)

    def test_rejects_missing_grounds(self) -> None:
        with pytest.raises(T03ValuationError, match="fundamento"):
            validate_valuation("ACCEPTED", None)  # type: ignore[arg-type]

    def test_rejects_grounds_below_minimum(self) -> None:
        with pytest.raises(T03ValuationError, match="fundamento"):
            validate_valuation("ACCEPTED", "x" * (MIN_GROUNDS_LENGTH - 1))

    def test_minimum_ignores_surrounding_spaces(self) -> None:
        padded = "   " + "x" * (MIN_GROUNDS_LENGTH - 1) + "   "
        with pytest.raises(T03ValuationError, match="fundamento"):
            validate_valuation("REJECTED", padded)

    def test_accepts_grounds_at_minimum(self) -> None:
        assert validate_valuation("REJECTED", "x" * MIN_GROUNDS_LENGTH) == (
            T03ValuationResult.REJECTED
        )

    def test_accepts_grounds_at_maximum(self) -> None:
        assert validate_valuation("ACCEPTED", "x" * MAX_GROUNDS_LENGTH) == (
            T03ValuationResult.ACCEPTED
        )

    def test_rejects_grounds_above_maximum(self) -> None:
        with pytest.raises(T03ValuationError, match="fundamento"):
            validate_valuation("ACCEPTED", "x" * (MAX_GROUNDS_LENGTH + 1))

    def test_limits_match_spec(self) -> None:
        assert (MIN_GROUNDS_LENGTH, MAX_GROUNDS_LENGTH) == (20, 5000)


class TestNormalizeCaseNumber:
    """Brecha B6: la UI muestra N/YYYY y el número se guarda como EXP-NNNN/YYYY."""

    @pytest.mark.parametrize(
        "text",
        ["7/2026", "007/2026", "EXP-0007/2026", "exp-0007/2026", "  7/2026  ", " Exp-7/2026"],
    )
    def test_normalizes_accepted_formats(self, text: str) -> None:
        assert normalize_case_number(text) == "EXP-0007/2026"

    def test_keeps_numbers_wider_than_four_digits(self) -> None:
        assert normalize_case_number("12345/2026") == "EXP-12345/2026"

    @pytest.mark.parametrize(
        "text",
        ["", "   ", "7/26", "abc", "7-2026", "EXP-0007", "7/2026x", "EXP-/2026", None],
    )
    def test_rejects_invalid_formats(self, text: object) -> None:
        with pytest.raises(T03ValuationError, match="número de expediente"):
            normalize_case_number(text)  # type: ignore[arg-type]


class TestValidateAntecedentIds:
    """RF-12 y RF-14: cero o más antecedentes, sin repetidos ni el propio expediente."""

    def test_empty_list_is_valid(self) -> None:
        assert validate_antecedent_ids([], expediente_id=10) == []

    def test_keeps_order_of_valid_ids(self) -> None:
        assert validate_antecedent_ids([3, 1, 2], expediente_id=10) == [3, 1, 2]

    def test_rejects_repeated_antecedent(self) -> None:
        with pytest.raises(T03ValuationError, match="repetido"):
            validate_antecedent_ids([3, 4, 3], expediente_id=10)

    def test_rejects_own_expediente(self) -> None:
        with pytest.raises(T03ValuationError, match="mismo expediente"):
            validate_antecedent_ids([3, 10], expediente_id=10)


class TestConditionForPosition:
    """RF-5 y S-7: condición de Miembro Titular o Suplente según `idTipoSocio` del padrón."""

    def test_position_10_is_titular(self) -> None:
        assert condition_for_position(10) == TribunalCondition.TITULAR

    def test_position_11_is_suplente(self) -> None:
        assert condition_for_position(11) == TribunalCondition.SUPLENTE

    @pytest.mark.parametrize("position", [1, 9, 12, 0])
    def test_other_position_is_not_informed(self, position: int) -> None:
        assert condition_for_position(position) == TribunalCondition.NO_INFORMADA

    def test_missing_position_is_not_informed(self) -> None:
        assert condition_for_position(None) == TribunalCondition.NO_INFORMADA


class TestTribunalConditionPort:
    def test_any_object_with_condition_for_user_satisfies_port(self) -> None:
        class FakeProvider:
            def condition_for_user(self, user_id: int) -> TribunalCondition:
                return TribunalCondition.SUPLENTE

        assert isinstance(FakeProvider(), TribunalConditionPort)
        assert not isinstance(object(), TribunalConditionPort)
