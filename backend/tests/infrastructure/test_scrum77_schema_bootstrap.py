"""Preparación protegida, repetición y rechazo de divergencias sobre MySQL real."""

import importlib
import json
from collections.abc import Iterator
from copy import deepcopy
from io import StringIO
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import OperationalError, connections, transaction
from django.db.migrations.executor import MigrationExecutor

from tests.infrastructure.scratch_routing import route_default_to_scratch

DDL_PATH = Path(__file__).resolve().parents[2] / "core/sql/scrum77_legacy_schema.sql"
DATA_MIGRATION = "0004_recalculate_social_categories"


def _category_migration_state(database: Any) -> tuple[Any, list[tuple[str, str]]]:
    executor = MigrationExecutor(database)
    other_targets = [node for node in executor.loader.graph.leaf_nodes() if node[0] != "socios"]
    targets = other_targets + [("socios", "0003_local_social_categories")]
    executor.migrate(targets)
    return executor.loader.project_state(targets).apps, other_targets


def _historical_members(apps: Any, pairs: list[tuple[int | None, str]]) -> list[Any]:
    user_model = apps.get_model("auth", "User")
    socio_model = apps.get_model("socios", "Socio")
    subcommission = apps.get_model("socios", "Subcomision").objects.create(name="Histórica")
    members = []
    for index, (year, category) in enumerate(pairs):
        user = user_model.objects.create(
            username=f"recalculate-{index}",
            password=make_password("Synthetic-category-33"),
            email=f"recalculate-{index}@aveit.test",
            is_staff=index % 2 == 0,
            is_active=index % 2 != 0,
        )
        members.append(
            socio_model.objects.create(
                user=user,
                legajo=f"REC-{index}",
                first_name="Socio",
                last_name="Sintético",
                email=f"recalculate-{index}@aveit.test",
                subcomision=subcommission,
                social_year=year,
                category=category,
                role=["SOCIO", "TD", "CD"][index % 3],
                is_enabled=index % 2 == 0,
            )
        )
    return members


def _business_data(database: Any) -> dict[str, tuple[Any, ...]]:
    """Comparar filas de todas las tablas, excepto registro de migraciones y categorías."""
    with database.cursor() as cursor:
        cursor.execute("SHOW FULL TABLES WHERE Table_type='BASE TABLE'")
        names = [row[0] for row in cursor.fetchall() if row[0] != "django_migrations"]
        result = {}
        for name in names:
            cursor.execute(f"SELECT * FROM {database.ops.quote_name(name)}")
            columns = [column[0] for column in cursor.description]
            rows = cursor.fetchall()
            if name == "socios_socio":
                category_index = columns.index("category")
                rows = [row[:category_index] + row[category_index + 1 :] for row in rows]
            result[name] = tuple(sorted(rows, key=repr))
    return result


def _historical_links(apps: Any, database: Any, members: list[Any]) -> None:
    case = apps.get_model("expedientes", "Expediente").objects.create(
        numero="REC-33/2026", socio=members[2], motivo="Historial sintético"
    )
    case.socios.add(*members)
    descargo = apps.get_model("expedientes", "DescargoExpediente")
    descargo.objects.create(
        expediente=case,
        socio=members[2],
        tipo=descargo._meta.get_field("tipo").choices[0][0],
        causal="Fixture histórica",
        texto="Descargo sintético conservado",
    )
    audit = apps.get_model("expedientes", "CambioEstadoExpediente")
    states = audit._meta.get_field("estado_anterior").choices
    audit.objects.create(
        expediente=case,
        estado_anterior=states[0][0],
        estado_nuevo=case.estado,
        actor="recalculate-2",
        motivo="Auditoría sintética conservada",
    )
    group = apps.get_model("auth", "Group").objects.create(name="Histórico")
    members[2].user.groups.add(group)
    snapshot = {"id": 770033, "category": "PASSIVE", "social_year": 3}
    apps.get_model("expedientes", "SolicitudT01").objects.create(
        solicitante=members[2],
        destinatario_socio_id=770033,
        destinatarios_socios_ids=[770033],
        tipo_accion="SANCTION",
        estado="ISSUED",
        expediente=case,
        snapshot_destinatario=snapshot,
        snapshots_destinatarios=[snapshot],
        snapshot_emitido={"destinatarios": [snapshot], "category": "PASSIVE"},
    )
    # Sólo INSERT en un scratch propio: nroSocio institucional distinto de la PK local.
    with database.cursor() as cursor:
        for table, key in [
            ("socio_tipodocumento", "codTipoDoc"),
            ("socio_sexo", "codSexo"),
            ("socio_tiposubcomision", "codSubcomision"),
            ("socio_tipoSocio", "idTipoSocio"),
        ]:
            cursor.execute(f"INSERT INTO `{table}` (`{key}`, nombre) VALUES (1, 'Sintético')")
        cursor.execute(
            "INSERT INTO socio_lista "
            "(nroSocio, apellido, nombre, fechaIngreso, codTipoDoc, nroDoc, fechaNac, "
            "codSexo, codSubcomision, anoSocial, idTipoSocio, user_id) "
            "VALUES (770033, 'Sintético', 'Institucional', '2024-01-01', 1, 0, "
            "'2000-01-01', 1, 1, 3, 1, %s)",
            [members[2].user_id],
        )
        cursor.execute(
            "INSERT INTO tribunal_valorsancion (idSancion, nombre, valor) "
            "VALUES (1, 'Sintético', 2.5)"
        )
        cursor.execute(
            "INSERT INTO tribunal_datosresolucion "
            "(idDatosResolucion, reglamento1, consideracion, responsable1_id) "
            "VALUES (1, 'Fixture', 'Resolución sintética', 770033)"
        )
        cursor.execute(
            "INSERT INTO tribunal_expediente "
            "(idExpediente, nroExpediente, puntos_id, dataRes_id) VALUES (1, 'R33/2026', 1, 1)"
        )
        cursor.execute(
            "INSERT INTO tribunal_puntajeaplicado (puntajeAplicado, socio_id, expediente_id) "
            "VALUES (2.5, 770033, 1)"
        )
        cursor.execute(
            "INSERT INTO tribunal_puntajegeneral (socio_id, puntos, llamadosAtencion) "
            "VALUES (770033, 2.5, 1)"
        )


