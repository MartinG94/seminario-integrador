"""Tests unitarios para las reglas canónicas de dominio del padrón institucional.

Cobertura:
  - CA2: Identidad estable (legajo, DNI).
  - CA3: Categorización estatutaria (Pasivo 1-3, Activo 4-6, Unknown).
  - CA4: Desacoplamiento de vigencia de membresía vs. categoría.
  - BLK-004: Resolución de email institucional.
  - H03: Centinela de subcomisión (cod=99 → None).

Referencia: spec.md §RF-PADRON-02, §RF-PADRON-03, §RF-PADRON-04.
"""

from datetime import date

import pytest

from padron.domain import (
    MembershipStatusEnum,
    SocioCategoryEnum,
    SubcomisionDTO,
)

# ==============================================================================
# CA3: Categorización Estatutaria Automática
# ==============================================================================


class TestClassifyCategory:
    """Pruebas para la regla CA3: categorización por año social."""

    @pytest.mark.parametrize("ano_social", [1, 2, 3])
    def test_passive_years_1_to_3(self, ano_social: int) -> None:
        """Años sociales 1, 2 y 3 corresponden a categoría PASSIVE (Junior)."""
        from padron.services import classify_category

        result = classify_category(ano_social)
        assert result == SocioCategoryEnum.PASSIVE

    @pytest.mark.parametrize("ano_social", [4, 5, 6])
    def test_active_years_4_to_6(self, ano_social: int) -> None:
        """Años sociales 4, 5 y 6 corresponden a categoría ACTIVE (Senior)."""
        from padron.services import classify_category

        result = classify_category(ano_social)
        assert result == SocioCategoryEnum.ACTIVE

    @pytest.mark.parametrize("ano_social", [0, -1, 7, 99, 100])
    def test_invalid_year_returns_unknown(self, ano_social: int) -> None:
        """Años sociales fuera del rango 1-6 reportan UNKNOWN sin asumir categoría."""
        from padron.services import classify_category

        result = classify_category(ano_social)
        assert result == SocioCategoryEnum.UNKNOWN


# ==============================================================================
# CA2: Identidad Estable — Legajo
# ==============================================================================


class TestNormalizeLegajo:
    """Pruebas para la regla CA2: casteo determinista de legajo."""

    def test_legajo_integer_to_string(self) -> None:
        """nroLegajo entero se castea a representación textual estricta."""
        from padron.services import normalize_legajo

        assert normalize_legajo(8921) == "8921"

    def test_legajo_large_number(self) -> None:
        """Legajos de más de 5 dígitos se castean correctamente."""
        from padron.services import normalize_legajo

        assert normalize_legajo(100201) == "100201"

    def test_legajo_none_returns_none(self) -> None:
        """Socio sin registro en socio_estudio: legajo = None."""
        from padron.services import normalize_legajo

        assert normalize_legajo(None) is None

    def test_legajo_zero_returns_none(self) -> None:
        """Legajo con valor 0 (centinela residual) se modela como None."""
        from padron.services import normalize_legajo

        assert normalize_legajo(0) is None


# ==============================================================================
# CA2: Identidad Estable — DNI
# ==============================================================================


class TestNormalizeDni:
    """Pruebas para la regla CA2/H15: normalización de documento de identidad."""

    def test_dni_positive_to_string(self) -> None:
        """nroDoc > 0 se castea a cadena de texto limpia."""
        from padron.services import normalize_dni

        assert normalize_dni(38111222) == "38111222"

    def test_dni_zero_returns_none(self) -> None:
        """nroDoc == 0 (centinela) se modela como None."""
        from padron.services import normalize_dni

        assert normalize_dni(0) is None

    def test_dni_negative_returns_none(self) -> None:
        """nroDoc negativo (dato anómalo) se modela como None."""
        from padron.services import normalize_dni

        assert normalize_dni(-1) is None

    def test_dni_none_returns_none(self) -> None:
        """nroDoc nulo se modela como None."""
        from padron.services import normalize_dni

        assert normalize_dni(None) is None


# ==============================================================================
# CA4: Resolución de Estado de Membresía (Desacoplamiento de Vigencia)
# ==============================================================================


