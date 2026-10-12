"""TS77.07: catálogo sintético, referencias y oráculos de la carga futura."""

import hashlib
import json
from collections import Counter
from dataclasses import FrozenInstanceError, asdict, replace
from datetime import date
from decimal import Decimal
from importlib import import_module

import pytest


@pytest.fixture
def catalog_module():
    return import_module("socios.demo_catalog")


def test_catalog_has_the_confirmed_cut_and_additive_junior_groups(catalog_module) -> None:
    catalog = catalog_module.CATALOG
    assert [(g.number, g.social_year, g.category) for g in catalog.groups] == [
        (57, None, "EX_TRAVELER"),
        (58, 6, "SENIOR"),
        (59, 5, "SENIOR"),
        (60, 4, "SENIOR"),
        (62, 2, "JUNIOR"),
        (63, 1, "JUNIOR"),
    ]
    assert Counter(m.group_key for m in catalog.members) == {
        "group.g57": 4,
        "group.g58": 4,
        "group.g59": 4,
        "group.g60": 4,
        "group.g62": 2,
        "group.g63": 2,
    }
    assert len(catalog.members) == 20
    assert catalog.profile == "scrum77-g57-g60-v1"
    assert catalog.social_cycle == "PO-SCRUM77-CORTE-01"
    assert catalog.recorded_on == date(2026, 10, 12)
    assert "SRC77-PO-02" in catalog.source_reference
    catalog_module.validate_catalog(catalog)


def test_ex_travelers_have_explicit_markers_with_source_and_cycle(catalog_module) -> None:
    catalog = catalog_module.CATALOG
    ex_members = {m.fixture_key for m in catalog.members if m.group_key == "group.g57"}
    assert {c.member_key for c in catalog.conditions} == ex_members
    assert len(catalog.conditions) == 4
    assert all(c.condition == "EX_TRAVELER" for c in catalog.conditions)
    assert all(c.source_reference == catalog.source_reference for c in catalog.conditions)
    assert all(c.social_cycle == catalog.social_cycle for c in catalog.conditions)


def test_map_separates_institutional_academic_user_and_local_identities(catalog_module) -> None:
    catalog = catalog_module.CATALOG
    assert len(catalog.accounts) == 10
    members = {m.fixture_key: m for m in catalog.members}
    for account in catalog.accounts:
        member = members[account.member_key]
        assert account.username == str(member.academic_number)
        assert member.institutional_number != member.academic_number
        assert account.user_key != account.local_socio_key != account.member_key
        assert not hasattr(account, "user_id")
        assert not hasattr(account, "local_socio_id")
        assert not hasattr(account, "password")
    assert len({a.member_key for a in catalog.accounts}) == 10
    assert {a.role for a in catalog.accounts} == {"SOCIO", "CD", "FISCALIZADORA"}


def test_existing_seed_demo_accounts_are_preserved_references(catalog_module) -> None:
    catalog = catalog_module.CATALOG
    assert {a.legajo for a in catalog.preserved_accounts} == {
        "74907",
        "85194",
        "87414",
        "408917",
        "403655",
    }
    assert all(not hasattr(a, "password") for a in catalog.preserved_accounts)
    assert not {a.legajo for a in catalog.preserved_accounts} & {
        a.username for a in catalog.accounts
    }


def test_fixture_names_emails_and_ranges_fit_the_existing_models(catalog_module) -> None:
    from padron.models import Socio as InstitutionalSocio
    from padron.models import SocioEmail
    from socios.models import Role, Socio

    catalog = catalog_module.CATALOG
    assert all(a.role in Role.values for a in catalog.accounts)
    for member in catalog.members:
        assert len(member.first_name) <= InstitutionalSocio._meta.get_field("nombre").max_length
        assert len(member.last_name) <= InstitutionalSocio._meta.get_field("apellido").max_length
        assert len(member.email) <= SocioEmail._meta.get_field("email").max_length
        assert len(str(member.academic_number)) <= Socio._meta.get_field("legajo").max_length
        assert member.email.endswith("@scrum77.test")
        assert member.document_number >= 100000000
        assert member.birth_date < member.joined_on <= catalog.recorded_on
        for field in (
            "institutional_number",
            "academic_number",
            "document_number",
            "study_key",
            "email_key",
        ):
            assert 0 < getattr(member, field) <= 2147483647
    assert any("Á" in m.first_name or "á" in m.last_name for m in catalog.members)
    assert any(len(m.last_name) >= 25 for m in catalog.members)


