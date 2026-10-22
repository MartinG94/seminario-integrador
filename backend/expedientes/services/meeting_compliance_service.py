"""Servicio de validación de plazos procesales para reuniones y eventos (CA1, CA2, CA8).

Implementa:
- Verificación de preaviso mínimo de 2 días hábiles (Art. 95).
- Verificación de plazo perentorio de 72 horas hábiles (Art. 99).
- Fallback ordenado del timestamp base: cierre_efectivo -> fin -> inicio.
- Determinación inmutable de sancionabilidad (es_sancionable).
"""

import logging
from datetime import datetime
from typing import TYPE_CHECKING

from expedientes.domain.calendar import compute_business_deadline
from expedientes.domain.holiday_provider import DbHolidayProvider

if TYPE_CHECKING:
    from expedientes.domain.ports import HolidayProviderPort
    from expedientes.models import EventoInstitucional

logger = logging.getLogger(__name__)


class MeetingComplianceService:
    """Valida los plazos procesales e institucionales de convocatorias y reportes de eventos."""

    MIN_NOTICE_BUSINESS_DAYS: int = 2
    REPORTING_DEADLINE_BUSINESS_DAYS: int = 3  # 72 horas hábiles = 3 días hábiles

    MOTIVO_PREAVISO_INSUFICIENTE: str = (
        "Convocatoria con menos de 2 días hábiles de antelación reglamentaria (Art. 95 R.I.)."
    )
    MOTIVO_REPORTE_EXTEMPORANEO: str = (
        "Reporte de asistencia fuera del plazo perentorio de 72 horas hábiles (Art. 99 R.I.)."
    )

    @classmethod
    def get_holiday_provider(
        cls, holiday_provider: "HolidayProviderPort | None" = None
    ) -> "HolidayProviderPort":
        if holiday_provider is not None:
            return holiday_provider
        return DbHolidayProvider()

    @classmethod
    def calculate_notice_deadline(
        cls,
        fecha_publicacion: datetime,
        holiday_provider: "HolidayProviderPort | None" = None,
    ) -> datetime:
        """Calcula el límite mínimo en el cual debe iniciar el evento para cumplir el preaviso."""
        provider = cls.get_holiday_provider(holiday_provider)
        return compute_business_deadline(
            start_at=fecha_publicacion,
            business_days=cls.MIN_NOTICE_BUSINESS_DAYS,
            holiday_provider=provider,
        )

    @classmethod
    def validate_notice_period(
        cls,
        fecha_publicacion: datetime,
        fecha_programada: datetime,
        holiday_provider: "HolidayProviderPort | None" = None,
    ) -> tuple[bool, str | None]:
        """
        Evalúa si median al menos 2 días hábiles entre la publicación y el inicio del evento.

        Retorna:
            (True, None) si cumple el preaviso.
            (False, motivo) si no cumple el preaviso reglamentario.
        """
        limite_minimo = cls.calculate_notice_deadline(
            fecha_publicacion, holiday_provider=holiday_provider
        )
        if fecha_programada < limite_minimo:
            return False, cls.MOTIVO_PREAVISO_INSUFICIENTE
        return True, None

    @classmethod
    def calculate_reporting_deadline(
        cls,
        *,
        fecha_fin: datetime | None = None,
        fecha_programada: datetime | None = None,
        fecha_hora_cierre_efectivo: datetime | None = None,
        holiday_provider: "HolidayProviderPort | None" = None,
    ) -> datetime:
        """
        Calcula la fecha y hora límite (72 horas hábiles) para reportar la asistencia.

        Aplica la prelación de timestamp base:
        1. fecha_hora_cierre_efectivo si existe.
        2. fecha_fin si existe.
        3. fecha_programada como fallback subsidiario.
        """
        base_timestamp = fecha_hora_cierre_efectivo or fecha_fin or fecha_programada
        if not base_timestamp:
            raise ValueError(
                "Debe proporcionarse: fecha_hora_cierre_efectivo, fecha_fin o fecha_programada."
            )

        provider = cls.get_holiday_provider(holiday_provider)
        return compute_business_deadline(
            start_at=base_timestamp,
            business_days=cls.REPORTING_DEADLINE_BUSINESS_DAYS,
            holiday_provider=provider,
        )

    @classmethod
    def validate_reporting_deadline(
        cls,
        *,
        fecha_reporte: datetime,
        fecha_fin: datetime | None = None,
        fecha_programada: datetime | None = None,
        fecha_hora_cierre_efectivo: datetime | None = None,
        holiday_provider: "HolidayProviderPort | None" = None,
    ) -> tuple[bool, str | None]:
        """
        Evalúa si el informe de asistencia fue elevado dentro de las 72 hs hábiles.

        Retorna:
            (True, None) si el reporte está en plazo.
            (False, motivo) si el reporte es extemporáneo.
        """
        limite_reporte = cls.calculate_reporting_deadline(
            fecha_fin=fecha_fin,
            fecha_programada=fecha_programada,
            fecha_hora_cierre_efectivo=fecha_hora_cierre_efectivo,
            holiday_provider=holiday_provider,
        )
        if fecha_reporte > limite_reporte:
            return False, cls.MOTIVO_REPORTE_EXTEMPORANEO
        return True, None

    @classmethod
    def evaluate_event_sanctionability(
        cls,
        evento: "EventoInstitucional",
        fecha_reporte: datetime | None = None,
        holiday_provider: "HolidayProviderPort | None" = None,
    ) -> tuple[bool, str | None]:
        """
        Evalúa integralmente si un evento institucional reviste carácter sancionable.

        Criterios acumulativos:
        1. Si es_obligatoria es False -> no sancionable.
        2. Preaviso de 2 días hábiles (Art. 95).
        3. Si existe fecha_reporte, reporte dentro de las 72 hs hábiles (Art. 99).
        """
        if not evento.es_obligatoria:
            return False, "Evento no obligatorio por definición estatutaria."

        # 1. Validar preaviso
        cumple_preaviso, motivo_preaviso = cls.validate_notice_period(
            fecha_publicacion=evento.fecha_publicacion,
            fecha_programada=evento.fecha_programada,
            holiday_provider=holiday_provider,
        )
        if not cumple_preaviso:
            return False, motivo_preaviso

        # 2. Validar reporte si existe fecha de elevación
        reporte_at = fecha_reporte or evento.fecha_reporte
        if reporte_at:
            cumple_reporte, motivo_reporte = cls.validate_reporting_deadline(
                fecha_reporte=reporte_at,
                fecha_fin=evento.fecha_fin,
                fecha_programada=evento.fecha_programada,
                fecha_hora_cierre_efectivo=evento.fecha_hora_cierre_efectivo,
                holiday_provider=holiday_provider,
            )
            if not cumple_reporte:
                return False, motivo_reporte

        return True, None
