"""TS77.15: antecedentes sintéticos respaldados e individualizados en MySQL real."""

from dataclasses import replace
from decimal import Decimal
from typing import Any

import pytest
from django.db.models import Sum

from ranking.models import PuntajeAplicado, PuntajeGeneral
from socios.demo_catalog import CATALOG, expected_balances
from tests.infrastructure.test_scrum77_schema_bootstrap import (
    bootstrap_database as bootstrap_database,
)
from tests.infrastructure.test_scrum77_seed_scenes import load_scenes, prepare_scene_test

pytestmark = pytest.mark.django_db(transaction=True, databases="__all__")


def test_eight_individual_movements_link_seven_formal_resolutions_and_legacy_cases(
    bootstrap_database: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    scenes, registry, members = prepare_scene_test(bootstrap_database, monkeypatch)
    result = load_scenes(scenes, registry, members)
    assert len(result.movements) == 8
    assert len(result.historical_resolutions) == len(result.historical_expedientes) == 7
    with bootstrap_database.cursor() as cursor:
        cursor.execute(
            "SELECT p.socio_id,p.puntajeAplicado,p.expediente_id,e.dataRes_id,"
            "r.consideracion,e.nroExpediente FROM tribunal_puntajeaplicado p "
            "JOIN tribunal_expediente e ON e.idExpediente=p.expediente_id "
            "JOIN tribunal_datosresolucion r ON r.idDatosResolucion=e.dataRes_id "
            "ORDER BY p.idPuntajeAplicado"
        )
        rows = cursor.fetchall()
    assert len(rows) == 8
    for index, fixture in enumerate(CATALOG.historical_movements):
        member = members.institutional_members[fixture.member_key]
        row = rows[index]
        assert row[0] == member.pk and row[1] == fixture.points
        assert (
            row[2] == result.historical_expedientes[fixture.legacy_expediente_key]["idExpediente"]
        )
        assert row[3] == result.historical_resolutions[fixture.resolution_key]["idDatosResolucion"]
        assert "RESOLUCIÓN" in row[4] and "VISTO" in row[4]
        assert "CONSIDERANDO" in row[4] and "SE RESUELVE" in row[4]
        assert "sintético" in row[4].lower() and str(member.pk) in row[4]
        assert row[5].startswith("D77") and len(row[5]) <= 9
    # El mérito compartido conserva dos destinatarios y puntos distintos (+2/+1).
    assert rows[0][2:4] == rows[1][2:4]
    assert rows[0][1] == Decimal("2") and rows[1][1] == Decimal("1")


def test_balance_comes_only_from_individual_history_without_general_score_cache(
    bootstrap_database: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    scenes, registry, members = prepare_scene_test(bootstrap_database, monkeypatch)
    load_scenes(scenes, registry, members)
    expected = expected_balances(replace(CATALOG, advanced_causes=()))
    for fixture in CATALOG.members:
        balance = PuntajeAplicado.objects.filter(socio_id=fixture.institutional_number).aggregate(
            balance=Sum("puntajeAplicado")
        )["balance"] or Decimal("0")
        assert balance == expected[fixture.fixture_key]
    assert PuntajeAplicado.objects.aggregate(balance=Sum("puntajeAplicado"))["balance"] == Decimal(
        "1"
    )
    assert not PuntajeGeneral.objects.exists()
    assert all(
        row.puntajeAplicado == row.puntajeAplicado.to_integral_value()
        for row in PuntajeAplicado.objects.all()
    )


def test_history_second_load_has_no_points_updates_and_preserves_all_rows(
    bootstrap_database: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    scenes, registry, members = prepare_scene_test(bootstrap_database, monkeypatch)
    first = load_scenes(scenes, registry, members)
    tables = (
        "tribunal_valorsancion",
        "tribunal_datosresolucion",
        "tribunal_expediente",
        "tribunal_puntajeaplicado",
    )
    with bootstrap_database.cursor() as cursor:
        before = {}
        for table in tables:
            cursor.execute(f"SELECT * FROM `{table}`")
            before[table] = cursor.fetchall()
    sql_statements: list[str] = []

    def capture(execute: Any, sql: str, params: Any, many: bool, context: Any) -> Any:
        sql_statements.append(sql)
        return execute(sql, params, many, context)

    with bootstrap_database.execute_wrapper(capture):
        second = load_scenes(scenes, registry, members)
    with bootstrap_database.cursor() as cursor:
        for table in tables:
            cursor.execute(f"SELECT * FROM `{table}`")
            assert cursor.fetchall() == before[table]
    assert {key: row["idPuntajeAplicado"] for key, row in second.movements.items()} == {
        key: row["idPuntajeAplicado"] for key, row in first.movements.items()
    }
    writes = [
        sql
        for sql in sql_statements
        if sql.lstrip().upper().startswith(("INSERT", "UPDATE", "DELETE"))
    ]
    assert not any("tribunal_" in sql.lower() for sql in writes)


def test_failure_after_real_history_insert_rolls_back_asientos_respaldo_and_property(
    bootstrap_database: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    scenes, registry, members = prepare_scene_test(bootstrap_database, monkeypatch)
    original = registry.ensure_legacy
    inserted = 0

    def fail_after_ledger(*args: Any, **kwargs: Any) -> Any:
        nonlocal inserted
        result = original(*args, **kwargs)
        table = kwargs.get("table", args[1] if len(args) > 1 else "")
        if table == "tribunal_puntajeaplicado":
            inserted += 1
            if inserted == 3:
                raise RuntimeError("Fallo histórico después de tres INSERT reales")
        return result

    monkeypatch.setattr(registry, "ensure_legacy", fail_after_ledger)
    with pytest.raises(RuntimeError, match="Fallo histórico"):
        load_scenes(scenes, registry, members)
    assert not PuntajeAplicado.objects.exists()
    with bootstrap_database.cursor() as cursor:
        for table in ("tribunal_valorsancion", "tribunal_datosresolucion", "tribunal_expediente"):
            cursor.execute(f"SELECT COUNT(*) FROM `{table}`")
            assert cursor.fetchone() == (0,)
    assert all(
        registry.get(fixture.fixture_key) is None for fixture in CATALOG.historical_movements
    )
