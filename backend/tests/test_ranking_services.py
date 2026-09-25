"""Pruebas unitarias para la lógica de cálculo y reconciliación de saldos."""

import re
from decimal import Decimal

import pytest

from padron.models import Socio, Subcomision
from ranking.serializers import RankingSocioSerializer
from ranking.services import calculate_reconciliation, make_accent_insensitive_regex


@pytest.mark.unit
class TestReconciliationCalculation:
    """Pruebas de la función pura de reconciliación de saldos."""

    def test_calculate_reconciliation_zero_balances(self) -> None:
        """Caso 1: Socio sin movimientos previos ni saldo histórico (0 y 0)."""
        sh, sc, diff, rec = calculate_reconciliation(Decimal("0.00"), Decimal("0.00"))
        assert sh == Decimal("0.00")
        assert sc == Decimal("0.00")
        assert diff == Decimal("0.00")
        assert rec is True

    def test_calculate_reconciliation_matching_positive_balances(self) -> None:
        """Caso 2: Saldo histórico y caché coincidentes en valor positivo (+5.0)."""
        sh, sc, diff, rec = calculate_reconciliation(Decimal("5.00"), Decimal("5.00"))
        assert sh == Decimal("5.00")
        assert sc == Decimal("5.00")
        assert diff == Decimal("0.00")
        assert rec is True

    def test_calculate_reconciliation_matching_negative_balances(self) -> None:
        """Caso 3: Saldo histórico y caché coincidentes en valor negativo (-1.0)."""
        sh, sc, diff, rec = calculate_reconciliation(Decimal("-1.00"), Decimal("-1.00"))
        assert sh == Decimal("-1.00")
        assert sc == Decimal("-1.00")
        assert diff == Decimal("0.00")
        assert rec is True

    def test_calculate_reconciliation_discrepancy_positive_diff(self) -> None:
        """Caso 4: Discrepancia donde el libro mayor supera a la caché (+3.5 vs +3.0)."""
        sh, sc, diff, rec = calculate_reconciliation(Decimal("3.50"), Decimal("3.00"))
        assert sh == Decimal("3.50")
        assert sc == Decimal("3.00")
        assert diff == Decimal("0.50")
        assert rec is False

    def test_calculate_reconciliation_discrepancy_negative_diff(self) -> None:
        """Caso 5: Discrepancia donde el libro mayor es menor a la caché (-2.0 vs -1.5)."""
        sh, sc, diff, rec = calculate_reconciliation(Decimal("-2.00"), Decimal("-1.50"))
        assert sh == Decimal("-2.00")
        assert sc == Decimal("-1.50")
        assert diff == Decimal("-0.50")
        assert rec is False

    def test_calculate_reconciliation_none_values(self) -> None:
        """Caso 6: Valores nulos se tratan defensivamente como 0.0."""
        sh, sc, diff, rec = calculate_reconciliation(None, None)
        assert sh == Decimal("0.00")
        assert sc == Decimal("0.00")
        assert diff == Decimal("0.00")
        assert rec is True


@pytest.mark.unit
class TestSocioCategoryDerivation:
    """Pruebas de derivación de categoría estatutaria (Regla canónica AVEIT)."""

    def test_categoria_pasivo_for_first_three_social_years(self) -> None:
        """Años sociales 1, 2 y 3 deben categorizarse como 'PASIVO' (ex Junior)."""
        sub = Subcomision(codSubcomision=1, nombre="Cómputos")

        s1 = Socio(anoSocial=1, subcomision=sub, idTipoSocio=1)
        s2 = Socio(anoSocial=2, subcomision=sub, idTipoSocio=1)
        s3 = Socio(anoSocial=3, subcomision=sub, idTipoSocio=1)

        assert RankingSocioSerializer().get_categoria(s1) == "PASIVO"
        assert RankingSocioSerializer().get_categoria(s2) == "PASIVO"
        assert RankingSocioSerializer().get_categoria(s3) == "PASIVO"

    def test_categoria_activo_for_fourth_to_sixth_social_years(self) -> None:
        """Años sociales 4, 5 y 6 deben categorizarse como 'ACTIVO' (ex Senior)."""
        sub = Subcomision(codSubcomision=1, nombre="Cómputos")

        s4 = Socio(anoSocial=4, subcomision=sub, idTipoSocio=1)
        s5 = Socio(anoSocial=5, subcomision=sub, idTipoSocio=1)
        s6 = Socio(anoSocial=6, subcomision=sub, idTipoSocio=1)

        assert RankingSocioSerializer().get_categoria(s4) == "ACTIVO"
        assert RankingSocioSerializer().get_categoria(s5) == "ACTIVO"
        assert RankingSocioSerializer().get_categoria(s6) == "ACTIVO"

    def test_categoria_none_or_zero_social_year_defaults_to_pasivo(self) -> None:
        """Año social None o 0 debe categorizarse como 'PASIVO' sin elevar excepciones."""
        sub = Subcomision(codSubcomision=1, nombre="Cómputos")

        s_none = Socio(anoSocial=None, subcomision=sub, idTipoSocio=1)
        s_zero = Socio(anoSocial=0, subcomision=sub, idTipoSocio=1)

        assert RankingSocioSerializer().get_categoria(s_none) == "PASIVO"
        assert RankingSocioSerializer().get_categoria(s_zero) == "PASIVO"


@pytest.mark.unit
class TestAccentInsensitiveRegex:
    """Pruebas de construcción de expresiones regulares insensibles a tildes."""

    def test_make_accent_insensitive_regex_expands_vowels(self) -> None:
        pat = make_accent_insensitive_regex("perez")
        assert re.search(pat, "Pérez", re.IGNORECASE)
        assert re.search(pat, "perez", re.IGNORECASE)

        pat_comp = make_accent_insensitive_regex("computos")
        assert re.search(pat_comp, "Cómputos", re.IGNORECASE)
        assert re.search(pat_comp, "computos", re.IGNORECASE)


@pytest.mark.unit
@pytest.mark.parametrize("model_name", ["PuntajeAplicado", "PuntajeGeneral"])
def test_score_models_are_read_only_unmanaged_decimal(model_name):
    from django.core.exceptions import PermissionDenied
    from django.db.models import DecimalField

    from ranking import models as ranking_models

    model = getattr(ranking_models, model_name)
    field_name = "puntajeAplicado" if model_name == "PuntajeAplicado" else "puntos"
    field = model._meta.get_field(field_name)
    assert model._meta.managed is False
    assert isinstance(field, DecimalField)
    assert (field.max_digits, field.decimal_places) == (10, 2)
    assert model._meta.get_field("socio").related_model is Socio
    with pytest.raises(PermissionDenied):
        model().save()
    with pytest.raises(PermissionDenied):
        model.objects.bulk_create([])


@pytest.mark.unit
def test_ranking_only_registers_score_models():
    from django.apps import apps

    assert {model.__name__ for model in apps.get_app_config("ranking").get_models()} == {
        "PuntajeAplicado",
        "PuntajeGeneral",
    }
