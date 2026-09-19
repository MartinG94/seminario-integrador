"""Pruebas del padrón: RF-06-WS (unicidad de legajo, categoría Pasivo/Activo)."""

import pytest
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError

from socios.models import Role, SocialCategory, Socio


@pytest.mark.parametrize(
    "social_year,expected",
    [
        (1, SocialCategory.PASSIVE),
        (2, SocialCategory.PASSIVE),
        (3, SocialCategory.PASSIVE),
        (4, SocialCategory.ACTIVE),
        (5, SocialCategory.ACTIVE),
        (6, SocialCategory.ACTIVE),
    ],
)
@pytest.mark.django_db
def test_category_is_derived_from_social_year(make_socio, social_year, expected):
    socio = make_socio(legajo=f"7000{social_year}", social_year=social_year)

    assert socio.category == expected


@pytest.mark.django_db
def test_category_is_independent_from_account_status(make_socio):
    """Constitución ppio. 8: la vigencia de la cuenta no surge de la categoría."""
    socio = make_socio(legajo="74907", social_year=5, is_enabled=False)

    assert socio.category == SocialCategory.ACTIVE
    assert socio.is_enabled is False


@pytest.mark.django_db
def test_legajo_is_unique(make_socio):
    make_socio(legajo="74907")

    with pytest.raises((IntegrityError, ValidationError)):
        make_socio(legajo="74907", email="otro@aveit.test")


@pytest.mark.django_db
def test_social_year_out_of_range_is_rejected(make_socio):
    with pytest.raises(ValidationError):
        make_socio(legajo="99999", social_year=7)


@pytest.mark.django_db
def test_default_role_is_socio(make_socio):
    socio = Socio.objects.get(pk=make_socio(legajo="74907").pk)

    assert socio.role == Role.SOCIO
