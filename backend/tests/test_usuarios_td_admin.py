"""Gestión de miembros con rol TD (Spec 010, T6): nómina, alta, revocación y auditoría."""

import io
import logging

import pytest
from django.core.exceptions import ValidationError

from core.models import AccionRolTribunal, CambioRolTribunal
from socios.models import Role, Socio

LIST_URL = "/api/v1/admin/usuarios-td/"
PADRON_URL = "/api/v1/socios/"


def detail_url(socio_id: int) -> str:
    return f"{LIST_URL}{socio_id}/"


@pytest.fixture
def admin(make_socio) -> Socio:
    return make_socio(legajo="403655", role=Role.ADMIN)


@pytest.fixture
def admin_client(admin, authenticate):
    return authenticate(admin)


@pytest.fixture
def security_log() -> io.StringIO:
    buffer = io.StringIO()
    handler = logging.StreamHandler(buffer)
    logger = logging.getLogger("security")
    logger.addHandler(handler)
    try:
        yield buffer
    finally:
        logger.removeHandler(handler)


# --- RF-01 ---


@pytest.mark.django_db
def test_anonymous_request_is_rejected(api_client) -> None:
    assert api_client.get(LIST_URL).status_code == 401


@pytest.mark.parametrize("role", [Role.SOCIO, Role.FISCALIZADORA, Role.CD, Role.TD])
@pytest.mark.django_db
def test_non_admin_roles_cannot_manage_members(make_socio, authenticate, role) -> None:
    candidato = make_socio(legajo="50001")
    miembro = make_socio(legajo="50002", role=Role.TD)
    client = authenticate(make_socio(legajo=f"40{role}", role=role))

    assert client.get(LIST_URL).status_code == 403
    assert client.post(LIST_URL, {"socio_id": candidato.pk}, format="json").status_code == 403
    assert client.delete(detail_url(miembro.pk)).status_code == 403
    candidato.refresh_from_db()
    miembro.refresh_from_db()
    assert (candidato.role, miembro.role) == (Role.SOCIO, Role.TD)
    assert not CambioRolTribunal.objects.exists()


# --- RF-10: nómina ---


@pytest.mark.django_db
def test_admin_lists_only_td_members_with_atomic_fields(admin_client, make_socio) -> None:
    make_socio(legajo="11239", role=Role.TD, social_year=6)
    make_socio(legajo="11737", role=Role.TD, social_year=4)
    make_socio(legajo="74907", role=Role.SOCIO)
    make_socio(legajo="87414", role=Role.CD)

    response = admin_client.get(LIST_URL)

    assert response.status_code == 200
    assert [m["legajo"] for m in response.data] == ["11239", "11737"]
    assert set(response.data[0]) == {
        "id",
        "legajo",
        "last_name",
        "first_name",
        "social_year",
        "email",
        "subcomision",
    }
    assert response.data[0]["last_name"] == "Apellido11239"
    assert response.data[0]["social_year"] == 6


# --- RF-11 / RF-13: alta ---


@pytest.mark.django_db
def test_admin_assigns_td_role_with_audit(admin, admin_client, make_socio, security_log) -> None:
    candidato = make_socio(legajo="12123", social_year=5)

    response = admin_client.post(LIST_URL, {"socio_id": candidato.pk}, format="json")

    assert response.status_code == 201
    assert response.data["legajo"] == "12123"
    candidato.refresh_from_db()
    assert candidato.role == Role.TD
    cambio = CambioRolTribunal.objects.get()
    assert (cambio.socio_id, cambio.accion, cambio.rol_anterior, cambio.rol_nuevo) == (
        candidato.pk,
        AccionRolTribunal.ALTA,
        Role.SOCIO,
        Role.TD,
    )
    assert cambio.autor == admin.user
    assert "event=ROLE_CHANGED user=403655 target=12123 previous_role=SOCIO new_role=TD" in (
        security_log.getvalue()
    )
    assert [m["legajo"] for m in admin_client.get(LIST_URL).data] == ["12123"]


