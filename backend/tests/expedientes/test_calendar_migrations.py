"""Actualiza esquemas previos y reaplica 0010 en la base MySQL de pruebas."""

from datetime import date, datetime, timezone

import pytest
from django.contrib.auth import get_user_model
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from rest_framework.test import APIClient

from expedientes.models import Holiday


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("previous_calendar", ["seeded", "empty", "custom"])
def test_existing_environment_migrates_and_reapplies_without_breaking_read(
    previous_calendar: str,
) -> None:
    executor = MigrationExecutor(connection)
    latest = executor.loader.graph.leaf_nodes()
    previous = [("expedientes", "0008_seed_calendario_2026")]
    try:
        # Recrear el estado previo mediante sus migraciones reales. No restaurar
        # snapshots globales: otros tests transaccionales recrean ContentType.
        executor.migrate([("expedientes", "0007_calendarioversion_feriadoexcepcion_and_more")])
        executor = MigrationExecutor(connection)
        executor.migrate(previous)
        historical = executor.loader.project_state(previous).apps
        calendar_model = historical.get_model("expedientes", "CalendarioVersion")
        legacy_model = historical.get_model("expedientes", "FeriadoExcepcion")
        timestamp = datetime(2026, 10, 8, 18, 30, 12, 654321, tzinfo=timezone.utc)
        if previous_calendar == "empty":
            calendar_model.objects.update(activa=False)
        elif previous_calendar == "custom":
            calendar = calendar_model.objects.create(
                version=2,
                nombre="Calendario existente antes de actualizar",
                vigencia_desde=date(2026, 10, 1),
                motivo_cambio="Alta previa",
            )
            prior = legacy_model.objects.create(
                calendario_version=calendar,
                fecha=date(2026, 10, 13),
                descripcion="Asueto previo",
            )
            legacy_model.objects.filter(pk=prior.pk).update(created_at=timestamp)
            legacy_model.objects.create(
                calendario_version=calendar,
                fecha=date(2026, 10, 14),
                descripcion="Día laborable previo",
                es_laborable=True,
            )

        MigrationExecutor(connection).migrate(latest)
        user = get_user_model().objects.create_user(username="migration_calendar_reader")
        client = APIClient()
        client.force_authenticate(user)
        url = "/api/v1/expedientes/calendario/feriados/"
        response = client.get(url)
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        if previous_calendar == "empty":
            assert response.json() == []
        elif previous_calendar == "custom":
            assert [item["fecha"] for item in response.json()] == ["2026-10-13"]
            holiday = Holiday.objects.get(date=date(2026, 10, 13))
            assert holiday.origin == Holiday.Origin.LEGACY
            assert holiday.created_at == timestamp
        else:
            assert len(response.json()) == 16
            dates = {item["fecha"] for item in response.json()}
            assert {"2026-06-15", "2026-11-23"}.issubset(dates)

        created = Holiday.objects.create(
            date=date(2099, 1, 1),
            description="Alta posterior a actualizar el entorno",
            created_by=user,
            created_at=timestamp,
        )
        before = list(Holiday.objects.values().order_by("date"))
        MigrationExecutor(connection).migrate([("expedientes", "0009_institutional_calendar")])
        assert Holiday.objects.filter(pk=created.pk, created_by=user).exists()
        MigrationExecutor(connection).migrate(latest)

        assert list(Holiday.objects.values().order_by("date")) == before
        assert client.get(url).status_code == 200
        assert legacy_model.objects.filter(calendario_version__version=1).count() == 16
    finally:
        # Dejar siempre el esquema vigente para las siguientes pruebas.
        MigrationExecutor(connection).migrate(latest)