@pytest.mark.django_db(transaction=True)
def test_category_data_migration_preserves_history_and_repeats(bootstrap_database: Any) -> None:
    _bootstrap().prepare_schema(bootstrap_database)
    apps, other_targets = _category_migration_state(bootstrap_database)
    pairs = [
        (1, "PASSIVE"),
        (2, "ACTIVE"),
        (3, "PASSIVE"),
        (4, "ACTIVE"),
        (5, "PASSIVE"),
        (6, "ACTIVE"),
        (1, "JUNIOR"),
        (3, "SENIOR"),
        (None, "EX_TRAVELER"),
    ]
    members = _historical_members(apps, pairs)
    _historical_links(apps, bootstrap_database, members)
    original_data = _business_data(bootstrap_database)
    original_schema = _snapshot(bootstrap_database)
    original_schema.pop("django_migrations")
    targets = other_targets + [("socios", DATA_MIGRATION)]

    executor = MigrationExecutor(bootstrap_database)
    executor.migrate(targets)
    migrated_apps = executor.loader.project_state(targets).apps
    socio = migrated_apps.get_model("socios", "Socio")
    assert list(socio.objects.order_by("pk").values_list("social_year", "category")) == [
        (1, "JUNIOR"),
        (2, "JUNIOR"),
        (3, "SENIOR"),
        (4, "SENIOR"),
        (5, "SENIOR"),
        (6, "SENIOR"),
        (1, "JUNIOR"),
        (3, "SENIOR"),
        (None, "EX_TRAVELER"),
    ]
    # Booleano para no imprimir credenciales en un eventual fallo de pytest.
    preserved = _business_data(bootstrap_database) == original_data
    assert preserved
    migrated_schema = _snapshot(bootstrap_database)
    migrated_schema.pop("django_migrations")
    assert migrated_schema == original_schema

    module = importlib.import_module(f"socios.migrations.{DATA_MIGRATION}")
    updates = []

    def observe_updates(execute: Any, sql: str, params: Any, many: bool, context: Any) -> Any:
        if sql.lstrip().upper().startswith("UPDATE"):
            updates.append(sql)
        return execute(sql, params, many, context)

    with bootstrap_database.execute_wrapper(observe_updates):
        with bootstrap_database.schema_editor() as editor:
            module.recalculate_categories(migrated_apps, editor)
    assert updates == [], (
        "La repetición ejecuta el cuerpo; no alcanza con omitir una migración aplicada."
    )
    preserved = _business_data(bootstrap_database) == original_data
    assert preserved

    executor = MigrationExecutor(bootstrap_database)
    executor.migrate(other_targets + [("socios", "0003_local_social_categories")])
    assert list(socio.objects.order_by("pk").values_list("social_year", "category")) == [
        (1, "PASSIVE"),
        (2, "PASSIVE"),
        (3, "PASSIVE"),
        (4, "ACTIVE"),
        (5, "ACTIVE"),
        (6, "ACTIVE"),
        (1, "PASSIVE"),
        (3, "PASSIVE"),
        (None, "EX_TRAVELER"),
    ]
    preserved = _business_data(bootstrap_database) == original_data
    assert preserved
    reversed_schema = _snapshot(bootstrap_database)
    reversed_schema.pop("django_migrations")
    assert reversed_schema == original_schema
    MigrationExecutor(bootstrap_database).migrate(targets)
    assert list(socio.objects.order_by("pk").values_list("category", flat=True)) == [
        "JUNIOR",
        "JUNIOR",
        "SENIOR",
        "SENIOR",
        "SENIOR",
        "SENIOR",
        "JUNIOR",
        "SENIOR",
        "EX_TRAVELER",
    ]


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("reverse", [False, True], ids=["forward", "reverse"])
@pytest.mark.parametrize(
    "category, year",
    [
        ("UNKNOWN", 3),
        ("", 3),
        ("junior", 1),
        ("PASSIVE", None),
        ("PASSIVE", 0),
        ("ACTIVE", 7),
        ("EX_TRAVELER", 3),
        ("ex_traveler", None),
        ("EX_TRAVELER ", None),
    ],
)
def test_category_data_migration_rejects_anomalies_before_updates(
    bootstrap_database: Any, category: str, year: int | None, reverse: bool
) -> None:
    apps, _ = _category_migration_state(bootstrap_database)
    # Simular historial corrupto sólo en la base descartable de esta prueba.
    with bootstrap_database.cursor() as cursor:
        cursor.execute("ALTER TABLE socios_socio DROP CHECK socios_category_social_year_ck")
    _historical_members(apps, [(1, "PASSIVE"), (3, "PASSIVE"), (year, category)])
    socio = apps.get_model("socios", "Socio")
    original = list(socio.objects.order_by("pk").values())
    original_schema = _snapshot(bootstrap_database)
    updates = []

    def observe_updates(execute: Any, sql: str, params: Any, many: bool, context: Any) -> Any:
        if sql.lstrip().upper().startswith("UPDATE"):
            updates.append(sql)
        return execute(sql, params, many, context)

    module = importlib.import_module(f"socios.migrations.{DATA_MIGRATION}")
    operation = module.restore_legacy_categories if reverse else module.recalculate_categories
    with bootstrap_database.execute_wrapper(observe_updates):
        with bootstrap_database.schema_editor() as editor:
            with pytest.raises(RuntimeError, match="antes de recategorizar"):
                operation(apps, editor)
    assert updates == []
    assert list(socio.objects.order_by("pk").values()) == original
    assert _snapshot(bootstrap_database) == original_schema


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("reverse", [False, True], ids=["forward", "reverse"])
def test_category_data_migration_rolls_back_after_executed_update(
    bootstrap_database: Any, reverse: bool
) -> None:
    apps, other_targets = _category_migration_state(bootstrap_database)
    _historical_members(apps, [(1, "PASSIVE"), (3, "PASSIVE"), (6, "ACTIVE")])
    new_targets = other_targets + [("socios", DATA_MIGRATION)]
    old_targets = other_targets + [("socios", "0003_local_social_categories")]
    if reverse:
        MigrationExecutor(bootstrap_database).migrate(new_targets)
    socio = apps.get_model("socios", "Socio")
    original = list(socio.objects.order_by("pk").values())
    original_schema = _snapshot(bootstrap_database)
    updated_before_failure = False

    def fail_after_write(execute: Any, sql: str, params: Any, many: bool, context: Any) -> Any:
        nonlocal updated_before_failure
        result = execute(sql, params, many, context)
        if sql.lstrip().upper().startswith("UPDATE") and "socios_socio" in sql:
            updated_before_failure = list(socio.objects.order_by("pk").values()) != original
            raise OperationalError("Fallo simulado después de recategorizar")
        return result

    with bootstrap_database.execute_wrapper(fail_after_write):
        with pytest.raises(OperationalError, match="Fallo simulado después"):
            MigrationExecutor(bootstrap_database).migrate(old_targets if reverse else new_targets)
    assert updated_before_failure, "El fallo debe ocurrir después de una escritura real."
    assert list(socio.objects.order_by("pk").values()) == original
    assert _snapshot(bootstrap_database) == original_schema
    applied = MigrationExecutor(bootstrap_database).loader.applied_migrations
    assert (("socios", DATA_MIGRATION) in applied) is reverse
    MigrationExecutor(bootstrap_database).migrate(old_targets if reverse else new_targets)
    assert list(socio.objects.order_by("pk").values_list("category", flat=True)) == (
        ["PASSIVE", "PASSIVE", "ACTIVE"] if reverse else ["JUNIOR", "SENIOR", "SENIOR"]
    )


