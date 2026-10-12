"""TS77.40: asociación institucional explícita, sin FK al padrón legado."""

import importlib
from datetime import date
from typing import Any

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, connection, transaction
from django.test.utils import CaptureQueriesContext

from padron.models import Socio as InstitutionalSocio
from tests.legacy_schema import create_legacy_record


def _condition_api() -> Any:
    return importlib.import_module("socios.institutional_conditions")


def _member(number: int = 7740001, year: int | None = None) -> InstitutionalSocio:
    member = InstitutionalSocio(
        nroSocio=number,
        nombre="Condición",
        apellido="Sintética",
        fechaIngreso=date(2024, 1, 1),
        fechaNac=date(2000, 1, 1),
        codTipoDoc=1,
        nroDoc=0,
        codSexo=1,
        subcomision_id=None,
        anoSocial=year,
        idTipoSocio=1,
    )
    member._allow_write = True
    member.save(force_insert=True)
    return member


def _register(member: InstitutionalSocio, **overrides: Any) -> Any:
    return _condition_api().register_ex_traveler(
        institutional_member=member,
        source_reference="test:SCRUM-77:RN77-01",
        social_cycle="TEST-2026",
        **overrides,
    )


def test_condition_mapping_has_institutional_identity_and_no_physical_foreign_key() -> None:
    from socios.models import InstitutionalMembershipCondition

    model = _condition_api().InstitutionalMembershipCondition
    assert model is InstitutionalMembershipCondition
    assert model._meta.managed
    assert model._meta.pk.name == "institutional_number"
    assert not any(field.is_relation for field in model._meta.get_fields())


@pytest.mark.django_db
def test_registration_preserves_institutional_and_operational_data(make_socio: Any) -> None:
    api = _condition_api()
    local = make_socio(legajo="7740001", social_year=3)
    member = _member(number=local.pk + 900000)
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM socio_lista WHERE nroSocio=%s", [member.pk])
        original_member = cursor.fetchone()
    original_local = dict(type(local).objects.values().get(pk=local.pk))
    original_password = local.user.password

    marker = _register(member)

    assert marker.pk == member.nroSocio and marker.pk != local.pk
    assert marker.condition == "EX_TRAVELER"
    assert marker.source_reference == "test:SCRUM-77:RN77-01"
    assert marker.social_cycle == "TEST-2026"
    assert api.InstitutionalMembershipCondition.objects.count() == 1
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM socio_lista WHERE nroSocio=%s", [member.pk])
        preserved = cursor.fetchone() == original_member
    assert preserved
    preserved = dict(type(local).objects.values().get(pk=local.pk)) == original_local
    assert preserved
    local.user.refresh_from_db()
    assert local.user.password == original_password


@pytest.mark.django_db
def test_same_source_registration_repeats_without_dml() -> None:
    api = _condition_api()
    member = _member()
    marker = _register(member)
    with CaptureQueriesContext(connection) as queries:
        repeated = _register(member)
    assert repeated.pk == marker.pk
    assert api.InstitutionalMembershipCondition.objects.count() == 1
    assert not any(
        item["sql"].lstrip().split()[0].upper() in {"INSERT", "UPDATE", "DELETE", "REPLACE"}
        for item in queries
    )


@pytest.mark.django_db
@pytest.mark.parametrize("field", ["source_reference", "social_cycle"])
def test_existing_marker_from_another_source_is_not_overwritten(field: str) -> None:
    api = _condition_api()
    member = _member()
    marker = _register(member)
    options = {
        "institutional_member": member,
        "source_reference": marker.source_reference,
        "social_cycle": marker.social_cycle,
    }
    options[field] = "Otra fuente o corte"
    with pytest.raises(ValidationError):
        api.register_ex_traveler(**options)
    marker.refresh_from_db()
    assert marker.source_reference == "test:SCRUM-77:RN77-01"
    assert marker.social_cycle == "TEST-2026"


@pytest.mark.django_db
@pytest.mark.parametrize("year", [0, 1, 2, 3, 6, 7])
def test_registration_rejects_a_contradictory_social_year(year: int) -> None:
    api = _condition_api()
    member = _member(year=year)
    with pytest.raises(ValidationError):
        _register(member)
    assert api.InstitutionalMembershipCondition.objects.count() == 0


@pytest.mark.django_db
@pytest.mark.parametrize("field", ["source_reference", "social_cycle"])
@pytest.mark.parametrize("value", ["", "   ", None, True])
def test_registration_requires_explicit_source_and_cut(field: str, value: Any) -> None:
    api = _condition_api()
    member = _member()
    options = {
        "institutional_member": member,
        "source_reference": "test:SCRUM-77:RN77-01",
        "social_cycle": "TEST-2026",
    }
    options[field] = value
    with pytest.raises(ValidationError):
        api.register_ex_traveler(**options)
    assert api.InstitutionalMembershipCondition.objects.count() == 0


