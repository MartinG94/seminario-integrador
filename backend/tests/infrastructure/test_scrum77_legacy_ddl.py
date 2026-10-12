"""Contrato del DDL demo y compilación contra un esquema MySQL temporal propio."""

import re
from collections.abc import Iterator
from copy import deepcopy
from pathlib import Path
from typing import Any
from uuid import uuid4

import pytest
from django.core.management import call_command
from django.db import IntegrityError, connections

from padron.models import (
    Socio,
    SocioEmail,
    SocioEstado,
    SocioEstadoHistorial,
    SocioEstudio,
    Subcomision,
)
from ranking.models import PuntajeAplicado, PuntajeGeneral
from tests.infrastructure.scratch_routing import route_default_to_scratch

BACKEND_ROOT = Path(__file__).resolve().parents[2]
DDL_PATH = BACKEND_ROOT / "core/sql/scrum77_legacy_schema.sql"
SOURCE_PATH = (
    BACKEND_ROOT.parent
    / "docs/analisis-proceso-actual/sistema-actual/sistema_actual_legado_schema.sql"
)
MODELS = (
    Subcomision,
    Socio,
    SocioEstudio,
    SocioEmail,
    SocioEstado,
    SocioEstadoHistorial,
    PuntajeGeneral,
    PuntajeAplicado,
)
CREATE_TABLE = re.compile(r"CREATE TABLE `([^`]+)` \(.*?\) ENGINE=InnoDB[^;]*;", re.DOTALL)


def _definitions(sql: str) -> dict[str, str]:
    return {match.group(1): match.group(0) for match in CREATE_TABLE.finditer(sql)}


def _references(statement: str) -> set[str]:
    return set(re.findall(r"REFERENCES `([^`]+)`", statement))


@pytest.fixture(scope="module")
def ddl_definitions() -> dict[str, str]:
    return _definitions(DDL_PATH.read_text(encoding="utf-8"))


def test_ddl_contains_only_creation_and_preserves_managed_auth() -> None:
    sql = re.sub(r"--[^\n]*", "", DDL_PATH.read_text(encoding="utf-8"))
    statements = [statement.strip() + ";" for statement in sql.split(";") if statement.strip()]
    assert statements
    assert all(CREATE_TABLE.fullmatch(statement) for statement in statements)
    assert "auth_user" not in _definitions(sql)
    assert "expedientes_expediente" not in sql
    assert "IF NOT EXISTS" not in sql.upper()


def test_ddl_is_the_minimal_ordered_foreign_key_closure(ddl_definitions: Any) -> None:
    source = _definitions(SOURCE_PATH.read_text(encoding="utf-8"))
    required = {model._meta.db_table for model in MODELS}
    pending = list(required)
    while pending:
        for target in _references(source[pending.pop()]):
            if target not in required:
                required.add(target)
                pending.append(target)
    assert set(ddl_definitions) == required - {"auth_user"}
    available = {"auth_user"}
    for table, statement in ddl_definitions.items():
        assert _references(statement) <= available, table
        available.add(table)


def test_ddl_retains_source_constraints_with_only_three_adaptations(
    ddl_definitions: Any,
) -> None:
    source = _definitions(SOURCE_PATH.read_text(encoding="utf-8"))
    for table, statement in ddl_definitions.items():
        expected = source[table]
        if table == "tribunal_puntajeaplicado":
            expected = expected.replace(
                "`puntajeAplicado` double", "`puntajeAplicado` decimal(10,2)"
            )
        elif table == "tribunal_puntajegeneral":
            expected = expected.replace("`puntos` double", "`puntos` decimal(10,2)")
        elif table == "socio_lista":
            expected = expected.replace(
                "`anoSocial` int(11) NOT NULL", "`anoSocial` int(11) DEFAULT NULL"
            )
        assert statement == expected, table


