"""Orquestación completa: manifiesto real, conservación y rollback del conjunto."""

import hashlib
import json
from dataclasses import replace
from io import StringIO
from typing import Any

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from tests.infrastructure.test_scrum77_schema_bootstrap import (
    bootstrap_database as bootstrap_database,
)


def prepare_seed(database: Any, monkeypatch: pytest.MonkeyPatch) -> Any:
    from django.conf import settings

    from core import demo_seed
    from core.demo_schema import prepare_schema

    prepare_schema(database)
    monkeypatch.setattr(settings, "DEBUG", True)
    monkeypatch.setattr(demo_seed, "assert_demo_seed_environment", lambda *_: None)
    monkeypatch.setattr(demo_seed, "assert_demo_seed_database", lambda *_: None)
    monkeypatch.setattr(demo_seed, "assert_demo_seed_schema", lambda *_: None)
    return demo_seed


def snapshot(database: Any) -> dict[str, str]:
    with database.cursor() as cursor:
        cursor.execute("SHOW FULL TABLES WHERE Table_type='BASE TABLE'")
        names = [row[0] for row in cursor.fetchall()]
        result = {}
        for name in names:
            cursor.execute(f"SELECT * FROM {database.ops.quote_name(name)}")
            rows = sorted(cursor.fetchall(), key=repr)
            result[name] = hashlib.sha256(json.dumps(rows, default=str).encode()).hexdigest()
        return result


