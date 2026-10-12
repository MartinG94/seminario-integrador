"""Carga las identidades del catálogo demo sin sobrescribir personas existentes."""

from dataclasses import dataclass
from io import StringIO
from typing import Any

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.utils import timezone

from core.demo_fixtures import DemoFixtureRegistry
from padron.models import Socio as InstitutionalSocio
from padron.models import SocioEmail, SocioEstudio
from socios.demo_catalog import DemoCatalog, MemberFixture, validate_catalog
from socios.management.commands.seed_demo import DEMO_PASSWORD
from socios.models import InstitutionalMembershipCondition, Socio, Subcomision


@dataclass
class DemoMembersResult:
    users: dict[str, Any]
    local_socios: dict[str, Socio]
    accounts: dict[str, Socio]
    institutional_members: dict[str, InstitutionalSocio]
    groups: dict[str, int]
    subcommissions: dict[str, Subcomision | None]
    preserved_accounts: dict[str, Socio]


def _assert_model_identity(
    registry: DemoFixtureRegistry, key: str, model: Any, lookup: dict[str, Any]
) -> None:
    record = registry.get(key)
    matches = model.objects.using(registry.connection.alias).filter(**lookup)
    if record is not None:
        matches = matches.exclude(pk=record.object_key)
    if matches.exists():
        raise CommandError("Una identidad del catálogo coincide con una fila ajena.")


def _check_member_namespaces(catalog: DemoCatalog, registry: DemoFixtureRegistry) -> None:
    user_model = get_user_model()
    members = {member.fixture_key: member for member in catalog.members}
    for account in catalog.accounts:
        member = members[account.member_key]
        _assert_model_identity(
            registry, account.user_key, user_model, {"username": account.username}
        )
        _assert_model_identity(registry, account.user_key, user_model, {"email": member.email})
        _assert_model_identity(
            registry, account.local_socio_key, Socio, {"legajo": account.username}
        )
        _assert_model_identity(registry, account.local_socio_key, Socio, {"email": member.email})
    for member in catalog.members:
        _assert_model_identity(
            registry, member.fixture_key, InstitutionalSocio, {"nroDoc": member.document_number}
        )
        studies = SocioEstudio.objects.using(registry.connection.alias).filter(
            nroLegajo=member.academic_number
        )
        emails = SocioEmail.objects.using(registry.connection.alias).filter(email=member.email)
        if (
            studies.exclude(socio_id=member.institutional_number).exists()
            or emails.exclude(socio_id=member.institutional_number).exists()
        ):
            raise CommandError("La identidad académica o el correo pertenecen a una ficha ajena.")


def _preserved_accounts(catalog: DemoCatalog, registry: DemoFixtureRegistry) -> dict[str, Socio]:
    user_model = get_user_model()
    alias = registry.connection.alias
    before = {
        reference.legajo: Socio.objects.using(alias).filter(legajo=reference.legajo).first()
        for reference in catalog.preserved_accounts
    }
    for reference in catalog.preserved_accounts:
        if before[reference.legajo] is None:
            if (
                user_model.objects.using(alias).filter(username=reference.legajo).exists()
                or Socio.objects.using(alias)
                .filter(email=f"{reference.legajo}@aveit.test")
                .exists()
            ):
                raise CommandError("Una identidad seed_demo coincide con una cuenta ajena.")
    # El comando original define las cinco credenciales y roles; se conserva sin replicarlo.
    if any(row is None for row in before.values()):
        call_command("seed_demo", stdout=StringIO())
    preserved = {}
    for reference in catalog.preserved_accounts:
        local = Socio.objects.using(alias).get(legajo=reference.legajo)
        existing = before[reference.legajo] is not None
        registry.record(reference.fixture_key, Socio._meta.db_table, local.pk, owned=not existing)
        registry.record(
            f"{reference.fixture_key}.user",
            user_model._meta.db_table,
            local.user_id,
            owned=not existing,
        )
        preserved[reference.fixture_key] = local
    return preserved