@pytest.mark.django_db(transaction=True)
def test_local_category_choices_migration_preserves_history_and_schema(
    bootstrap_database: Any,
) -> None:
    """TS77.32: cambiar opciones sin ejecutar el recálculo histórico de TS77.33."""
    executor = MigrationExecutor(bootstrap_database)
    other_targets = [node for node in executor.loader.graph.leaf_nodes() if node[0] != "socios"]
    old_target = other_targets + [("socios", "0002_ex_traveler_representation")]
    new_target = other_targets + [("socios", "0003_local_social_categories")]
    executor.migrate(old_target)
    old_apps = executor.loader.project_state(old_target).apps
    old_user = old_apps.get_model("auth", "User")
    old_socio = old_apps.get_model("socios", "Socio")
    for index, (year, category) in enumerate(
        [(3, "PASSIVE"), (6, "ACTIVE"), (None, "EX_TRAVELER")]
    ):
        user = old_user.objects.create(username=f"category-{index}", password="!")
        old_socio.objects.create(
            user=user,
            legajo=f"CAT-{index}",
            first_name="Socio",
            last_name="Ficticio",
            email=f"category-{index}@aveit.test",
            social_year=year,
            category=category,
            role="CD",
            is_enabled=False,
        )
    original = list(old_socio.objects.order_by("pk").values())
    credentials = list(old_user.objects.order_by("pk").values_list("pk", "password"))
    old_case = old_apps.get_model("expedientes", "Expediente")
    members = list(old_socio.objects.order_by("pk"))
    case = old_case.objects.create(numero="CAT-32/2026", socio=members[0], motivo="Fixture")
    case.socios.add(*members)
    original_cases = list(old_case.objects.values())
    original_links = list(old_case.socios.through.objects.values())
    original_schema = _snapshot(bootstrap_database)
    original_schema.pop("django_migrations")

    executor = MigrationExecutor(bootstrap_database)
    executor.migrate(new_target)
    new_apps = executor.loader.project_state(new_target).apps
    new_socio = new_apps.get_model("socios", "Socio")
    new_user = new_apps.get_model("auth", "User")
    new_case = new_apps.get_model("expedientes", "Expediente")
    assert list(new_socio._meta.get_field("category").choices) == [
        ("JUNIOR", "Junior"),
        ("SENIOR", "Senior"),
        ("EX_TRAVELER", "Exviajero"),
    ]
    assert list(new_socio.objects.order_by("pk").values()) == original
    credentials_preserved = (
        list(new_user.objects.order_by("pk").values_list("pk", "password")) == credentials
    )
    assert credentials_preserved
    assert list(new_case.objects.values()) == original_cases
    assert list(new_case.socios.through.objects.values()) == original_links
    new_schema = _snapshot(bootstrap_database)
    new_schema.pop("django_migrations")
    assert new_schema == original_schema

    from socios.models import Socio

    current = Socio.objects.using(bootstrap_database.alias).get(pk=members[0].pk)
    current.save(using=bootstrap_database.alias, update_fields=["category"])
    current.refresh_from_db(using=bootstrap_database.alias)
    assert (current.social_year, current.category) == (3, "SENIOR")
    assert (current.role, current.is_enabled) == ("CD", False)
    after_selected_save = list(new_socio.objects.order_by("pk").values())

    executor = MigrationExecutor(bootstrap_database)
    executor.migrate(old_target)
    reversed_socio = executor.loader.project_state(old_target).apps.get_model("socios", "Socio")
    assert list(reversed_socio.objects.order_by("pk").values()) == after_selected_save
    reversed_schema = _snapshot(bootstrap_database)
    reversed_schema.pop("django_migrations")
    assert reversed_schema == original_schema


@pytest.mark.django_db(transaction=True)
def test_local_ex_traveler_migration_preserves_existing_socios(bootstrap_database: Any) -> None:
    """TS77.31: ampliar representación sin recategorizar ni reemplazar identidades."""
    executor = MigrationExecutor(bootstrap_database)
    other_targets = [node for node in executor.loader.graph.leaf_nodes() if node[0] != "socios"]
    old_target = other_targets + [("socios", "0001_initial")]
    new_target = other_targets + [("socios", "0002_ex_traveler_representation")]
    executor.migrate(old_target)
    old_apps = executor.loader.project_state(old_target).apps
    old_user = old_apps.get_model("auth", "User")
    old_socio = old_apps.get_model("socios", "Socio")
    subcomision = old_apps.get_model("socios", "Subcomision").objects.create(name="Demo")
    for year, category in [(3, "PASSIVE"), (6, "ACTIVE")]:
        user = old_user.objects.create(username=f"migration-{year}", password="!")
        old_socio.objects.create(
            user=user,
            legajo=f"MIG-{year}",
            first_name="Socio",
            last_name="Ficticio",
            email=f"migration-{year}@aveit.test",
            subcomision=subcomision,
            social_year=year,
            category=category,
            role="CD",
            is_enabled=False,
        )
    original = list(old_socio.objects.order_by("pk").values())
    credentials = list(old_user.objects.order_by("pk").values_list("pk", "password"))
    old_case = old_apps.get_model("expedientes", "Expediente")
    members = list(old_socio.objects.order_by("pk"))
    case = old_case.objects.create(numero="MIG-31/2026", socio=members[0], motivo="Fixture")
    case.socios.add(*members)
    original_cases = list(old_case.objects.values())
    original_links = list(old_case.socios.through.objects.values())

    executor = MigrationExecutor(bootstrap_database)
    executor.migrate(new_target)
    new_apps = executor.loader.project_state(new_target).apps
    new_socio = new_apps.get_model("socios", "Socio")
    new_user = new_apps.get_model("auth", "User")

    assert list(new_socio.objects.order_by("pk").values()) == original
    credentials_preserved = (
        list(new_user.objects.order_by("pk").values_list("pk", "password")) == credentials
    )
    assert credentials_preserved
    new_case = new_apps.get_model("expedientes", "Expediente")
    assert list(new_case.objects.values()) == original_cases
    assert list(new_case.socios.through.objects.values()) == original_links
    user = new_user.objects.create(username="migration-ex-traveler", password="!")
    ex_traveler = new_socio.objects.create(
        user=user,
        legajo="MIG-EX",
        first_name="Socio",
        last_name="Exviajero",
        email="migration-ex-traveler@aveit.test",
        subcomision_id=subcomision.pk,
        social_year=None,
        category="EX_TRAVELER",
        role="SOCIO",
        is_enabled=True,
    )
    ex_traveler.refresh_from_db()
    assert (ex_traveler.category, ex_traveler.social_year) == ("EX_TRAVELER", None)
    assert ex_traveler.get_category_display() == "Exviajero"


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("invalid_year", [0, 7])
def test_ex_traveler_migration_rejects_invalid_history_before_ddl(
    bootstrap_database: Any, invalid_year: int
) -> None:
    old_target = [("socios", "0001_initial")]
    new_target = [("socios", "0002_ex_traveler_representation")]
    executor = MigrationExecutor(bootstrap_database)
    executor.migrate(old_target)
    old_apps = executor.loader.project_state(old_target).apps
    user = old_apps.get_model("auth", "User").objects.create(username="invalid", password="!")
    old_socio = old_apps.get_model("socios", "Socio")
    old_socio.objects.create(
        user=user,
        legajo="MIG-INVALID",
        first_name="Socio",
        last_name="Ficticio",
        email="invalid-migration@aveit.test",
        social_year=invalid_year,
        category="PASSIVE",
        role="SOCIO",
        is_enabled=True,
    )
    original_schema = _snapshot(bootstrap_database)
    original_data = list(old_socio.objects.values())

    with pytest.raises(RuntimeError, match="antes de alterar"):
        MigrationExecutor(bootstrap_database).migrate(new_target)

    assert _snapshot(bootstrap_database) == original_schema
    assert list(old_socio.objects.values()) == original_data


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("category, social_year", [("EX_TRAVELER", None), ("OTHER_STATUS", 3)])
def test_ex_traveler_migration_reversal_rejects_data_loss_before_ddl(
    bootstrap_database: Any, category: str, social_year: int | None
) -> None:
    new_target = [("socios", "0002_ex_traveler_representation")]
    old_target = [("socios", "0001_initial")]
    executor = MigrationExecutor(bootstrap_database)
    executor.migrate(new_target)
    apps = executor.loader.project_state(new_target).apps
    user = apps.get_model("auth", "User").objects.create(username="reverse-ex", password="!")
    socio = apps.get_model("socios", "Socio")
    socio.objects.create(
        user=user,
        legajo="MIG-REVERSE",
        first_name="Socio",
        last_name="Exviajero",
        email="reverse-ex@aveit.test",
        social_year=social_year,
        category=category,
        role="TD",
        is_enabled=False,
    )
    original_schema = _snapshot(bootstrap_database)
    original_data = list(socio.objects.values())

    with pytest.raises(RuntimeError, match="antes de revertir"):
        MigrationExecutor(bootstrap_database).migrate(old_target)

    assert _snapshot(bootstrap_database) == original_schema
    assert list(socio.objects.values()) == original_data


