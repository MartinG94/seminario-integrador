"""Pruebas de autorización RBAC: CA2 (mapeo legado) y CA3 (403 server-side)."""

import io
import logging

import pytest

from accounts.legacy_rbac import (
    LEGACY_PERMISSION_TO_ROLES,
    LEGACY_POSITION_TO_ROLE,
    UNMAPPED_LEGACY_POSITIONS,
    role_for_legacy_position,
    satisfies_legacy_permission,
)
from socios.models import Role
from tests.conftest import VALID_PASSWORD

PADRON_URL = "/api/v1/socios/"
ME_URL = "/api/v1/auth/me/"


@pytest.fixture
def security_log() -> io.StringIO:
    buffer = io.StringIO()
    handler = logging.StreamHandler(buffer)
    handler.setFormatter(logging.Formatter("%(levelname)s %(message)s"))
    logger = logging.getLogger("security")
    logger.addHandler(handler)
    try:
        yield buffer
    finally:
        logger.removeHandler(handler)


# --- 3. Usuario autenticado con permiso suficiente -> acceso permitido -----


@pytest.mark.parametrize("role", [Role.TD, Role.CD, Role.ADMIN])
@pytest.mark.django_db
def test_authorized_roles_can_list_padron(make_socio, authenticate, role):
    socio = make_socio(legajo=f"1000{role}", role=role)
    client = authenticate(socio)

    response = client.get(PADRON_URL)

    assert response.status_code == 200


@pytest.mark.django_db
def test_any_authenticated_socio_can_read_own_profile(make_socio, authenticate):
    socio = make_socio(legajo="74907", role=Role.SOCIO)
    client = authenticate(socio)

    response = client.get(ME_URL)

    assert response.status_code == 200
    assert response.data["legajo"] == "74907"


# --- 4. Usuario autenticado sin permiso -> 403 -----------------------------


@pytest.mark.parametrize("role", [Role.SOCIO, Role.FISCALIZADORA])
@pytest.mark.django_db
def test_unauthorized_roles_get_403_on_padron(make_socio, authenticate, role):
    socio = make_socio(legajo=f"2000{role}", role=role)
    client = authenticate(socio)

    response = client.get(PADRON_URL)

    assert response.status_code == 403
    assert "results" not in response.data


@pytest.mark.django_db
def test_disabled_account_cannot_use_previously_issued_token(
    make_socio, authenticate
):
    """La autorización se revalida contra el padrón, no contra el token."""
    socio = make_socio(legajo="74907", role=Role.TD)
    client = authenticate(socio)
    assert client.get(PADRON_URL).status_code == 200

    socio.is_enabled = False
    socio.save()

    assert client.get(PADRON_URL).status_code == 403


@pytest.mark.django_db
def test_role_downgrade_takes_effect_immediately(make_socio, authenticate):
    socio = make_socio(legajo="74907", role=Role.TD)
    client = authenticate(socio)
    assert client.get(PADRON_URL).status_code == 200

    socio.role = Role.SOCIO
    socio.save()

    assert client.get(PADRON_URL).status_code == 403


# --- 5. Acceso directo a ruta protegida sin pasar por la UI ----------------


@pytest.mark.django_db
def test_direct_access_without_token_is_rejected(api_client, make_socio):
    """CA3: la protección no depende de que la SPA oculte el enlace."""
    make_socio(legajo="74907", role=Role.TD)

    assert api_client.get(PADRON_URL).status_code == 401
    assert api_client.get(ME_URL).status_code == 401


@pytest.mark.django_db
def test_direct_access_with_malformed_token_is_rejected(api_client):
    api_client.credentials(HTTP_AUTHORIZATION="Bearer no-es-un-jwt")

    assert api_client.get(PADRON_URL).status_code == 401


@pytest.mark.django_db
def test_denied_access_is_audited(make_socio, authenticate, security_log):
    socio = make_socio(legajo="74907", role=Role.SOCIO)
    client = authenticate(socio)

    client.get(PADRON_URL)

    logged = security_log.getvalue()
    assert "event=ACCESS_DENIED" in logged
    assert f"resource={PADRON_URL}" in logged
    assert "role=SOCIO" in logged
    assert VALID_PASSWORD not in logged


