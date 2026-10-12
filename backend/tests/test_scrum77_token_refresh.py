"""TS77.42: clasificación actual sin reutilizar claims sociales históricos."""

from collections.abc import Callable
from datetime import datetime, timedelta, timezone

import pytest
from django.apps import apps
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt import serializers as jwt_serializers
from rest_framework_simplejwt import tokens as jwt_tokens
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

from socios.models import Role, SocialCategory, Socio
from tests.conftest import VALID_PASSWORD

pytestmark = pytest.mark.django_db

LOGIN_URL = "/api/v1/auth/login/"
REFRESH_URL = "/api/v1/auth/refresh/"
ME_URL = "/api/v1/auth/me/"
PADRON_URL = "/api/v1/socios/"


def _classified_socio(
    make_socio: Callable[..., Socio], social_year: int | None, role: str = Role.CD
) -> Socio:
    socio = make_socio(social_year=1 if social_year is None else social_year, role=role)
    if social_year is None:
        socio.category = SocialCategory.EX_TRAVELER
        socio.social_year = None
        socio.save(update_fields=["category", "social_year"])
    return socio


def _historical_token(socio: Socio, category: str | None = "PASSIVE") -> RefreshToken:
    token = RefreshToken.for_user(socio.user)
    token["legajo"] = socio.legajo
    token["role"] = socio.role
    if category is not None:
        token["category"] = category
    return token


@pytest.mark.parametrize(
    "social_year,category,label",
    [
        (1, "JUNIOR", "Junior"),
        (2, "JUNIOR", "Junior"),
        (3, "SENIOR", "Senior"),
        (4, "SENIOR", "Senior"),
        (6, "SENIOR", "Senior"),
        (None, "EX_TRAVELER", "Exviajero"),
    ],
)
def test_login_tokens_and_profile_share_persisted_classification(
    api_client: APIClient,
    make_socio: Callable[..., Socio],
    social_year: int | None,
    category: str,
    label: str,
) -> None:
    socio = _classified_socio(make_socio, social_year)
    original = (socio.pk, socio.user_id, socio.user.password, socio.role, socio.is_enabled)

    response = api_client.post(
        LOGIN_URL,
        {"identifier": socio.legajo, "password": VALID_PASSWORD},
        format="json",
    )

    assert response.status_code == 200
    for token in (
        AccessToken(response.data["access"]),
        RefreshToken(response.data["refresh"]),
    ):
        assert token["category"] == category
        assert token["legajo"] == socio.legajo
        assert token["role"] == Role.CD
        assert str(token["user_id"]) == str(socio.user_id)
    assert response.data["user"]["category"] == category
    assert response.data["user"]["category_display"] == label
    assert "password" not in response.data["user"]
    socio.refresh_from_db()
    socio.user.refresh_from_db()
    assert (socio.pk, socio.user_id, socio.user.password, socio.role, socio.is_enabled) == original


@pytest.mark.parametrize(
    "social_year,historical_category,current_category",
    [
        (3, "PASSIVE", "SENIOR"),
        (2, "ACTIVE", "JUNIOR"),
        (6, "PASSIVE", "SENIOR"),
        (None, "ACTIVE", "EX_TRAVELER"),
        (3, "EX_TRAVELER", "SENIOR"),
        (1, None, "JUNIOR"),
    ],
)
def test_refresh_reads_current_socio_instead_of_translating_old_claim(
    api_client: APIClient,
    make_socio: Callable[..., Socio],
    social_year: int | None,
    historical_category: str | None,
    current_category: str,
) -> None:
    socio = _classified_socio(make_socio, social_year)
    token = _historical_token(socio, historical_category)
    historical_value = str(token)
    original = (socio.pk, socio.user_id, socio.user.password, socio.role, socio.is_enabled)

    response = api_client.post(REFRESH_URL, {"refresh": historical_value}, format="json")

    assert response.status_code == 200
    access = AccessToken(response.data["access"])
    assert access["category"] == current_category
    assert str(access["user_id"]) == str(socio.user_id)
    assert access["legajo"] == token["legajo"]
    assert access["role"] == token["role"]
    assert "refresh" not in response.data
    assert str(token) == historical_value
    assert token.get("category") == historical_category
    socio.refresh_from_db()
    socio.user.refresh_from_db()
    assert (socio.pk, socio.user_id, socio.user.password, socio.role, socio.is_enabled) == original