@pytest.mark.django_db(transaction=True)
def test_ex_traveler_migration_reversal_preserves_compatible_rows(
    bootstrap_database: Any,
) -> None:
    new_target = [("socios", "0002_ex_traveler_representation")]
    old_target = [("socios", "0001_initial")]
    executor = MigrationExecutor(bootstrap_database)
    executor.migrate(new_target)
    apps = executor.loader.project_state(new_target).apps
    user = apps.get_model("auth", "User").objects.create(username="reverse-normal", password="!")
    socio = apps.get_model("socios", "Socio")
    socio.objects.create(
        user=user,
        legajo="MIG-NORMAL",
        first_name="Socio",
        last_name="Ficticio",
        email="reverse-normal@aveit.test",
        social_year=3,
        category="PASSIVE",
        role="CD",
        is_enabled=True,
    )
    original_data = list(socio.objects.values())
    executor = MigrationExecutor(bootstrap_database)
    executor.migrate(old_target)
    old_socio = executor.loader.project_state(old_target).apps.get_model("socios", "Socio")
    assert list(old_socio.objects.values()) == original_data
    with bootstrap_database.cursor() as cursor:
        cursor.execute(
            "SELECT IS_NULLABLE, CHARACTER_MAXIMUM_LENGTH FROM information_schema.COLUMNS "
            "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'socios_socio' "
            "AND COLUMN_NAME IN ('category', 'social_year') ORDER BY COLUMN_NAME"
        )
        assert cursor.fetchall() == (("NO", 10), ("NO", None))


@pytest.fixture
def guarded_transition(monkeypatch: pytest.MonkeyPatch) -> Any:
    module = importlib.import_module("core.management.commands.transition_demo_schema")
    for name in ("_check_configuration", "_check_mysql", "_check_http_health"):
        monkeypatch.setattr(module.preflight, name, MagicMock())
    monkeypatch.setattr(
        module,
        "transition_social_year_schema",
        MagicMock(return_value={"altered_columns": ["socio_lista.anoSocial"], "row_count": 0}),
    )
    return module


@pytest.mark.parametrize("guard", ["_check_configuration", "_check_mysql", "_check_http_health"])
def test_transition_command_rejects_failed_preflight_before_any_write(
    guarded_transition: Any, guard: str
) -> None:
    getattr(guarded_transition.preflight, guard).side_effect = CommandError("Demo inválida")
    with pytest.raises(CommandError, match="Demo inválida"):
        call_command("transition_demo_schema", stdout=StringIO())
    guarded_transition.transition_social_year_schema.assert_not_called()


def test_transition_command_reports_success(guarded_transition: Any) -> None:
    output = StringIO()
    call_command("transition_demo_schema", stdout=output)
    assert json.loads(output.getvalue()) == {
        "status": "ok",
        "altered_columns": ["socio_lista.anoSocial"],
        "row_count": 0,
    }
    guarded_transition.transition_social_year_schema.assert_called_once()


def test_transition_command_redacts_driver_error_and_does_not_promise_rollback(
    guarded_transition: Any,
) -> None:
    guarded_transition.transition_social_year_schema.side_effect = OperationalError(
        "sentinel-private-password"
    )
    with pytest.raises(CommandError) as error:
        call_command("transition_demo_schema", stdout=StringIO())
    assert "sentinel-private-password" not in str(error.value)
    assert "aplicado" in str(error.value)


def test_transition_command_rejects_an_alternate_database(guarded_transition: Any) -> None:
    with pytest.raises(TypeError, match="database"):
        call_command("transition_demo_schema", database="other", stdout=StringIO())
    guarded_transition.transition_social_year_schema.assert_not_called()


def _transition_database(database: Any, *, nullable: bool = False) -> Any:
    module = _bootstrap()
    module.prepare_schema(database)
    if not nullable:
        with database.cursor() as cursor:
            cursor.execute("ALTER TABLE socio_lista MODIFY anoSocial INT NOT NULL")
    return module


def _transition_writes(writes: list[str]) -> Any:
    def observe(execute: Any, sql: str, params: Any, many: bool, context: Any) -> Any:
        if sql.lstrip().split()[0].upper() in {
            "CREATE",
            "ALTER",
            "DROP",
            "INSERT",
            "UPDATE",
            "DELETE",
            "TRUNCATE",
            "REPLACE",
        }:
            writes.append(sql)
        return execute(sql, params, many, context)

    return observe


@pytest.mark.django_db(transaction=True, databases="__all__")
def test_transition_preserves_all_business_data_and_repeats_without_writes(
    bootstrap_database: Any,
) -> None:
    module = _transition_database(bootstrap_database)
    executor = MigrationExecutor(bootstrap_database)
    apps = executor.loader.project_state(executor.loader.graph.leaf_nodes()).apps
    members = _historical_members(
        apps, [(1, "JUNIOR"), (6, "SENIOR"), (3, "SENIOR"), (None, "EX_TRAVELER")]
    )
    _historical_links(apps, bootstrap_database, members)
    with bootstrap_database.cursor() as cursor:
        cursor.execute("ALTER TABLE socio_lista AUTO_INCREMENT=880033")
    before_data = _business_data(bootstrap_database)
    socio = apps.get_model("socios", "Socio")
    before_socios = list(socio.objects.order_by("pk").values())
    before = _snapshot(bootstrap_database)
    writes = []
    with bootstrap_database.execute_wrapper(_transition_writes(writes)):
        report = module.transition_social_year_schema(bootstrap_database)
    assert report == {
        "altered_columns": ["socio_lista.anoSocial"],
        "row_count": 1,
        "legacy_tables": 27,
        "foreign_keys": 39,
        "foreign_key_checks": True,
    }
    assert len(writes) == 1 and writes[0].lstrip().upper().startswith("ALTER TABLE")
    after = _snapshot(bootstrap_database)
    assert after.pop("socio_lista") == before.pop("socio_lista").replace(
        "`anoSocial` int NOT NULL", "`anoSocial` int DEFAULT NULL"
    )
    assert after == before
    preserved = _business_data(bootstrap_database) == before_data
    assert preserved
    assert list(socio.objects.order_by("pk").values()) == before_socios
    assert module.validate_existing_schema(bootstrap_database, module.read_contracts()) == []
    complete_schema = _snapshot(bootstrap_database)
    writes.clear()
    with bootstrap_database.execute_wrapper(_transition_writes(writes)):
        repeated = module.transition_social_year_schema(bootstrap_database)
    assert repeated == {**report, "altered_columns": []}
    assert writes == []
    assert _snapshot(bootstrap_database) == complete_schema
    preserved = _business_data(bootstrap_database) == before_data
    assert preserved