@pytest.mark.django_db
@pytest.mark.parametrize("reference", ["unsaved", "foreign_alias", "wrong_type"])
def test_registration_rejects_unconfirmed_or_foreign_references(
    reference: str, make_socio: Any
) -> None:
    api = _condition_api()
    if reference == "wrong_type":
        member = make_socio(legajo="7740001", social_year=3)
    elif reference == "unsaved":
        member = InstitutionalSocio(nroSocio=7740001, anoSocial=None)
    else:
        member = _member()
        member._state.db = "another_database"
    with pytest.raises(ValidationError):
        api.register_ex_traveler(
            institutional_member=member,
            source_reference="test:SCRUM-77:RN77-01",
            social_cycle="TEST-2026",
            using="default",
        )
    assert api.InstitutionalMembershipCondition.objects.count() == 0


@pytest.mark.django_db
def test_model_save_and_full_clean_reject_an_orphan_without_a_legacy_fk() -> None:
    api = _condition_api()
    marker = api.InstitutionalMembershipCondition(
        institutional_number=7740999,
        condition="EX_TRAVELER",
        source_reference="test:SCRUM-77:RN77-01",
        social_cycle="TEST-2026",
    )
    with pytest.raises(ValidationError):
        marker.full_clean()
    with pytest.raises(ValidationError):
        marker.save()
    assert api.InstitutionalMembershipCondition.objects.count() == 0


@pytest.mark.django_db
def test_duplicate_identity_and_marker_edits_are_rejected() -> None:
    api = _condition_api()
    member = _member()
    marker = _register(member)
    with pytest.raises(ValidationError):
        api.InstitutionalMembershipCondition.objects.create(
            institutional_number=member.pk,
            condition="EX_TRAVELER",
            source_reference=marker.source_reference,
            social_cycle=marker.social_cycle,
        )
    marker.source_reference = "Otra fuente"
    with pytest.raises(ValidationError):
        marker.save(update_fields=["source_reference"])
    marker.refresh_from_db()
    assert marker.source_reference == "test:SCRUM-77:RN77-01"


@pytest.mark.django_db
@pytest.mark.parametrize("operation", ["update", "bulk_update", "bulk_create", "delete"])
def test_queryset_methods_cannot_skip_association_validation(operation: str) -> None:
    api = _condition_api()
    marker = _register(_member())
    queryset = api.InstitutionalMembershipCondition.objects.all()
    with pytest.raises(ValidationError):
        if operation == "update":
            queryset.update(source_reference="Otra fuente")
        elif operation == "bulk_update":
            queryset.bulk_update([marker], ["source_reference"])
        elif operation == "bulk_create":
            queryset.bulk_create([marker])
        else:
            queryset.delete()
    assert api.InstitutionalMembershipCondition.objects.count() == 1


@pytest.mark.django_db(transaction=True)
def test_registration_rolls_back_with_its_callers_transaction() -> None:
    api = _condition_api()
    member = _member()
    with pytest.raises(RuntimeError, match="Fixture rollback"):
        with transaction.atomic():
            _register(member)
            raise RuntimeError("Fixture rollback")
    assert api.InstitutionalMembershipCondition.objects.count() == 0
    assert InstitutionalSocio.objects.filter(pk=member.pk).exists()


@pytest.mark.django_db
def test_invalid_marker_does_not_reinterpret_membership_flags() -> None:
    api = _condition_api()
    member = create_legacy_record(InstitutionalSocio, nroSocio=7740001, anoSocial=6)
    with pytest.raises(ValidationError):
        _register(member)
    assert api.InstitutionalMembershipCondition.objects.count() == 0


@pytest.mark.django_db
def test_physical_identity_has_a_primary_key_and_no_legacy_foreign_key() -> None:
    model = _condition_api().InstitutionalMembershipCondition
    with connection.cursor() as cursor:
        constraints = connection.introspection.get_constraints(cursor, model._meta.db_table)
    assert any(
        item["primary_key"] and item["columns"] == ["institutional_number"]
        for item in constraints.values()
    )
    assert not any(item["foreign_key"] for item in constraints.values())


@pytest.mark.django_db
@pytest.mark.parametrize(
    "number, condition, source, cut",
    [
        (0, "EX_TRAVELER", "Fuente", "Corte"),
        (7740001, "ex_traveler", "Fuente", "Corte"),
        (7740001, "EX_TRAVELER ", "Fuente", "Corte"),
        (7740001, "EX_TRAVELER", "   ", "Corte"),
        (7740001, "EX_TRAVELER", "Fuente", "   "),
    ],
)
def test_mysql_rejects_invalid_marker_values_even_bypassing_the_model(
    number: int, condition: str, source: str, cut: str
) -> None:
    model = _condition_api().InstitutionalMembershipCondition
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute(
                    f"INSERT INTO {connection.ops.quote_name(model._meta.db_table)} "
                    "(institutional_number, `condition`, source_reference, social_cycle) "
                    "VALUES (%s, %s, %s, %s)",
                    [number, condition, source, cut],
                )
    assert model.objects.count() == 0


@pytest.mark.django_db
def test_mysql_rejects_duplicate_institutional_identity() -> None:
    model = _condition_api().InstitutionalMembershipCondition
    marker = _register(_member())
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute(
                    f"INSERT INTO {connection.ops.quote_name(model._meta.db_table)} "
                    "(institutional_number, `condition`, source_reference, social_cycle) "
                    "VALUES (%s, 'EX_TRAVELER', 'Otra fuente', 'Otro corte')",
                    [marker.pk],
                )
    assert model.objects.count() == 1
