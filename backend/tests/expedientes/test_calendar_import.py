"""Comprueba importación no destructiva, origen veraz y timestamps exactos."""

from datetime import date, datetime, timezone
from importlib import import_module
from types import SimpleNamespace

import pytest
from django.apps import apps
from django.contrib.auth import get_user_model
from django.db import connection

from expedientes.models import CalendarioVersion, FeriadoExcepcion, Holiday

import_holidays = import_module(
    "expedientes.migrations.0010_import_institutional_holidays"
).import_current_holidays


@pytest.mark.django_db
def test_import_preserves_timestamps_and_distinguishes_human_additions() -> None:
    Holiday.objects.all().delete()
    calendar = CalendarioVersion.objects.get(version=1)
    prior = FeriadoExcepcion.objects.create(
        calendario_version=calendar,
        fecha=date(2026, 10, 13),
        descripcion="Asueto cargado previamente",
    )
    timestamp = datetime(2026, 10, 8, 18, 30, 12, 654321, tzinfo=timezone.utc)
    FeriadoExcepcion.objects.filter(pk=prior.pk).update(created_at=timestamp)
    import_holidays(apps, SimpleNamespace(connection=connection))

    holiday = Holiday.objects.get(date=prior.fecha)
    assert holiday.origin == Holiday.Origin.LEGACY
    assert holiday.created_by_id is None
    assert holiday.created_at == timestamp
    seed = FeriadoExcepcion.objects.get(calendario_version=calendar, fecha=date(2026, 11, 20))
    shifted = Holiday.objects.get(date=date(2026, 11, 23))
    assert shifted.origin == Holiday.Origin.SYSTEM
    assert shifted.created_at == seed.created_at
    assert FeriadoExcepcion.objects.filter(pk=prior.pk).exists()
    assert FeriadoExcepcion.objects.filter(pk=seed.pk, fecha=date(2026, 11, 20)).exists()


@pytest.mark.django_db
def test_import_only_uses_last_active_calendar_and_excludes_working_days() -> None:
    Holiday.objects.all().delete()
    calendar = CalendarioVersion.objects.create(
        version=2,
        nombre="Calendario previo vigente",
        vigencia_desde=date(2026, 10, 1),
        motivo_cambio="Calendario anterior",
    )
    FeriadoExcepcion.objects.create(
        calendario_version=calendar, fecha=date(2026, 10, 13), descripcion="Asueto"
    )
    FeriadoExcepcion.objects.create(
        calendario_version=calendar,
        fecha=date(2026, 10, 14),
        descripcion="Excepción laborable anterior",
        es_laborable=True,
    )
    FeriadoExcepcion.objects.create(
        calendario_version=calendar,
        fecha=date(2026, 11, 20),
        descripcion="Día de la Soberanía Nacional",
    )
    import_holidays(apps, SimpleNamespace(connection=connection))
    assert list(Holiday.objects.values_list("date", flat=True)) == [
        date(2026, 10, 13),
        date(2026, 11, 20),
    ]
    assert all(record.origin == Holiday.Origin.LEGACY for record in Holiday.objects.all())
    assert CalendarioVersion.objects.count() == 2


@pytest.mark.django_db
def test_import_without_active_calendar_leaves_operational_calendar_empty() -> None:
    Holiday.objects.all().delete()
    CalendarioVersion.objects.all().update(activa=False)
    import_holidays(apps, SimpleNamespace(connection=connection))
    assert not Holiday.objects.exists()
    assert CalendarioVersion.objects.exists()


@pytest.mark.django_db
def test_import_can_repeat_without_duplicating_or_changing_audit() -> None:
    Holiday.objects.all().delete()
    import_holidays(apps, SimpleNamespace(connection=connection))
    before = list(Holiday.objects.values().order_by("date"))

    import_holidays(apps, SimpleNamespace(connection=connection))

    assert list(Holiday.objects.values().order_by("date")) == before


@pytest.mark.django_db
def test_import_preserves_existing_user_holiday_on_seed_date() -> None:
    Holiday.objects.all().delete()
    user = get_user_model().objects.create_user(username="calendar_migration_author")
    timestamp = datetime(2026, 10, 8, 18, 30, 12, 654321, tzinfo=timezone.utc)
    holiday = Holiday.objects.create(
        date=date(2026, 10, 12),
        description="Denominación operativa registrada por autoridad",
        created_by=user,
        created_at=timestamp,
    )

    import_holidays(apps, SimpleNamespace(connection=connection))

    holiday.refresh_from_db()
    assert holiday.description == "Denominación operativa registrada por autoridad"
    assert holiday.created_by_id == user.pk
    assert holiday.created_at == timestamp
    assert holiday.origin == Holiday.Origin.USER
    assert Holiday.objects.count() == 16
