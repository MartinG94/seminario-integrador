"""Carga transaccional del catálogo aprobado, exclusivamente en MySQL demo."""

import re
from typing import Any

from django.apps import apps
from django.core.management.base import CommandError
from django.db import connection, transaction
from django.db.backends.base.base import BaseDatabaseWrapper
from django.db.migrations.exceptions import InconsistentMigrationHistory
from django.db.migrations.executor import MigrationExecutor

from core.demo_schema import read_contracts, validate_existing_schema
from core.management.commands import check_demo_mysql as preflight
from socios.demo_catalog import CATALOG, validate_catalog


def assert_demo_seed_environment(profile: str) -> None:
    """Rechazar un perfil desconocido antes de abrir la conexión."""
    if not isinstance(profile, str) or profile != CATALOG.profile:
        raise CommandError("El perfil solicitado no corresponde al catálogo demo aprobado.")
    preflight._check_configuration()


def assert_demo_seed_database(database: BaseDatabaseWrapper) -> None:
    """Validar destino efectivo y sesión sin DDL/DML, incluso dentro de atomic."""
    expected = {
        "NAME": preflight.DEMO_DATABASE,
        "USER": preflight.DEMO_USER,
        "HOST": "db",
        "PORT": "3306",
    }
    if database.vendor != "mysql" or any(
        str(database.settings_dict.get(field, "")) != value for field, value in expected.items()
    ):
        raise CommandError("La carga requiere la conexión MySQL de la demo habilitada.")
    with database.cursor() as cursor:
        cursor.execute(
            "SELECT DATABASE(), VERSION(), @@session.foreign_key_checks, @@session.sql_mode"
        )
        name, version, foreign_keys, mode = cursor.fetchone()
        if (
            name != preflight.DEMO_DATABASE
            or not re.match(r"^8\.0\.\d+(?:[-.]|$)", version)
            or "mariadb" in version.lower()
            or foreign_keys != 1
            or not set(mode.split(",")).intersection({"STRICT_TRANS_TABLES", "STRICT_ALL_TABLES"})
        ):
            raise CommandError(
                "La sesión efectiva no acredita MySQL demo estricto con FKs activas."
            )
        cursor.execute(
            "SELECT TABLE_NAME FROM information_schema.TABLES "
            "WHERE TABLE_SCHEMA=DATABASE() AND TABLE_TYPE='BASE TABLE' AND ENGINE <> 'InnoDB'"
        )
        if cursor.fetchall():
            raise CommandError("La carga requiere tablas transaccionales InnoDB.")
    # Mismo diagnóstico autenticado de grants que usa la CLI; también para imports internos.
    preflight._check_mysql()


def assert_demo_seed_schema(database: BaseDatabaseWrapper) -> None:
    """La carga no prepara ni migra un esquema incompleto o divergente."""
    if validate_existing_schema(database, read_contracts()):
        raise CommandError("Faltan tablas del esquema demo; preparalo antes de cargar datos.")
    executor = MigrationExecutor(database)
    try:
        executor.loader.check_consistent_history(database)
    except InconsistentMigrationHistory:
        raise CommandError("El historial managed es inconsistente; no se cargaron datos.") from None
    if executor.migration_plan(executor.loader.graph.leaf_nodes()):
        raise CommandError("Hay migraciones pendientes; prepará el esquema antes de cargar datos.")
    existing = set(database.introspection.table_names())
    required = set()
    for model in apps.get_models():
        if model._meta.managed and not model._meta.proxy:
            required.add(model._meta.db_table)
            required.update(
                field.remote_field.through._meta.db_table
                for field in model._meta.local_many_to_many
                if field.remote_field.through._meta.auto_created
            )
    if required - existing:
        raise CommandError("El historial no acredita todas las tablas managed requeridas.")
    from core.models import DemoFixtureOwnership

    with database.cursor() as cursor:
        constraints = database.introspection.get_constraints(
            cursor, DemoFixtureOwnership._meta.db_table
        )
    unique_columns = {tuple(item["columns"]) for item in constraints.values() if item.get("unique")}
    if not {("profile", "fixture_key"), ("namespace", "object_key")}.issubset(unique_columns):
        raise CommandError(
            "Las unicidades físicas del registro de propiedad no corresponden al contrato."
        )


