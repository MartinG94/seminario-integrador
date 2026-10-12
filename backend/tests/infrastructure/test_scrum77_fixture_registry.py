"""TS77.09: propiedad persistente y exclusión sobre MySQL descartable."""

import importlib
from typing import Any

import pytest
from django.conf import settings
from django.core.management.base import CommandError
from django.db import transaction

from core.demo_schema import prepare_schema
from socios.demo_catalog import CATALOG
from socios.models import Subcomision
from tests.infrastructure.test_scrum77_schema_bootstrap import (
    bootstrap_database as bootstrap_database,
)


@pytest.fixture
def fixture_database(bootstrap_database: Any, monkeypatch: pytest.MonkeyPatch) -> Any:
    prepare_schema(bootstrap_database)
    monkeypatch.setattr(settings, "DEBUG", True)
    module = importlib.import_module("core.demo_fixtures")
    # La identidad demo se prueba por TS77.08; aquí el destino es un scratch UUID propio.
    monkeypatch.setattr(module, "_assert_environment", lambda profile, database: None)
    monkeypatch.setattr(module, "_assert_schema", lambda database: None, raising=False)
    monkeypatch.setattr(module, "_assert_lock", lambda database: None, raising=False)
    return bootstrap_database


def _registry(database: Any, profile: str = CATALOG.profile) -> Any:
    module = importlib.import_module("core.demo_fixtures")
    return module.DemoFixtureRegistry(profile=profile, connection=database)


@pytest.mark.django_db(transaction=True, databases="__all__")
def test_registry_reuses_owned_pk_and_preserves_an_edited_row(fixture_database: Any) -> None:
    registry = _registry(fixture_database)
    with transaction.atomic():
        first = registry.ensure_model("test.subcommission", Subcomision, {"name": "Inicial"}, {})
    first.name = "Edición válida"
    first.save(update_fields=["name"])
    writes = []

    def observe(execute: Any, sql: str, params: Any, many: bool, context: Any) -> Any:
        if sql.lstrip().upper().startswith(("INSERT", "UPDATE", "DELETE")):
            writes.append(sql)
        return execute(sql, params, many, context)

    with fixture_database.execute_wrapper(observe), transaction.atomic():
        second = _registry(fixture_database).ensure_model(
            "test.subcommission", Subcomision, {"name": "Inicial"}, {}
        )
    assert second.pk == first.pk
    assert second.name == "Edición válida"
    assert writes == []
    assert registry.get("test.subcommission").owned is True


@pytest.mark.django_db(transaction=True, databases="__all__")
def test_registry_does_not_claim_an_identical_foreign_row(fixture_database: Any) -> None:
    from core.models import DemoFixtureOwnership

    foreign = Subcomision.objects.create(name="Coincidente")
    with pytest.raises(CommandError, match="ajena"), transaction.atomic():
        _registry(fixture_database).ensure_model(
            "test.foreign", Subcomision, {"name": "Coincidente"}, {}
        )
    assert Subcomision.objects.get(pk=foreign.pk).name == "Coincidente"
    assert DemoFixtureOwnership.objects.count() == 0


@pytest.mark.django_db(transaction=True, databases="__all__")
def test_compatible_shared_reference_is_recorded_without_ownership(fixture_database: Any) -> None:
    shared = Subcomision.objects.create(name="Cómputos", description="Conservada")
    with transaction.atomic():
        result = _registry(fixture_database).ensure_model(
            "reference.computing", Subcomision, {"name": "Cómputos"}, {}, reference=True
        )
    assert result.pk == shared.pk
    assert result.description == "Conservada"
    assert _registry(fixture_database).get("reference.computing").owned is False


@pytest.mark.django_db(transaction=True, databases="__all__")
def test_target_namespace_cannot_belong_to_two_profiles(fixture_database: Any) -> None:
    with transaction.atomic():
        first = _registry(fixture_database).ensure_model(
            "test.owner", Subcomision, {"name": "Propia"}, {}
        )
    with pytest.raises(CommandError, match="propiedad"), transaction.atomic():
        _registry(fixture_database, "another-profile").record(
            "test.other", Subcomision._meta.db_table, first.pk
        )
    assert _registry(fixture_database, "another-profile").get("test.other") is None


