"""Contrato del DDL aprobado y preparación MySQL exclusiva del comando demo."""

import re
from dataclasses import dataclass, field, replace
from decimal import Decimal
from io import StringIO
from pathlib import Path
from typing import Any

from django.core.management import call_command
from django.core.management.base import CommandError
from django.db.backends.base.base import BaseDatabaseWrapper
from django.db.migrations.exceptions import InconsistentMigrationHistory
from django.db.migrations.executor import MigrationExecutor
from django.db.migrations.operations.fields import AddField
from django.db.migrations.operations.models import CreateModel

DDL_PATH = Path(__file__).resolve().parent / "sql/scrum77_legacy_schema.sql"
IDENTIFIER = r"[A-Za-z_][A-Za-z0-9_]*"
COLUMN = re.compile(
    rf"`({IDENTIFIER})` "
    r"((?:int|tinyint|bigint|varchar|decimal|datetime)(?:\([\d,]+\))?|date|double|longtext)"
    r"( unsigned)?(?: CHARACTER SET (\w+))?(?: COLLATE (\w+))?(?: (NOT NULL|NULL))?"
    r"(?: DEFAULT (NULL|'[^']*'|-?\d+(?:\.\d+)?|CURRENT_TIMESTAMP(?:\(\d+\))?))?"
    r"( AUTO_INCREMENT)?(?: ON UPDATE (CURRENT_TIMESTAMP(?:\(\d+\))?))?",
    re.IGNORECASE,
)
CREATE = re.compile(
    rf"CREATE TABLE `({IDENTIFIER})` \(\s*(.*?)\s*\) ENGINE=(\w+)"
    r"(?: AUTO_INCREMENT=\d+)? DEFAULT CHARSET=(\w+) COLLATE=(\w+);",
    re.DOTALL | re.IGNORECASE,
)
KEY = re.compile(rf"(?:(UNIQUE) )?KEY `({IDENTIFIER})` \((.*?)\)", re.IGNORECASE)
FOREIGN_KEY = re.compile(
    rf"CONSTRAINT `({IDENTIFIER})` FOREIGN KEY \((.*?)\) REFERENCES "
    rf"(?:`({IDENTIFIER})`\.)?`({IDENTIFIER})` \((.*?)\)"
    r"(?: ON DELETE (SET NULL|CASCADE|RESTRICT|NO ACTION))?"
    r"(?: ON UPDATE (SET NULL|CASCADE|RESTRICT|NO ACTION))?",
    re.IGNORECASE,
)


@dataclass
class TableContract:
    name: str
    statement: str = field(compare=False)
    columns: dict[str, tuple[Any, ...]]
    indexes: dict[str, tuple[bool, tuple[str, ...]]]
    foreign_keys: dict[str, tuple[Any, ...]]
    options: tuple[str, str, str]


def _column_names(value: str) -> tuple[str, ...]:
    if not re.fullmatch(rf"`{IDENTIFIER}`(?:,\s*`{IDENTIFIER}`)*", value):
        raise CommandError("El DDL contiene una clave no soportada por el contrato demo.")
    return tuple(re.findall(r"`([^`]+)`", value))


def _canonical_type(value: str) -> str:
    return re.sub(r"\b(int|bigint)\(\d+\)", r"\1", value.lower())


def _default(value: str | None, column_type: str) -> str | None:
    if value is None or value.upper() == "NULL":
        return None
    value = value.strip("'")
    if column_type.startswith(("int", "tinyint", "bigint", "decimal", "double")):
        return str(Decimal(value).normalize())
    if column_type.startswith("datetime"):
        return value.lower()
    return value


def _action(value: str | None) -> str:
    return "RESTRICT" if value is None or value.upper() == "NO ACTION" else value.upper()


