"""TS77.32: clasificación local por año, sin efectos sobre roles o vigencia."""

from collections.abc import Callable

import pytest
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError

from socios.models import Role, Socio


@pytest.mark.parametrize(
    "social_year,expected,label",
    [
        (1, "JUNIOR", "Junior"),
        (2, "JUNIOR", "Junior"),
        (3, "SENIOR", "Senior"),
        (4, "SENIOR", "Senior"),
        (5, "SENIOR", "Senior"),
        (6, "SENIOR", "Senior"),
    ],
)
@pytest.mark.django_db
def test_category_is_derived_from_social_year(
    make_socio: Callable[..., Socio], social_year: int, expected: str, label: str
) -> None:
    socio = make_socio(legajo=f"7000{social_year}", social_year=social_year)
    socio.refresh_from_db()
    assert socio.category == expected
    assert socio.get_category_display() == label


@pytest.mark.django_db
@pytest.mark.parametrize(
    "social_year,role,is_enabled,expected",
    [
        (1, Role.TD, True, "JUNIOR"),
        (2, Role.SOCIO, False, "JUNIOR"),
        (3, Role.CD, True, "SENIOR"),
        (6, Role.ADMIN, False, "SENIOR"),
    ],
)
def test_category_is_independent_from_account_status(
    make_socio: Callable[..., Socio],
    social_year: int,
    role: str,
    is_enabled: bool,
    expected: str,
) -> None:
    """Constitución ppio. 8: la vigencia de la cuenta no surge de la categoría."""
    socio = make_socio(social_year=social_year, role=role, is_enabled=is_enabled)
    socio.refresh_from_db()

    assert socio.category == expected
    assert socio.role == role
    assert socio.is_enabled is is_enabled


@pytest.mark.django_db
def test_legajo_is_unique(make_socio: Callable[..., Socio]) -> None:
    make_socio(legajo="74907")

    with pytest.raises((IntegrityError, ValidationError)):
        make_socio(legajo="74907", email="otro@aveit.test")


@pytest.mark.django_db
@pytest.mark.parametrize("social_year", [None, -1, 0, 7])
def test_social_year_out_of_range_is_rejected(
    make_socio: Callable[..., Socio], social_year: int | None
) -> None:
    with pytest.raises(ValidationError):
        make_socio(legajo="99999", social_year=social_year)


@pytest.mark.django_db
def test_default_role_is_socio(make_socio: Callable[..., Socio]) -> None:
    socio = Socio.objects.get(pk=make_socio(legajo="74907").pk)

    assert socio.role == Role.SOCIO


@pytest.mark.parametrize(
    "social_year,expected",
    [(1, "JUNIOR"), (2, "JUNIOR"), (3, "SENIOR"), (4, "SENIOR"), (5, "SENIOR"), (6, "SENIOR")],
)
def test_classifier_matches_the_confirmed_scale(social_year: int, expected: str) -> None:
    assert Socio.category_for_social_year(social_year) == expected


@pytest.mark.parametrize("invalid_year", [None, -1, 0, 7, True, 1.5, "2"])
def test_classifier_rejects_values_outside_the_integer_scale(invalid_year: object) -> None:
    with pytest.raises(ValidationError) as error:
        Socio.category_for_social_year(invalid_year)
    assert "social_year" in error.value.message_dict


@pytest.mark.django_db
@pytest.mark.parametrize("update_fields", [("social_year",), ("category",)])
@pytest.mark.parametrize("initial_year,new_year,expected", [(2, 3, "SENIOR"), (3, 2, "JUNIOR")])
def test_partial_update_crosses_the_junior_senior_boundary(
    make_socio: Callable[..., Socio],
    update_fields: tuple[str, ...],
    initial_year: int,
    new_year: int,
    expected: str,
) -> None:
    socio = make_socio(social_year=initial_year, role=Role.TD, is_enabled=False)
    identity = (socio.pk, socio.user_id, socio.legajo, socio.email, socio.subcomision_id)
    credentials = socio.user.password
    socio.social_year = new_year
    socio.save(update_fields=update_fields)
    socio.refresh_from_db()
    socio.user.refresh_from_db()

    assert (socio.social_year, socio.category) == (new_year, expected)
    assert (socio.role, socio.is_enabled) == (Role.TD, False)
    assert (socio.pk, socio.user_id, socio.legajo, socio.email, socio.subcomision_id) == identity
    credentials_preserved = socio.user.password == credentials
    assert credentials_preserved


@pytest.mark.django_db
@pytest.mark.parametrize("supplied_category", ["JUNIOR", "ACTIVE"])
def test_social_year_overrides_a_supplied_category(
    make_socio: Callable[..., Socio], supplied_category: str
) -> None:
    socio = make_socio()
    socio.social_year = 3
    socio.category = supplied_category
    socio.save()
    socio.refresh_from_db()
    assert (socio.social_year, socio.category) == (3, "SENIOR")


@pytest.mark.django_db
def test_unrelated_update_preserves_historical_category_until_data_migration(
    make_socio: Callable[..., Socio],
) -> None:
    socio = make_socio(social_year=3)
    Socio.objects.filter(pk=socio.pk).update(category="PASSIVE")
    socio.refresh_from_db()
    socio.first_name = "Nombre actualizado"
    socio.save(update_fields=["first_name"])
    socio.refresh_from_db()
    assert (socio.social_year, socio.category) == (3, "PASSIVE")
    assert socio.first_name == "Nombre actualizado"
