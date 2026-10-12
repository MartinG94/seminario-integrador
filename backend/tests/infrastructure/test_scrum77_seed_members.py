"""TS77.10/11: identidades reales, referencias completas y conservación del seed."""

import importlib
from io import StringIO
from typing import Any

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import transaction

from padron.adapters import DatabasePadronAdapter
from padron.models import Socio as InstitutionalSocio
from padron.models import SocioEmail, SocioEstadoHistorial, SocioEstudio
from socios.demo_catalog import CATALOG
from socios.models import InstitutionalMembershipCondition, Socio
from tests.infrastructure.test_scrum77_fixture_registry import (
    bootstrap_database as bootstrap_database,
)
from tests.infrastructure.test_scrum77_fixture_registry import (
    fixture_database as fixture_database,
)


def _load(database: Any) -> Any:
    fixtures = importlib.import_module("core.demo_fixtures")
    members = importlib.import_module("core.demo_members")
    with transaction.atomic():
        return members.load_demo_members(
            CATALOG, fixtures.DemoFixtureRegistry(CATALOG.profile, connection=database)
        )


def _rows(database: Any) -> dict[str, Any]:
    tables = [
        "auth_user",
        "socios_socio",
        "socios_subcomision",
        "core_demofixtureownership",
        "socios_institutionalmembershipcondition",
        "socio_lista",
        "grupo_lista",
        "socio_email",
        "socio_estudio",
        "socio_estadoHistorial",
    ]
    with database.cursor() as cursor:
        output = {}
        for table in tables:
            cursor.execute(f"SELECT * FROM `{table}`")
            output[table] = tuple(sorted(cursor.fetchall(), key=repr))
        return output


def _assert_rows_preserved(database: Any, before: dict[str, Any]) -> None:
    preserved = _rows(database) == before
    assert preserved, "Las filas se conservan sin exponer credenciales en el diagnóstico."


@pytest.mark.django_db(transaction=True, databases="__all__")
def test_complete_member_catalog_has_real_and_separate_identity_links(
    fixture_database: Any,
) -> None:
    result = _load(fixture_database)
    assert InstitutionalSocio.objects.count() == 20
    assert SocioEstudio.objects.count() == 20
    assert SocioEmail.objects.count() == 20
    assert SocioEstadoHistorial.objects.count() == 20
    assert InstitutionalMembershipCondition.objects.count() == 4
    assert Socio.objects.count() == get_user_model().objects.count() == 15
    assert len(result.users) == len(result.local_socios) == len(result.accounts) == 10
    assert len(result.institutional_members) == 20
    assert len(result.preserved_accounts) == 5
    for account in CATALOG.accounts:
        user = result.users[account.user_key]
        local = result.local_socios[account.local_socio_key]
        institutional = result.institutional_members[account.member_key]
        assert institutional.user_id == local.user_id == user.pk
        assert institutional.nroSocio != local.pk
        assert local.legajo == account.username
        assert local.role == account.role
        assert local.is_enabled == account.is_enabled
        assert user.is_active is True
        assert result.accounts[account.fixture_key].pk == local.pk
    account_members = {account.member_key for account in CATALOG.accounts}
    assert all(
        result.institutional_members[member.fixture_key].user_id is None
        for member in CATALOG.members
        if member.fixture_key not in account_members
    )


@pytest.mark.django_db(transaction=True, databases="__all__")
def test_cut_social_categories_and_membership_vigency_remain_independent(
    fixture_database: Any,
) -> None:
    _load(fixture_database)
    repository = DatabasePadronAdapter()
    groups = {group.fixture_key: group for group in CATALOG.groups}
    for member in CATALOG.members:
        dto = repository.get_by_id(member.institutional_number)
        group = groups[member.group_key]
        assert dto.social_year == group.social_year
        assert dto.category.value == group.category
        assert dto.is_active == (member.membership_state_code == 1)
        assert dto.legajo == str(member.academic_number)
    assert Socio.objects.get(legajo="99077001").category == "EX_TRAVELER"
    assert Socio.objects.get(legajo="99077001").social_year is None
    assert Socio.objects.get(legajo="99077002").is_enabled is False
    assert Socio.objects.get(legajo="99077005").category == "SENIOR"
    for legajo, year in (("99077017", 2), ("99077018", 2), ("99077019", 1), ("99077020", 1)):
        junior = Socio.objects.get(legajo=legajo)
        assert (junior.category, junior.social_year) == ("JUNIOR", year)
        assert junior.role == "SOCIO"
        assert junior.is_enabled is True