def test_subcommissions_match_source_codes_and_unassigned_uses_sentinel(catalog_module) -> None:
    from padron.services import resolve_subcomision

    catalog = catalog_module.CATALOG
    assert [(s.institutional_code, s.name) for s in catalog.subcommissions] == [
        (1, "Cómputos"),
        (2, "Recursos Humanos"),
        (3, "Relaciones Institucionales"),
        (99, "Sin Subcomisión"),
    ]
    refs = {s.fixture_key for s in catalog.subcommissions}
    assert all(m.subcommission_key in refs for m in catalog.members)
    unassigned = [m for m in catalog.members if m.subcommission_key == "subcommission.unassigned"]
    assert len(unassigned) == 1
    assert resolve_subcomision(99, "Sin Subcomisión") is None


def test_vigencia_is_explicit_and_independent_of_ex_traveler_condition(catalog_module) -> None:
    catalog = catalog_module.CATALOG
    ex_keys = {m.fixture_key for m in catalog.members if m.group_key == "group.g57"}
    assert {a.is_enabled for a in catalog.accounts if a.member_key in ex_keys} == {True, False}
    assert {m.membership_state_code for m in catalog.members if m.fixture_key in ex_keys} == {1, 2}
    assert all(a.role == "SOCIO" for a in catalog.accounts if a.member_key in ex_keys)


def test_current_scenes_use_only_two_stages_and_real_urgency_codes(catalog_module) -> None:
    from expedientes.models import EstadoExpedienteEnum, UrgenciaExpedienteEnum

    catalog = catalog_module.CATALOG
    assert len(catalog.causes) == 3
    assert all(c.stage == EstadoExpedienteEnum.CREADO for c in catalog.causes)
    assert {c.urgency for c in catalog.causes} == set(UrgenciaExpedienteEnum.values)
    assert any(len(c.recipient_member_keys) > 1 for c in catalog.causes)
    assert len(catalog.t01_scenes) == 4
    assert Counter(s.status for s in catalog.t01_scenes) == {"DRAFT": 2, "ISSUED": 2}
    issued = [s for s in catalog.t01_scenes if s.status == "ISSUED"]
    assert len({s.creator_account_key for s in issued}) == 2
    assert any(len(s.recipient_member_keys) > 1 for s in issued)
    assert all(s.resulting_stage == EstadoExpedienteEnum.JUSTIFICANDO for s in issued)
    assert all(s.resulting_stage is None for s in catalog.t01_scenes if s.status == "DRAFT")
    assert all(
        not hasattr(scene, "expediente_id") and not hasattr(scene, "opened_at")
        for scene in (*catalog.causes, *catalog.t01_scenes)
    )


def test_future_historical_oracle_is_individual_and_does_not_add_pending_points(
    catalog_module,
) -> None:
    catalog = catalog_module.CATALOG
    assert len(catalog.historical_movements) == 8
    assert len({m.resolution_key for m in catalog.historical_movements}) == 7
    assert len({m.legacy_expediente_key for m in catalog.historical_movements}) == 7
    balances = catalog_module.expected_balances(catalog)
    assert len(balances) == 20
    assert balances["member.g57.01"] == Decimal("2.00")
    assert balances["member.g57.02"] == Decimal("-1.00")
    assert balances["member.g58.01"] == Decimal("0.00")
    assert balances["member.g58.02"] == Decimal("1.00")
    assert balances["member.g59.01"] == Decimal("2.00")
    assert balances["member.g59.02"] == Decimal("-4.00")
    assert balances["member.g60.01"] == Decimal("1.00")
    assert sum(balances.values()) == Decimal("1.00")
    shared = [
        m
        for m in catalog.historical_movements
        if m.resolution_key == "history.resolution.shared-merit"
    ]
    assert {(m.member_key, m.points) for m in shared} == {
        ("member.g57.01", Decimal("2.00")),
        ("member.g58.02", Decimal("1.00")),
    }
    changed_causes = tuple(replace(c, requested_points=Decimal("99.00")) for c in catalog.causes)
    assert catalog_module.expected_balances(replace(catalog, causes=changed_causes)) == balances


def test_junior_extension_preserves_the_original_catalog_payload(catalog_module) -> None:
    """Huella previa a TS77.46: identidades, escenas y puntos aprobados en la UAT."""
    catalog = catalog_module.CATALOG
    original_payload = {
        "members": [asdict(value) for value in catalog.members[:16]],
        "accounts": [asdict(value) for value in catalog.accounts[:6]],
        **{
            field: [asdict(value) for value in getattr(catalog, field)]
            for field in ("conditions", "causes", "t01_scenes", "historical_movements")
        },
    }
    fingerprint = hashlib.sha256(
        json.dumps(original_payload, default=str, ensure_ascii=False, sort_keys=True).encode()
    ).hexdigest()
    assert fingerprint == "eb2803063850c9873d813118d3bd26dbf8db8a2e278db80111a14db8db3f5b24"


