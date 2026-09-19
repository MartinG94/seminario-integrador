"""Pruebas de autenticación: CA1 (401 sin filtración) y CA4 (expiración, auditoría)."""

import io
import logging
from datetime import datetime, timedelta, timezone

import pytest
from rest_framework_simplejwt.tokens import AccessToken

from socios.models import Role, SocialCategory
from tests.conftest import VALID_PASSWORD

LOGIN_URL = "/api/v1/auth/login/"
ME_URL = "/api/v1/auth/me/"
PADRON_URL = "/api/v1/socios/"


@pytest.fixture
def security_log() -> io.StringIO:
    """Captura la pista de auditoría.

    El logger `security` no propaga al root, así que `caplog` no lo ve: se le
    adjunta un handler propio en memoria.
    """
    buffer = io.StringIO()
    handler = logging.StreamHandler(buffer)
    handler.setFormatter(logging.Formatter("%(levelname)s %(message)s"))
    logger = logging.getLogger("security")
    logger.addHandler(handler)
    try:
        yield buffer
    finally:
        logger.removeHandler(handler)


# --- 1. Login con credenciales válidas -> 200 + token válido ---------------


@pytest.mark.django_db
def test_login_success_returns_tokens_and_profile(api_client, make_socio):
    socio = make_socio(legajo="74907", role=Role.TD, social_year=5)

    response = api_client.post(
        LOGIN_URL,
        {"identifier": "74907", "password": VALID_PASSWORD},
        format="json",
    )

    assert response.status_code == 200
    assert response.data["access"]
    assert response.data["refresh"]
    assert response.data["user"]["legajo"] == socio.legajo
    assert response.data["user"]["role"] == Role.TD
    assert response.data["user"]["category"] == SocialCategory.ACTIVE
    assert response.data["user"]["category_display"] == "Activo"
    # El perfil devuelto no debe arrastrar credenciales.
    assert "password" not in response.data["user"]


@pytest.mark.django_db
def test_login_accepts_email_as_identifier(api_client, make_socio):
    make_socio(legajo="85194", email="lucas@aveit.test")

    response = api_client.post(
        LOGIN_URL,
        {"identifier": "lucas@aveit.test", "password": VALID_PASSWORD},
        format="json",
    )

    assert response.status_code == 200


@pytest.mark.django_db
def test_access_token_carries_rbac_claims(api_client, make_socio):
    make_socio(legajo="408917", role=Role.CD, social_year=6)

    response = api_client.post(
        LOGIN_URL,
        {"identifier": "408917", "password": VALID_PASSWORD},
        format="json",
    )

    claims = AccessToken(response.data["access"])
    assert claims["legajo"] == "408917"
    assert claims["role"] == Role.CD
    assert claims["category"] == SocialCategory.ACTIVE


# --- 2. Login con credenciales inválidas -> 401 sin filtración -------------


@pytest.mark.django_db
def test_login_wrong_password_returns_401(api_client, make_socio):
    make_socio(legajo="74907")

    response = api_client.post(
        LOGIN_URL,
        {"identifier": "74907", "password": "contrasena-incorrecta"},
        format="json",
    )

    assert response.status_code == 401
    assert "access" not in response.data
    assert "refresh" not in response.data
    assert "user" not in response.data


@pytest.mark.django_db
def test_login_failures_are_indistinguishable(api_client, make_socio):
    """CA1: no debe poder deducirse si el usuario existe ni el motivo real."""
    make_socio(legajo="74907", email="existe@aveit.test")
    make_socio(legajo="99999", email="baja@aveit.test", is_enabled=False)

    unknown_user = api_client.post(
        LOGIN_URL,
        {"identifier": "00000", "password": VALID_PASSWORD},
        format="json",
    )
    wrong_password = api_client.post(
        LOGIN_URL,
        {"identifier": "74907", "password": "otra-clave"},
        format="json",
    )
    disabled_account = api_client.post(
        LOGIN_URL,
        {"identifier": "99999", "password": VALID_PASSWORD},
        format="json",
    )

    statuses = {
        unknown_user.status_code,
        wrong_password.status_code,
        disabled_account.status_code,
    }
    bodies = {
        str(unknown_user.data),
        str(wrong_password.data),
        str(disabled_account.data),
    }
    assert statuses == {401}
    # Un único cuerpo de respuesta para los tres motivos de rechazo.
    assert len(bodies) == 1

    body = str(unknown_user.data).lower()
    for leak in ("existe@aveit.test", "baja@aveit.test", "apellido", "inactiv",
                 "deshabilit", "no existe", "password", "contraseña"):
        assert leak not in body


# --- 6. Token expirado -> acceso rechazado --------------------------------


@pytest.mark.django_db
def test_expired_token_is_rejected(api_client, make_socio):
    socio = make_socio(legajo="74907", role=Role.TD)

    token = AccessToken.for_user(socio.user)
    token.set_exp(
        from_time=datetime.now(timezone.utc) - timedelta(hours=2),
        lifetime=timedelta(minutes=60),
    )
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    assert api_client.get(ME_URL).status_code == 401
    assert api_client.get(PADRON_URL).status_code == 401


@pytest.mark.django_db
def test_valid_token_has_limited_lifetime(api_client, make_socio):
    """CA4: la sesión dura 60 minutos, no indefinidamente."""
    socio = make_socio(legajo="74907")

    token = AccessToken.for_user(socio.user)
    lifetime = datetime.fromtimestamp(
        token["exp"], tz=timezone.utc
    ) - datetime.fromtimestamp(token["iat"], tz=timezone.utc)

    assert lifetime == timedelta(minutes=60)


# --- 7. La auditoría no contiene contraseñas ni tokens completos -----------


@pytest.mark.django_db
def test_audit_logs_success_and_failure_without_secrets(
    api_client, make_socio, security_log
):
    make_socio(legajo="74907", role=Role.TD)

    ok = api_client.post(
        LOGIN_URL,
        {"identifier": "74907", "password": VALID_PASSWORD},
        format="json",
    )
    api_client.post(
        LOGIN_URL,
        {"identifier": "74907", "password": VALID_PASSWORD + "-mala"},
        format="json",
    )

    logged = security_log.getvalue()

    # Diferencia eventos de autenticación exitosa y fallida.
    assert "event=AUTH_SUCCESS" in logged
    assert "event=AUTH_FAILURE" in logged
    assert "result=GRANTED" in logged
    assert "result=DENIED" in logged
    # Identifica al usuario y el motivo interno del rechazo.
    assert "user=74907" in logged
    assert "reason=BAD_PASSWORD" in logged

    # Nunca contraseñas ni tokens completos.
    assert VALID_PASSWORD not in logged
    assert (VALID_PASSWORD + "-mala") not in logged
    assert ok.data["access"] not in logged
    assert ok.data["refresh"] not in logged
    for token_segment in ok.data["access"].split("."):
        assert token_segment not in logged


@pytest.mark.django_db
def test_audit_truncates_oversized_identifier(api_client, security_log):
    """Si alguien pega su contraseña en el campo usuario, no se vuelca entera."""
    oversized = "x" * 200

    api_client.post(
        LOGIN_URL, {"identifier": oversized, "password": "y"}, format="json"
    )

    logged = security_log.getvalue()
    assert oversized not in logged
    assert "(truncado)" in logged