@pytest.mark.django_db(transaction=True, databases="__all__")
@pytest.mark.parametrize("source", ["local", "institutional"])
def test_repeat_rejects_group_social_year_contradictions_without_reclassifying(
    fixture_database: Any, source: str
) -> None:
    _load(fixture_database)
    if source == "local":
        local = Socio.objects.get(legajo="99077005")
        local.social_year = 3
        local.save(update_fields=["social_year"])
    else:
        # Hook exclusivo de fixtures sobre un scratch propio; sin puntos ni expedientes.
        institutional = InstitutionalSocio.objects.get(pk=770001)
        institutional._allow_write = True
        institutional.anoSocial = 1
        institutional.save(update_fields=["anoSocial"])
    before = _rows(fixture_database)
    with pytest.raises(CommandError, match="corte|año|clasificaci"):
        _load(fixture_database)
    _assert_rows_preserved(fixture_database, before)


@pytest.mark.django_db(transaction=True, databases="__all__")
def test_repeat_preserves_every_fixture_row_and_valid_profile_edits(fixture_database: Any) -> None:
    first = _load(fixture_database)
    local = first.accounts["account.g58.01"]
    local.first_name = "Editada"
    local.role = "SOCIO"
    local.is_enabled = False
    local.save(update_fields=["first_name", "role", "is_enabled"])
    user = local.user
    user.set_password("Credencial editada sintética")
    user.save(update_fields=["password"])
    before = _rows(fixture_database)
    second = _load(fixture_database)
    preserved = _rows(fixture_database) == before
    assert preserved, (
        "La repetición debe conservar filas completas, incluidas credenciales sin exponerlas."
    )
    assert second.accounts["account.g58.01"].pk == local.pk
    assert second.accounts["account.g58.01"].first_name == "Editada"
    assert second.accounts["account.g58.01"].role == "SOCIO"
    assert second.accounts["account.g58.01"].is_enabled is False


@pytest.mark.django_db(transaction=True, databases="__all__")
def test_seed_demo_existing_credentials_permissions_and_edits_are_references(
    fixture_database: Any,
) -> None:
    from core.models import DemoFixtureOwnership

    call_command("seed_demo", stdout=StringIO())
    existing = Socio.objects.get(legajo="74907")
    existing.first_name = "Conservada"
    existing.role = "CD"
    existing.is_enabled = False
    existing.save(update_fields=["first_name", "role", "is_enabled"])
    user = existing.user
    user.set_password("Preservar credencial sintética")
    user.save(update_fields=["password"])
    before = list(get_user_model().objects.order_by("pk").values())
    before_local = list(Socio.objects.order_by("pk").values())
    _load(fixture_database)
    preserved = (
        list(
            get_user_model()
            .objects.filter(pk__in=[row["id"] for row in before])
            .order_by("pk")
            .values()
        )
        == before
    )
    assert preserved
    assert (
        list(
            Socio.objects.filter(pk__in=[row["id"] for row in before_local]).order_by("pk").values()
        )
        == before_local
    )
    refs = DemoFixtureOwnership.objects.filter(fixture_key__startswith="preserved.seed-demo")
    assert refs.count() == 10
    assert not refs.filter(owned=True).exists()


@pytest.mark.django_db(transaction=True, databases="__all__")
def test_seed_demo_absent_accounts_use_original_roles_and_credentials(
    fixture_database: Any,
) -> None:
    from core.models import DemoFixtureOwnership
    from socios.management.commands.seed_demo import DEMO_PASSWORD, DEMO_SOCIOS

    _load(fixture_database)
    for legajo, last_name, first_name, role, year in DEMO_SOCIOS:
        socio = Socio.objects.get(legajo=legajo)
        assert socio.role == role
        assert (socio.first_name, socio.last_name, socio.social_year) == (
            first_name,
            last_name,
            year,
        )
        assert socio.user.check_password(DEMO_PASSWORD) is True
    assert (
        DemoFixtureOwnership.objects.filter(
            fixture_key__startswith="preserved.seed-demo", owned=True
        ).count()
        == 10
    )


