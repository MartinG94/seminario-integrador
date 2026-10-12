"""Diagnóstico autenticado y de sólo lectura del entorno MySQL de SCRUM-77."""

import json
import os
import re
from typing import Any
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import DatabaseError, connection

DEMO_DATABASE = "aveit_tribunal_scrum77_demo"
DEMO_USER = "aveit_dev"
TEST_DATABASE = f"test_{DEMO_DATABASE}"
REQUIRED_PRIVILEGES = frozenset(
    {"SELECT", "INSERT", "UPDATE", "DELETE", "CREATE", "DROP", "ALTER", "INDEX", "REFERENCES"}
)
HEALTH_URL = "http://127.0.0.1:8000/api/health/"


def _check_configuration() -> None:
    if not settings.DEBUG or connection.vendor != "mysql":
        raise CommandError("El preflight requiere el backend demo con DEBUG y MySQL habilitados.")
    if os.environ.get("PADRON_ADAPTER", "").lower() != "database":
        raise CommandError("El preflight requiere el adaptador de padrón database.")
    config = connection.settings_dict
    expected = {"NAME": DEMO_DATABASE, "USER": DEMO_USER, "HOST": "db", "PORT": "3306"}
    if any(str(config.get(field, "")) != value for field, value in expected.items()):
        raise CommandError("La conexión configurada no corresponde al perfil MySQL demo.")
    if config.get("TEST", {}).get("NAME") not in (None, TEST_DATABASE):
        raise CommandError("La base de pruebas configurada no corresponde a la demo.")


def _matches_schema(pattern: str, database: str) -> bool:
    """Resolver patrones de grants MySQL con partial_revokes deshabilitado."""
    expression = []
    escaped = False
    for character in pattern:
        if escaped:
            expression.append(re.escape(character))
            escaped = False
        elif character == "\\":
            escaped = True
        elif character == "%":
            expression.append(".*")
        elif character == "_":
            expression.append(".")
        else:
            expression.append(re.escape(character))
    if escaped:
        expression.append(re.escape("\\"))
    return re.fullmatch("".join(expression), database) is not None


def _check_grants(rows: list[tuple[str, str]]) -> dict[str, bool]:
    schema_privileges: dict[str, set[str]] = {}
    for schema, privilege in rows:
        schema_privileges.setdefault(schema, set()).add(privilege)
    for database in (DEMO_DATABASE, TEST_DATABASE):
        matching = [
            privileges
            for pattern, privileges in schema_privileges.items()
            if _matches_schema(pattern, database)
        ]
        # No sumar patrones superpuestos: MySQL puede elegir sólo el primero aplicable.
        if len(matching) != 1 or not REQUIRED_PRIVILEGES.issubset(matching[0]):
            raise CommandError(
                "Los grants directos no acreditan los permisos de la base demo y de pruebas."
            )
    return {"application": True, "tests": True}


def _check_mysql() -> dict[str, Any]:
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            if cursor.fetchone() != (1,):
                raise CommandError("La consulta autenticada de diagnóstico no fue satisfactoria.")
            cursor.execute(
                "SELECT DATABASE(), CURRENT_USER(), VERSION(), @@session.sql_mode, "
                "@@character_set_connection, @@collation_connection, "
                "@@session.foreign_key_checks, @@GLOBAL.partial_revokes, CURRENT_ROLE()"
            )
            (
                database,
                current_user,
                version,
                sql_mode,
                charset,
                collation,
                foreign_key_checks,
                partial_revokes,
                current_role,
            ) = cursor.fetchone()
            user, separator, host = current_user.rpartition("@")
            if database != DEMO_DATABASE or not separator or user != DEMO_USER:
                raise CommandError("La base y el usuario autenticados no corresponden a la demo.")
            if not re.match(r"^8\.0\.\d+(?:[-.]|$)", version) or "mariadb" in version.lower():
                raise CommandError("El servidor demo debe ser MySQL 8.0.")
            modes = set(sql_mode.split(","))
            if not modes.intersection({"STRICT_TRANS_TABLES", "STRICT_ALL_TABLES"}):
                raise CommandError("La sesión MySQL debe operar en modo estricto.")
            if charset != "utf8mb4" or not collation.startswith("utf8mb4_"):
                raise CommandError("La sesión MySQL debe utilizar utf8mb4.")
            if foreign_key_checks != 1:
                raise CommandError("La sesión MySQL debe tener activadas las claves foráneas.")
            if partial_revokes != 0 or current_role != "NONE":
                raise CommandError("El perfil demo requiere grants directos sin roles ni revokes.")
            cursor.execute(
                "SELECT TABLE_SCHEMA, PRIVILEGE_TYPE "
                "FROM information_schema.SCHEMA_PRIVILEGES WHERE GRANTEE = %s",
                [f"'{user}'@'{host}'"],
            )
            grants = _check_grants(cursor.fetchall())
    except DatabaseError:
        raise CommandError("No se pudo verificar la conexión autenticada al MySQL demo.") from None
    return {
        "database": database,
        "current_user": current_user,
        "mysql_version": version,
        "sql_mode": sorted(modes),
        "charset": charset,
        "collation": collation,
        "foreign_key_checks": True,
        "padron_adapter": "database",
        "grants": grants,
        "test_database": TEST_DATABASE,
    }


class _RejectRedirects(HTTPRedirectHandler):
    def redirect_request(
        self, req: Request, fp: Any, code: int, msg: str, headers: Any, newurl: str
    ) -> None:
        return None


def _open_local_health() -> Any:
    opener = build_opener(ProxyHandler({}), _RejectRedirects())
    return opener.open(HEALTH_URL, timeout=3)


def _check_http_health() -> dict[str, str]:
    try:
        with _open_local_health() as response:
            healthy = {"status": "ok", "db": "connected"}
            if (
                response.status != 200
                or response.geturl() != HEALTH_URL
                or json.loads(response.read()) != healthy
            ):
                raise CommandError("El endpoint HTTP de salud no acredita conexión con la base.")
    except (OSError, ValueError):
        raise CommandError("No se pudo verificar el endpoint HTTP de salud de la demo.") from None
    return healthy


class Command(BaseCommand):
    help = "Verifica MySQL y HTTP del perfil demo SCRUM-77 sin modificar datos."
    requires_system_checks: list[str] = []

    def handle(self, *args: str, **options: Any) -> None:
        _check_configuration()
        report = {"status": "ok", **_check_mysql(), "health": _check_http_health()}
        self.stdout.write(json.dumps(report, ensure_ascii=False, sort_keys=True))
