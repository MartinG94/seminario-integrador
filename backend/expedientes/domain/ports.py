"""Puertos del dominio de expedientes (Arquitectura Hexagonal)."""

from datetime import date
from typing import Protocol, runtime_checkable


@runtime_checkable
class HolidayProviderPort(Protocol):
    """Puerto para consultar si una fecha calendario específica es día feriado o no laborable."""

    def is_holiday(self, target_date: date) -> bool:
        """Determina si target_date es un feriado nacional, provincial o institucional."""
        ...