def test_me_uses_current_profile_with_a_historical_access_token(
    api_client: APIClient, make_socio: Callable[..., Socio]
) -> None:
    socio = _classified_socio(make_socio, None, role=Role.SOCIO)
    token = _historical_token(socio, "ACTIVE").access_token
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    response = api_client.get(ME_URL)

    assert response.status_code == 200
    assert response.data["category"] == "EX_TRAVELER"
    assert response.data["category_display"] == "Exviajero"
    assert response.data["role"] == Role.SOCIO
    assert response.data["id"] == socio.pk
    assert token["category"] == "ACTIVE"
    assert api_client.get(PADRON_URL).status_code == 403


def test_repeated_refresh_reloads_classification_without_changing_source_token(
    api_client: APIClient, make_socio: Callable[..., Socio]
) -> None:
    socio = make_socio(social_year=2)
    historical = str(_historical_token(socio))

    for social_year, category in [(2, "JUNIOR"), (3, "SENIOR"), (None, "EX_TRAVELER")]:
        socio.social_year = social_year
        socio.category = category
        socio.save(update_fields=["social_year", "category"])
        response = api_client.post(REFRESH_URL, {"refresh": historical}, format="json")
        assert response.status_code == 200
        assert AccessToken(response.data["access"])["category"] == category

    assert RefreshToken(historical)["category"] == "PASSIVE"


@pytest.mark.parametrize("change", ["role", "membership"])
def test_refreshed_token_keeps_rbac_and_membership_checks_in_server(
    api_client: APIClient, make_socio: Callable[..., Socio], change: str
) -> None:
    socio = make_socio(role=Role.TD, social_year=3)
    token = _historical_token(socio)
    if change == "role":
        socio.role = Role.SOCIO
        socio.save(update_fields=["role"])
    else:
        socio.is_enabled = False
        socio.save(update_fields=["is_enabled"])

    response = api_client.post(REFRESH_URL, {"refresh": str(token)}, format="json")

    assert response.status_code == 200
    access = AccessToken(response.data["access"])
    assert access["category"] == "SENIOR"
    assert access["role"] == Role.TD
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
    assert api_client.get(PADRON_URL).status_code == 403
    assert api_client.get(ME_URL).status_code == (200 if change == "role" else 403)


@pytest.mark.parametrize("invalid", ["expired", "access_type", "malformed", "signature"])
def test_refresh_retains_token_validation(
    api_client: APIClient, make_socio: Callable[..., Socio], invalid: str
) -> None:
    socio = make_socio(social_year=3)
    token = _historical_token(socio)
    if invalid == "expired":
        token.set_exp(from_time=datetime.now(timezone.utc) - timedelta(days=8))
        value = str(token)
    elif invalid == "access_type":
        value = str(token.access_token)
    elif invalid == "malformed":
        value = "not-a-jwt"
    else:
        encoded = str(token)
        header, payload, signature = encoded.split(".")
        replacement = "A" if signature[0] != "A" else "B"
        value = f"{header}.{payload}.{replacement}{signature[1:]}"

    response = api_client.post(REFRESH_URL, {"refresh": value}, format="json")

    assert response.status_code == 401
    assert "access" not in response.data
    assert "refresh" not in response.data