def _parse_table(statement: str) -> TableContract:
    """Gramática cerrada del archivo aprobado; rechaza cláusulas desconocidas."""
    match = CREATE.fullmatch(statement.strip())
    if not match:
        raise CommandError("El DDL no corresponde a una creación de tabla demo soportada.")
    name, body, engine, charset, collation = match.groups()
    columns: dict[str, tuple[Any, ...]] = {}
    indexes: dict[str, tuple[bool, tuple[str, ...]]] = {}
    foreign_keys: dict[str, tuple[Any, ...]] = {}
    for line in body.splitlines():
        line = line.strip().removesuffix(",")
        column = COLUMN.fullmatch(line)
        key = KEY.fullmatch(line)
        foreign_key = FOREIGN_KEY.fullmatch(line)
        if column:
            (
                column_name,
                data_type,
                unsigned,
                column_charset,
                column_collation,
                nullable,
                default,
                auto_increment,
                update,
            ) = column.groups()
            column_type = _canonical_type(data_type + (unsigned or ""))
            if column_name in columns:
                raise CommandError(f"El DDL repite una columna en {name}.")
            columns[column_name] = (
                column_type,
                nullable != "NOT NULL",
                _default(default, column_type),
                bool(auto_increment),
                (update or "").lower(),
                (column_charset or charset).lower()
                if column_type.startswith(("varchar", "longtext"))
                else None,
                (column_collation or collation).lower()
                if column_type.startswith(("varchar", "longtext"))
                else None,
            )
        elif line.startswith("PRIMARY KEY (") and line.endswith(")"):
            indexes["PRIMARY"] = (True, _column_names(line[len("PRIMARY KEY (") : -1]))
        elif key:
            unique, key_name, key_columns = key.groups()
            indexes[key_name] = (bool(unique), _column_names(key_columns))
        elif foreign_key:
            constraint, key_columns, target_schema, target, target_columns, delete, update = (
                foreign_key.groups()
            )
            foreign_keys[constraint] = (
                _column_names(key_columns),
                target_schema,
                target,
                _column_names(target_columns),
                _action(delete),
                _action(update),
            )
        else:
            raise CommandError(f"El DDL contiene una definición no soportada en {name}.")
    if not columns or "PRIMARY" not in indexes:
        raise CommandError(f"El DDL carece de columnas o clave primaria en {name}.")
    return TableContract(
        name,
        statement,
        columns,
        indexes,
        foreign_keys,
        (engine.lower(), charset.lower(), collation.lower()),
    )


def read_contracts(path: Path = DDL_PATH) -> list[TableContract]:
    sql = re.sub(r"--[^\n]*", "", path.read_text(encoding="utf-8"))
    contracts = [_parse_table(part.strip() + ";") for part in sql.split(";") if part.strip()]
    available = {"auth_user"}
    for contract in contracts:
        if contract.name in available or not contract.name.startswith(
            ("socio_", "grupo_", "tribunal_")
        ):
            raise CommandError("El DDL incluye una tabla repetida o ajena al cierre legado demo.")
        for relation in contract.foreign_keys.values():
            if relation[1] is not None or relation[2] not in available:
                raise CommandError("El DDL incluye una dependencia externa o fuera de orden.")
        available.add(contract.name)
    if len(contracts) != 27 or sum(len(item.foreign_keys) for item in contracts) != 39:
        raise CommandError("El DDL no conserva el cierre aprobado de 27 tablas y 39 FKs.")
    return contracts


def _existing_tables(database: BaseDatabaseWrapper) -> dict[str, str]:
    with database.cursor() as cursor:
        cursor.execute(
            "SELECT TABLE_NAME, TABLE_TYPE FROM information_schema.TABLES "
            "WHERE TABLE_SCHEMA=DATABASE()"
        )
        return dict(cursor.fetchall())


def _physical_contract(database: BaseDatabaseWrapper, name: str) -> TableContract:
    with database.cursor() as cursor:
        cursor.execute(f"SHOW CREATE TABLE {database.ops.quote_name(name)}")
        definition = cursor.fetchone()[1]
    try:
        return _parse_table(definition + ";")
    except CommandError as error:
        raise CommandError(
            f"El esquema existente diverge del DDL aprobado en {name}: {error}"
        ) from None


