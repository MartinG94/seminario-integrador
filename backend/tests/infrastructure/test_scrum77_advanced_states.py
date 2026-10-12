"""Importación aditiva de historias sintéticas con los seis estados en MySQL."""

from collections import Counter
from datetime import timedelta
from decimal import Decimal
from typing import Any

import pytest
from django.core.exceptions import ValidationError
from django.core.management.base import CommandError
from django.db.models import Sum
from django.utils import timezone

from expedientes.domain.calendar import compute_business_deadline
from expedientes.domain.holiday_provider import DbHolidayProvider
from expedientes.models import CambioEstadoExpediente, Expediente, ExpedienteNumberSequence, Holiday
from expedientes.services.workflow_service import ExpedienteWorkflowService
from notifications.models import EmailOutbox
from ranking.models import PuntajeAplicado, PuntajeGeneral
from socios.demo_catalog import CATALOG, expected_balances
from tests.infrastructure.test_scrum77_schema_bootstrap import (
    bootstrap_database as bootstrap_database,
)
from tests.infrastructure.test_scrum77_seed_integration import _all_rows, prepare_seed, snapshot

pytestmark = pytest.mark.django_db(transaction=True, databases="__all__")


def _load_previous(seed: Any, monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    from dataclasses import replace

    previous = replace(CATALOG, advanced_causes=())
    with monkeypatch.context() as setup:
        setup.setattr(seed, "CATALOG", previous)
        return seed.run_demo_seed()


def test_advanced_states_have_server_numbers_complete_history_and_expired_business_deadlines(
    bootstrap_database: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    seed = prepare_seed(bootstrap_database, monkeypatch)
    before = timezone.now()
    report = seed.run_demo_seed()
    scenes = report["mappings"]["advanced_causes"]
    assert len(scenes) == 10
    assert len(report["fixtures"]) == 272
    cases = list(Expediente.objects.order_by("pk"))
    assert Counter(case.estado for case in cases) == {
        "creado": 3,
        "justificando": 2,
        "revision_resolucion": 3,
        "espera_resolucion": 1,
        "pendiente_correos": 2,
        "emitido": 4,
    }
    assert len(cases) == 15
    expected_path = (
        "creado",
        "justificando",
        "revision_resolucion",
        "espera_resolucion",
        "pendiente_correos",
        "emitido",
    )
    for fixture in CATALOG.advanced_causes:
        case = Expediente.objects.get(pk=scenes[fixture.fixture_key])
        changes = list(case.cambios_estado.order_by("fecha_hora", "pk"))
        states = expected_path[: expected_path.index(fixture.stage) + 1]
        assert [change.estado_nuevo for change in changes] == list(states)
        assert [change.estado_anterior for change in changes] == ["creado", *states[:-1]]
        assert changes[0].fecha_hora == case.created_at == fixture.opened_at
        assert changes[1].fecha_hora == case.plazo_inicio_at == fixture.justification_started_at
        assert case.plazo_limite_at == compute_business_deadline(
            start_at=case.plazo_inicio_at, business_days=5, holiday_provider=DbHolidayProvider()
        )
        assert case.plazo_limite_at < changes[2].fecha_hora
        assert changes[-1].fecha_hora == case.updated_at == fixture.updated_at
        assert case.created_at < case.updated_at <= before
        assert all("sintétic" in change.motivo.lower() and change.actor for change in changes)
        expected_legajos = {
            str(
                next(
                    member.academic_number
                    for member in CATALOG.members
                    if member.fixture_key == key
                )
            )
            for key in fixture.recipient_member_keys
        }
        assert set(case.socios.values_list("legajo", flat=True)) == expected_legajos
    year = CATALOG.advanced_causes[0].opened_at.year
    assert ExpedienteNumberSequence.objects.get(year=year).last_value == 15
    assert not EmailOutbox.objects.exists()


def test_four_emissions_have_individual_resolutions_and_keep_original_eight_movements(
    bootstrap_database: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    seed = prepare_seed(bootstrap_database, monkeypatch)
    report = seed.run_demo_seed()
    mappings = report["mappings"]
    assert len(mappings["historical_resolutions"]) == 7
    assert len(mappings["movements"]) == 8
    assert (
        len(mappings["advanced_resolutions"])
        == len(mappings["advanced_expedientes"])
        == len(mappings["advanced_movements"])
        == 4
    )
    with bootstrap_database.cursor() as cursor:
        cursor.execute(
            "SELECT p.idPuntajeAplicado,p.socio_id,p.puntajeAplicado,e.idExpediente,"
            "e.dataRes_id,r.consideracion,e.nroExpediente FROM tribunal_puntajeaplicado p "
            "JOIN tribunal_expediente e ON e.idExpediente=p.expediente_id "
            "JOIN tribunal_datosresolucion r ON r.idDatosResolucion=e.dataRes_id"
        )
        rows = {str(row[0]): row for row in cursor.fetchall()}
    assert len(rows) == PuntajeAplicado.objects.count() == 12
    for fixture in CATALOG.advanced_causes:
        if fixture.stage != "emitido":
            assert fixture.fixture_key not in mappings["advanced_movements"]
            continue
        row = rows[mappings["advanced_movements"][fixture.fixture_key]]
        member = next(
            member
            for member in CATALOG.members
            if member.fixture_key == fixture.recipient_member_keys[0]
        )
        managed = Expediente.objects.get(pk=mappings["advanced_causes"][fixture.fixture_key])
        assert row[1:3] == (member.institutional_number, fixture.requested_points)
        assert str(row[3]) == mappings["advanced_expedientes"][fixture.fixture_key]
        assert str(row[4]) == mappings["advanced_resolutions"][fixture.fixture_key]
        assert managed.numero in row[5] and fixture.fixture_key in row[5]
        assert str(member.academic_number) in row[5] and str(member.institutional_number) in row[5]
        assert "VISTO" in row[5] and "CONSIDERANDO" in row[5] and "SE RESUELVE" in row[5]
        assert timezone.localtime(fixture.emitted_at).strftime("%H:%M hs") in row[5]
        assert (
            "sin firma productiva" in row[5] and fixture.emitted_at.strftime("%d/%m/%Y") in row[5]
        )
        assert row[6].startswith("A77") and len(row[6]) <= 9
    for fixture in CATALOG.members:
        balance = PuntajeAplicado.objects.filter(socio_id=fixture.institutional_number).aggregate(
            total=Sum("puntajeAplicado")
        )["total"] or Decimal("0")
        assert balance == expected_balances(CATALOG)[fixture.fixture_key]
    assert not PuntajeGeneral.objects.exists()


def test_upgrade_preserves_previous_and_uat_rows_and_repeats_without_writes(
    bootstrap_database: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    seed = prepare_seed(bootstrap_database, monkeypatch)
    previous = _load_previous(seed, monkeypatch)
    case = Expediente.objects.get(pk=previous["mappings"]["causes"]["cause.created.low"])
    case.motivo = "Motivo válido conservado de UAT"
    case.save(update_fields=["motivo"])
    ExpedienteWorkflowService.open_expediente(
        motivo="Alta propia de UAT que no pertenece al seed",
        socio_ids=[case.socio_id],
        actor="UAT",
        points=Decimal("-2"),
    )
    before = _all_rows(bootstrap_database)
    report = seed.run_demo_seed()
    after = _all_rows(bootstrap_database)
    for table, rows in before.items():
        if table != ExpedienteNumberSequence._meta.db_table:
            assert rows <= after[table], f"No se conserva {table}"
    assert Expediente.objects.count() == 16
    assert ExpedienteNumberSequence.objects.get(year=timezone.localdate().year).last_value == 16
    assert len(previous["fixtures"]) == 188 and len(report["fixtures"]) == 272
    original = {item["fixture_key"]: item for item in previous["fixtures"]}
    current = {item["fixture_key"]: item for item in report["fixtures"]}
    assert all(current[key] == value for key, value in original.items())
    stable = snapshot(bootstrap_database)
    writes = []

    def capture(execute: Any, sql: str, params: Any, many: bool, context: Any) -> Any:
        if sql.lstrip().upper().startswith(("INSERT", "UPDATE", "DELETE")):
            writes.append(sql)
        return execute(sql, params, many, context)

    with bootstrap_database.execute_wrapper(capture):
        assert seed.run_demo_seed() == report
    assert not writes
    assert snapshot(bootstrap_database) == stable


def test_foreign_advanced_scene_collision_rolls_back_without_adopting_it(
    bootstrap_database: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    from core.demo_scenes import _scene_reason

    seed = prepare_seed(bootstrap_database, monkeypatch)
    previous = _load_previous(seed, monkeypatch)
    base = Expediente.objects.get(pk=previous["mappings"]["causes"]["cause.created.low"])
    ExpedienteWorkflowService.open_expediente(
        motivo=_scene_reason("advanced.signature.01"), socio_ids=[base.socio_id], actor="UAT"
    )
    before = snapshot(bootstrap_database)
    with pytest.raises(CommandError, match="ajena"):
        seed.run_demo_seed()
    assert snapshot(bootstrap_database) == before


def test_late_advanced_ledger_failure_rolls_back_all_new_states_and_numbering(
    bootstrap_database: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    from core.demo_fixtures import DemoFixtureRegistry

    seed = prepare_seed(bootstrap_database, monkeypatch)
    _load_previous(seed, monkeypatch)
    before = snapshot(bootstrap_database)
    original = DemoFixtureRegistry.ensure_legacy

    def fail_after_insert(registry: Any, key: str, *args: Any, **kwargs: Any) -> Any:
        row = original(registry, key, *args, **kwargs)
        if key == "advanced.emitted.04.movement":
            raise RuntimeError("Fallo posterior al cuarto asiento avanzado")
        return row

    monkeypatch.setattr(DemoFixtureRegistry, "ensure_legacy", fail_after_insert)
    with pytest.raises(RuntimeError, match="cuarto asiento"):
        seed.run_demo_seed()
    assert snapshot(bootstrap_database) == before


def test_calendar_that_prevents_historical_expiration_rejects_without_writes(
    bootstrap_database: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    seed = prepare_seed(bootstrap_database, monkeypatch)
    _load_previous(seed, monkeypatch)
    start = CATALOG.advanced_causes[0].justification_started_at.date()
    for days in range(1, 20):
        Holiday.objects.create(
            date=start + timedelta(days=days), description="Calendario sintético", origin="SYSTEM"
        )
    before = snapshot(bootstrap_database)
    with pytest.raises(ValidationError, match="plazo"):
        seed.run_demo_seed()
    assert snapshot(bootstrap_database) == before


def test_missing_advanced_audit_is_not_reconstructed(
    bootstrap_database: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    seed = prepare_seed(bootstrap_database, monkeypatch)
    report = seed.run_demo_seed()
    case_id = report["mappings"]["advanced_causes"]["advanced.review.01"]
    CambioEstadoExpediente.objects.filter(expediente_id=case_id).first().delete()
    before = snapshot(bootstrap_database)
    with pytest.raises(ValidationError, match="no existe"):
        seed.run_demo_seed()
    assert snapshot(bootstrap_database) == before


def test_owned_advanced_audit_moved_to_another_case_rejects_without_repair(
    bootstrap_database: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    seed = prepare_seed(bootstrap_database, monkeypatch)
    report = seed.run_demo_seed()
    case_id = report["mappings"]["advanced_causes"]["advanced.review.01"]
    audit = CambioEstadoExpediente.objects.filter(expediente_id=case_id).first()
    audit.expediente_id = report["mappings"]["causes"]["cause.created.low"]
    audit.save(update_fields=["expediente"])
    before = snapshot(bootstrap_database)
    with pytest.raises(ValidationError, match="auditoría"):
        seed.run_demo_seed()
    assert snapshot(bootstrap_database) == before


def test_future_importation_time_rejects_synthetic_history_without_partial_changes(
    bootstrap_database: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    from core import demo_scenes

    seed = prepare_seed(bootstrap_database, monkeypatch)
    _load_previous(seed, monkeypatch)
    before = snapshot(bootstrap_database)
    monkeypatch.setattr(demo_scenes.timezone, "now", lambda: CATALOG.advanced_causes[0].opened_at)
    with pytest.raises(ValidationError, match="posteriores"):
        seed.run_demo_seed()
    assert snapshot(bootstrap_database) == before