@pytest.mark.parametrize("missing", ["user", "profile", "claim", "invalid_id"])
def test_refresh_with_unresolvable_user_does_not_emit_a_profile_claim(
    api_client: APIClient, make_socio: Callable[..., Socio], missing: str
) -> None:
    socio = make_socio(social_year=3)
    token = _historical_token(socio)
    if missing == "user":
        token["user_id"] = "99999999"
    elif missing == "profile":
        unrelated = get_user_model().objects.create_user(username="no-profile")
        token["user_id"] = str(unrelated.pk)
    elif missing == "claim":
        del token["user_id"]
    else:
        token["user_id"] = "invalid-primary-key"

    response = api_client.post(REFRESH_URL, {"refresh": str(token)}, format="json")

    assert response.status_code == 401
    assert "access" not in response.data
    assert "refresh" not in response.data


@pytest.mark.parametrize("rule", ["inactive_user", "configured_rule"])
def test_refresh_preserves_the_existing_user_authentication_rule(
    api_client: APIClient,
    make_socio: Callable[..., Socio],
    monkeypatch: pytest.MonkeyPatch,
    rule: str,
) -> None:
    socio = make_socio(social_year=3)
    token = _historical_token(socio)
    if rule == "inactive_user":
        socio.user.is_active = False
        socio.user.save(update_fields=["is_active"])
    else:
        monkeypatch.setattr(
            jwt_serializers.api_settings, "USER_AUTHENTICATION_RULE", lambda user: user.is_staff
        )

    response = api_client.post(REFRESH_URL, {"refresh": str(token)}, format="json")

    assert response.status_code == 401
    assert "access" not in response.data
    assert "refresh" not in response.data


@pytest.mark.parametrize("rotate,blacklist", [(False, False), (True, False), (True, True)])
def test_refresh_preserves_rotation_options_and_lifetimes(
    api_client: APIClient,
    make_socio: Callable[..., Socio],
    monkeypatch: pytest.MonkeyPatch,
    rotate: bool,
    blacklist: bool,
) -> None:
    monkeypatch.setattr(jwt_serializers.api_settings, "ROTATE_REFRESH_TOKENS", rotate)
    monkeypatch.setattr(jwt_serializers.api_settings, "BLACKLIST_AFTER_ROTATION", blacklist)
    monkeypatch.setattr(AccessToken, "lifetime", timedelta(minutes=9))
    monkeypatch.setattr(RefreshToken, "lifetime", timedelta(days=3))
    socio = make_socio(social_year=3)
    token = _historical_token(socio)

    response = api_client.post(REFRESH_URL, {"refresh": str(token)}, format="json")

    assert response.status_code == 200
    access = AccessToken(response.data["access"])
    assert access["category"] == "SENIOR"
    assert access["exp"] - access["iat"] == int(AccessToken.lifetime.total_seconds())
    assert ("refresh" in response.data) is rotate
    if rotate:
        refreshed = RefreshToken(response.data["refresh"])
        assert refreshed["jti"] != token["jti"]
        assert refreshed["category"] == "SENIOR"
        assert refreshed["user_id"] == token["user_id"]
        assert refreshed["exp"] - refreshed["iat"] == int(RefreshToken.lifetime.total_seconds())

    repeated = api_client.post(REFRESH_URL, {"refresh": str(token)}, format="json")
    revoked = rotate and blacklist and apps.is_installed("rest_framework_simplejwt.token_blacklist")
    assert repeated.status_code == (401 if revoked else 200)


def test_refresh_uses_configured_user_identity_field_and_claim(
    api_client: APIClient, make_socio: Callable[..., Socio], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(jwt_tokens.api_settings, "USER_ID_FIELD", "username")
    monkeypatch.setattr(jwt_tokens.api_settings, "USER_ID_CLAIM", "subject")
    socio = make_socio(social_year=3)
    token = _historical_token(socio)

    response = api_client.post(REFRESH_URL, {"refresh": str(token)}, format="json")

    assert response.status_code == 200
    access = AccessToken(response.data["access"])
    assert access["subject"] == socio.user.get_username()
    assert "user_id" not in access
    assert access["category"] == "SENIOR"