@pytest.mark.django_db
def test_new_member_gains_tribunal_permissions_immediately(
    admin_client, make_socio, api_client
) -> None:
    candidato = make_socio(legajo="12123")
    admin_client.post(LIST_URL, {"socio_id": candidato.pk}, format="json")

    api_client.credentials()
    login = api_client.post(
        "/api/v1/auth/login/", {"identifier": "12123", "password": "Aveit-Test-2026!"}
    )
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")

    assert login.data["user"]["role"] == Role.TD
    assert api_client.get(PADRON_URL).status_code == 200


@pytest.mark.parametrize(
    ("role", "is_enabled", "fragment"),
    [
        (Role.TD, True, "ya integra"),
        (Role.CD, True, "Comisión Directiva"),
        (Role.FISCALIZADORA, True, "Socio Ordinario"),
        (Role.ADMIN, True, "Socio Ordinario"),
        (Role.SOCIO, False, "habilitada"),
    ],
)
@pytest.mark.django_db
def test_ineligible_socios_are_rejected(
    admin_client, make_socio, role, is_enabled, fragment
) -> None:
    socio = make_socio(legajo="60001", role=role, is_enabled=is_enabled)

    response = admin_client.post(LIST_URL, {"socio_id": socio.pk}, format="json")

    assert response.status_code == 400
    assert fragment in response.data["detail"]
    socio.refresh_from_db()
    assert socio.role == role
    assert not CambioRolTribunal.objects.exists()


@pytest.mark.parametrize("payload", [{}, {"socio_id": None}, {"socio_id": "abc"}, {"socio_id": 0}])
@pytest.mark.django_db
def test_malformed_assignment_is_rejected(admin_client, payload) -> None:
    response = admin_client.post(LIST_URL, payload, format="json")

    assert response.status_code == 400
    assert "socio" in response.data["socio_id"][0]


@pytest.mark.django_db
def test_unknown_socio_is_rejected(admin_client) -> None:
    response = admin_client.post(LIST_URL, {"socio_id": 999999}, format="json")

    assert response.status_code == 400
    assert "no existe" in response.data["detail"]


# --- RF-12 / RF-13: revocación ---


@pytest.mark.django_db
def test_admin_revokes_td_role_back_to_ordinary_socio(
    admin, admin_client, make_socio, authenticate, api_client
) -> None:
    miembro = make_socio(legajo="11239", role=Role.TD)

    response = admin_client.delete(detail_url(miembro.pk))

    assert response.status_code == 204
    miembro.refresh_from_db()
    assert miembro.role == Role.SOCIO
    cambio = CambioRolTribunal.objects.get()
    assert (cambio.accion, cambio.rol_anterior, cambio.rol_nuevo, cambio.autor) == (
        AccionRolTribunal.BAJA,
        Role.TD,
        Role.SOCIO,
        admin.user,
    )
    assert admin_client.get(LIST_URL).data == []
    # El permiso se relee del padrón: la baja rige sin esperar a que venza el token.
    assert authenticate(miembro).get(PADRON_URL).status_code == 403


@pytest.mark.django_db
def test_revoking_someone_outside_the_tribunal_returns_404(admin_client, make_socio) -> None:
    directivo = make_socio(legajo="87414", role=Role.CD)

    assert admin_client.delete(detail_url(directivo.pk)).status_code == 404
    assert admin_client.delete(detail_url(999999)).status_code == 404
    directivo.refresh_from_db()
    assert directivo.role == Role.CD
    assert not CambioRolTribunal.objects.exists()


@pytest.mark.django_db
def test_role_audit_records_are_immutable(admin_client, make_socio) -> None:
    miembro = make_socio(legajo="11239", role=Role.TD)
    admin_client.delete(detail_url(miembro.pk))
    cambio = CambioRolTribunal.objects.get()

    cambio.rol_nuevo = Role.ADMIN
    with pytest.raises(ValidationError):
        cambio.save()
    with pytest.raises(ValidationError):
        cambio.delete()
