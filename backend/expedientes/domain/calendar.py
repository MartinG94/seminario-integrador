"""Dominio de cálculo de plazos en días hábiles (Business Calendar).

Implementa la regla canónica:
Fecha_Limite_Descargo = SumarDiasHabiles(Fecha_Hora_Acuse_Sancion, 5)

Características:
- Desacoplado 100% de Django, ORM y HTTP.
- Determinista y puro.
- Obligatoriamente timezone-aware.
- Ignora fines de semana (sábado y domingo).
- Ignora feriados provistos por HolidayProviderPort.
- Preserva horas, minutos, segundos y microsegundos.
"""

from datetime import datetime, timedelta

from expedientes.domain.ports import HolidayProviderPort


def compute_business_deadline(
    start_at: datetime,
    business_days: int,
    holiday_provider: HolidayProviderPort,
) -> datetime:
    """
    Calcula la fecha y hora exacta de vencimiento tras transcurrir `business_days` días hábiles.

    Regla:
    - El plazo comienza inmediatamente a partir del instante de `start_at`.
    - Cada día hábil completo se suma de forma sucesiva.
    - Los días sábado (weekday 5) y domingo (weekday 6) son inhábiles.
    - Las fechas reportadas como True por `holiday_provider.is_holiday(date)` son inhábiles.
    - Se preserva la componente horaria exacta de `start_at`.

    Lanza:
    - ValueError si `start_at` es un datetime naive.
    - ValueError si `business_days` es menor o igual a 0.
    """
    if start_at.tzinfo is None or start_at.tzinfo.utcoffset(start_at) is None:
        raise ValueError("start_at debe ser un objeto datetime timezone-aware.")

    if business_days <= 0:
        raise ValueError("business_days debe ser mayor a 0.")

    current_date = start_at.date()
    days_counted = 0

    while days_counted < business_days:
        current_date += timedelta(days=1)
        # 0 = Lunes, ..., 4 = Viernes, 5 = Sábado, 6 = Domingo
        if current_date.weekday() >= 5:
            continue
        if holiday_provider.is_holiday(current_date):
            continue
        days_counted += 1

    return datetime.combine(
        current_date,
        start_at.time(),
        tzinfo=start_at.tzinfo,
    )
