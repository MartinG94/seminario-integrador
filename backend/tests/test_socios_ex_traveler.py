"""TS77.31: condición local exviajero explícita, sin año social ficticio."""

from collections.abc import Callable

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from socios.models import Role, SocialCategory, Socio, Subcomision

pytestmark = pytest.mark.django_db

EX_TRAVELER = "EX_TRAVELER"


@pytest.mark.parametrize("role,is_enabled", [(Role.SOCIO, True), (Role.TD, False)])
def test_explicit_ex_traveler_persists_without_year(
    subcomision: Subcomision, role: str, is_enabled: bool
) -> None:
    user = get_user_model().objects.create_user(username="ex-traveler")
    socio = Socio.objects.create(
        user=user,
        legajo="EX-5701",
        first_name="Socio",
        last_name="Ficticio",
        email="ex-traveler@aveit.test",
        subcomision=subcomision,
        social_year=None,
        category=EX_TRAVELER,
        role=role,
        is_enabled=is_enabled,
    )

    socio.refresh_from_db()

    assert socio.category == EX_TRAVELER
    assert socio.get_category_display() == "Exviajero"
    assert socio.social_year is None
    assert socio.role == role
    assert socio.is_enabled is is_enabled
    assert socio.user_id == user.pk
    assert socio.subcomision_id == subcomision.pk


@pytest.mark.parametrize(
    "category,social_year",
    [
        ("", None),
        (SocialCategory.JUNIOR, None),
        (SocialCategory.SENIOR, None),
        ("UNKNOWN", None),
        (EX_TRAVELER, 1),
        (EX_TRAVELER, 6),
        (EX_TRAVELER, 0),
        (EX_TRAVELER, 7),
    ],
)
def test_inconsistent_ex_traveler_is_rejected_before_persistence(
    make_socio: Callable[..., Socio], category: str, social_year: int | None
) -> None:
    socio = make_socio()
    original = (socio.category, socio.social_year)
    socio.category = category
    socio.social_year = social_year

    with pytest.raises(ValidationError) as error:
        socio.save()

    assert "social_year" in error.value.message_dict
    socio.refresh_from_db()
    assert (socio.category, socio.social_year) == original


def test_conversion_to_ex_traveler_preserves_account_and_identity(
    make_socio: Callable[..., Socio],
) -> None:
    socio = make_socio(role=Role.CD, social_year=6, is_enabled=False)
    identity = (socio.pk, socio.user_id, socio.legajo, socio.email, socio.subcomision_id)
    password_hash = socio.user.password
    socio.category = EX_TRAVELER
    socio.social_year = None

    socio.save()
    socio.refresh_from_db()
    socio.user.refresh_from_db()

    credentials_preserved = socio.user.password == password_hash
    assert credentials_preserved
    assert (socio.pk, socio.user_id, socio.legajo, socio.email, socio.subcomision_id) == identity
    assert (socio.role, socio.is_enabled) == (Role.CD, False)
    assert (socio.category, socio.social_year) == (EX_TRAVELER, None)


@pytest.mark.parametrize("update_fields", [("category",), ("social_year",)])
def test_partial_classification_update_preserves_the_complete_pair(
    make_socio: Callable[..., Socio], update_fields: tuple[str, ...]
) -> None:
    socio = make_socio()
    socio.category = EX_TRAVELER
    socio.social_year = None
    socio.save(update_fields=update_fields)
    socio.refresh_from_db()

    assert (socio.category, socio.social_year) == (EX_TRAVELER, None)

    socio.category = SocialCategory.JUNIOR
    socio.social_year = 2
    socio.save(update_fields=update_fields)
    socio.refresh_from_db()

    assert (socio.category, socio.social_year) == (SocialCategory.JUNIOR, 2)


def test_unrelated_partial_update_does_not_persist_an_unselected_classification(
    make_socio: Callable[..., Socio],
) -> None:
    socio = make_socio()
    original = (socio.category, socio.social_year)
    socio.category = EX_TRAVELER
    socio.social_year = None
    socio.first_name = "Nombre actualizado"

    socio.save(update_fields=["first_name"])
    socio.refresh_from_db()

    assert socio.first_name == "Nombre actualizado"
    assert (socio.category, socio.social_year) == original


@pytest.mark.parametrize(
    "category,social_year",
    [
        (SocialCategory.JUNIOR, None),
        (EX_TRAVELER, 2),
        (SocialCategory.JUNIOR, 0),
        (SocialCategory.SENIOR, 7),
        ("ex_traveler", None),
        ("EX_TRAVELER ", None),
    ],
)
def test_database_rejects_an_inconsistent_pair_when_save_is_bypassed(
    make_socio: Callable[..., Socio], category: str, social_year: int | None
) -> None:
    socio = make_socio()
    original = (socio.category, socio.social_year)

    with pytest.raises(IntegrityError), transaction.atomic():
        Socio.objects.filter(pk=socio.pk).update(category=category, social_year=social_year)

    socio.refresh_from_db()
    assert (socio.category, socio.social_year) == original