@pytest.mark.django_db(transaction=True, databases="__all__")
def test_complete_manifest_contains_real_nullable_and_legacy_resolution_identities(
    bootstrap_database: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    seed = prepare_seed(bootstrap_database, monkeypatch)
    report = seed.run_demo_seed()
    assert report["status"] == "ok"
    assert len(report["identities"]) == 20
    assert report["mappings"]["subcommissions"]["subcommission.unassigned"] is None
    assert len(report["mappings"]["historical_resolutions"]) == 7
    for item in report["identities"]:
        assert item["institutional_number"] != item["academic_number"]
        assert item["group"] in (57, 58, 59, 60, 62, 63)
        assert (item["local_socio_id"] is None) == (item["user_id"] is None)
        if item["user_id"] is not None:
            assert item["local_legajo"] == str(item["academic_number"])
        else:
            assert item["local_legajo"] is None
    forbidden = {"password", "token", "secret", "initial_fingerprint", "password_hash"}

    def check_keys(value: Any) -> None:
        if isinstance(value, dict):
            assert not forbidden.intersection(value)
            for child in value.values():
                check_keys(child)
        elif isinstance(value, list):
            for child in value:
                check_keys(child)

    check_keys(report)


def _load_previous_catalog(seed: Any, monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    """Preparar el conjunto aprobado previo en scratch, con sus loaders reales.

    Sólo la configuración histórica omite la validación del catálogo ampliado;
    ORM, MySQL, lock, propiedad y servicios mantienen su implementación real.
    Al salir del contexto, la carga de 20 vuelve a usar toda la validación vigente.
    """
    from core import demo_members, demo_scenes
    from socios.demo_catalog import CATALOG

    previous = replace(
        CATALOG,
        groups=CATALOG.groups[:4],
        members=CATALOG.members[:16],
        accounts=CATALOG.accounts[:6],
        advanced_causes=(),
    )
    assert {group.number for group in previous.groups} == {57, 58, 59, 60}
    assert len(previous.members) == 16 and len(previous.accounts) == 6
    with monkeypatch.context() as historical_setup:
        historical_setup.setattr(seed, "CATALOG", previous)
        for module in (seed, demo_members, demo_scenes):
            historical_setup.setattr(module, "validate_catalog", lambda _: None)
        return seed.run_demo_seed()


def _all_rows(database: Any) -> dict[str, set[tuple[Any, ...]]]:
    with database.cursor() as cursor:
        cursor.execute("SHOW FULL TABLES WHERE Table_type='BASE TABLE'")
        tables = [row[0] for row in cursor.fetchall()]
        rows = {}
        for table in tables:
            cursor.execute(f"SELECT * FROM {database.ops.quote_name(table)}")
            # Algunos campos JSON no son hashables; repr preserva sus valores completos.
            rows[table] = {tuple(repr(value) for value in row) for row in cursor.fetchall()}
    return rows


@pytest.mark.django_db(transaction=True, databases="__all__")
def test_junior_extension_adds_only_new_rows_and_preserves_previous_edits_and_counter(
    bootstrap_database: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    from django.contrib.auth import get_user_model

    from expedientes.models import ExpedienteNumberSequence
    from socios.models import Socio

    seed = prepare_seed(bootstrap_database, monkeypatch)
    previous = _load_previous_catalog(seed, monkeypatch)
    edited = Socio.objects.get(legajo="99077001")
    edited.first_name = "Nombre conservado de la UAT"
    edited.save(update_fields=["first_name"])
    edited.user.set_password("Synthetic preserved UAT credential")
    edited.user.save(update_fields=["password"])
    before = _all_rows(bootstrap_database)
    from socios.demo_catalog import CATALOG

    # El upgrade Junior original precede a las escenas avanzadas y debe
    # seguir acreditando que esas cuatro altas por sí solas no aplican puntos.
    with monkeypatch.context() as original_junior_upgrade:
        original_junior_upgrade.setattr(seed, "CATALOG", replace(CATALOG, advanced_causes=()))
        extended = seed.run_demo_seed()
    after = _all_rows(bootstrap_database)
    preserved = all(rows <= after[table] for table, rows in before.items())
    assert preserved, "La ampliación conserva las filas anteriores sin exponer credenciales."
    assert len(previous["fixtures"]) == 162
    assert len(extended["fixtures"]) == 188
    original_refs = {item["fixture_key"]: item for item in previous["fixtures"]}
    new_refs = {item["fixture_key"]: item for item in extended["fixtures"]}
    assert all(new_refs[key] == value for key, value in original_refs.items())
    assert {identity["institutional_number"] for identity in extended["identities"]} == set(
        range(770001, 770021)
    )
    assert get_user_model().objects.count() == Socio.objects.count() == 15
    for legajo, year in (("99077017", 2), ("99077018", 2), ("99077019", 1), ("99077020", 1)):
        junior = Socio.objects.get(legajo=legajo)
        assert (junior.role, junior.social_year, junior.category, junior.is_enabled) == (
            "SOCIO",
            year,
            "JUNIOR",
            True,
        )
    for table in (
        "expedientes_expediente",
        ExpedienteNumberSequence._meta.db_table,
        "expedientes_solicitudt01",
        "tribunal_puntajeaplicado",
        "tribunal_puntajegeneral",
    ):
        assert before[table] == after[table]
    stable = snapshot(bootstrap_database)
    with monkeypatch.context() as original_junior_upgrade:
        original_junior_upgrade.setattr(seed, "CATALOG", replace(CATALOG, advanced_causes=()))
        repeated = seed.run_demo_seed()
    assert repeated == extended
    assert snapshot(bootstrap_database) == stable


@pytest.mark.django_db(transaction=True, databases="__all__")
def test_junior_foreign_username_rejects_extension_without_partial_changes(
    bootstrap_database: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    from django.contrib.auth import get_user_model

    seed = prepare_seed(bootstrap_database, monkeypatch)
    _load_previous_catalog(seed, monkeypatch)
    get_user_model().objects.create_user(username="99077017", email="foreign-junior@scrum77.test")
    before = snapshot(bootstrap_database)
    with pytest.raises(CommandError, match="ajena"):
        seed.run_demo_seed()
    assert snapshot(bootstrap_database) == before


@pytest.mark.django_db(transaction=True, databases="__all__")
def test_failure_after_junior_insert_rolls_back_extension_preserving_previous_catalog(
    bootstrap_database: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    from core.demo_fixtures import DemoFixtureRegistry

    seed = prepare_seed(bootstrap_database, monkeypatch)
    _load_previous_catalog(seed, monkeypatch)
    before = snapshot(bootstrap_database)
    real_insert = DemoFixtureRegistry.ensure_legacy
    inserted_juniors = []

    def fail_after_junior_insert(
        registry: Any, key: str, table: str, *args: Any, **kwargs: Any
    ) -> Any:
        row = real_insert(registry, key, table, *args, **kwargs)
        if table == "socio_lista" and row["nroSocio"] >= 770017:
            inserted_juniors.append(row["nroSocio"])
            if row["nroSocio"] == 770019:
                raise RuntimeError("Fallo posterior a tercera ficha Junior")
        return row

    monkeypatch.setattr(DemoFixtureRegistry, "ensure_legacy", fail_after_junior_insert)
    with pytest.raises(RuntimeError, match="tercera ficha Junior"):
        seed.run_demo_seed()
    assert inserted_juniors == [770017, 770018, 770019]
    assert snapshot(bootstrap_database) == before


@pytest.mark.django_db(transaction=True, databases="__all__")
def test_second_complete_run_preserves_rows_edits_credentials_and_formal_counter(
    bootstrap_database: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    from expedientes.models import Expediente
    from socios.models import Socio

    seed = prepare_seed(bootstrap_database, monkeypatch)
    first = seed.run_demo_seed()
    profile = Socio.objects.get(legajo="99077001")
    profile.first_name = "Editado en la demo"
    profile.is_enabled = False
    profile.save(update_fields=["first_name", "is_enabled"])
    profile.user.set_password("Synthetic edited credential")
    profile.user.save(update_fields=["password"])
    case = Expediente.objects.get(pk=first["mappings"]["causes"]["cause.created.low"])
    case.motivo = "Motivo modificado válidamente"
    case.save(update_fields=["motivo"])
    before = snapshot(bootstrap_database)
    second = seed.run_demo_seed()
    assert first["fixtures"] == second["fixtures"]
    assert first["mappings"] == second["mappings"]
    assert snapshot(bootstrap_database) == before


@pytest.mark.django_db(transaction=True, databases="__all__")
def test_failure_after_both_loaders_rolls_back_all_data_property_and_numbering(
    bootstrap_database: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    from core import demo_scenes

    seed = prepare_seed(bootstrap_database, monkeypatch)
    before = snapshot(bootstrap_database)
    real_loader = demo_scenes.load_demo_scenes

    def fail_after_real_load(*args: Any, **kwargs: Any) -> Any:
        real_loader(*args, **kwargs)
        raise RuntimeError("Fallo posterior al conjunto completo")

    monkeypatch.setattr(demo_scenes, "load_demo_scenes", fail_after_real_load)
    with pytest.raises(RuntimeError, match="posterior"):
        seed.run_demo_seed()
    assert snapshot(bootstrap_database) == before


@pytest.mark.django_db(transaction=True, databases="__all__")
def test_second_load_rejects_missing_owned_audit_without_repairing_it(
    bootstrap_database: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    from expedientes.models import CambioEstadoExpediente

    seed = prepare_seed(bootstrap_database, monkeypatch)
    seed.run_demo_seed()
    audit = CambioEstadoExpediente.objects.order_by("pk").first()
    assert audit is not None
    audit.delete()
    before = snapshot(bootstrap_database)
    with pytest.raises(CommandError):
        seed.run_demo_seed()
    assert snapshot(bootstrap_database) == before


def test_command_redacts_unexpected_failure_without_printing_manifest(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from core import demo_seed

    monkeypatch.setattr(demo_seed, "assert_demo_seed_environment", lambda *_: None)
    monkeypatch.setattr(demo_seed.preflight, "_check_mysql", lambda: None)
    monkeypatch.setattr(demo_seed.preflight, "_check_http_health", lambda: None)

    def fail(**kwargs: Any) -> Any:
        raise RuntimeError("credential-sentinel-that-must-not-leak")

    monkeypatch.setattr(demo_seed, "run_demo_seed", fail)
    output = StringIO()
    with pytest.raises(CommandError) as caught:
        call_command("seed_expedientes", stdout=output)
    assert "credential-sentinel" not in str(caught.value)
    assert output.getvalue() == ""