def _load_reference_catalogs(registry: DemoFixtureRegistry) -> None:
    # Valores fuente: namespace de vigencia legado; no son la clasificación Junior/Senior.
    references = (
        (
            "reference.document.dni",
            "socio_tipodocumento",
            "codTipoDoc",
            1,
            "DNI",
            "Documento Nacional de Identidad",
        ),
        ("reference.sex.other", "socio_sexo", "codSexo", 3, "Otro", "No binario / Otro"),
        (
            "reference.member-type.ordinary",
            "socio_tipoSocio",
            "idTipoSocio",
            12,
            "Socio Ordinario",
            None,
        ),
        (
            "reference.membership.enabled",
            "socio_estado",
            "codEstadoSocio",
            1,
            "Activo",
            "Socio activo con plenos derechos",
        ),
        (
            "reference.membership.recess",
            "socio_estado",
            "codEstadoSocio",
            2,
            "Pasivo",
            "Socio pasivo en receso justificado",
        ),
        (
            "reference.change-reason.regular",
            "socio_motivoCambioEstado",
            "idMotivoCambio",
            1,
            "Regular",
            "Evolución normal de membresía",
        ),
        (
            "reference.specialty.systems",
            "socio_especialidad",
            "codEspecialidad",
            1,
            "Ingeniería en Sistemas de Información",
            "UTN FRC",
        ),
    )
    for key, table, pk, code, name, description in references:
        values = {pk: code, "nombre": name}
        if description is not None:
            values["descripcion"] = description
        registry.ensure_legacy(key, table, pk, {pk: code}, values, reference=True)


def _load_member(
    member: MemberFixture,
    catalog: DemoCatalog,
    registry: DemoFixtureRegistry,
    users_by_member: dict[str, Any],
) -> InstitutionalSocio:
    groups = {group.fixture_key: group for group in catalog.groups}
    subcommissions = {sub.fixture_key: sub for sub in catalog.subcommissions}
    group = groups[member.group_key]
    user = users_by_member.get(member.fixture_key)
    user_id = user.pk if user is not None else None
    if (
        user_id is not None
        and InstitutionalSocio.objects.using(registry.connection.alias)
        .filter(user_id=user_id)
        .exclude(pk=member.institutional_number)
        .exists()
    ):
        raise CommandError("El vínculo de cuenta identifica una ficha institucional ajena.")
    row = registry.ensure_legacy(
        member.fixture_key,
        "socio_lista",
        "nroSocio",
        {"nroSocio": member.institutional_number},
        {
            "nroSocio": member.institutional_number,
            "nombre": member.first_name,
            "apellido": member.last_name,
            "fechaIngreso": member.joined_on,
            "codTipoDoc": member.document_type_code,
            "nroDoc": member.document_number,
            "fechaNac": member.birth_date,
            "codSexo": member.sex_code,
            "codSubcomision": subcommissions[member.subcommission_key].institutional_code,
            "anoSocial": group.social_year,
            "idTipoSocio": member.member_type_code,
            "user_id": user_id,
            "ingresante": False,
            "forzarCambioClave": False,
        },
    )
    if row["anoSocial"] != group.social_year:
        raise CommandError("El año institucional contradice el corte social confirmado del grupo.")
    if row["user_id"] != user_id:
        raise CommandError("La asociación institucional de la cuenta no corresponde al manifiesto.")
    registry.ensure_legacy(
        f"{member.fixture_key}.study",
        "socio_estudio",
        "compositeKey",
        {"compositeKey": member.study_key},
        {
            "compositeKey": member.study_key,
            "nroSocio": member.institutional_number,
            "nroLegajo": member.academic_number,
            "codEspecialidad": member.specialty_code,
        },
    )
    registry.ensure_legacy(
        f"{member.fixture_key}.email",
        "socio_email",
        "compositeKey",
        {"compositeKey": member.email_key},
        {
            "compositeKey": member.email_key,
            "nroSocio": member.institutional_number,
            "idEmail": 1,
            "email": member.email,
            "comprobado": True,
            "habilitado": True,
        },
    )
    history = registry.ensure_legacy(
        f"{member.fixture_key}.membership-history",
        "socio_estadoHistorial",
        "idEstadoHistorial",
        {"nroSocio": member.institutional_number},
        {
            "idGrupo": group.number,
            "nroSocio": member.institutional_number,
            "fechaHora": timezone.now().replace(tzinfo=None),
            "codEstadoSocio": member.membership_state_code,
            "socio_motivoCambioEstado": member.change_reason_code,
        },
    )
    if history["idGrupo"] != group.number or history["nroSocio"] != member.institutional_number:
        raise CommandError(
            "El historial institucional contradice la referencia y el corte del grupo."
        )
    study = SocioEstudio.objects.using(registry.connection.alias).get(pk=member.study_key)
    email = SocioEmail.objects.using(registry.connection.alias).get(pk=member.email_key)
    if (
        study.socio_id != member.institutional_number
        or email.socio_id != member.institutional_number
    ):
        raise CommandError("Un satélite institucional no corresponde a su referencia de socio.")
    return InstitutionalSocio.objects.using(registry.connection.alias).get(pk=row["nroSocio"])