@pytest.mark.django_db(transaction=True, databases="__all__")
def test_transition_on_current_empty_contract_is_read_only(bootstrap_database: Any) -> None:
    module = _transition_database(bootstrap_database, nullable=True)
    before = _snapshot(bootstrap_database)
    writes = []
    with bootstrap_database.execute_wrapper(_transition_writes(writes)):
        report = module.transition_social_year_schema(bootstrap_database)
    assert report["altered_columns"] == []
    assert report["row_count"] == 0
    assert writes == []
    assert _snapshot(bootstrap_database) == before


@pytest.mark.django_db(transaction=True, databases="__all__")
@pytest.mark.parametrize("fail_read", [False, True], ids=["current_counter", "read_failure"])
def test_transition_identity_bypasses_warm_statistics_and_restores_session(
    bootstrap_database: Any, fail_read: bool
) -> None:
    module = _transition_database(bootstrap_database)
    executor = MigrationExecutor(bootstrap_database)
    apps = executor.loader.project_state(executor.loader.graph.leaf_nodes()).apps
    members = _historical_members(apps, [(1, "JUNIOR"), (6, "SENIOR"), (3, "SENIOR")])
    with bootstrap_database.cursor() as cursor:
        cursor.execute("SELECT @@session.information_schema_stats_expiry")
        original_expiry = cursor.fetchone()[0]
        cursor.execute("SET SESSION information_schema_stats_expiry=86400")
        cursor.execute(
            "SELECT AUTO_INCREMENT FROM information_schema.TABLES "
            "WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='socio_lista'"
        )
        cursor.fetchone()
    try:
        _historical_links(apps, bootstrap_database, members)

        def fail_counter(execute: Any, sql: str, params: Any, many: bool, context: Any) -> Any:
            if sql.startswith("SELECT AUTO_INCREMENT"):
                raise OperationalError("Fallo simulado al leer el contador")
            return execute(sql, params, many, context)

        if fail_read:
            with bootstrap_database.execute_wrapper(fail_counter):
                with pytest.raises(OperationalError, match="leer el contador"):
                    module._social_year_identity(bootstrap_database)
        else:
            rows, counter = module._social_year_identity(bootstrap_database)
            assert len(rows) == 1
            assert counter == 770034
            with bootstrap_database.cursor() as cursor:
                cursor.execute("SHOW CREATE TABLE socio_lista")
                assert f"AUTO_INCREMENT={counter}" in cursor.fetchone()[1]
        with bootstrap_database.cursor() as cursor:
            cursor.execute("SELECT @@session.information_schema_stats_expiry")
            assert cursor.fetchone() == (86400,)
    finally:
        with bootstrap_database.cursor() as cursor:
            cursor.execute("SET SESSION information_schema_stats_expiry=%s", [original_expiry])


@pytest.mark.django_db(transaction=True, databases="__all__")
@pytest.mark.parametrize("nullable", [False, True], ids=["previous", "current"])
@pytest.mark.parametrize(
    "change", ["year_default", "other_nullable", "late_precision", "foreign_key"]
)
def test_transition_rejects_any_other_divergence_before_writes(
    bootstrap_database: Any, nullable: bool, change: str
) -> None:
    module = _transition_database(bootstrap_database, nullable=nullable)
    year_nullability = "NULL" if nullable else "NOT NULL"
    mutations = {
        "year_default": (
            f"ALTER TABLE socio_lista MODIFY anoSocial INT {year_nullability} DEFAULT 2"
        ),
        "other_nullable": "ALTER TABLE socio_lista MODIFY codSubcomision INT NULL",
        "late_precision": (
            "ALTER TABLE tribunal_puntajegeneral MODIFY puntos DECIMAL(11,2) NOT NULL DEFAULT 0"
        ),
        "foreign_key": "ALTER TABLE tribunal_puntajegeneral DROP FOREIGN KEY fk_ptjgral_socio",
    }
    with bootstrap_database.cursor() as cursor:
        cursor.execute(mutations[change])
    before = _snapshot(bootstrap_database)
    writes = []
    with bootstrap_database.execute_wrapper(_transition_writes(writes)):
        with pytest.raises(CommandError):
            module.transition_social_year_schema(bootstrap_database)
    assert writes == []
    assert _snapshot(bootstrap_database) == before


@pytest.mark.django_db(transaction=True, databases="__all__")
@pytest.mark.parametrize("partial", [False, True], ids=["empty", "partial"])
def test_transition_requires_a_complete_prepared_closure(
    bootstrap_database: Any, partial: bool
) -> None:
    module = _bootstrap()
    if partial:
        _transition_database(bootstrap_database)
        with bootstrap_database.cursor() as cursor:
            cursor.execute("DROP TABLE socio_email")
    before = _snapshot(bootstrap_database)
    writes = []
    with bootstrap_database.execute_wrapper(_transition_writes(writes)):
        with pytest.raises(CommandError, match="cierre completo"):
            module.transition_social_year_schema(bootstrap_database)
    assert writes == []
    assert _snapshot(bootstrap_database) == before


@pytest.mark.django_db(transaction=True, databases="__all__")
def test_transition_shares_the_preparation_lock(bootstrap_database: Any) -> None:
    module = _transition_database(bootstrap_database)
    before = _snapshot(bootstrap_database)
    peer = bootstrap_database.copy(alias="scrum77_transition_peer")
    lock_name = f"scrum77-schema:{bootstrap_database.settings_dict['NAME']}"
    try:
        with peer.cursor() as cursor:
            cursor.execute("SELECT GET_LOCK(%s, 0)", [lock_name])
            assert cursor.fetchone() == (1,)
        with pytest.raises(CommandError, match="otra preparación"):
            module.transition_social_year_schema(bootstrap_database)
        assert _snapshot(bootstrap_database) == before
    finally:
        with peer.cursor() as cursor:
            cursor.execute("SELECT RELEASE_LOCK(%s)", [lock_name])
        peer.close()