def test_juniors_keep_ordinary_accounts_and_only_the_authorized_advanced_points(
    catalog_module,
) -> None:
    catalog = catalog_module.CATALOG
    members = catalog.members[16:]
    assert [(member.group_key, member.academic_number) for member in members] == [
        ("group.g62", 99077017),
        ("group.g62", 99077018),
        ("group.g63", 99077019),
        ("group.g63", 99077020),
    ]
    junior_keys = {member.fixture_key for member in members}
    accounts = [account for account in catalog.accounts if account.member_key in junior_keys]
    assert len(accounts) == 4
    assert all(account.role == "SOCIO" and account.is_enabled for account in accounts)
    assert all(member.membership_state_code == 1 for member in members)
    balances = catalog_module.expected_balances(catalog)
    assert not any(move.member_key in junior_keys for move in catalog.historical_movements)
    assert {key: balances[key] for key in junior_keys} == {
        "member.g62.01": Decimal("2"),
        "member.g62.02": Decimal("-1"),
        "member.g63.01": Decimal("-2"),
        "member.g63.02": Decimal("1"),
    }
    assert not {marker.member_key for marker in catalog.conditions} & junior_keys


@pytest.mark.parametrize("number,year,category", [(62, 1, "JUNIOR"), (63, 2, "JUNIOR")])
def test_catalog_rejects_a_junior_group_cut_different_from_the_declared_cycle(
    catalog_module, number: int, year: int, category: str
) -> None:
    catalog = catalog_module.CATALOG
    groups = tuple(
        replace(group, social_year=year, category=category) if group.number == number else group
        for group in catalog.groups
    )
    with pytest.raises(ValueError):
        catalog_module.validate_catalog(replace(catalog, groups=groups))


@pytest.mark.parametrize("changes", [{"role": "TD"}, {"is_enabled": False}])
def test_catalog_rejects_junior_extension_accounts_with_unapproved_permissions(
    catalog_module, changes: dict[str, object]
) -> None:
    catalog = catalog_module.CATALOG
    account = replace(catalog.accounts[-1], **changes)
    with pytest.raises(ValueError):
        catalog_module.validate_catalog(
            replace(catalog, accounts=(*catalog.accounts[:-1], account))
        )


def test_catalog_is_immutable_and_never_opens_a_database_connection(
    catalog_module, monkeypatch
) -> None:
    from django.db import connection

    def unexpected_cursor(*args, **kwargs):
        raise AssertionError("El catálogo debe ser independiente de la conexión de datos.")

    monkeypatch.setattr(connection, "cursor", unexpected_cursor)
    catalog_module.validate_catalog(catalog_module.CATALOG)
    catalog_module.expected_balances(catalog_module.CATALOG)
    assert isinstance(catalog_module.CATALOG.members, tuple)
    with pytest.raises(FrozenInstanceError):
        catalog_module.CATALOG.members[0].first_name = "Otro"


@pytest.mark.parametrize("field", ["profile", "source_reference", "social_cycle"])
def test_catalog_rejects_missing_cut_or_profile(catalog_module, field: str) -> None:
    with pytest.raises(ValueError):
        catalog_module.validate_catalog(replace(catalog_module.CATALOG, **{field: "  "}))


@pytest.mark.parametrize(
    "number,year,category",
    [(57, 7, "SENIOR"), (58, 5, "SENIOR"), (59, 2, "JUNIOR"), (60, None, "EX_TRAVELER")],
)
def test_catalog_rejects_a_group_cut_that_disagrees_with_the_po(
    catalog_module, number, year, category
) -> None:
    catalog = catalog_module.CATALOG
    groups = tuple(
        replace(g, social_year=year, category=category) if g.number == number else g
        for g in catalog.groups
    )
    with pytest.raises(ValueError):
        catalog_module.validate_catalog(replace(catalog, groups=groups))


def test_catalog_rejects_missing_group_members_or_marker(catalog_module) -> None:
    catalog = catalog_module.CATALOG
    for changed in (
        replace(catalog, members=catalog.members[:-1]),
        replace(catalog, conditions=catalog.conditions[:-1]),
    ):
        with pytest.raises(ValueError):
            catalog_module.validate_catalog(changed)


