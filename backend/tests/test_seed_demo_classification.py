"""TS77.36: el seed local crea por año y nunca migra socios existentes."""

from io import StringIO

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import IntegrityError, connection
from django.test.utils import CaptureQueriesContext

from socios.management.commands import seed_demo
from socios.models import Role, SocialCategory, Socio, Subcomision

pytestmark = pytest.mark.django_db
UserModel = get_user_model()


def run_seed(settings) -> str:
    settings.DEBUG = True
    output = StringIO()
    call_command("seed_demo", stdout=output)
    return output.getvalue()


def test_new_demo_accounts_keep_their_identities_credentials_and_roles(settings) -> None:
    output = run_seed(settings)
    expected = {
        "74907": (Role.SOCIO, 2, SocialCategory.JUNIOR, "Junior"),
        "85194": (Role.FISCALIZADORA, 4, SocialCategory.SENIOR, "Senior"),
        "87414": (Role.CD, 5, SocialCategory.SENIOR, "Senior"),
        "408917": (Role.TD, 6, SocialCategory.SENIOR, "Senior"),
        "403655": (Role.ADMIN, 5, SocialCategory.SENIOR, "Senior"),
    }

    assert Socio.objects.count() == UserModel.objects.count() == 5
    assert Subcomision.objects.count() == 1
    for socio in Socio.objects.select_related("user", "subcomision"):
        role, year, category, label = expected[socio.legajo]
        assert (socio.role, socio.social_year, socio.category) == (role, year, category)
        assert socio.subcomision.name == "Cómputos"
        assert socio.user.username == socio.legajo
        assert socio.user.email == socio.email == f"{socio.legajo}@aveit.test"
        assert socio.user.check_password(seed_demo.DEMO_PASSWORD)
        assert socio.user.is_active and socio.is_enabled
        assert not socio.user.is_staff and not socio.user.is_superuser
        assert not socio.user.groups.exists() and not socio.user.user_permissions.exists()
        assert f"categoria={label}" in output
    assert "categoria=Activo" not in output and "categoria=Pasivo" not in output


def test_demo_uses_the_year_three_cut_instead_of_an_old_category_alias(
    settings, monkeypatch
) -> None:
    monkeypatch.setattr(seed_demo, "DEMO_SOCIOS", [("74907", "Gastiaburu", "Lucas", Role.SOCIO, 3)])
    output = run_seed(settings)
    socio = Socio.objects.get(legajo="74907")
    assert socio.social_year == 3 and socio.category == SocialCategory.SENIOR
    assert "categoria=Senior" in output


@pytest.mark.parametrize(
    ("year", "condition"),
    [(1, SocialCategory.JUNIOR), (3, SocialCategory.SENIOR), (None, SocialCategory.EX_TRAVELER)],
)
def test_existing_demo_account_is_omitted_without_reclassification_or_access_changes(
    settings, make_socio, year: int | None, condition: str
) -> None:
    # An explicit ex-traveler has no inferred social year, even for this familiar legajo.
    existing = make_socio(legajo="74907", role=Role.TD, social_year=1, is_enabled=False)
    existing.social_year = year
    existing.category = condition
    existing.first_name = "Nombre conservado"
    existing.save()
    existing.user.is_active = False
    existing.user.set_password("Different-Demo-Password-2026!")
    existing.user.save()
    group = Group.objects.create(name="Cuenta previa")
    permission = Permission.objects.order_by("id").first()
    existing.user.groups.add(group)
    existing.user.user_permissions.add(permission)
    before_socio = Socio.objects.values().get(pk=existing.pk)
    before_user = UserModel.objects.values().get(pk=existing.user_id)

    output = run_seed(settings)

    assert "= 74907 ya existe, se omite" in output
    assert Socio.objects.values().get(pk=existing.pk) == before_socio
    assert UserModel.objects.values().get(pk=existing.user_id) == before_user
    assert list(existing.user.groups.values_list("id", flat=True)) == [group.pk]
    assert list(existing.user.user_permissions.values_list("id", flat=True)) == [permission.pk]
    assert Socio.objects.count() == UserModel.objects.count() == 5


def test_repeated_demo_seed_performs_no_data_writes(settings) -> None:
    run_seed(settings)
    before_socios = list(Socio.objects.order_by("pk").values())
    before_users = list(UserModel.objects.order_by("pk").values())

    with CaptureQueriesContext(connection) as queries:
        output = run_seed(settings)

    assert output.count("ya existe, se omite") == 5
    assert list(Socio.objects.order_by("pk").values()) == before_socios
    assert list(UserModel.objects.order_by("pk").values()) == before_users
    assert not any(
        query["sql"].lstrip().upper().startswith(("INSERT", "UPDATE", "DELETE"))
        for query in queries
    )


def test_demo_seed_keeps_the_debug_guard_before_any_write(settings) -> None:
    settings.DEBUG = False
    with pytest.raises(CommandError, match="DEBUG=1"):
        call_command("seed_demo", stdout=StringIO())
    assert not Socio.objects.exists()
    assert not UserModel.objects.exists()
    assert not Subcomision.objects.exists()


def test_demo_seed_rolls_back_on_a_username_owned_by_an_existing_account(settings) -> None:
    existing_user = UserModel.objects.create_user(
        username="87414", email="existing@example.test", password="Preserved-Password-2026!"
    )
    before_user = UserModel.objects.values().get(pk=existing_user.pk)
    settings.DEBUG = True

    with pytest.raises(IntegrityError):
        call_command("seed_demo", stdout=StringIO())

    assert not Socio.objects.exists()
    assert not Subcomision.objects.exists()
    assert list(UserModel.objects.values()) == [before_user]