@pytest.mark.django_db(transaction=True, databases="__all__")
@pytest.mark.parametrize("session", ["atomic", "autocommit", "foreign_keys"])
def test_transition_rejects_an_incompatible_session(bootstrap_database: Any, session: str) -> None:
    module = _transition_database(bootstrap_database)
    before = _snapshot(bootstrap_database)
    writes = []
    try:
        with bootstrap_database.execute_wrapper(_transition_writes(writes)):
            if session == "atomic":
                with transaction.atomic(using=bootstrap_database.alias):
                    with pytest.raises(CommandError, match="autocommit"):
                        module.transition_social_year_schema(bootstrap_database)
            else:
                if session == "autocommit":
                    bootstrap_database.set_autocommit(False)
                else:
                    with bootstrap_database.cursor() as cursor:
                        cursor.execute("SET SESSION foreign_key_checks=0")
                with pytest.raises(CommandError):
                    module.transition_social_year_schema(bootstrap_database)
    finally:
        bootstrap_database.rollback()
        bootstrap_database.set_autocommit(True)
        with bootstrap_database.cursor() as cursor:
            cursor.execute("SET SESSION foreign_key_checks=1")
    assert writes == []
    assert _snapshot(bootstrap_database) == before


@pytest.mark.django_db(transaction=True, databases="__all__")
def test_transition_after_executed_ddl_failure_can_retry_without_rollback_claim(
    bootstrap_database: Any,
) -> None:
    module = _transition_database(bootstrap_database)
    before_data = _business_data(bootstrap_database)
    executed = False

    def fail_after_alter(execute: Any, sql: str, params: Any, many: bool, context: Any) -> Any:
        nonlocal executed
        result = execute(sql, params, many, context)
        if sql.lstrip().upper().startswith("ALTER TABLE"):
            executed = True
            raise OperationalError("Fallo después del ALTER real")
        return result

    with bootstrap_database.execute_wrapper(fail_after_alter):
        with pytest.raises(OperationalError, match="después del ALTER"):
            module.transition_social_year_schema(bootstrap_database)
    assert executed
    assert module.validate_existing_schema(bootstrap_database, module.read_contracts()) == []
    preserved = _business_data(bootstrap_database) == before_data
    assert preserved
    peer = bootstrap_database.copy(alias="scrum77_transition_release_peer")
    lock_name = f"scrum77-schema:{bootstrap_database.settings_dict['NAME']}"
    try:
        with peer.cursor() as cursor:
            cursor.execute("SELECT GET_LOCK(%s, 0)", [lock_name])
            assert cursor.fetchone() == (1,), "Otra conexión debe poder adquirir el bloqueo."
    finally:
        with peer.cursor() as cursor:
            cursor.execute("SELECT RELEASE_LOCK(%s)", [lock_name])
        peer.close()
    writes = []
    with bootstrap_database.execute_wrapper(_transition_writes(writes)):
        assert module.transition_social_year_schema(bootstrap_database)["altered_columns"] == []
    assert writes == []


