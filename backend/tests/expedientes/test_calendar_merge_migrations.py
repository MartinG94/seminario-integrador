"""Integra calendario y urgencia conservando datos de cada esquema publicado."""

from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from rest_framework.test import APIClient

from expedientes.models import Expediente, Holiday, SolicitudT01


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    "previous_migration",
    ["0010_import_institutional_holidays", "0008_expediente_points_precision"],
    ids=["calendar_environment", "urgency_environment"],
)
def test_calendar_and_urgency_upgrade_preserves_existing_records(previous_migration: str) -> None:
    executor = MigrationExecutor(connection)
    latest = executor.loader.graph.leaf_nodes()
    previous = [("expedientes", previous_migration)]
    has_calendar = previous_migration == "0010_import_institutional_holidays"
    timestamp = datetime(2026, 10, 8, 18, 30, 12, 654321, tzinfo=timezone.utc)
    deadline = datetime(2026, 10, 16, 18, 30, 12, 654321, tzinfo=timezone.utc)
    try:
        executor.migrate([("expedientes", "0006_solicitudt01_expediente")])
        executor = MigrationExecutor(connection)
        executor.migrate(previous)
        historical = executor.loader.project_state(previous).apps
        user = get_user_model().objects.create_user(username="merge_calendar_reader")
        subcomision = historical.get_model("socios", "Subcomision").objects.create(
            name="Cómputos de prueba"
        )
        socio = historical.get_model("socios", "Socio").objects.create(
            user_id=user.pk,
            first_name="Socio",
            last_name="Integración",
            legajo="MERGE-001",
            email="merge@example.test",
            subcomision=subcomision,
            social_year=2,
            role="SOCIO",
            is_enabled=True,
        )
        if has_calendar:
            calendar = historical.get_model("expedientes", "CalendarioVersion").objects.get(
                version=1
            )
            case_fields = {"calendario_version_id": calendar.pk}
        else:
            case_fields = {"urgencia": "urgente"}
        case = historical.get_model("expedientes", "Expediente").objects.create(
            numero="MERGE-001/2026",
            socio=socio,
            motivo="Expediente existente antes de integrar las ramas",
            puntos=Decimal("12.34") if has_calendar else Decimal("12345678.90"),
            estado="justificando",
            plazo_inicio_at=timestamp,
            plazo_limite_at=deadline,
            **case_fields,
        )
        case.socios.add(socio)
        request = historical.get_model("expedientes", "SolicitudT01").objects.create(
            solicitante=socio,
            tipo_accion="MERIT",
            estado="ISSUED",
            expediente=case,
            puntos=case.puntos,
            snapshot_emitido={"motivo": "Solicitud emitida antes de integrar las ramas"},
            **({} if has_calendar else {"urgencia": "urgente"}),
        )
        case_before = case.__class__.objects.values().get(pk=case.pk)
        request_before = request.__class__.objects.values().get(pk=request.pk)
        holidays_before = []
        if has_calendar:
            holiday_model = historical.get_model("expedientes", "Holiday")
            holiday_model.objects.create(
                date=date(2099, 1, 1),
                description="Feriado auditado antes de integrar main",
                created_by_id=user.pk,
                created_at=timestamp,
                origin="USER",
            )
            holidays_before = list(holiday_model.objects.values().order_by("date"))

        MigrationExecutor(connection).migrate(latest)

        loader = MigrationExecutor(connection).loader
        assert loader.detect_conflicts() == {}
        case_after = Expediente.objects.values().get(pk=case.pk)
        request_after = SolicitudT01.objects.values().get(pk=request.pk)
        assert {key: case_after[key] for key in case_before} == case_before
        assert {key: request_after[key] for key in request_before} == request_before
        assert case_after["urgencia"] == ("normal" if has_calendar else "urgente")
        assert request_after["urgencia"] == ("normal" if has_calendar else "urgente")
        assert list(Expediente.objects.get(pk=case.pk).socios.values_list("pk", flat=True)) == [
            socio.pk
        ]
        if has_calendar:
            assert list(Holiday.objects.values().order_by("date")) == holidays_before
        else:
            assert Holiday.objects.count() == 16
            assert (
                Holiday.objects.filter(date__in=[date(2026, 6, 15), date(2026, 11, 23)]).count()
                == 2
            )
        client = APIClient()
        client.force_authenticate(user)
        response = client.get("/api/v1/expedientes/calendario/feriados/")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    finally:
        MigrationExecutor(connection).migrate(latest)
