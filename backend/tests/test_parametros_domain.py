"""Catálogo y validación de parámetros del sistema (Spec 010, T1). Dominio puro, sin base."""

from decimal import Decimal

import pytest

from core.domain.system_parameters import (
    CATALOG,
    ParameterType,
    ParameterValidationError,
    UnknownParameterError,
    get_definition,
    normalize_value,
)

EXPECTED_KEYS = {
    "plazo_descargo_dias_habiles",
    "plazo_apelacion_dias_habiles",
    "umbral_critico",
    "umbral_preventivo",
    "umbral_preventivo_activo",
    "email_comision_directiva",
    "email_tribunal_disciplina",
    "adjuntos_tamano_maximo_mb",
    "adjuntos_cantidad_maxima",
}


def test_catalog_exposes_the_nine_parameters_grouped_in_four_cards() -> None:
    assert {definition.clave for definition in CATALOG} == EXPECTED_KEYS
    assert {definition.categoria for definition in CATALOG} == {
        "PLAZOS",
        "UMBRALES",
        "CORREOS",
        "ADJUNTOS",
    }


def test_initial_values_match_the_rules_in_force() -> None:
    assert get_definition("plazo_descargo_dias_habiles").default == 5
    assert get_definition("plazo_apelacion_dias_habiles").default == 5
    assert get_definition("umbral_critico").default == Decimal("-10.0")
    assert get_definition("umbral_preventivo").default == Decimal("-7.0")
    assert get_definition("umbral_preventivo_activo").default is False
    assert get_definition("adjuntos_tamano_maximo_mb").default == 5
    assert get_definition("adjuntos_cantidad_maxima").default == 5


def test_critical_threshold_is_the_only_read_only_parameter() -> None:
    assert [d.clave for d in CATALOG if not d.editable] == ["umbral_critico"]


def test_unknown_key_is_rejected() -> None:
    with pytest.raises(UnknownParameterError):
        get_definition("inexistente")


@pytest.mark.parametrize("raw", [1, 30, "7", 5.0])
def test_integer_within_limits_is_normalized(raw: object) -> None:
    value = normalize_value(get_definition("plazo_descargo_dias_habiles"), raw)
    assert value == int(float(raw))
    assert isinstance(value, int)


@pytest.mark.parametrize("raw", [0, 31, -1, 2.5, "abc", None, True, ""])
def test_integer_out_of_limits_or_malformed_is_rejected(raw: object) -> None:
    with pytest.raises(ParameterValidationError) as exc:
        normalize_value(get_definition("plazo_descargo_dias_habiles"), raw)
    assert "entre 1 y 30" in str(exc.value) or "número entero" in str(exc.value)


@pytest.mark.parametrize(("raw", "expected"), [("-8", "-8"), (-7.5, "-7.5"), ("-0.01", "-0.01")])
def test_preventive_threshold_is_stored_as_decimal_text(raw: object, expected: str) -> None:
    assert normalize_value(get_definition("umbral_preventivo"), raw) == expected


@pytest.mark.parametrize("raw", ["-10", "-12", "0", "3", "-7.555", "x", None, True])
def test_preventive_threshold_must_stay_above_critical_and_below_zero(raw: object) -> None:
    with pytest.raises(ParameterValidationError):
        normalize_value(get_definition("umbral_preventivo"), raw)


@pytest.mark.parametrize("raw", [True, False])
def test_boolean_accepts_only_booleans(raw: bool) -> None:
    assert normalize_value(get_definition("umbral_preventivo_activo"), raw) is raw


@pytest.mark.parametrize("raw", ["true", 1, 0, None, "sí"])
def test_boolean_rejects_other_types(raw: object) -> None:
    with pytest.raises(ParameterValidationError):
        normalize_value(get_definition("umbral_preventivo_activo"), raw)


def test_email_is_trimmed_and_lowercased() -> None:
    definition = get_definition("email_tribunal_disciplina")
    assert definition.tipo == ParameterType.EMAIL
    assert normalize_value(definition, "  Tribunal@AVEIT.test ") == "tribunal@aveit.test"


@pytest.mark.parametrize("raw", ["", "sin-arroba", "a@b", "a b@c.d", 5, None, "x" * 150 + "@a.io"])
def test_invalid_email_is_rejected(raw: object) -> None:
    with pytest.raises(ParameterValidationError):
        normalize_value(get_definition("email_tribunal_disciplina"), raw)


def test_read_only_parameter_cannot_be_normalized_for_writing() -> None:
    with pytest.raises(ParameterValidationError) as exc:
        normalize_value(get_definition("umbral_critico"), "-12")
    assert "reglamentario" in str(exc.value)