class TestResolveMembershipStatus:
    """Pruebas para la regla CA4/BLK-005: membresía desde historial transaccional."""

    def test_cod_estado_1_is_enabled(self) -> None:
        """codEstadoSocio=1 (Activo) → ENABLED, is_active=True."""
        from padron.services import resolve_membership_status

        status, is_active = resolve_membership_status(cod_estado_socio=1, fecha_baja=None)
        assert status == MembershipStatusEnum.ENABLED
        assert is_active is True

    def test_cod_estado_2_is_suspended(self) -> None:
        """codEstadoSocio=2 (Pasivo/receso) → SUSPENDED, is_active=False."""
        from padron.services import resolve_membership_status

        status, is_active = resolve_membership_status(cod_estado_socio=2, fecha_baja=None)
        assert status == MembershipStatusEnum.SUSPENDED
        assert is_active is False

    def test_cod_estado_3_is_suspended(self) -> None:
        """codEstadoSocio=3 (Impasivo/mora) → SUSPENDED, is_active=False."""
        from padron.services import resolve_membership_status

        status, is_active = resolve_membership_status(cod_estado_socio=3, fecha_baja=None)
        assert status == MembershipStatusEnum.SUSPENDED
        assert is_active is False

    def test_cod_estado_4_is_suspended(self) -> None:
        """codEstadoSocio=4 (Inactivo/en trámite de baja) → SUSPENDED, is_active=False."""
        from padron.services import resolve_membership_status

        status, is_active = resolve_membership_status(cod_estado_socio=4, fecha_baja=None)
        assert status == MembershipStatusEnum.SUSPENDED
        assert is_active is False

    def test_cod_estado_5_is_terminated(self) -> None:
        """codEstadoSocio=5 (Baja) → TERMINATED, is_active=False."""
        from padron.services import resolve_membership_status

        status, is_active = resolve_membership_status(cod_estado_socio=5, fecha_baja=None)
        assert status == MembershipStatusEnum.TERMINATED
        assert is_active is False

    def test_fecha_baja_overrides_any_estado(self) -> None:
        """fechaBaja no nula prevalece como TERMINATED, incluso si codEstado=1."""
        from padron.services import resolve_membership_status

        status, is_active = resolve_membership_status(
            cod_estado_socio=1, fecha_baja=date(2024, 6, 15)
        )
        assert status == MembershipStatusEnum.TERMINATED
        assert is_active is False

    def test_no_history_defaults_to_enabled(self) -> None:
        """Sin registros en historial (None) → fallback defensivo ENABLED."""
        from padron.services import resolve_membership_status

        status, is_active = resolve_membership_status(cod_estado_socio=None, fecha_baja=None)
        assert status == MembershipStatusEnum.ENABLED
        assert is_active is True

    @pytest.mark.parametrize("unknown_cod", [6, 7, 99, -1])
    def test_unknown_cod_estado_defaults_to_suspended(self, unknown_cod: int) -> None:
        """Cualquier código no documentado defaultea de forma conservadora a SUSPENDED."""
        from padron.services import resolve_membership_status

        status, is_active = resolve_membership_status(cod_estado_socio=unknown_cod, fecha_baja=None)
        assert status == MembershipStatusEnum.SUSPENDED
        assert is_active is False


# ==============================================================================
# CA4: Desacoplamiento — categoría independiente de vigencia
# ==============================================================================


class TestCategoryIndependentOfMembership:
    """Prueba de integración lógica: un socio ACTIVE puede estar SUSPENDED."""

    def test_active_category_with_suspended_membership(self) -> None:
        """Un socio de 4.º año (ACTIVE) puede estar suspendido (SUSPENDED)."""
        from padron.services import classify_category, resolve_membership_status

        category = classify_category(4)
        status, is_active = resolve_membership_status(cod_estado_socio=3, fecha_baja=None)

        assert category == SocioCategoryEnum.ACTIVE
        assert status == MembershipStatusEnum.SUSPENDED
        assert is_active is False

    def test_passive_category_with_enabled_membership(self) -> None:
        """Un socio de 2.º año (PASSIVE) puede estar habilitado (ENABLED)."""
        from padron.services import classify_category, resolve_membership_status

        category = classify_category(2)
        status, is_active = resolve_membership_status(cod_estado_socio=1, fecha_baja=None)

        assert category == SocioCategoryEnum.PASSIVE
        assert status == MembershipStatusEnum.ENABLED
        assert is_active is True


# ==============================================================================
# BLK-004: Resolución de Email Institucional
# ==============================================================================


class TestResolveEmail:
    """Pruebas para la resolución prioritaria de email desde registros satélite."""

    def test_email_habilitado_y_comprobado_tiene_prioridad(self) -> None:
        """Casilla con habilitado=True y comprobado=True se selecciona primero."""
        from padron.services import resolve_email

        emails = [
            {"email": "viejo@test.com", "habilitado": True, "comprobado": False},
            {"email": "oficial@aveit.utn.edu.ar", "habilitado": True, "comprobado": True},
        ]
        assert resolve_email(emails) == "oficial@aveit.utn.edu.ar"

    def test_email_solo_habilitado_como_fallback(self) -> None:
        """Si no hay comprobado, se usa la primera casilla habilitada."""
        from padron.services import resolve_email

        emails = [
            {"email": "no_habilitado@test.com", "habilitado": False, "comprobado": False},
            {"email": "habilitado@test.com", "habilitado": True, "comprobado": False},
        ]
        assert resolve_email(emails) == "habilitado@test.com"

    def test_sin_emails_retorna_none(self) -> None:
        """Lista vacía de emails → None."""
        from padron.services import resolve_email

        assert resolve_email([]) is None

    def test_ningun_email_habilitado_retorna_none(self) -> None:
        """Si ningún email está habilitado, retorna None."""
        from padron.services import resolve_email

        emails = [
            {"email": "deshabilitado@test.com", "habilitado": False, "comprobado": False},
        ]
        assert resolve_email(emails) is None


# ==============================================================================
# H03: Centinela de Subcomisión (codSubcomision = 99)
# ==============================================================================


class TestResolveSubcomision:
    """Pruebas para la interceptación del valor centinela de subcomisión."""

    def test_subcomision_normal_returns_dto(self) -> None:
        """Subcomisión válida (cod != 99) retorna SubcomisionDTO."""
        from padron.services import resolve_subcomision

        result = resolve_subcomision(cod_subcomision=1, nombre="Cómputos")
        assert result is not None
        assert isinstance(result, SubcomisionDTO)
        assert result.id == 1
        assert result.name == "Cómputos"

    def test_subcomision_centinela_99_returns_none(self) -> None:
        """codSubcomision=99 ('Sin Subcomisión') → None."""
        from padron.services import resolve_subcomision

        result = resolve_subcomision(cod_subcomision=99, nombre="Sin Subcomisión")
        assert result is None