@pytest.mark.django_db(transaction=True, databases="__all__")
def test_target_ownership_uses_the_canonical_pk_instead_of_numeric_aliases(
    fixture_database: Any,
) -> None:
    with transaction.atomic():
        registry = _registry(fixture_database)
        row = registry.ensure_model("test.owner", Subcomision, {"name": "Canónica"}, {})
    with pytest.raises(CommandError, match="propiedad"), transaction.atomic():
        registry.record("test.alias", Subcomision._meta.db_table, f"0{row.pk}")
    assert registry.get("test.alias") is None


@pytest.mark.django_db(transaction=True, databases="__all__")
def test_registration_key_cannot_change_target_namespace(fixture_database: Any) -> None:
    with transaction.atomic():
        registry = _registry(fixture_database)
        row = registry.ensure_model("test.stable", Subcomision, {"name": "Estable"}, {})
    with pytest.raises(CommandError, match="referencia"), transaction.atomic():
        registry.record("test.stable", "auth_user", row.pk)
    assert registry.get("test.stable").namespace == Subcomision._meta.db_table


@pytest.mark.django_db(transaction=True, databases="__all__")
def test_owned_reference_missing_target_aborts_instead_of_recreating(fixture_database: Any) -> None:
    with transaction.atomic():
        registry = _registry(fixture_database)
        row = registry.ensure_model("test.deleted", Subcomision, {"name": "Eliminada"}, {})
    row.delete()
    with pytest.raises(CommandError, match="existe"), transaction.atomic():
        registry.ensure_model("test.deleted", Subcomision, {"name": "Eliminada"}, {})
    assert not Subcomision.objects.exists()


@pytest.mark.django_db(transaction=True, databases="__all__")
def test_registry_requires_the_outer_data_transaction(fixture_database: Any) -> None:
    with pytest.raises(CommandError, match="transacci"):
        _registry(fixture_database).ensure_model("test.atomic", Subcomision, {"name": "Atomic"}, {})
    assert Subcomision.objects.count() == 0


@pytest.mark.django_db(transaction=True, databases="__all__")
def test_model_and_registry_creation_rollback_together(fixture_database: Any) -> None:
    from core.models import DemoFixtureOwnership

    with pytest.raises(RuntimeError, match="fallo"), transaction.atomic():
        _registry(fixture_database).ensure_model(
            "test.rollback", Subcomision, {"name": "Temporal"}, {}
        )
        raise RuntimeError("fallo intermedio sintético")
    assert Subcomision.objects.count() == 0
    assert DemoFixtureOwnership.objects.count() == 0


@pytest.mark.django_db(transaction=True, databases="__all__")
def test_manifest_exports_only_identity_and_provenance(fixture_database: Any) -> None:
    with transaction.atomic():
        registry = _registry(fixture_database)
        row = registry.ensure_model("test.safe", Subcomision, {"name": "Segura"}, {})
    assert registry.export() == [
        {
            "fixture_key": "test.safe",
            "namespace": "socios_subcomision",
            "object_key": str(row.pk),
            "owned": True,
        }
    ]


@pytest.mark.django_db(transaction=True, databases="__all__")
def test_seed_and_schema_preparation_share_one_mysql_lock(fixture_database: Any) -> None:
    module = importlib.import_module("core.demo_fixtures")
    peer = fixture_database.copy(alias="scrum77_seed_peer")
    lock_name = f"scrum77-schema:{fixture_database.settings_dict['NAME']}"
    try:
        with peer.cursor() as cursor:
            cursor.execute("SELECT GET_LOCK(%s, 0)", [lock_name])
            assert cursor.fetchone() == (1,)
        with pytest.raises(CommandError, match="curso"):
            with module.demo_fixture_lock(fixture_database):
                pytest.fail("El bloqueo compartido no debe concederse a otra conexión.")
    finally:
        with peer.cursor() as cursor:
            cursor.execute("SELECT RELEASE_LOCK(%s)", [lock_name])
        peer.close()