def validate_existing_schema(
    database: BaseDatabaseWrapper, contracts: list[TableContract]
) -> list[str]:
    """Sólo SELECT/SHOW: revisar el conjunto completo antes de migrar o crear."""
    tables = _existing_tables(database)
    missing = []
    for expected in contracts:
        if expected.name not in tables:
            missing.append(expected.name)
            continue
        if tables[expected.name] != "BASE TABLE":
            raise CommandError(f"El esquema existente diverge del DDL aprobado en {expected.name}.")
        actual = _physical_contract(database, expected.name)
        # SHOW CREATE califica explícitamente las referencias a otras bases.
        for relation in actual.foreign_keys.values():
            if relation[1] is not None or relation[2] not in tables:
                raise CommandError(
                    f"Una FK existente es ajena o carece de destino en {expected.name}."
                )
        if actual != expected or list(actual.columns) != list(expected.columns):
            raise CommandError(f"El esquema existente diverge del DDL aprobado en {expected.name}.")
    if "auth_user" in tables:
        auth = _physical_contract(database, "auth_user")
        identity = auth.columns.get("id")
        if (
            tables["auth_user"] != "BASE TABLE"
            or auth.options[0] != "innodb"
            or identity != ("int", False, None, True, "", None, None)
            or auth.indexes.get("PRIMARY") != (True, ("id",))
        ):
            raise CommandError("auth_user no tiene la identidad INT firmada requerida por las FKs.")
    return missing


def _check_session(database: BaseDatabaseWrapper) -> None:
    if database.vendor != "mysql" or database.in_atomic_block or not database.get_autocommit():
        raise CommandError("La preparación requiere MySQL con autocommit y fuera de atomic().")
    with database.cursor() as cursor:
        cursor.execute("SELECT @@session.foreign_key_checks")
        if cursor.fetchone() != (1,):
            raise CommandError("La preparación requiere claves foráneas activas.")


def _check_managed_collisions(
    database: BaseDatabaseWrapper, executor: MigrationExecutor, migration_plan: list[Any]
) -> None:
    tables = _existing_tables(database)
    try:
        executor.loader.check_consistent_history(database)
    except InconsistentMigrationHistory:
        raise CommandError("El historial de migraciones managed es inconsistente.") from None
    for migration, backwards in migration_plan:
        if backwards:
            raise CommandError("La preparación demo no admite revertir migraciones.")
        state = executor.loader.project_state((migration.app_label, migration.name), at_end=False)
        for operation in migration.operations:
            operation.state_forwards(migration.app_label, state)
            if isinstance(operation, CreateModel):
                model_name = operation.name
            elif isinstance(operation, AddField) and operation.field.many_to_many:
                model_name = operation.model_name
            else:
                continue
            model = state.apps.get_model(migration.app_label, model_name)
            if not model._meta.managed or model._meta.proxy:
                continue
            new_tables = {model._meta.db_table} if isinstance(operation, CreateModel) else set()
            relations = (
                model._meta.local_many_to_many
                if isinstance(operation, CreateModel)
                else [model._meta.get_field(operation.name)]
            )
            new_tables.update(
                relation.remote_field.through._meta.db_table
                for relation in relations
                if relation.remote_field.through._meta.auto_created
            )
            for table in sorted(new_tables & tables.keys()):
                raise CommandError(
                    f"La tabla managed {table} existe sin su migración aplicada; "
                    "no se realizaron cambios."
                )


def prepare_schema(database: BaseDatabaseWrapper) -> dict[str, Any]:
    """Entrada interna; el comando público acredita primero el perfil demo completo."""
    contracts = read_contracts()
    _check_session(database)
    lock_name = f"scrum77-schema:{database.settings_dict['NAME']}"
    with database.cursor() as cursor:
        cursor.execute("SELECT GET_LOCK(%s, 0)", [lock_name])
        if cursor.fetchone() != (1,):
            raise CommandError(
                "Hay otra preparación de esquema en curso; no se realizaron cambios."
            )
    try:
        missing = validate_existing_schema(database, contracts)
        executor = MigrationExecutor(database)
        migration_plan = executor.migration_plan(executor.loader.graph.leaf_nodes())
        _check_managed_collisions(database, executor, migration_plan)
        if migration_plan:
            call_command(
                "migrate",
                database=database.alias,
                interactive=False,
                verbosity=0,
                stdout=StringIO(),
            )
        # Las migraciones managed deben proporcionar auth_user; nunca se crea desde el dump.
        if "auth_user" not in _existing_tables(database):
            raise CommandError("Las migraciones managed no proporcionaron auth_user.")
        validate_existing_schema(database, contracts)
        created = []
        for contract in contracts:
            if contract.name in missing:
                _check_session(database)
                with database.cursor() as cursor:
                    cursor.execute(contract.statement)
                created.append(contract.name)
        if validate_existing_schema(database, contracts):
            raise CommandError("La preparación no completó todas las tablas del cierre legado.")
        _check_session(database)
        return {
            "legacy_tables": len(contracts),
            "foreign_keys": sum(len(item.foreign_keys) for item in contracts),
            "created_tables": created,
            "existing_tables": [item.name for item in contracts if item.name not in missing],
            "migrations_applied": len(migration_plan),
            "foreign_key_checks": True,
        }
    finally:
        with database.cursor() as cursor:
            cursor.execute("SELECT RELEASE_LOCK(%s)", [lock_name])