@pytest.mark.django_db
def test_granted_access_is_audited(make_socio, authenticate, security_log):
    socio = make_socio(legajo="74907", role=Role.TD)
    client = authenticate(socio)

    client.get(PADRON_URL)

    logged = security_log.getvalue()
    assert "event=ACCESS_GRANTED" in logged
    assert "role=TD" in logged


# --- 8. Mapeo de permisos legados y cargos al RBAC documentado -------------


@pytest.mark.parametrize(
    "legacy_permission,expected_roles",
    [
        ("tribunal_bajo", {Role.SOCIO, Role.FISCALIZADORA, Role.CD, Role.TD, Role.ADMIN}),
        ("tribunal_medio", {Role.CD, Role.TD}),
        ("tribunal_alto", {Role.TD}),
    ],
)
def test_legacy_permission_maps_to_documented_roles(
    legacy_permission, expected_roles
):
    assert set(LEGACY_PERMISSION_TO_ROLES[legacy_permission]) == expected_roles


def test_legacy_permission_hierarchy_is_cumulative():
    """Quien alcanzaba un nivel alto alcanzaba también los inferiores."""
    assert satisfies_legacy_permission(Role.TD, "tribunal_bajo")
    assert satisfies_legacy_permission(Role.TD, "tribunal_medio")
    assert satisfies_legacy_permission(Role.TD, "tribunal_alto")

    assert satisfies_legacy_permission(Role.CD, "tribunal_medio")
    assert not satisfies_legacy_permission(Role.CD, "tribunal_alto")

    assert satisfies_legacy_permission(Role.SOCIO, "tribunal_bajo")
    assert not satisfies_legacy_permission(Role.SOCIO, "tribunal_medio")


def test_tribunal_alto_is_exclusive_to_tribunal():
    """Sólo el TD dictamina, resuelve y firma disposiciones."""
    for role in (Role.SOCIO, Role.FISCALIZADORA, Role.CD, Role.ADMIN):
        assert not satisfies_legacy_permission(role, "tribunal_alto")


@pytest.mark.parametrize(
    "position_id,expected_role",
    [
        (1, Role.FISCALIZADORA),  # Presidente de Subcomisión
        (2, Role.FISCALIZADORA),  # Vicepresidente de Subcomisión
        (3, Role.CD),  # Presidente de AVEIT
        (5, Role.CD),  # Tesorero
        (8, Role.CD),  # Secretario General
        (9, Role.CD),  # Prosecretario
        (10, Role.TD),  # Titular del Tribunal de Disciplina
        (11, Role.TD),  # Suplente del Tribunal de Disciplina
        (12, Role.SOCIO),  # Socio Ordinario
    ],
)
def test_legacy_position_maps_to_expected_role(position_id, expected_role):
    assert role_for_legacy_position(position_id) == expected_role


def test_all_fifteen_legacy_positions_are_accounted_for():
    """Los 15 cargos de `socio_tipoSocio` están mapeados o marcados como pendientes."""
    covered = set(LEGACY_POSITION_TO_ROLE) | set(UNMAPPED_LEGACY_POSITIONS)
    assert covered == set(range(1, 16))
    assert not set(LEGACY_POSITION_TO_ROLE) & set(UNMAPPED_LEGACY_POSITIONS)


@pytest.mark.parametrize("position_id", sorted(UNMAPPED_LEGACY_POSITIONS))
def test_unmapped_positions_default_to_least_privilege(position_id):
    """Sin decisión del PO, el cargo ambiguo se migra con privilegio mínimo."""
    assert role_for_legacy_position(position_id) == Role.SOCIO


def test_legacy_positions_only_map_to_defined_roles():
    valid_roles = set(Role.values)
    assert set(LEGACY_POSITION_TO_ROLE.values()) <= valid_roles
    for roles in LEGACY_PERMISSION_TO_ROLES.values():
        assert set(roles) <= valid_roles