@pytest.mark.django_db(transaction=True, databases="__all__")
def test_direct_registry_write_requires_the_real_mysql_lock(
    bootstrap_database: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    from core import demo_seed

    prepare_schema(bootstrap_database)
    module = importlib.import_module("core.demo_fixtures")
    monkeypatch.setattr(demo_seed, "assert_demo_seed_environment", lambda profile: None)
    monkeypatch.setattr(demo_seed, "assert_demo_seed_database", lambda database: None)
    monkeypatch.setattr(demo_seed, "assert_demo_seed_schema", lambda database: None)
    registry = module.DemoFixtureRegistry(CATALOG.profile, connection=bootstrap_database)
    with pytest.raises(CommandError, match="bloqueo"), transaction.atomic():
        registry.ensure_model("test.direct", Subcomision, {"name": "Directa"}, {})
    assert not Subcomision.objects.exists()
    with module.demo_fixture_lock(bootstrap_database), transaction.atomic():
        row = registry.ensure_model("test.direct", Subcomision, {"name": "Directa"}, {})
    assert row.name == "Directa"


@pytest.mark.django_db(transaction=True, databases="__all__")
def test_reused_registry_revalidates_schema_after_the_mysql_lock_is_reacquired(
    bootstrap_database: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    from core import demo_seed

    prepare_schema(bootstrap_database)
    module = importlib.import_module("core.demo_fixtures")
    monkeypatch.setattr(demo_seed, "assert_demo_seed_environment", lambda profile: None)
    monkeypatch.setattr(demo_seed, "assert_demo_seed_database", lambda database: None)
    registry = module.DemoFixtureRegistry(CATALOG.profile, connection=bootstrap_database)
    with module.demo_fixture_lock(bootstrap_database), transaction.atomic():
        row = registry.ensure_model("test.first-lease", Subcomision, {"name": "Primera"}, {})
    with bootstrap_database.cursor() as cursor:
        cursor.execute("ALTER TABLE core_demofixtureownership DROP INDEX demo_fixture_target_uq")
    before = list(Subcomision.objects.order_by("pk").values())
    with pytest.raises(CommandError, match="propiedad|unicidad"):
        with module.demo_fixture_lock(bootstrap_database), transaction.atomic():
            registry.ensure_model("test.second-lease", Subcomision, {"name": "Segunda"}, {})
    assert list(Subcomision.objects.order_by("pk").values()) == before
    assert registry.get("test.second-lease") is None
    assert Subcomision.objects.get(pk=row.pk).name == "Primera"
    with bootstrap_database.cursor() as cursor:
        constraints = bootstrap_database.introspection.get_constraints(
            cursor, "core_demofixtureownership"
        )
    assert "demo_fixture_target_uq" not in constraints


@pytest.mark.django_db(transaction=True, databases="__all__")
def test_export_rejects_every_registered_reference_that_lost_its_child(
    fixture_database: Any,
) -> None:
    with transaction.atomic():
        registry = _registry(fixture_database)
        row = registry.ensure_model("test.child", Subcomision, {"name": "Hija"}, {})
    row.delete()
    with pytest.raises(CommandError, match="existe"):
        registry.export()


@pytest.mark.django_db(transaction=True, databases="__all__")
def test_legacy_reference_reuses_canonical_row_without_rewriting(fixture_database: Any) -> None:
    with fixture_database.cursor() as cursor:
        cursor.execute(
            "INSERT INTO grupo_lista(nroGrupo,nombre,descripcion) VALUES(57,'G57','Conservada')"
        )
    with transaction.atomic():
        registry = _registry(fixture_database)
        row = registry.ensure_legacy(
            "reference.g57",
            "grupo_lista",
            "nroGrupo",
            {"nroGrupo": 57},
            {"nroGrupo": 57, "nombre": "G57"},
            reference=True,
        )
    assert row["descripcion"] == "Conservada"
    assert registry.get("reference.g57").owned is False


@pytest.mark.django_db(transaction=True, databases="__all__")
def test_incompatible_legacy_reference_aborts_without_overwriting(fixture_database: Any) -> None:
    with fixture_database.cursor() as cursor:
        cursor.execute("INSERT INTO grupo_lista(nroGrupo,nombre) VALUES(57,'Otro grupo')")
    with pytest.raises(CommandError, match="referencia"), transaction.atomic():
        _registry(fixture_database).ensure_legacy(
            "reference.g57",
            "grupo_lista",
            "nroGrupo",
            {"nroGrupo": 57},
            {"nroGrupo": 57, "nombre": "G57"},
            reference=True,
        )
    with fixture_database.cursor() as cursor:
        cursor.execute("SELECT nombre FROM grupo_lista WHERE nroGrupo=57")
        assert cursor.fetchone() == ("Otro grupo",)