@pytest.mark.django_db(transaction=True, databases="__all__")
def test_transition_refuses_success_if_identity_verification_differs(
    bootstrap_database: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = _transition_database(bootstrap_database)
    identity = module._social_year_identity
    calls = 0

    def inconsistent_identity(database: Any) -> Any:
        nonlocal calls
        rows, counter = identity(database)
        calls += 1
        return rows, counter if calls == 1 else (counter or 0) + 1

    monkeypatch.setattr(module, "_social_year_identity", inconsistent_identity)
    with pytest.raises(CommandError, match="acreditar"):
        module.transition_social_year_schema(bootstrap_database)
    assert module.validate_existing_schema(bootstrap_database, module.read_contracts()) == []


def _bootstrap() -> Any:
    return importlib.import_module("core.demo_schema")


@pytest.fixture
def guarded_command(monkeypatch: pytest.MonkeyPatch) -> Any:
    module = importlib.import_module("core.management.commands.prepare_demo_schema")
    for name in ("_check_configuration", "_check_mysql", "_check_http_health"):
        monkeypatch.setattr(module.preflight, name, MagicMock())
    prepare = MagicMock(return_value={"legacy_tables": 27, "created_tables": []})
    monkeypatch.setattr(module, "prepare_schema", prepare)
    return module


@pytest.mark.parametrize("guard", ["_check_configuration", "_check_mysql", "_check_http_health"])
def test_command_rejects_failed_preflight_before_any_schema_write(
    guarded_command: Any, guard: str
) -> None:
    getattr(guarded_command.preflight, guard).side_effect = CommandError("Demo inválida")
    with pytest.raises(CommandError, match="Demo inválida"):
        call_command("prepare_demo_schema", stdout=StringIO())
    guarded_command.prepare_schema.assert_not_called()


def test_command_reports_success_without_exposing_connection_secrets(guarded_command: Any) -> None:
    output = StringIO()
    call_command("prepare_demo_schema", stdout=output)
    assert json.loads(output.getvalue()) == {
        "status": "ok",
        "legacy_tables": 27,
        "created_tables": [],
    }
    guarded_command.prepare_schema.assert_called_once()


def test_command_redacts_driver_errors(guarded_command: Any) -> None:
    guarded_command.prepare_schema.side_effect = OperationalError("sentinel-private-password")
    with pytest.raises(CommandError) as error:
        call_command("prepare_demo_schema", stdout=StringIO())
    assert "sentinel-private-password" not in str(error.value)
    assert "parcial" in str(error.value).lower()


def test_invalid_ddl_cannot_be_silently_ignored(tmp_path: Path) -> None:
    source = tmp_path / "invalid.sql"
    source.write_text(
        DDL_PATH.read_text(encoding="utf-8") + "\nDELETE FROM socio_lista;", encoding="utf-8"
    )
    with pytest.raises(CommandError, match="DDL"):
        _bootstrap().read_contracts(source)


@pytest.fixture
def bootstrap_database(django_db_setup: Any, django_db_blocker: Any) -> Iterator[Any]:
    with django_db_blocker.unblock():
        parent = connections["default"]
        assert parent.vendor == "mysql"
        assert parent.settings_dict["NAME"].startswith("test_")
        alias = f"scrum77_bootstrap_{uuid4().hex[:10]}"
        database = f"test_{alias}"
        with parent.cursor() as cursor:
            cursor.execute(
                f"CREATE DATABASE `{database}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
        config = deepcopy(parent.settings_dict)
        config["NAME"] = database
        connections.databases[alias] = config
        probe = connections[alias]
        try:
            with route_default_to_scratch(probe):
                yield probe
        finally:
            probe.close()
            del connections[alias]
            del connections.databases[alias]
            with parent.cursor() as cursor:
                cursor.execute(f"DROP DATABASE `{database}`")


def _snapshot(database: Any) -> dict[str, str]:
    with database.cursor() as cursor:
        cursor.execute("SHOW FULL TABLES WHERE Table_type='BASE TABLE'")
        names = [row[0] for row in cursor.fetchall()]
        result = {}
        for name in names:
            cursor.execute(f"SHOW CREATE TABLE {database.ops.quote_name(name)}")
            result[name] = cursor.fetchone()[1]
    return result


@pytest.mark.django_db(transaction=True, databases="__all__")
def test_institutional_condition_migrates_before_the_legacy_closure(
    bootstrap_database: Any,
) -> None:
    module = _bootstrap()
    executor = MigrationExecutor(bootstrap_database)
    executor.migrate(executor.loader.graph.leaf_nodes())
    managed_only = _snapshot(bootstrap_database)
    metadata_table = "socios_institutionalmembershipcondition"
    assert metadata_table in managed_only
    assert "FOREIGN KEY" not in managed_only[metadata_table]
    assert not any(contract.name in managed_only for contract in module.read_contracts())
    with bootstrap_database.cursor() as cursor:
        cursor.execute(f"SELECT COUNT(*) FROM {metadata_table}")
        assert cursor.fetchone() == (0,)
    report = module.prepare_schema(bootstrap_database)
    assert report["migrations_applied"] == 0
    assert len(report["created_tables"]) == 27
    assert report["foreign_keys"] == 39
    assert _snapshot(bootstrap_database)[metadata_table] == managed_only[metadata_table]


@pytest.mark.django_db(transaction=True, databases="__all__")
def test_previous_social_year_contract_is_rejected_before_any_write(
    bootstrap_database: Any,
) -> None:
    """TS77.38 no habilita el contrato anterior ni inicia la transición TS77.39."""
    module = _bootstrap()
    module.prepare_schema(bootstrap_database)
    apps, _ = _category_migration_state(bootstrap_database)
    _historical_members(apps, [(3, "PASSIVE")])
    socio = apps.get_model("socios", "Socio")
    with bootstrap_database.cursor() as cursor:
        cursor.execute("ALTER TABLE socio_lista MODIFY anoSocial INT NOT NULL")
        cursor.execute("DROP TABLE socio_email")
        cursor.execute(
            "INSERT INTO grupo_lista (nroGrupo, nombre, descripcion) "
            "VALUES (63, 'Propio', 'Conservar')"
        )
    before = _snapshot(bootstrap_database)
    before_data = _business_data(bootstrap_database)
    before_socios = list(socio.objects.order_by("pk").values())
    writes = []

    def observe_writes(execute: Any, sql: str, params: Any, many: bool, context: Any) -> Any:
        if sql.lstrip().split()[0].upper() in {
            "CREATE",
            "ALTER",
            "DROP",
            "INSERT",
            "UPDATE",
            "DELETE",
        }:
            writes.append(sql)
        return execute(sql, params, many, context)

    with bootstrap_database.execute_wrapper(observe_writes):
        with pytest.raises(CommandError, match="socio_lista"):
            module.prepare_schema(bootstrap_database)
    assert writes == []
    assert _snapshot(bootstrap_database) == before
    preserved = _business_data(bootstrap_database) == before_data
    assert preserved
    assert list(socio.objects.order_by("pk").values()) == before_socios
    assert "socio_email" not in before
    assert ("socios", DATA_MIGRATION) not in MigrationExecutor(
        bootstrap_database
    ).loader.applied_migrations


@pytest.mark.django_db(transaction=True, databases="__all__")
def test_empty_bootstrap_and_second_run_preserve_schema_data_and_auth(
    bootstrap_database: Any,
) -> None:
    module = _bootstrap()
    first = module.prepare_schema(bootstrap_database)
    assert len(first["created_tables"]) == 27
    assert first["existing_tables"] == []
    assert first["legacy_tables"] == 27
    assert first["foreign_keys"] == 39
    assert first["migrations_applied"] > 0
    with bootstrap_database.cursor() as cursor:
        cursor.execute("SELECT `last_value` FROM expedientes_numero_secuencia")
        assert cursor.fetchall() == ((0,),), "RunPython debe inicializar el contador en el scratch."
    user = (
        get_user_model()
        .objects.db_manager(bootstrap_database.alias)
        .create_user(username="scrum77-demo-audit")
    )
    with bootstrap_database.cursor() as cursor:
        cursor.execute(
            "INSERT INTO grupo_lista (nroGrupo, nombre, descripcion) "
            "VALUES (63, 'Prueba propia', 'Conservar')"
        )
        cursor.execute("SELECT COUNT(*) FROM django_migrations")
        migration_count = cursor.fetchone()[0]
    before = _snapshot(bootstrap_database)
    second = module.prepare_schema(bootstrap_database)
    assert second["created_tables"] == []
    assert len(second["existing_tables"]) == 27
    assert second["migrations_applied"] == 0
    assert _snapshot(bootstrap_database) == before
    with bootstrap_database.cursor() as cursor:
        cursor.execute("SELECT nroGrupo, nombre, descripcion FROM grupo_lista")
        assert cursor.fetchall() == ((63, "Prueba propia", "Conservar"),)
        cursor.execute("SELECT id, username FROM auth_user")
        assert cursor.fetchall() == ((user.pk, "scrum77-demo-audit"),)
        cursor.execute("SELECT COUNT(*) FROM django_migrations")
        assert cursor.fetchone() == (migration_count,)
        cursor.execute("SELECT @@session.foreign_key_checks")
        assert cursor.fetchone() == (1,)


@pytest.mark.django_db(transaction=True, databases="__all__")
def test_valid_partial_bootstrap_is_completed_without_replacing_existing_rows(
    bootstrap_database: Any,
) -> None:
    module = _bootstrap()
    contracts = module.read_contracts()
    with bootstrap_database.cursor() as cursor:
        cursor.execute(contracts[0].statement)
        cursor.execute("INSERT INTO socio_tipodocumento (nombre) VALUES ('Documento propio')")
    before = _snapshot(bootstrap_database)
    report = module.prepare_schema(bootstrap_database)
    assert len(report["created_tables"]) == 26
    assert report["existing_tables"] == ["socio_tipodocumento"]
    assert _snapshot(bootstrap_database)["socio_tipodocumento"] == before["socio_tipodocumento"]
    with bootstrap_database.cursor() as cursor:
        cursor.execute("SELECT codTipoDoc, nombre FROM socio_tipodocumento")
        assert cursor.fetchall() == ((1, "Documento propio"),)


@pytest.mark.parametrize(
    "change",
    [
        "type",
        "signedness",
        "length",
        "nullability",
        "default",
        "auto_increment",
        "primary_key",
        "extra_column",
        "extra_index",
        "engine",
        "collation",
    ],
)
@pytest.mark.django_db(transaction=True, databases="__all__")
def test_late_divergence_aborts_before_migrations_or_earlier_creations(
    bootstrap_database: Any, change: str
) -> None:
    module = _bootstrap()
    original = next(
        item.statement for item in module.read_contracts() if item.name == "tribunal_afectados"
    )
    mutations = {
        "type": ("`idAfectados` int(11)", "`idAfectados` bigint"),
        "signedness": ("`idAfectados` int(11)", "`idAfectados` int unsigned"),
        "length": ("varchar(30)", "varchar(31)"),
        "nullability": ("`nombre` varchar(30) NOT NULL", "`nombre` varchar(30) DEFAULT NULL"),
        "default": (
            "`nombre` varchar(30) NOT NULL",
            "`nombre` varchar(30) NOT NULL DEFAULT 'Ajeno'",
        ),
        "auto_increment": (" AUTO_INCREMENT", ""),
        "primary_key": ("PRIMARY KEY (`idAfectados`)", "PRIMARY KEY (`idAfectados`, `nombre`)"),
        "extra_column": ("PRIMARY KEY", "`extra` int DEFAULT NULL, PRIMARY KEY"),
        "extra_index": (
            "PRIMARY KEY (`idAfectados`)",
            "PRIMARY KEY (`idAfectados`), KEY `extra_idx` (`nombre`)",
        ),
        "engine": ("ENGINE=InnoDB", "ENGINE=MyISAM"),
        "collation": ("utf8mb4_unicode_ci", "utf8mb4_0900_ai_ci"),
    }
    with bootstrap_database.cursor() as cursor:
        cursor.execute(original.replace(*mutations[change]))
    before = _snapshot(bootstrap_database)
    with pytest.raises(CommandError, match="tribunal_afectados"):
        module.prepare_schema(bootstrap_database)
    assert _snapshot(bootstrap_database) == before
    assert list(before) == ["tribunal_afectados"]


@pytest.mark.parametrize(
    "change",
    ["foreign_key_missing", "delete_action", "update_action", "unique_missing", "precision"],
)
@pytest.mark.django_db(transaction=True, databases="__all__")
def test_relational_divergences_preserve_every_existing_table(
    bootstrap_database: Any, change: str
) -> None:
    module = _bootstrap()
    module.prepare_schema(bootstrap_database)
    drop_fk = "ALTER TABLE tribunal_puntajegeneral DROP FOREIGN KEY fk_ptjgral_socio"
    add_fk = (
        "ALTER TABLE tribunal_puntajegeneral ADD CONSTRAINT fk_ptjgral_socio "
        "FOREIGN KEY (socio_id) REFERENCES socio_lista(nroSocio) "
    )
    mutations = {
        "foreign_key_missing": (drop_fk,),
        "delete_action": (drop_fk, add_fk + "ON DELETE RESTRICT"),
        "update_action": (drop_fk, add_fk + "ON DELETE CASCADE ON UPDATE CASCADE"),
        "unique_missing": (
            "ALTER TABLE tribunal_puntajegeneral DROP INDEX socio_id_unique, "
            "ADD INDEX socio_id_unique (socio_id)",
        ),
        "precision": (
            "ALTER TABLE tribunal_puntajegeneral MODIFY puntos DECIMAL(11,2) NOT NULL DEFAULT 0",
        ),
    }
    with bootstrap_database.cursor() as cursor:
        for statement in mutations[change]:
            cursor.execute(statement)
    before = _snapshot(bootstrap_database)
    with pytest.raises(CommandError, match="tribunal_puntajegeneral"):
        module.prepare_schema(bootstrap_database)
    assert _snapshot(bootstrap_database) == before


@pytest.mark.django_db(transaction=True, databases="__all__")
def test_incompatible_external_auth_is_rejected_before_any_migration(
    bootstrap_database: Any,
) -> None:
    with bootstrap_database.cursor() as cursor:
        cursor.execute(
            "CREATE TABLE auth_user (id BIGINT UNSIGNED NOT NULL PRIMARY KEY) ENGINE=InnoDB"
        )
    before = _snapshot(bootstrap_database)
    with pytest.raises(CommandError, match="auth_user"):
        _bootstrap().prepare_schema(bootstrap_database)
    assert _snapshot(bootstrap_database) == before


@pytest.mark.parametrize("table", ["auth_user", "expedientes_expediente_socios"])
@pytest.mark.django_db(transaction=True, databases="__all__")
def test_managed_table_without_migration_history_aborts_before_any_write(
    bootstrap_database: Any,
    table: str,
) -> None:
    with bootstrap_database.cursor() as cursor:
        cursor.execute(
            f"CREATE TABLE `{table}` (id INT NOT NULL AUTO_INCREMENT PRIMARY KEY) ENGINE=InnoDB"
        )
    before = _snapshot(bootstrap_database)
    with pytest.raises(CommandError, match=table):
        _bootstrap().prepare_schema(bootstrap_database)
    assert _snapshot(bootstrap_database) == before


@pytest.mark.django_db(transaction=True, databases="__all__")
def test_foreign_key_to_another_schema_is_rejected(bootstrap_database: Any) -> None:
    module = _bootstrap()
    module.prepare_schema(bootstrap_database)
    parent_name = connections.databases["default"]["NAME"]
    with bootstrap_database.cursor() as cursor:
        cursor.execute("ALTER TABLE tribunal_puntajegeneral DROP FOREIGN KEY fk_ptjgral_socio")
        cursor.execute(
            "ALTER TABLE tribunal_puntajegeneral ADD CONSTRAINT fk_ptjgral_socio "
            "FOREIGN KEY (socio_id) REFERENCES "
            f"{bootstrap_database.ops.quote_name(parent_name)}.socio_lista(nroSocio) "
            "ON DELETE CASCADE"
        )
    before = _snapshot(bootstrap_database)
    with pytest.raises(CommandError, match="tribunal_puntajegeneral"):
        module.prepare_schema(bootstrap_database)
    assert _snapshot(bootstrap_database) == before


@pytest.mark.django_db(transaction=True, databases="__all__")
def test_another_preparation_lock_prevents_any_schema_write(bootstrap_database: Any) -> None:
    peer = bootstrap_database.copy(alias="scrum77_lock_peer")
    lock_name = f"scrum77-schema:{bootstrap_database.settings_dict['NAME']}"
    try:
        with peer.cursor() as cursor:
            cursor.execute("SELECT GET_LOCK(%s, 0)", [lock_name])
            assert cursor.fetchone() == (1,)
        with pytest.raises(CommandError, match="otra preparación"):
            _bootstrap().prepare_schema(bootstrap_database)
        assert _snapshot(bootstrap_database) == {}
    finally:
        with peer.cursor() as cursor:
            cursor.execute("SELECT RELEASE_LOCK(%s)", [lock_name])
        peer.close()


@pytest.mark.django_db(transaction=True, databases="__all__")
def test_failure_preserves_partial_schema_and_allows_a_safe_retry(bootstrap_database: Any) -> None:
    module = _bootstrap()
    original = bootstrap_database.create_cursor
    failed = False

    def failing_cursor(name: str | None = None) -> Any:
        nonlocal failed
        cursor = original(name)
        execute = cursor.execute

        def execute_with_failure(sql: str, params: Any = None) -> Any:
            nonlocal failed
            if sql.startswith("CREATE TABLE `socio_sexo`") and not failed:
                failed = True
                raise OperationalError("Fallo simulado de DDL")
            return execute(sql, params)

        cursor.execute = execute_with_failure
        return cursor

    bootstrap_database.create_cursor = failing_cursor
    try:
        with pytest.raises(OperationalError, match="Fallo simulado"):
            module.prepare_schema(bootstrap_database)
    finally:
        bootstrap_database.create_cursor = original
    assert "socio_tipodocumento" in _snapshot(bootstrap_database)
    report = module.prepare_schema(bootstrap_database)
    assert len(report["created_tables"]) == 26
    assert report["existing_tables"] == ["socio_tipodocumento"]
