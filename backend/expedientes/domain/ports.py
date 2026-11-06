"""Puertos del dominio de expedientes (Arquitectura Hexagonal)."""

from datetime import date
from typing import Protocol, runtime_checkable

from expedientes.domain.t03_valuation import TribunalCondition


@runtime_checkable
class HolidayProviderPort(Protocol):
    """Puerto para consultar si una fecha calendario específica es día feriado o no laborable."""

    def is_holiday(self, target_date: date) -> bool:
        """Determina si target_date es un feriado nacional, provincial o institucional."""
        ...


@runtime_checkable
class TribunalConditionPort(Protocol):
    """Puerto para consultar en el padrón si un usuario es Miembro Titular o Suplente."""

    def condition_for_user(self, user_id: int) -> TribunalCondition:
        """Devuelve la condición vigente del usuario o `NO_INFORMADA` si no figura."""
        ...