@pytest.fixture(scope="module")
def ddl_database(
    ddl_definitions: Any, django_db_setup: Any, django_db_blocker: Any
) -> Iterator[Any]:
    """El esquema creado por esta fixture nunca es la base de aplicación ni la de pytest."""
    with django_db_blocker.unblock():
        parent = connections["default"]
        assert parent.vendor == "mysql", "Esta prueba requiere MySQL real."
        assert parent.settings_dict["NAME"].startswith("test_"), "Se requiere la base de pytest."
        alias = f"scrum77_ddl_{uuid4().hex[:10]}"
        database = f"test_{alias}"
        assert re.fullmatch(r"test_scrum77_ddl_[a-f0-9]{10}", database)
        with parent.cursor() as cursor:
            cursor.execute(
                f"CREATE DATABASE `{database}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
        configuration = deepcopy(parent.settings_dict)
        configuration["NAME"] = database
        connections.databases[alias] = configuration
        probe = connections[alias]
        try:
            # Migraciones reales: no importar ni recrear el auth_user simplificado del dump.
            with route_default_to_scratch(probe):
                call_command("migrate", database=alias, interactive=False, verbosity=0)
                with probe.cursor() as cursor:
                    cursor.execute("SELECT `last_value` FROM expedientes_numero_secuencia")
                    assert cursor.fetchall() == ((0,),)
            with probe.cursor() as cursor:
                cursor.execute("SHOW CREATE TABLE auth_user")
                auth_before = cursor.fetchone()[1]
                cursor.execute("SELECT @@session.foreign_key_checks")
                assert cursor.fetchone() == (1,)
                for statement in ddl_definitions.values():
                    cursor.execute(statement)
                cursor.execute("SHOW CREATE TABLE auth_user")
                assert cursor.fetchone()[1] == auth_before
            yield probe
        finally:
            probe.close()
            del connections[alias]
            del connections.databases[alias]
            # Sólo borrar el esquema nuevo cuyo CREATE anterior fue satisfactorio.
            with parent.cursor() as cursor:
                cursor.execute(f"DROP DATABASE `{database}`")


@pytest.mark.django_db(transaction=True, databases="__all__")
def test_mysql_compiles_every_foreign_key_with_matching_types(
    ddl_database: Any, ddl_definitions: Any
) -> None:
    expected = {
        (table, column, target, target_column)
        for table, statement in ddl_definitions.items()
        for column, target, target_column in re.findall(
            r"FOREIGN KEY \(`([^`]+)`\) REFERENCES `([^`]+)` \(`([^`]+)`\)", statement
        )
    }
    with ddl_database.cursor() as cursor:
        cursor.execute(
            "SELECT k.TABLE_NAME, k.COLUMN_NAME, k.REFERENCED_TABLE_NAME, "
            "k.REFERENCED_COLUMN_NAME, c.COLUMN_TYPE, r.COLUMN_TYPE "
            "FROM information_schema.KEY_COLUMN_USAGE k "
            "JOIN information_schema.COLUMNS c ON c.TABLE_SCHEMA=k.TABLE_SCHEMA "
            "AND c.TABLE_NAME=k.TABLE_NAME AND c.COLUMN_NAME=k.COLUMN_NAME "
            "JOIN information_schema.COLUMNS r ON r.TABLE_SCHEMA=k.REFERENCED_TABLE_SCHEMA "
            "AND r.TABLE_NAME=k.REFERENCED_TABLE_NAME AND r.COLUMN_NAME=k.REFERENCED_COLUMN_NAME "
            "WHERE k.TABLE_SCHEMA=DATABASE() AND k.REFERENCED_TABLE_NAME IS NOT NULL"
        )
        actual = [row for row in cursor.fetchall() if row[0] in ddl_definitions]
        assert {row[:4] for row in actual} == expected
        assert all(row[4] == row[5] for row in actual)
        cursor.execute("SELECT @@session.foreign_key_checks")
        assert cursor.fetchone() == (1,)
        cursor.execute(
            "SELECT TABLE_NAME, ENGINE, TABLE_COLLATION FROM information_schema.TABLES "
            "WHERE TABLE_SCHEMA=DATABASE()"
        )
        tables = {table: (engine, collation) for table, engine, collation in cursor.fetchall()}
        assert all(tables[table] == ("InnoDB", "utf8mb4_unicode_ci") for table in ddl_definitions)


def _canonical_type(value: str) -> str:
    value = (
        value.lower()
        .replace("integer", "int")
        .replace("numeric", "decimal")
        .replace("bool", "tinyint(1)")
    )
    value = value.replace(" auto_increment", "")
    value = re.sub(r"\s+", "", value)
    return re.sub(r"\bint\(\d+\)", "int", value)


@pytest.mark.django_db(transaction=True, databases="__all__")
def test_mysql_empty_demo_has_nullable_social_year(ddl_database: Any, ddl_definitions: Any) -> None:
    """TS77.38: contrato físico nuevo sin introducir filas o años ficticios."""
    with ddl_database.cursor() as cursor:
        cursor.execute(
            "SELECT COLUMN_TYPE, IS_NULLABLE, COLUMN_DEFAULT "
            "FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=DATABASE() "
            "AND TABLE_NAME='socio_lista' AND COLUMN_NAME='anoSocial'"
        )
        column_type, nullable, default = cursor.fetchone()
        assert _canonical_type(column_type) == "int"
        assert nullable == "YES"
        assert default is None
        for name in ddl_definitions:
            cursor.execute(f"SELECT COUNT(*) FROM {ddl_database.ops.quote_name(name)}")
            assert cursor.fetchone() == (0,), name
        cursor.execute("SELECT @@session.foreign_key_checks")
        assert cursor.fetchone() == (1,)


@pytest.mark.django_db(transaction=True, databases="__all__")
def test_mysql_columns_match_unmanaged_models_with_demo_adaptation(ddl_database: Any) -> None:
    with ddl_database.cursor() as cursor:
        cursor.execute(
            "SELECT TABLE_NAME, COLUMN_NAME, COLUMN_TYPE, IS_NULLABLE, EXTRA "
            "FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=DATABASE()"
        )
        columns = {
            (table, column): (column_type, nullable == "YES", extra)
            for table, column, column_type, nullable, extra in cursor.fetchall()
        }
    for model in MODELS:
        for field in model._meta.local_fields:
            column_type, nullable, extra = columns[(model._meta.db_table, field.column)]
            expected_type = field.db_type(ddl_database)
            assert _canonical_type(column_type) == _canonical_type(expected_type)
            assert ("auto_increment" in extra) == ("auto_increment" in expected_type.lower())
            assert nullable == field.null
        with ddl_database.cursor() as cursor:
            constraints = ddl_database.introspection.get_constraints(cursor, model._meta.db_table)
        assert any(
            item["primary_key"] and item["columns"] == [model._meta.pk.column]
            for item in constraints.values()
        )
        for field in model._meta.local_fields:
            if field.unique and not field.primary_key:
                assert any(
                    item["unique"] and item["columns"] == [field.column]
                    for item in constraints.values()
                )


@pytest.mark.django_db(transaction=True, databases="__all__")
def test_mysql_rejects_an_orphan_ledger_entry(ddl_database: Any) -> None:
    with ddl_database.cursor() as cursor:
        with pytest.raises(IntegrityError) as error:
            cursor.execute(
                "INSERT INTO tribunal_puntajeaplicado (puntajeAplicado, socio_id) VALUES (%s, %s)",
                [1, 2147483647],
            )
        assert error.value.args[0] == 1452
        cursor.execute("SELECT COUNT(*) FROM tribunal_puntajeaplicado")
        assert cursor.fetchone() == (0,)
