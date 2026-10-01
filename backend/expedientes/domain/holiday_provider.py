"""Proveedores de días feriados (In-Memory y Argentina 2026)."""

from datetime import date

from expedientes.domain.ports import HolidayProviderPort


class InMemoryHolidayProvider(HolidayProviderPort):
    """Proveedor genérico en memoria para testing y configuraciones dinámicas."""

    def __init__(self, holidays: set[date] | None = None) -> None:
        self._holidays = holidays or set()

    def is_holiday(self, target_date: date) -> bool:
        return target_date in self._holidays


class Argentina2026HolidayProvider(HolidayProviderPort):
    """
    Proveedor oficial con el calendario de Feriados Nacionales e Inamovibles de Argentina para 2026.

    Incluye:
    - 01/01: Año Nuevo
    - 16/02: Carnaval (Lunes)
    - 17/02: Carnaval (Martes)
    - 24/03: Día Nacional de la Memoria por la Verdad y la Justicia
    - 02/04: Día del Veterano y de los Caídos en la Guerra de Malvinas / Jueves Santo
    - 03/04: Viernes Santo
    - 01/05: Día del Trabajador
    - 25/05: Día de la Revolución de Mayo
    - 17/06: Paso a la Inmortalidad del Gral. Don Martín Miguel de Güemes
    - 20/06: Paso a la Inmortalidad del Gral. Manuel Belgrano
    - 09/07: Día de la Independencia
    - 17/08: Paso a la Inmortalidad del Gral. José de San Martín
    - 12/10: Día del Respeto a la Diversidad Cultural
    - 20/11: Día de la Soberanía Nacional
    - 08/12: Inmaculada Concepción de María
    - 25/12: Navidad
    """

    OFFICIAL_2026_HOLIDAYS: frozenset[date] = frozenset(
        {
            date(2026, 1, 1),
            date(2026, 2, 16),
            date(2026, 2, 17),
            date(2026, 3, 24),
            date(2026, 4, 2),
            date(2026, 4, 3),
            date(2026, 5, 1),
            date(2026, 5, 25),
            date(2026, 6, 17),
            date(2026, 6, 20),
            date(2026, 7, 9),
            date(2026, 8, 17),
            date(2026, 10, 12),
            date(2026, 11, 20),
            date(2026, 12, 8),
            date(2026, 12, 25),
        }
    )

    def __init__(self, additional_holidays: set[date] | None = None) -> None:
        self._holidays = set(self.OFFICIAL_2026_HOLIDAYS)
        if additional_holidays:
            self._holidays.update(additional_holidays)

    def is_holiday(self, target_date: date) -> bool:
        return target_date in self._holidays
