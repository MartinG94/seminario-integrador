"""Comprobar el preflight público de la demo sin sustituir la prueba real de MySQL."""

import importlib
import json
import urllib.request
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, HTTPServer
from io import StringIO
from threading import Thread
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import OperationalError

DEMO_DATABASE = "aveit_tribunal_scrum77_demo"
PRIVILEGES = (
    "SELECT",
    "INSERT",
    "UPDATE",
    "DELETE",
    "CREATE",
    "DROP",
    "ALTER",
    "INDEX",
    "REFERENCES",
)


@pytest.fixture
def demo_backend(monkeypatch: pytest.MonkeyPatch, settings: Any) -> SimpleNamespace:
    module = importlib.import_module("core.management.commands.check_demo_mysql")
    settings.DEBUG = True
    monkeypatch.setenv("PADRON_ADAPTER", "database")
    database = MagicMock()
    database.vendor = "mysql"
    database.settings_dict = {
        "NAME": DEMO_DATABASE,
        "USER": "aveit_dev",
        "HOST": "db",
        "PORT": "3306",
        "PASSWORD": "sentinel-private-password",
        "TEST": {"NAME": None},
    }
    cursor = database.cursor.return_value.__enter__.return_value
    identity = [
        DEMO_DATABASE,
        "aveit_dev@%",
        "8.0.44",
        "STRICT_TRANS_TABLES",
        "utf8mb4",
        "utf8mb4_unicode_ci",
        1,
        0,
        "NONE",
    ]
    cursor.fetchone.side_effect = [(1,), identity]
    cursor.fetchall.return_value = [
        (schema, privilege) for schema in (DEMO_DATABASE, r"test\_%") for privilege in PRIVILEGES
    ]
    response = MagicMock()
    response.__enter__.return_value = response
    response.status = 200
    response.geturl.return_value = module.HEALTH_URL
    response.read.return_value = b'{"status":"ok","db":"connected"}'
    health = MagicMock(return_value=response)
    monkeypatch.setattr(module, "connection", database)
    monkeypatch.setattr(module, "_open_local_health", health)
    return SimpleNamespace(
        database=database, cursor=cursor, identity=identity, response=response, health=health
    )


def test_preflight_reports_authenticated_identity_grants_and_http(demo_backend: Any) -> None:
    output = StringIO()
    call_command("check_demo_mysql", stdout=output)
    report = json.loads(output.getvalue())

    assert report["status"] == "ok"
    assert report["database"] == DEMO_DATABASE
    assert report["current_user"] == "aveit_dev@%"
    assert report["mysql_version"] == "8.0.44"
    assert report["foreign_key_checks"] is True
    assert report["grants"] == {"application": True, "tests": True}
    assert report["test_database"] == f"test_{DEMO_DATABASE}"
    assert report["health"] == {"status": "ok", "db": "connected"}
    assert "sentinel-private-password" not in output.getvalue()
    assert all(
        call.args[0].lstrip().upper().startswith("SELECT")
        for call in demo_backend.cursor.execute.call_args_list
    )


@pytest.mark.parametrize(
    "field,value",
    [
        ("NAME", "aveit_tribunal_dev"),
        ("USER", "root"),
        ("HOST", "other-checkout-db"),
        ("PORT", "3307"),
        ("TEST", {"NAME": "test_other_checkout"}),
    ],
)
def test_invalid_configuration_is_rejected_before_connecting(
    demo_backend: Any, field: str, value: Any
) -> None:
    demo_backend.database.settings_dict[field] = value
    with pytest.raises(CommandError):
        call_command("check_demo_mysql")
    demo_backend.database.cursor.assert_not_called()
    demo_backend.health.assert_not_called()


@pytest.mark.parametrize("environment", ["production", "sqlite", "mock"])
def test_unsupported_environment_is_rejected_before_connecting(
    demo_backend: Any, settings: Any, monkeypatch: pytest.MonkeyPatch, environment: str
) -> None:
    if environment == "production":
        settings.DEBUG = False
    elif environment == "sqlite":
        demo_backend.database.vendor = "sqlite"
    else:
        monkeypatch.setenv("PADRON_ADAPTER", "mock")
    with pytest.raises(CommandError):
        call_command("check_demo_mysql")
    demo_backend.database.cursor.assert_not_called()


@pytest.mark.parametrize(
    "index,value",
    [
        (0, "other_actual_database"),
        (1, "anonymous@%"),
        (2, "10.11.6-MariaDB"),
        (2, "8.4.6"),
        (3, "NO_ENGINE_SUBSTITUTION"),
        (4, "latin1"),
        (5, "latin1_swedish_ci"),
        (6, 0),
        (7, 1),
        (8, "`external_role`@`%`"),
    ],
)
def test_invalid_effective_mysql_session_is_rejected(
    demo_backend: Any, index: int, value: Any
) -> None:
    demo_backend.identity[index] = value
    with pytest.raises(CommandError):
        call_command("check_demo_mysql")
    demo_backend.health.assert_not_called()


