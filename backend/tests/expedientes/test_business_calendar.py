"""Tests exhaustivos del calendario laboral y cálculo de días hábiles (FASE 1 / S3-02).

Cubre:
1. Inicio en día hábil (lunes a viernes).
2. Fin de semana (inicio en sábado o domingo).
3. Fin de semana transcurrido dentro del plazo.
4. Feriados dentro del plazo (nacionales e institucionales).
5. Feriados consecutivos (ej. Carnaval, Semana Santa).
6. Cambio de mes.
7. Cambio de año.
8. Preservación estricta de hora, minuto, segundo y microsegundo.
9. Timezone-aware con America/Argentina/Buenos_Aires.
10. Determinismo absoluto sin depender del reloj del sistema.
11. Proveedor de feriados vacío o nulo.
12. 5 días hábiles exactos conforme a Art. 12 Inc. 2 Reglamento Procesal.
"""

from datetime import date, datetime, time
from zoneinfo import ZoneInfo

import pytest

from expedientes.domain.calendar import compute_business_deadline
from expedientes.domain.holiday_provider import (
    Argentina2026HolidayProvider,
    InMemoryHolidayProvider,
)
from expedientes.domain.ports import HolidayProviderPort

BA_TZ = ZoneInfo("America/Argentina/Buenos_Aires")


class DummyHolidayProvider(HolidayProviderPort):
    """Proveedor mock para pruebas de aislamiento total."""

    def __init__(self, holidays: set[date] | None = None) -> None:
        self._holidays = holidays or set()

    def is_holiday(self, target_date: date) -> bool:
        return target_date in self._holidays