@pytest.mark.django_db(transaction=True, databases="__all__")
@pytest.mark.parametrize("username", ["99077001", "74907"])
def test_foreign_username_collision_aborts_without_claim_or_partial_seed(
    fixture_database: Any, username: str
) -> None:
    user = get_user_model().objects.create_user(username=username, email="foreign@scrum77.test")
    before = _rows(fixture_database)
    with pytest.raises(CommandError, match="ajena"):
        _load(fixture_database)
    preserved = _rows(fixture_database) == before
    assert preserved
    assert get_user_model().objects.get(pk=user.pk).username == username


@pytest.mark.django_db(transaction=True, databases="__all__")
def test_foreign_identical_institutional_row_is_not_adopted(fixture_database: Any) -> None:
    _load(fixture_database)
    from core.models import DemoFixtureOwnership

    DemoFixtureOwnership.objects.filter(fixture_key="member.g57.01").delete()
    before = _rows(fixture_database)
    with pytest.raises(CommandError, match="ajena"):
        _load(fixture_database)
    _assert_rows_preserved(fixture_database, before)


@pytest.mark.django_db(transaction=True, databases="__all__")
@pytest.mark.parametrize("namespace", ["document", "academic", "email", "user-link"])
def test_duplicate_natural_identity_aborts_even_on_repeat(
    fixture_database: Any, namespace: str
) -> None:
    _load(fixture_database)
    member = CATALOG.members[0]
    with fixture_database.cursor() as cursor:
        if namespace in ("document", "user-link"):
            cursor.execute(
                "INSERT INTO socio_lista(nroSocio,apellido,nombre,fechaIngreso,codTipoDoc,"
                "nroDoc,fechaNac,codSexo,codSubcomision,anoSocial,idTipoSocio,user_id) "
                "SELECT 780001,apellido,nombre,fechaIngreso,codTipoDoc,%s,fechaNac,codSexo,"
                "codSubcomision,anoSocial,idTipoSocio,%s FROM socio_lista WHERE nroSocio=%s",
                [
                    member.document_number if namespace == "document" else 100078001,
                    InstitutionalSocio.objects.get(pk=member.institutional_number).user_id
                    if namespace == "user-link"
                    else None,
                    member.institutional_number,
                ],
            )
        elif namespace == "academic":
            cursor.execute(
                "INSERT INTO socio_estudio(compositeKey,nroSocio,nroLegajo,codEspecialidad) "
                "VALUES(1870001,%s,%s,1)",
                [CATALOG.members[1].institutional_number, member.academic_number],
            )
        else:
            cursor.execute(
                "INSERT INTO socio_email(compositeKey,nroSocio,idEmail,email) "
                "VALUES(2870001,%s,2,%s)",
                [CATALOG.members[1].institutional_number, member.email],
            )
    before = _rows(fixture_database)
    with pytest.raises(CommandError, match="identidad|ajena"):
        _load(fixture_database)
    _assert_rows_preserved(fixture_database, before)


@pytest.mark.django_db(transaction=True, databases="__all__")
def test_failure_after_member_insert_rolls_back_users_registry_and_legacy(
    fixture_database: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixtures = importlib.import_module("core.demo_fixtures")
    original = fixtures.DemoFixtureRegistry.ensure_legacy
    count = 0

    def fail_after_insert(self: Any, key: str, table: str, *args: Any, **kwargs: Any) -> Any:
        nonlocal count
        row = original(self, key, table, *args, **kwargs)
        if table == "socio_lista":
            count += 1
            if count == 2:
                raise RuntimeError("fallo intermedio comprobado")
        return row

    monkeypatch.setattr(fixtures.DemoFixtureRegistry, "ensure_legacy", fail_after_insert)
    before = _rows(fixture_database)
    with pytest.raises(RuntimeError, match="intermedio"):
        _load(fixture_database)
    assert count == 2
    _assert_rows_preserved(fixture_database, before)
