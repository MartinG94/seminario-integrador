"""Verificar el aislamiento del modelo Compose resuelto para la demo SCRUM-77."""

import base64
import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pytest

BASE_FILE = "docker-compose.yml"
DEMO_FILE = "docker-compose.scrum77-demo.yml"


def _sanitized_model(model: dict[str, Any]) -> dict[str, Any]:
    for service in model["services"].values():
        environment = service.get("environment", {})
        for key in list(environment):
            if any(word in key.lower() for word in ("password", "secret", "token", "key")):
                del environment[key]
    return model


def _render_model(
    root: Path, filename: str, project: str, environment: dict[str, str]
) -> dict[str, Any]:
    result = subprocess.run(
        [
            "docker",
            "compose",
            "-p",
            project,
            "--profile",
            "frontend",
            "-f",
            str(root / filename),
            "config",
            "--format",
            "json",
        ],
        cwd=root.parent,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert result.returncode == 0, "Compose no pudo resolver la configuración de prueba."
    return _sanitized_model(json.loads(result.stdout))


@pytest.fixture(scope="module")
def compose_models() -> dict[str, Any]:
    root = Path(os.getenv("SCRUM77_REPOSITORY_ROOT", str(Path(__file__).resolve().parents[3])))
    encoded = os.getenv("SCRUM77_COMPOSE_CONFIG_B64")
    if (
        not (root / BASE_FILE).is_file()
        and not os.getenv("SCRUM77_REPOSITORY_ROOT")
        and not encoded
    ):
        pytest.skip("La prueba Compose requiere el checkout completo, no sólo el mount /app.")
    assert (root / DEMO_FILE).is_file(), "Falta la configuración Docker aislada de SCRUM-77."

    if encoded:
        payload = json.loads(base64.b64decode(encoded, validate=True))
        for filename in (BASE_FILE, DEMO_FILE):
            digest = hashlib.sha256((root / filename).read_bytes()).hexdigest()
            assert payload["source_sha256"][filename] == digest, "Snapshot Compose desactualizado."
        return payload

    if not shutil.which("docker"):
        pytest.skip("Se necesita Docker CLI o un snapshot Compose recién generado y saneado.")

    environment = os.environ.copy()
    conflicting_environment = {
        **environment,
        "MYSQL_HOST": "other-checkout-db",
        "MYSQL_PORT": "3399",
        "MYSQL_DATABASE": "other_checkout_database",
        "MYSQL_USER": "other_checkout_user",
        "USE_SQLITE": "True",
        "PADRON_ADAPTER": "mock",
        "CORS_ALLOWED_ORIGINS": "http://other-checkout.invalid",
        "COMPOSE_PROJECT_NAME": "other-checkout",
    }
    return {
        "repository_root": str(root),
        "base": _render_model(root, BASE_FILE, "seminario-integrador", environment),
        "demo": _render_model(root, DEMO_FILE, "sgd-aveit-scrum77-demo", environment),
        "demo_conflicting_env": _render_model(
            root, DEMO_FILE, "sgd-aveit-scrum77-demo", conflicting_environment
        ),
    }


def _resource_names(model: dict[str, Any], resource: str) -> set[str]:
    return {item["name"] for item in model.get(resource, {}).values()}


def _normalized_path(value: str) -> str:
    return value.replace("\\", "/").rstrip("/").casefold()


def test_demo_docker_resources_are_disjoint(compose_models: dict[str, Any]) -> None:
    base = compose_models["base"]
    demo = compose_models["demo"]
    base_containers = {service["container_name"] for service in base["services"].values()}
    demo_containers = {service["container_name"] for service in demo["services"].values()}

    assert base["name"] != demo["name"]
    assert len(demo_containers) == len(demo["services"])
    assert base_containers.isdisjoint(demo_containers)
    assert _resource_names(base, "networks").isdisjoint(_resource_names(demo, "networks"))
    assert _resource_names(base, "volumes").isdisjoint(_resource_names(demo, "volumes"))


def test_mysql_uses_a_dedicated_persistent_volume(compose_models: dict[str, Any]) -> None:
    demo = compose_models["demo"]
    mounts = [
        mount for mount in demo["services"]["db"]["volumes"] if mount["target"] == "/var/lib/mysql"
    ]

    assert len(mounts) == 1
    assert mounts[0]["type"] == "volume"
    actual_name = demo["volumes"][mounts[0]["source"]]["name"]
    assert actual_name == "sgd_aveit_scrum77_demo_mysql_data"
    assert actual_name not in _resource_names(compose_models["base"], "volumes")


def test_demo_publications_are_loopback_and_do_not_inherit_base_ports(
    compose_models: dict[str, Any],
) -> None:
    base_ports = {
        str(port["published"])
        for service in compose_models["base"]["services"].values()
        for port in service.get("ports", [])
    }
    demo_ports = set()
    for name, service in compose_models["demo"]["services"].items():
        ports = service.get("ports", [])
        if name == "demo-setup":
            assert not ports
            continue
        assert len(ports) == 1
        assert ports[0]["host_ip"] == "127.0.0.1"
        demo_ports.add(str(ports[0]["published"]))

    assert len(demo_ports) == 3
    assert demo_ports.isdisjoint(base_ports)


@pytest.mark.parametrize(
    "service,directory",
    [("backend", "backend"), ("demo-setup", "backend"), ("frontend", "frontend")],
)
def test_application_mounts_use_the_checkout_containing_the_compose_file(
    compose_models: dict[str, Any], service: str, directory: str
) -> None:
    mounts = compose_models["demo"]["services"][service]["volumes"]
    application = [mount for mount in mounts if mount["target"] == "/app"]
    assert len(application) == 1
    assert application[0]["type"] == "bind"
    expected = f"{compose_models['repository_root']}/{directory}"
    assert _normalized_path(application[0]["source"]) == _normalized_path(expected)


def test_demo_database_and_adapter_are_explicit(compose_models: dict[str, Any]) -> None:
    services = compose_models["demo"]["services"]
    database = services["db"]["environment"]
    backend = services["backend"]["environment"]

    assert database["MYSQL_DATABASE"] == "aveit_tribunal_scrum77_demo"
    assert backend["DATABASE_NAME"] == database["MYSQL_DATABASE"]
    assert backend["DATABASE_USER"] == database["MYSQL_USER"]
    assert backend["DATABASE_HOST"] == "db"
    assert str(backend["DATABASE_PORT"]) == "3306"
    assert str(backend["USE_SQLITE"]).lower() == "false"
    assert backend["PADRON_ADAPTER"] == "database"


def test_demo_spa_uses_its_backend_and_matching_origin(compose_models: dict[str, Any]) -> None:
    services = compose_models["demo"]["services"]
    frontend = services["frontend"]
    assert "frontend" in frontend["profiles"]
    assert frontend["depends_on"]["backend"]["condition"] == "service_healthy"
    assert services["backend"]["depends_on"]["db"]["condition"] == "service_healthy"
    published = frontend["ports"][0]["published"]
    origins = services["backend"]["environment"]["CORS_ALLOWED_ORIGINS"].split(",")
    assert f"http://localhost:{published}" in origins
    assert f"http://127.0.0.1:{published}" in origins
    command = frontend["command"]
    assert command[command.index("--proxy-config") + 1] == "proxy.docker.conf.json"
    assert services["backend"]["networks"].keys() == frontend["networks"].keys()


def test_demo_initializes_data_before_exposing_the_spa(compose_models: dict[str, Any]) -> None:
    """Una copia sin volumen debe cargar el catálogo sin una intervención local oculta."""
    services = compose_models["demo"]["services"]
    assert "demo-setup" in services, "El arranque todavía omite preparar/cargar la demo."
    setup = services["demo-setup"]
    assert setup["depends_on"]["backend"]["condition"] == "service_healthy"
    assert setup["network_mode"] == "service:backend"
    assert setup["environment"] == services["backend"]["environment"]
    assert setup["volumes"] == services["backend"]["volumes"]
    assert setup.get("restart", "no") == "no"
    assert not setup.get("ports")
    assert not setup.get("healthcheck")
    assert services["frontend"]["depends_on"]["demo-setup"]["condition"] == (
        "service_completed_successfully"
    )
    command = setup["command"]
    assert command[:2] == ["sh", "-c"]
    assert "python manage.py prepare_demo_schema &&" in command[2]
    assert "python manage.py seed_expedientes --profile scrum77-g57-g60-v1" in command[2]


def test_generic_environment_does_not_redirect_demo(compose_models: dict[str, Any]) -> None:
    assert compose_models["demo_conflicting_env"] == compose_models["demo"]
