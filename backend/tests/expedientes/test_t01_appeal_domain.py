"""Dominio puro de apelación y adecuación del T01 (PB-02, Spec 008)."""

from decimal import Decimal

import pytest

from expedientes.domain.t01_appeal import (
    DEFAULT_APPEAL_BUSINESS_DAYS,
    ActionType,
    AppealError,
    evaluate_adjustment,
    validate_appeal_text,
    validate_business_days,
)

GROUNDS = "El debate acreditó la participación de un tercer socio."


def evaluar(**overrides):
    params = {
        "action": ActionType.SANCTION,
        "old_points": Decimal("-2"),
        "new_points": Decimal("-2"),
        "old_ids": {1, 2},
        "new_ids": {1, 2},
        "grounds": GROUNDS,
        "reopen": False,
    }
    params.update(overrides)
    return evaluate_adjustment(**params)


class TestPlazo:
    def test_valor_por_defecto_del_art_12(self):
        assert DEFAULT_APPEAL_BUSINESS_DAYS == 5

    @pytest.mark.parametrize("dias", [1, 5, 30])
    def test_plazo_valido(self, dias):
        validate_business_days(dias)

    @pytest.mark.parametrize("dias", [0, -1, 31])
    def test_plazo_fuera_de_rango(self, dias):
        with pytest.raises(AppealError, match="entre 1 y 30"):
            validate_business_days(dias)


class TestTextoApelacion:
    def test_recorta_y_acepta(self):
        assert validate_appeal_text("  No estuve presente en el lugar del hecho.  ") == (
            "No estuve presente en el lugar del hecho."
        )

    def test_texto_breve(self):
        with pytest.raises(AppealError, match="20 caracteres"):
            validate_appeal_text("No fui yo")

    def test_texto_extenso(self):
        with pytest.raises(AppealError, match="5000"):
            validate_appeal_text("a" * 5001)


class TestAdecuacion:
    def test_agregar_involucrado(self):
        resultado = evaluar(new_ids={1, 2, 3})
        assert resultado.added == {3}
        assert resultado.removed == set()
        assert resultado.worsens is False
        assert resultado.affected == {3}

    def test_quitar_involucrado_no_afecta_a_nadie(self):
        resultado = evaluar(new_ids={1})
        assert resultado.removed == {2}
        assert resultado.affected == set()

    def test_agravar_puntos_afecta_a_todos_los_involucrados(self):
        resultado = evaluar(new_points=Decimal("-3"))
        assert resultado.worsens is True
        assert resultado.affected == {1, 2}

    def test_atenuar_puntos_no_afecta(self):
        resultado = evaluar(new_points=Decimal("-1"))
        assert resultado.points_changed is True
        assert resultado.worsens is False
        assert resultado.affected == set()

    def test_reducir_un_merito_lo_agrava(self):
        resultado = evaluar(
            action=ActionType.MERIT, old_points=Decimal("2"), new_points=Decimal("1")
        )
        assert resultado.worsens is True

    def test_sin_cambios(self):
        with pytest.raises(AppealError, match="no modifica"):
            evaluar()

    def test_sin_involucrados(self):
        with pytest.raises(AppealError, match="al menos un involucrado"):
            evaluar(new_ids=set())

    def test_sancion_con_puntos_positivos(self):
        with pytest.raises(AppealError, match="negativos"):
            evaluar(new_points=Decimal("1"))

    def test_merito_con_puntos_negativos(self):
        with pytest.raises(AppealError, match="positivos"):
            evaluar(action=ActionType.MERIT, old_points=Decimal("2"), new_points=Decimal("-1"))

    def test_motivos_obligatorios(self):
        with pytest.raises(AppealError, match="motivos"):
            evaluar(new_ids={1}, grounds="Breve")

    def test_reabrir_plazo_sin_afectados(self):
        with pytest.raises(AppealError, match="afectados"):
            evaluar(new_ids={1}, reopen=True)

    def test_reabrir_plazo_con_afectados(self):
        assert evaluar(new_ids={1, 2, 3}, reopen=True).affected == {3}