def _mapping_ids(values: dict[str, Any]) -> dict[str, Any]:
    """Exportar sólo PKs, evitando datos de cuenta, credenciales y hashes."""
    result: dict[str, Any] = {}
    for key, value in values.items():
        if value is None:
            result[key] = None
        elif hasattr(value, "pk"):
            result[key] = str(value.pk)
        elif isinstance(value, (str, int)) and not isinstance(value, bool):
            result[key] = value
        elif isinstance(value, dict):
            for name in (
                "id",
                "nroSocio",
                "nroGrupo",
                "codSubcomision",
                "idDatosResolucion",
                "idExpediente",
                "idPuntajeAplicado",
                "compositeKey",
            ):
                if name in value:
                    result[key] = str(value[name])
                    break
            else:
                raise CommandError("Una referencia del manifiesto carece de identidad explícita.")
        else:
            raise CommandError("Una referencia del manifiesto no tiene un namespace reconocido.")
    return result


def _member_identities() -> list[dict[str, Any]]:
    """Correspondencia persistida entre namespaces, sin nombres ni credenciales."""
    identifiers = [member.institutional_number for member in CATALOG.members]
    placeholders = ",".join(["%s"] * len(identifiers))
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT s.nroSocio, e.nroLegajo, s.user_id, l.id, l.legajo, h.idGrupo, "
            "s.codSubcomision, l.subcomision_id "
            "FROM socio_lista s LEFT JOIN socio_estudio e ON e.nroSocio=s.nroSocio "
            "LEFT JOIN socios_socio l ON l.user_id=s.user_id "
            "LEFT JOIN socio_estadoHistorial h ON h.idEstadoHistorial=("
            "SELECT hh.idEstadoHistorial FROM socio_estadoHistorial hh "
            "WHERE hh.nroSocio=s.nroSocio ORDER BY hh.fechaHora DESC,"
            "hh.idEstadoHistorial DESC LIMIT 1) "
            f"WHERE s.nroSocio IN ({placeholders}) ORDER BY s.nroSocio",
            identifiers,
        )
        rows = cursor.fetchall()
    keys = {member.institutional_number: member.fixture_key for member in CATALOG.members}
    result: dict[int, dict[str, Any]] = {}
    for (
        number,
        academic,
        user,
        local,
        legajo,
        group,
        institutional_subcommission,
        local_subcommission,
    ) in rows:
        item = {
            "fixture_key": keys[number],
            "institutional_number": number,
            "academic_number": academic,
            "user_id": user,
            "local_socio_id": local,
            "local_legajo": legajo,
            "group": group,
            "institutional_subcommission": institutional_subcommission,
            "local_subcommission_id": local_subcommission,
        }
        if number in result and result[number] != item:
            raise CommandError("La correspondencia de namespaces del manifiesto es ambigua.")
        if academic is None or group is None or (user is None) != (local is None):
            raise CommandError("La correspondencia de namespaces del manifiesto está incompleta.")
        result[number] = item
    if set(result) != set(identifiers):
        raise CommandError("El manifiesto no concilia todas las identidades del catálogo.")
    return list(result.values())


def run_demo_seed(*, profile: str = CATALOG.profile, password: str | None = None) -> dict[str, Any]:
    """Un lock compartido con DDL y una única transacción para datos/propiedad/contador."""
    assert_demo_seed_environment(profile)
    assert_demo_seed_database(connection)
    assert_demo_seed_schema(connection)
    validate_catalog(CATALOG)
    if connection.in_atomic_block or not connection.get_autocommit():
        raise CommandError("La carga debe iniciarse fuera de otra transacción.")

    # Imports diferidos evitan ciclos con los guards usados por el registro de propiedad.
    from core.demo_fixtures import DemoFixtureRegistry, demo_fixture_lock
    from core.demo_members import load_demo_members
    from core.demo_scenes import load_demo_scenes
    from socios.management.commands.seed_demo import DEMO_PASSWORD

    with demo_fixture_lock():
        assert_demo_seed_schema(connection)
        with transaction.atomic():
            registry = DemoFixtureRegistry(profile)
            members = load_demo_members(CATALOG, registry, password=password or DEMO_PASSWORD)
            scenes = load_demo_scenes(CATALOG, registry, members)
            mappings = {
                name: _mapping_ids(getattr(members, name))
                for name in (
                    "users",
                    "local_socios",
                    "institutional_members",
                    "accounts",
                    "groups",
                    "subcommissions",
                )
            }
            mappings.update(
                {
                    name: _mapping_ids(getattr(scenes, name))
                    for name in (
                        "causes",
                        "t01s",
                        "issued_causes",
                        "historical_resolutions",
                        "historical_expedientes",
                        "movements",
                        "advanced_causes",
                        "advanced_resolutions",
                        "advanced_expedientes",
                        "advanced_movements",
                    )
                }
            )
            report = {
                "status": "ok",
                "profile": profile,
                "social_cycle": CATALOG.social_cycle,
                "fixtures": registry.export(),
                "mappings": mappings,
                "identities": _member_identities(),
            }
    return report