@pytest.mark.parametrize(
    "field,value",
    [
        ("institutional_number", True),
        ("academic_number", 2147483648),
        ("document_number", 0),
        ("study_key", -1),
        ("email_key", 1),
        ("fixture_key", "Persona visible"),
        ("first_name", "x" * 46),
        ("last_name", " "),
        ("email", "persona@example.com"),
        ("email", "x" * 40 + "@scrum77.test"),
        ("group_key", "group.g63"),
        ("subcommission_key", "subcommission.new"),
        ("membership_state_code", 999),
        ("birth_date", date(2030, 1, 1)),
    ],
)
def test_catalog_rejects_invalid_or_dangling_member_data(catalog_module, field, value) -> None:
    catalog = catalog_module.CATALOG
    member = replace(catalog.members[0], **{field: value})
    with pytest.raises(ValueError):
        catalog_module.validate_catalog(replace(catalog, members=(member, *catalog.members[1:])))


@pytest.mark.parametrize(
    "field",
    [
        "fixture_key",
        "institutional_number",
        "academic_number",
        "document_number",
        "study_key",
        "email_key",
        "email",
    ],
)
def test_catalog_rejects_duplicate_identity_values(catalog_module, field: str) -> None:
    catalog = catalog_module.CATALOG
    duplicate = replace(catalog.members[1], **{field: getattr(catalog.members[0], field)})
    with pytest.raises(ValueError):
        catalog_module.validate_catalog(
            replace(catalog, members=(catalog.members[0], duplicate, *catalog.members[2:]))
        )


@pytest.mark.parametrize(
    "field,value",
    [
        ("member_key", "member.g63.01"),
        ("role", "AUTORIDAD"),
        ("username", "74907"),
        ("username", "alias-de-persona"),
        ("is_enabled", 1),
        ("user_key", "user.g57.02"),
        ("local_socio_key", "user.g57.01"),
    ],
)
def test_catalog_rejects_invalid_or_ambiguous_account_references(
    catalog_module, field, value
) -> None:
    catalog = catalog_module.CATALOG
    account = replace(catalog.accounts[0], **{field: value})
    with pytest.raises(ValueError):
        catalog_module.validate_catalog(replace(catalog, accounts=(account, *catalog.accounts[1:])))


@pytest.mark.parametrize(
    "field,value",
    [
        ("condition", "UNKNOWN"),
        ("source_reference", "otra fuente"),
        ("social_cycle", "2027"),
        ("member_key", "member.g58.01"),
    ],
)
def test_catalog_rejects_contradictory_condition_provenance(catalog_module, field, value) -> None:
    catalog = catalog_module.CATALOG
    condition = replace(catalog.conditions[0], **{field: value})
    with pytest.raises(ValueError):
        catalog_module.validate_catalog(
            replace(catalog, conditions=(condition, *catalog.conditions[1:]))
        )


@pytest.mark.parametrize(
    "field,value",
    [
        ("creator_account_key", "account.missing"),
        ("recipient_member_keys", ("member.g64.01",)),
        ("recipient_member_keys", ("member.g57.01", "member.g57.01")),
        ("stage", "emitido"),
        ("urgency", "critical"),
    ],
)
def test_catalog_rejects_invalid_current_scenes(catalog_module, field, value) -> None:
    catalog = catalog_module.CATALOG
    scene = replace(catalog.causes[0], **{field: value})
    with pytest.raises(ValueError):
        catalog_module.validate_catalog(replace(catalog, causes=(scene, *catalog.causes[1:])))


def test_catalog_rejects_two_creators_resolved_to_the_same_account(catalog_module) -> None:
    catalog = catalog_module.CATALOG
    first_creator = catalog.t01_scenes[2].creator_account_key
    scenes = tuple(
        replace(s, creator_account_key=first_creator) if s.status == "ISSUED" else s
        for s in catalog.t01_scenes
    )
    with pytest.raises(ValueError):
        catalog_module.validate_catalog(replace(catalog, t01_scenes=scenes))


@pytest.mark.parametrize(
    "field,value",
    [
        ("member_key", "member.missing"),
        ("resolution_key", " "),
        ("legacy_expediente_key", "cause.created.low"),
        ("points", Decimal("0.33")),
        ("points", Decimal("NaN")),
        ("points", Decimal("0.00")),
    ],
)
def test_catalog_rejects_invalid_historical_or_fractional_movements(
    catalog_module, field, value
) -> None:
    catalog = catalog_module.CATALOG
    movement = replace(catalog.historical_movements[0], **{field: value})
    with pytest.raises(ValueError):
        catalog_module.validate_catalog(
            replace(catalog, historical_movements=(movement, *catalog.historical_movements[1:]))
        )
