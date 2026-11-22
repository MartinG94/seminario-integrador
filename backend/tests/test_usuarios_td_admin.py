"""Gestión de miembros con rol TD (Spec 011, T6): nómina, alta, revocación y auditoría."""

import io
import logging

import pytest
from django.core.exceptions import ValidationError

from core.models import TribunalRoleAction, TribunalRoleChange
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
    assert not TribunalRoleChange.objects.exists()


# --- RF-10: nómina ---


@pytest.mark.django_db
def test_admin_lists_only_td_members_with_atomic_fields(admin_client, make_socio) -> None:
    primero = make_socio(legajo="11239", role=Role.TD, social_year=6)
    primero.numero_socio = 1033
    primero.save(update_fields=["numero_socio"])
    make_socio(legajo="11737", role=Role.TD, social_year=4)
    make_socio(legajo="74907", role=Role.SOCIO)
    make_socio(legajo="87414", role=Role.CD)

    response = admin_client.get(LIST_URL)

    assert response.status_code == 200
    assert [m["legajo"] for m in response.data] == ["11239", "11737"]
    assert [m["numero_socio"] for m in response.data] == [1033, None]
    assert set(response.data[0]) == {
        "id",
        "numero_socio",
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
    cambio = TribunalRoleChange.objects.get()
    assert (cambio.socio_id, cambio.action, cambio.previous_role, cambio.new_role) == (
        candidato.pk,
        TribunalRoleAction.GRANT,
        Role.SOCIO,
        Role.TD,
    )
    assert cambio.author == admin.user
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
    assert not TribunalRoleChange.objects.exists()


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
    cambio = TribunalRoleChange.objects.get()
    assert (cambio.action, cambio.previous_role, cambio.new_role, cambio.author) == (
        TribunalRoleAction.REVOKE,
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
    assert not TribunalRoleChange.objects.exists()


@pytest.mark.django_db
def test_role_audit_records_are_immutable(admin_client, make_socio) -> None:
    miembro = make_socio(legajo="11239", role=Role.TD)
    admin_client.delete(detail_url(miembro.pk))
    cambio = TribunalRoleChange.objects.get()

    cambio.new_role = Role.ADMIN
    with pytest.raises(ValidationError):
        cambio.save()
    with pytest.raises(ValidationError):
        cambio.delete()


# --- Revisión PR #78: seguridad, candidatos e inmutabilidad ---

CANDIDATES_URL = f"{LIST_URL}candidatos/"


@pytest.mark.django_db
def test_anonymous_writes_are_rejected_with_401(api_client, make_socio) -> None:
    socio = make_socio(legajo="50001")
    miembro = make_socio(legajo="50002", role=Role.TD)

    assert api_client.post(LIST_URL, {"socio_id": socio.pk}, format="json").status_code == 401
    assert api_client.delete(detail_url(miembro.pk)).status_code == 401
    assert api_client.get(CANDIDATES_URL, {"search": "Apellido"}).status_code == 401
    assert (
        api_client.put(
            "/api/v1/admin/parametros/plazo_descargo_dias_habiles/", {"valor": 7}
        ).status_code
        == 401
    )
    assert not TribunalRoleChange.objects.exists()


@pytest.mark.django_db
def test_disabled_admin_cannot_manage_members(admin, admin_client, make_socio) -> None:
    candidato = make_socio(legajo="50001")
    admin.is_enabled = False
    admin.save(update_fields=["is_enabled"])

    assert admin_client.get(LIST_URL).status_code == 403
    assert admin_client.post(LIST_URL, {"socio_id": candidato.pk}, format="json").status_code == 403
    candidato.refresh_from_db()
    assert candidato.role == Role.SOCIO


@pytest.mark.django_db
def test_token_issued_before_revocation_is_rejected(admin_client, make_socio) -> None:
    from rest_framework.test import APIClient

    miembro = make_socio(legajo="11239", role=Role.TD)
    login = APIClient().post(
        "/api/v1/auth/login/",
        {"identifier": "11239", "password": "Aveit-Test-2026!"},
        format="json",
    )
    token_previo = login.data["access"]
    cliente_previo = APIClient()
    cliente_previo.credentials(HTTP_AUTHORIZATION=f"Bearer {token_previo}")
    assert cliente_previo.get(PADRON_URL).status_code == 200

    assert admin_client.delete(detail_url(miembro.pk)).status_code == 204

    # El mismo JWT, emitido antes de la baja, ya no habilita permisos de Tribunal.
    assert cliente_previo.get(PADRON_URL).status_code == 403


@pytest.mark.django_db
def test_revocation_is_written_to_the_security_log(admin_client, make_socio, security_log) -> None:
    miembro = make_socio(legajo="11239", role=Role.TD)

    admin_client.delete(detail_url(miembro.pk))

    assert "event=ROLE_CHANGED user=403655 target=11239 previous_role=TD new_role=SOCIO" in (
        security_log.getvalue()
    )


@pytest.mark.django_db
def test_inactive_user_account_cannot_be_designated(admin_client, make_socio) -> None:
    socio = make_socio(legajo="60002")
    socio.user.is_active = False
    socio.user.save(update_fields=["is_active"])

    response = admin_client.post(LIST_URL, {"socio_id": socio.pk}, format="json")

    assert response.status_code == 400
    assert "habilitada" in response.data["detail"]
    socio.refresh_from_db()
    assert socio.role == Role.SOCIO


@pytest.mark.django_db
def test_candidates_are_searched_server_side_beyond_the_first_page(
    admin_client, make_socio
) -> None:
    for indice in range(30):
        make_socio(legajo=f"7{indice:04d}")
    objetivo = make_socio(legajo="79999")
    objetivo.last_name = "Zubiría"
    objetivo.numero_socio = 4321
    objetivo.save(update_fields=["last_name", "numero_socio"])
    directivo = make_socio(legajo="80000", role=Role.CD)
    directivo.last_name = "Zubiria Directivo"
    directivo.save(update_fields=["last_name"])
    inhabilitado = make_socio(legajo="80001", is_enabled=False)
    inhabilitado.last_name = "Zubiria Inhabilitado"
    inhabilitado.save(update_fields=["last_name"])

    por_apellido = admin_client.get(CANDIDATES_URL, {"search": "zubiria"})
    por_numero = admin_client.get(CANDIDATES_URL, {"search": "4321"})
    corto = admin_client.get(CANDIDATES_URL, {"search": ""})

    assert por_apellido.status_code == 200
    assert [c["id"] for c in por_apellido.data] == [objetivo.pk]
    assert set(por_apellido.data[0]) == {
        "id",
        "numero_socio",
        "last_name",
        "first_name",
        "social_year",
        "subcomision",
    }
    assert [c["numero_socio"] for c in por_numero.data] == [4321]
    assert corto.data == []


@pytest.mark.django_db
def test_candidates_endpoint_is_admin_only(make_socio, authenticate) -> None:
    client = authenticate(make_socio(legajo="40TD", role=Role.TD))
    assert client.get(CANDIDATES_URL, {"search": "Apellido"}).status_code == 403


@pytest.mark.django_db
def test_bulk_updates_and_deletes_on_audit_records_are_blocked(admin_client, make_socio) -> None:
    miembro = make_socio(legajo="11239", role=Role.TD)
    admin_client.delete(detail_url(miembro.pk))
    cambio = TribunalRoleChange.objects.get()

    with pytest.raises(ValidationError):
        TribunalRoleChange.objects.filter(pk=cambio.pk).update(new_role=Role.ADMIN)
    with pytest.raises(ValidationError):
        TribunalRoleChange.objects.all().delete()
    with pytest.raises(ValidationError):
        cambio.save(force_update=True)
    with pytest.raises(ValidationError):
        TribunalRoleChange(
            pk=cambio.pk,
            socio=miembro,
            action=TribunalRoleAction.GRANT,
            previous_role=Role.SOCIO,
            new_role=Role.TD,
            author=cambio.author,
        ).save()
    cambio.refresh_from_db()
    assert cambio.new_role == Role.SOCIO