def load_demo_members(
    catalog: DemoCatalog, registry: DemoFixtureRegistry, *, password: str = DEMO_PASSWORD
) -> DemoMembersResult:
    """Crea 10 cuentas/20 fichas y conserva las cinco cuentas del comando original."""
    validate_catalog(catalog)
    registry._check_write()
    if registry.profile != catalog.profile:
        raise CommandError("El perfil del registro no corresponde al catálogo aprobado.")
    if not isinstance(password, str) or not password:
        raise CommandError("La credencial de alta demo no puede estar vacía.")
    _check_member_namespaces(catalog, registry)
    subcommissions: dict[str, Subcomision | None] = {}
    for fixture in catalog.subcommissions:
        registry.ensure_legacy(
            f"{fixture.fixture_key}.institutional",
            "socio_tiposubcomision",
            "codSubcomision",
            {"codSubcomision": fixture.institutional_code},
            {"codSubcomision": fixture.institutional_code, "nombre": fixture.name},
            reference=True,
        )
        subcommissions[fixture.fixture_key] = (
            None
            if fixture.institutional_code == 99
            else registry.ensure_model(
                fixture.fixture_key, Subcomision, {"name": fixture.name}, {}, reference=True
            )
        )
    groups = {}
    for group in catalog.groups:
        registry.ensure_legacy(
            group.fixture_key,
            "grupo_lista",
            "nroGrupo",
            {"nroGrupo": group.number},
            {"nroGrupo": group.number, "nombre": f"G{group.number}"},
            reference=True,
        )
        groups[group.fixture_key] = group.number
    _load_reference_catalogs(registry)
    preserved = _preserved_accounts(catalog, registry)
    members = {member.fixture_key: member for member in catalog.members}
    group_fixtures = {group.fixture_key: group for group in catalog.groups}
    users, locals_, accounts, users_by_member = {}, {}, {}, {}
    user_model = get_user_model()
    for account in catalog.accounts:
        member = members[account.member_key]
        group = group_fixtures[member.group_key]
        user = registry.ensure_model(
            account.user_key,
            user_model,
            {"username": account.username},
            {},
            create=lambda account=account, member=member: user_model.objects.db_manager(
                registry.connection.alias
            ).create_user(
                username=account.username,
                email=member.email,
                password=password,
                first_name=member.first_name,
                last_name=member.last_name,
            ),
        )
        local = registry.ensure_model(
            account.local_socio_key,
            Socio,
            {"legajo": account.username},
            {
                "user": user,
                "first_name": member.first_name,
                "last_name": member.last_name,
                "email": member.email,
                "subcomision": subcommissions[member.subcommission_key],
                "social_year": group.social_year,
                "category": group.category,
                "role": account.role,
                "is_enabled": account.is_enabled,
            },
        )
        if local.user_id != user.pk:
            raise CommandError(
                "La cuenta y el socio operativo no corresponden a su referencia estable."
            )
        if (local.social_year, local.category) != (group.social_year, group.category):
            raise CommandError(
                "La clasificación operativa contradice el corte social confirmado del grupo."
            )
        users[account.user_key], locals_[account.local_socio_key] = user, local
        accounts[account.fixture_key], users_by_member[account.member_key] = local, user
    institutionals = {
        member.fixture_key: _load_member(member, catalog, registry, users_by_member)
        for member in catalog.members
    }
    for condition in catalog.conditions:
        member = members[condition.member_key]
        row = registry.ensure_model(
            condition.fixture_key,
            InstitutionalMembershipCondition,
            {"institutional_number": member.institutional_number},
            {
                "condition": condition.condition,
                "source_reference": condition.source_reference,
                "social_cycle": condition.social_cycle,
            },
        )
        if (row.condition, row.source_reference, row.social_cycle) != (
            condition.condition,
            condition.source_reference,
            condition.social_cycle,
        ):
            raise CommandError(
                "El metadato exviajero no conserva la fuente y el corte del catálogo."
            )
    return DemoMembersResult(
        users, locals_, accounts, institutionals, groups, subcommissions, preserved
    )