def _social_year_identity(
    database: BaseDatabaseWrapper,
) -> tuple[tuple[tuple[Any, ...], ...], int | None]:
    """Lectura interna de filas/IDs y contador; nunca imprimir estos datos."""
    with database.cursor() as cursor:
        cursor.execute("SELECT * FROM socio_lista ORDER BY nroSocio")
        rows = tuple(cursor.fetchall())
        cursor.execute("SELECT @@session.information_schema_stats_expiry")
        saved_expiry = cursor.fetchone()[0]
        try:
            cursor.execute("SET SESSION information_schema_stats_expiry=0")
            cursor.execute(
                "SELECT AUTO_INCREMENT FROM information_schema.TABLES "
                "WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='socio_lista'"
            )
            counter = cursor.fetchone()[0]
        finally:
            cursor.execute("SET SESSION information_schema_stats_expiry=%s", [saved_expiry])
    return rows, counter


def transition_social_year_schema(database: BaseDatabaseWrapper) -> dict[str, Any]:
    """Entrada interna: el comando acredita perfil/grants antes de un ALTER acotado.

    GET_LOCK coordina preparadores, sin prometer bloqueo de escrituras externas ni
    rollback de DDL MySQL. No migra Django, crea tablas ni modifica filas.
    """
    contracts = read_contracts()
    current = next(item for item in contracts if item.name == "socio_lista")
    new_column = ("int", True, None, False, "", None, None)
    old_column = ("int", False, None, False, "", None, None)
    if current.columns.get("anoSocial") != new_column:
        raise CommandError("El DDL no contiene el contrato nullable autorizado de anoSocial.")
    previous_columns = {**current.columns, "anoSocial": old_column}
    previous = [
        replace(item, columns=previous_columns) if item.name == "socio_lista" else item
        for item in contracts
    ]
    _check_session(database)
    lock_name = f"scrum77-schema:{database.settings_dict['NAME']}"
    with database.cursor() as cursor:
        cursor.execute("SELECT GET_LOCK(%s, 0)", [lock_name])
        if cursor.fetchone() != (1,):
            raise CommandError(
                "Hay otra preparación de esquema en curso; no se realizaron cambios."
            )
    try:
        tables = _existing_tables(database)
        if tables.get("socio_lista") != "BASE TABLE" or tables.get("auth_user") != "BASE TABLE":
            raise CommandError("La transición requiere un cierre completo ya preparado.")
        actual_column = _physical_contract(database, "socio_lista").columns.get("anoSocial")
        if actual_column == old_column:
            changed = True
            expected = previous
        elif actual_column == new_column:
            changed = False
            expected = contracts
        else:
            raise CommandError(
                "El esquema existente diverge del contrato de socio_lista.anoSocial."
            )
        if validate_existing_schema(database, expected):
            raise CommandError("La transición requiere un cierre completo ya preparado.")
        before = _social_year_identity(database)
        if changed:
            _check_session(database)
            with database.cursor() as cursor:
                cursor.execute(
                    "ALTER TABLE `socio_lista` MODIFY COLUMN `anoSocial` INT NULL DEFAULT NULL"
                )
        if validate_existing_schema(database, contracts):
            raise CommandError("No se pudo verificar el cierre completo después de la transición.")
        _check_session(database)
        if _social_year_identity(database) != before:
            raise CommandError(
                "No se pudo acreditar la conservación de filas/IDs/contador. "
                "El DDL puede estar aplicado; conservá la base y revisá la verificación."
            )
        return {
            "altered_columns": ["socio_lista.anoSocial"] if changed else [],
            "row_count": len(before[0]),
            "legacy_tables": len(contracts),
            "foreign_keys": sum(len(item.foreign_keys) for item in contracts),
            "foreign_key_checks": True,
        }
    finally:
        with database.cursor() as cursor:
            cursor.execute("SELECT RELEASE_LOCK(%s)", [lock_name])