def test_select_one_must_succeed(demo_backend: Any) -> None:
    demo_backend.cursor.fetchone.side_effect = [(0,)]
    with pytest.raises(CommandError):
        call_command("check_demo_mysql")


def test_connection_errors_do_not_expose_secrets(demo_backend: Any) -> None:
    demo_backend.database.cursor.side_effect = OperationalError("sentinel-private-password")
    output = StringIO()
    with pytest.raises(CommandError) as error:
        call_command("check_demo_mysql", stdout=output)
    assert "sentinel-private-password" not in str(error.value) + output.getvalue()


@pytest.mark.parametrize("schema", [DEMO_DATABASE, r"test\_%"])
def test_missing_schema_privileges_are_rejected(demo_backend: Any, schema: str) -> None:
    demo_backend.cursor.fetchall.return_value = [
        row for row in demo_backend.cursor.fetchall.return_value if row != (schema, "CREATE")
    ]
    with pytest.raises(CommandError):
        call_command("check_demo_mysql")
    demo_backend.health.assert_not_called()


@pytest.mark.parametrize("pattern,accepted", [(r"test\_%", True), ("test_other%", False)])
def test_test_database_grant_patterns_cover_the_actual_test_database(
    demo_backend: Any, pattern: str, accepted: bool
) -> None:
    demo_backend.cursor.fetchall.return_value = [
        (schema, privilege) for schema in (DEMO_DATABASE, pattern) for privilege in PRIVILEGES
    ]
    if accepted:
        call_command("check_demo_mysql", stdout=StringIO())
    else:
        with pytest.raises(CommandError):
            call_command("check_demo_mysql")


def test_overlapping_grants_are_not_combined_into_a_false_positive(demo_backend: Any) -> None:
    demo_backend.cursor.fetchall.return_value = [
        (schema, privilege)
        for schema in (DEMO_DATABASE, r"test\_%", r"test\_aveit%")
        for privilege in PRIVILEGES
    ]
    with pytest.raises(CommandError):
        call_command("check_demo_mysql")


@pytest.mark.parametrize(
    "status,body",
    [(503, b"{}"), (200, b'{"status":"ok","db":"unavailable"}'), (200, b"not-json")],
)
def test_http_health_must_be_successful_and_connected(
    demo_backend: Any, status: int, body: bytes
) -> None:
    demo_backend.response.status = status
    demo_backend.response.read.return_value = body
    with pytest.raises(CommandError):
        call_command("check_demo_mysql")


def test_http_errors_do_not_expose_secrets(demo_backend: Any) -> None:
    demo_backend.health.side_effect = OSError("sentinel-private-password")
    with pytest.raises(CommandError) as error:
        call_command("check_demo_mysql")
    assert "sentinel-private-password" not in str(error.value)


def test_health_from_another_destination_is_rejected(demo_backend: Any) -> None:
    demo_backend.response.geturl.return_value = "http://other-backend:8000/api/health/"
    with pytest.raises(CommandError):
        call_command("check_demo_mysql")


@pytest.fixture
def local_health_server() -> Iterator[SimpleNamespace]:
    state = SimpleNamespace(redirect=False, requests=[])

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            state.requests.append(self.path)
            if state.redirect and self.path == "/api/health/":
                self.send_response(302)
                self.send_header("Location", "/other-backend/")
                self.end_headers()
                return
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status":"ok","db":"connected"}')

        def log_message(self, format: str, *args: Any) -> None:
            pass

    server = HTTPServer(("127.0.0.1", 0), Handler)
    state.url = f"http://127.0.0.1:{server.server_port}/api/health/"
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield state
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


@pytest.mark.parametrize("scenario", ["direct", "redirect", "proxy"])
def test_real_http_health_stays_on_the_local_endpoint(
    local_health_server: SimpleNamespace, monkeypatch: pytest.MonkeyPatch, scenario: str
) -> None:
    module = importlib.import_module("core.management.commands.check_demo_mysql")
    monkeypatch.setattr(module, "HEALTH_URL", local_health_server.url)
    if scenario == "proxy":
        # Evaluar el proxy de esta ejecución, sin reutilizar un opener global anterior.
        monkeypatch.setattr(urllib.request, "_opener", None)
        for variable in ("HTTP_PROXY", "http_proxy"):
            monkeypatch.setenv(variable, "http://127.0.0.1:1")
        for variable in ("NO_PROXY", "no_proxy"):
            monkeypatch.setenv(variable, "")
    if scenario == "redirect":
        local_health_server.redirect = True
        with pytest.raises(CommandError):
            module._check_http_health()
    else:
        assert module._check_http_health() == {"status": "ok", "db": "connected"}
    assert local_health_server.requests == ["/api/health/"]