class TestBusinessCalendarDomain:
    """Suite de pruebas unitarias para el dominio de cálculo de plazos en días hábiles."""

    def test_start_on_monday_without_holidays(self) -> None:
        """Lunes 09:30 + 5 días hábiles -> Lunes siguiente 09:30."""
        # 2026-03-02 es Lunes.
        # Días hábiles computados: Mar(1), Mié(2), Jue(3), Vie(4), Lun 09(5).
        start_at = datetime(2026, 3, 2, 9, 30, 15, tzinfo=BA_TZ)
        provider = DummyHolidayProvider()

        deadline = compute_business_deadline(
            start_at=start_at,
            business_days=5,
            holiday_provider=provider,
        )

        expected = datetime(2026, 3, 9, 9, 30, 15, tzinfo=BA_TZ)
        assert deadline == expected
        assert deadline.tzinfo == BA_TZ

    def test_start_on_friday_crosses_weekend(self) -> None:
        """Viernes 14:00 + 5 días hábiles -> Viernes siguiente 14:00 (Sáb y Dom no cuentan)."""
        # 2026-03-06 es Viernes.
        # Días hábiles computados: Lun 09(1), Mar 10(2), Mié 11(3), Jue 12(4), Vie 13(5).
        start_at = datetime(2026, 3, 6, 14, 0, 0, tzinfo=BA_TZ)
        provider = DummyHolidayProvider()

        deadline = compute_business_deadline(
            start_at=start_at,
            business_days=5,
            holiday_provider=provider,
        )

        expected = datetime(2026, 3, 13, 14, 0, 0, tzinfo=BA_TZ)
        assert deadline == expected

    def test_holiday_inside_deadline_shifts_by_one_day(self) -> None:
        """Un feriado en medio desplaza la fecha límite un día hábil extra."""
        # 2026-03-02 es Lunes. Feriado: Miércoles 2026-03-04.
        # Días hábiles: Mar 03(1), Jue 05(2), Vie 06(3), Lun 09(4), Mar 10(5).
        start_at = datetime(2026, 3, 2, 10, 0, 0, tzinfo=BA_TZ)
        provider = DummyHolidayProvider(holidays={date(2026, 3, 4)})

        deadline = compute_business_deadline(
            start_at=start_at,
            business_days=5,
            holiday_provider=provider,
        )

        expected = datetime(2026, 3, 10, 10, 0, 0, tzinfo=BA_TZ)
        assert deadline == expected

    def test_consecutive_holidays_carnaval(self) -> None:
        """Carnaval 2026: Lunes 16 y Martes 17 de Febrero de 2026 son feriados consecutivos."""
        # Notificación: Viernes 13 de Febrero 2026 a las 18:00.
        # Sáb 14 y Dom 15 (Fin de semana - inhábil).
        # Lun 16 y Mar 17 (Carnaval - inhábil).
        # Mié 18(1), Jue 19(2), Vie 20(3).
        # Sáb 21 y Dom 22 (Fin de semana - inhábil).
        # Lun 23(4), Mar 24(5).
        start_at = datetime(2026, 2, 13, 18, 0, 0, tzinfo=BA_TZ)
        provider = Argentina2026HolidayProvider()

        deadline = compute_business_deadline(
            start_at=start_at,
            business_days=5,
            holiday_provider=provider,
        )

        expected = datetime(2026, 2, 24, 18, 0, 0, tzinfo=BA_TZ)
        assert deadline == expected

    def test_semana_santa_2026(self) -> None:
        """Semana Santa 2026: Jueves Santo (02/04) y Viernes Santo (03/04)."""
        # Notificación: Miércoles 01 de Abril 2026 a las 11:30.
        # Jue 02 y Vie 03 (Semana Santa y Día del Veterano - inhábil).
        # Sáb 04 y Dom 05 (Fin de semana - inhábil).
        # Lun 06(1), Mar 07(2), Mié 08(3), Jue 09(4), Vie 10(5).
        start_at = datetime(2026, 4, 1, 11, 30, 0, tzinfo=BA_TZ)
        provider = Argentina2026HolidayProvider()

        deadline = compute_business_deadline(
            start_at=start_at,
            business_days=5,
            holiday_provider=provider,
        )

        expected = datetime(2026, 4, 10, 11, 30, 0, tzinfo=BA_TZ)
        assert deadline == expected

    def test_cross_month_boundary(self) -> None:
        """Cálculo cruzando el fin de mes ordinario."""
        # Miércoles 29 de Julio 2026 a las 16:00.
        # Jue 30(1), Vie 31(2), Sáb 01 y Dom 02 (Fin de semana),
        # Lun 03(3), Mar 04(4), Mié 05(5) de Agosto.
        start_at = datetime(2026, 7, 29, 16, 0, 0, tzinfo=BA_TZ)
        provider = DummyHolidayProvider()

        deadline = compute_business_deadline(
            start_at=start_at,
            business_days=5,
            holiday_provider=provider,
        )

        expected = datetime(2026, 8, 5, 16, 0, 0, tzinfo=BA_TZ)
        assert deadline == expected

    def test_cross_year_boundary_with_new_year_holiday(self) -> None:
        """Cálculo cruzando año nuevo (31 de Diciembre / 1 de Enero feriado)."""
        # Lunes 28 de Diciembre 2026 a las 12:00.
        # Mar 29(1), Mié 30(2), Jue 31(3).
        # Viernes 01/01/2027 (Feriado Año Nuevo).
        # Sáb 02/01 y Dom 03/01 (Fin de semana).
        # Lun 04/01/2027(4), Mar 05/01/2027(5).
        start_at = datetime(2026, 12, 28, 12, 0, 0, tzinfo=BA_TZ)
        provider = InMemoryHolidayProvider(holidays={date(2027, 1, 1)})

        deadline = compute_business_deadline(
            start_at=start_at,
            business_days=5,
            holiday_provider=provider,
        )

        expected = datetime(2027, 1, 5, 12, 0, 0, tzinfo=BA_TZ)
        assert deadline == expected

    def test_notification_on_saturday_starts_counting_first_business_day(self) -> None:
        """Notificación en sábado computa 5 días hábiles a partir del lunes siguiente."""
        # Sábado 07/03/2026 a las 15:00.
        # Próximos días hábiles: Lun 09(1), Mar 10(2), Mié 11(3), Jue 12(4), Vie 13(5).
        start_at = datetime(2026, 3, 7, 15, 0, 0, tzinfo=BA_TZ)
        provider = DummyHolidayProvider()

        deadline = compute_business_deadline(
            start_at=start_at,
            business_days=5,
            holiday_provider=provider,
        )

        expected = datetime(2026, 3, 13, 15, 0, 0, tzinfo=BA_TZ)
        assert deadline == expected

    def test_notification_on_sunday(self) -> None:
        """Notificación despachada un domingo culmina el viernes siguiente."""
        start_at = datetime(2026, 3, 8, 20, 0, 0, tzinfo=BA_TZ)
        provider = DummyHolidayProvider()

        deadline = compute_business_deadline(
            start_at=start_at,
            business_days=5,
            holiday_provider=provider,
        )

        expected = datetime(2026, 3, 13, 20, 0, 0, tzinfo=BA_TZ)
        assert deadline == expected

    def test_notification_on_holiday_starts_next_business_day(self) -> None:
        """Si la notificación ocurre en feriado, el primer día contado es el siguiente hábil."""
        # 25 de Mayo (Lunes feriado). Notificación 25/05/2026 10:00.
        # Mar 26(1), Mié 27(2), Jue 28(3), Vie 29(4), Lun 01/06(5).
        start_at = datetime(2026, 5, 25, 10, 0, 0, tzinfo=BA_TZ)
        provider = Argentina2026HolidayProvider()

        deadline = compute_business_deadline(
            start_at=start_at,
            business_days=5,
            holiday_provider=provider,
        )

        expected = datetime(2026, 6, 1, 10, 0, 0, tzinfo=BA_TZ)
        assert deadline == expected

    def test_preserves_microsecond_precision_and_exact_time(self) -> None:
        """Conserva milisegundos y microsegundos exactos del evento de origen."""
        start_at = datetime(2026, 3, 2, 23, 59, 59, 999999, tzinfo=BA_TZ)
        provider = DummyHolidayProvider()

        deadline = compute_business_deadline(
            start_at=start_at,
            business_days=5,
            holiday_provider=provider,
        )

        assert deadline.time() == time(23, 59, 59, 999999)
        assert deadline.date() == date(2026, 3, 9)

    def test_rejects_naive_datetime(self) -> None:
        """Debe rechazar datetimes sin timezone explícito para evitar bugs de desfase horario."""
        naive_dt = datetime(2026, 3, 2, 10, 0, 0)
        with pytest.raises(ValueError, match="timezone-aware"):
            compute_business_deadline(naive_dt, 5, DummyHolidayProvider())

    def test_rejects_negative_or_zero_business_days(self) -> None:
        """business_days debe ser un entero estrictamente positivo."""
        start_at = datetime(2026, 3, 2, 10, 0, 0, tzinfo=BA_TZ)
        with pytest.raises(ValueError, match="business_days debe ser mayor a 0"):
            compute_business_deadline(start_at, 0, DummyHolidayProvider())

    def test_empty_holiday_provider_only_skips_weekends(self) -> None:
        """Con proveedor vacío sólo ignora sábados y domingos."""
        start_at = datetime(2026, 3, 4, 12, 0, 0, tzinfo=BA_TZ)  # Miércoles
        # Jue 05(1), Vie 06(2), Sáb/Dom, Lun 09(3), Mar 10(4), Mié 11(5)
        deadline = compute_business_deadline(start_at, 5, InMemoryHolidayProvider(set()))
        assert deadline == datetime(2026, 3, 11, 12, 0, 0, tzinfo=BA_TZ)
