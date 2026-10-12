"""El seed rechaza destinos/perfiles/esquemas ajenos sin iniciar escrituras."""

import importlib
from io import StringIO
from typing import Any
from unittest.mock import MagicMock

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from socios.demo_catalog import CATALOG
from tests.infrastructure.test_scrum77_schema_bootstrap import (
    bootstrap_database as bootstrap_database,
)


@pytest.fixture
def seed_module() -> Any:
    return importlib.import_module("core.demo_seed")


@pytest.mark.parametrize("profile", ["", "foreign", CATALOG.profile.upper(), None, True])
def test_unapproved_profile_fails_before_configuration_or_database(
    seed_module: Any, monkeypatch: pytest.MonkeyPatch, profile: Any
) -> None:
    check = MagicMock()
    monkeypatch.setattr(seed_module.preflight, "_check_configuration", check)
    with pytest.raises(CommandError):
        seed_module.assert_demo_seed_environment(profile)
    check.assert_not_called()


def test_environment_uses_existing_authenticated_demo_configuration_guard(
    seed_module: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    check = MagicMock(side_effect=CommandError("Destino ajeno."))
    monkeypatch.setattr(seed_module.preflight, "_check_configuration", check)
    with pytest.raises(CommandError, match="Destino ajeno"):
        seed_module.assert_demo_seed_environment(CATALOG.profile)
    check.assert_called_once_with()


@pytest.mark.parametrize(
    "row",
    [
        ("production", "8.0.46", 1, "STRICT_TRANS_TABLES"),
        ("aveit_tribunal_scrum77_demo", "10.11-MariaDB", 1, "STRICT_TRANS_TABLES"),
        ("aveit_tribunal_scrum77_demo", "8.0.46", 0, "STRICT_TRANS_TABLES"),
        ("aveit_tribunal_scrum77_demo", "8.0.46", 1, "NO_ENGINE_SUBSTITUTION"),
    ],
)
def test_effective_database_identity_mode_and_foreign_keys_are_read_before_writes(
    seed_module: Any, row: tuple[Any, ...]
) -> None:
    database = MagicMock(vendor="mysql")
    database.settings_dict = {
        "NAME": "aveit_tribunal_scrum77_demo",
        "USER": "aveit_dev",
        "HOST": "db",
        "PORT": "3306",
    }
    cursor = database.cursor.return_value.__enter__.return_value
    cursor.fetchone.return_value = row
    with pytest.raises(CommandError):
        seed_module.assert_demo_seed_database(database)
    assert cursor.execute.call_count > 0
    assert all(
        str(call.args[0]).lstrip().upper().startswith("SELECT")
        for call in cursor.execute.call_args_list
    )


@pytest.mark.parametrize(
    "field,value", [("HOST", "production"), ("USER", "root"), ("PORT", "3399")]
)
def test_provided_connection_must_match_the_same_demo_profile_before_opening_cursor(
    seed_module: Any, field: str, value: str
) -> None:
    database = MagicMock(vendor="mysql")
    database.settings_dict = {
        "NAME": "aveit_tribunal_scrum77_demo",
        "USER": "aveit_dev",
        "HOST": "db",
        "PORT": "3306",
    }
    database.settings_dict[field] = value
    with pytest.raises(CommandError):
        seed_module.assert_demo_seed_database(database)
    database.cursor.assert_not_called()


def test_seed_rejects_missing_legacy_table_without_bootstrap_or_migration(
    seed_module: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    database = MagicMock()
    monkeypatch.setattr(seed_module, "read_contracts", lambda: [])
    monkeypatch.setattr(seed_module, "validate_existing_schema", lambda *args: ["socio_email"])
    with pytest.raises(CommandError):
        seed_module.assert_demo_seed_schema(database)
    database.schema_editor.assert_not_called()


def test_seed_rejects_pending_managed_migration_without_applying_it(
    seed_module: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    database = MagicMock()
    monkeypatch.setattr(seed_module, "read_contracts", lambda: [])
    monkeypatch.setattr(seed_module, "validate_existing_schema", lambda *args: [])
    executor = MagicMock()
    executor.migration_plan.return_value = [(object(), False)]
    monkeypatch.setattr(seed_module, "MigrationExecutor", lambda _: executor)
    with pytest.raises(CommandError):
        seed_module.assert_demo_seed_schema(database)
    executor.migrate.assert_not_called()


def test_command_invalid_profile_does_not_call_loader_or_print_manifest(
    seed_module: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    run = MagicMock()
    monkeypatch.setattr(seed_module, "run_demo_seed", run)
    output = StringIO()
    with pytest.raises(CommandError):
        call_command("seed_expedientes", profile="foreign", stdout=output)
    run.assert_not_called()
    assert output.getvalue() == ""


@pytest.mark.django_db(transaction=True, databases="__all__")
def test_physical_ownership_uniqueness_must_match_even_with_applied_history(
    bootstrap_database: Any, seed_module: Any
) -> None:
    from core.demo_schema import prepare_schema

    prepare_schema(bootstrap_database)
    seed_module.assert_demo_seed_schema(bootstrap_database)
    with bootstrap_database.cursor() as cursor:
        cursor.execute("ALTER TABLE core_demofixtureownership DROP INDEX demo_fixture_target_uq")
    with pytest.raises(CommandError, match="propiedad"):
        seed_module.assert_demo_seed_schema(bootstrap_database)
