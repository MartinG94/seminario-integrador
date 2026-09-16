"""Pruebas unitarias para la lógica de cálculo y reconciliación de saldos."""

import pytest

from ranking.models import Socio, Subcomision, TipoSocio
from ranking.services import calculate_reconciliation


@pytest.mark.unit
class TestReconciliationCalculation:
    """Pruebas de la función pura de reconciliación de saldos."""

    def test_calculate_reconciliation_zero_balances(self) -> None:
        """Caso 1: Socio sin movimientos previos ni saldo histórico (0 y 0)."""
        sh, sc, diff, rec = calculate_reconciliation(0.0, 0.0)
        assert sh == 0.0
        assert sc == 0.0
        assert diff == 0.0
        assert rec is True

    def test_calculate_reconciliation_matching_positive_balances(self) -> None:
        """Caso 2: Saldo histórico y caché coincidentes en valor positivo (+5.0)."""
        sh, sc, diff, rec = calculate_reconciliation(5.0, 5.0)
        assert sh == 5.0
        assert sc == 5.0
        assert diff == 0.0
        assert rec is True

    def test_calculate_reconciliation_matching_negative_balances(self) -> None:
        """Caso 3: Saldo histórico y caché coincidentes en valor negativo (-1.0)."""
        sh, sc, diff, rec = calculate_reconciliation(-1.0, -1.0)
        assert sh == -1.0
        assert sc == -1.0
        assert diff == 0.0
        assert rec is True

    def test_calculate_reconciliation_discrepancy_positive_diff(self) -> None:
        """Caso 4: Discrepancia donde el libro mayor supera a la caché (+3.5 vs +3.0)."""
        sh, sc, diff, rec = calculate_reconciliation(3.5, 3.0)
        assert sh == 3.5
        assert sc == 3.0
        assert diff == 0.5
        assert rec is False

    def test_calculate_reconciliation_discrepancy_negative_diff(self) -> None:
        """Caso 5: Discrepancia donde el libro mayor es menor a la caché (-2.0 vs -1.5)."""
        sh, sc, diff, rec = calculate_reconciliation(-2.0, -1.5)
        assert sh == -2.0
        assert sc == -1.5
        assert diff == -0.5
        assert rec is False

    def test_calculate_reconciliation_none_values(self) -> None:
        """Caso 6: Valores nulos se tratan defensivamente como 0.0."""
        sh, sc, diff, rec = calculate_reconciliation(None, None)
        assert sh == 0.0
        assert sc == 0.0
        assert diff == 0.0
        assert rec is True


@pytest.mark.unit
class TestSocioCategoryDerivation:
    """Pruebas de derivación de categoría estatutaria (Regla canónica AVEIT)."""

    def test_categoria_pasivo_for_first_three_social_years(self) -> None:
        """Años sociales 1, 2 y 3 deben categorizarse como 'PASIVO' (ex Junior)."""
        sub = Subcomision(codSubcomision=1, nombre="Cómputos")
        tipo = TipoSocio(idTipoSocio=1, nombre="Socio Ordinario")

        s1 = Socio(anoSocial=1, subcomision=sub, tipoSocio=tipo)
        s2 = Socio(anoSocial=2, subcomision=sub, tipoSocio=tipo)
        s3 = Socio(anoSocial=3, subcomision=sub, tipoSocio=tipo)

        assert s1.categoria == "PASIVO"
        assert s2.categoria == "PASIVO"
        assert s3.categoria == "PASIVO"

    def test_categoria_activo_for_fourth_to_sixth_social_years(self) -> None:
        """Años sociales 4, 5 y 6 deben categorizarse como 'ACTIVO' (ex Senior)."""
        sub = Subcomision(codSubcomision=1, nombre="Cómputos")
        tipo = TipoSocio(idTipoSocio=1, nombre="Socio Ordinario")

        s4 = Socio(anoSocial=4, subcomision=sub, tipoSocio=tipo)
        s5 = Socio(anoSocial=5, subcomision=sub, tipoSocio=tipo)
        s6 = Socio(anoSocial=6, subcomision=sub, tipoSocio=tipo)

        assert s4.categoria == "ACTIVO"
        assert s5.categoria == "ACTIVO"
        assert s6.categoria == "ACTIVO"
