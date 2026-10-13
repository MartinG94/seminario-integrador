"""Catálogo sintético de SCRUM-77 y ampliación Junior, sin operaciones de carga.

El corte se declara conforme al PO; las escenas y saldos son oráculos para
TS77.12–15. La propiedad, colisiones y PK reales se resuelven en TS77.08–11.
"""

import re
from collections import Counter
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from types import MappingProxyType

from socios.demo_presentation import SCENE_PRESENTATIONS


@dataclass(frozen=True)
class GroupFixture:
    fixture_key: str
    number: int
    social_year: int | None
    category: str


@dataclass(frozen=True)
class SubcommissionFixture:
    fixture_key: str
    institutional_code: int
    name: str


@dataclass(frozen=True)
class MemberFixture:
    fixture_key: str
    institutional_number: int
    academic_number: int
    document_number: int
    study_key: int
    email_key: int
    group_key: str
    subcommission_key: str
    first_name: str
    last_name: str
    email: str
    birth_date: date
    joined_on: date
    membership_state_code: int
    document_type_code: int = 1
    sex_code: int = 3
    member_type_code: int = 12
    specialty_code: int = 1
    change_reason_code: int = 1


@dataclass(frozen=True)
class AccountFixture:
    fixture_key: str
    member_key: str
    user_key: str
    local_socio_key: str
    username: str
    role: str
    is_enabled: bool


@dataclass(frozen=True)
class PreservedAccountFixture:
    fixture_key: str
    legajo: str


@dataclass(frozen=True)
class ConditionFixture:
    fixture_key: str
    member_key: str
    condition: str
    source_reference: str
    social_cycle: str


@dataclass(frozen=True)
class CauseFixture:
    fixture_key: str
    creator_account_key: str
    recipient_member_keys: tuple[str, ...]
    stage: str
    urgency: str
    requested_points: Decimal


@dataclass(frozen=True)
class T01Fixture:
    fixture_key: str
    creator_account_key: str
    recipient_member_keys: tuple[str, ...]
    status: str
    resulting_stage: str | None
    urgency: str
    requested_points: Decimal


@dataclass(frozen=True)
class HistoricalMovementFixture:
    fixture_key: str
    member_key: str
    resolution_key: str
    legacy_expediente_key: str
    points: Decimal


_ADVANCED_SOURCE = "RF77-16 / historia sintética autorizada; sin firma productiva"


@dataclass(frozen=True)
class AdvancedCauseFixture:
    """Historia ficticia importada; no acredita un trámite o firma productivos."""

    fixture_key: str
    creator_account_key: str
    recipient_member_keys: tuple[str, ...]
    stage: str
    urgency: str
    requested_points: Decimal
    opened_at: datetime
    justification_started_at: datetime
    reviewed_at: datetime
    signature_pending_at: datetime | None = None
    dispatch_pending_at: datetime | None = None
    emitted_at: datetime | None = None
    source_reference: str = _ADVANCED_SOURCE

    @property
    def updated_at(self) -> datetime:
        return (
            self.emitted_at
            or self.dispatch_pending_at
            or self.signature_pending_at
            or self.reviewed_at
        )


@dataclass(frozen=True)
class DemoCatalog:
    profile: str
    social_cycle: str
    source_reference: str
    recorded_on: date
    groups: tuple[GroupFixture, ...]
    subcommissions: tuple[SubcommissionFixture, ...]
    members: tuple[MemberFixture, ...]
    accounts: tuple[AccountFixture, ...]
    preserved_accounts: tuple[PreservedAccountFixture, ...]
    conditions: tuple[ConditionFixture, ...]
    causes: tuple[CauseFixture, ...]
    t01_scenes: tuple[T01Fixture, ...]
    historical_movements: tuple[HistoricalMovementFixture, ...]
    advanced_causes: tuple[AdvancedCauseFixture, ...] = ()


# Rango propio del catálogo; la ausencia de colisiones se comprueba al cargar.
IDENTITY_RANGES = MappingProxyType(
    {
        "institutional_number": (770001, 770020),
        "academic_number": (99077001, 99077020),
        "document_number": (100077001, 100077020),
        "study_key": (1770001, 1770020),
        "email_key": (2770001, 2770020),
    }
)

_SOURCE = "SRC77-PO-02 / RN77-01–04 (versión escrita corregida del PO)"
_CYCLE = "PO-SCRUM77-CORTE-01"
_GROUPS = (
    GroupFixture("group.g57", 57, None, "EX_TRAVELER"),
    GroupFixture("group.g58", 58, 6, "SENIOR"),
    GroupFixture("group.g59", 59, 5, "SENIOR"),
    GroupFixture("group.g60", 60, 4, "SENIOR"),
    # Corte explícito de la ampliación: G63=1 del PO; G62=2 en la misma escala.
    # No se implementa una fórmula permanente ni un pase anual por calendario.
    GroupFixture("group.g62", 62, 2, "JUNIOR"),
    GroupFixture("group.g63", 63, 1, "JUNIOR"),
)
_SUBCOMMISSIONS = (
    SubcommissionFixture("subcommission.computing", 1, "Cómputos"),
    SubcommissionFixture("subcommission.people", 2, "Recursos Humanos"),
    SubcommissionFixture("subcommission.relations", 3, "Relaciones Institucionales"),
    SubcommissionFixture("subcommission.unassigned", 99, "Sin Subcomisión"),
)


def _members() -> tuple[MemberFixture, ...]:
    # Los IDs se generan desde un orden fijo; el corte social NO usa esa fórmula.
    names = (
        ("Ámbar", "Faro Demo"),
        ("Bastián", "Bruma Demo"),
        ("Cira", "Cumbre Demo"),
        ("Darío", "Duna Demo"),
        ("Elena", "Ensayo Demo"),
        ("Félix", "Fábula Demo"),
        ("Galatea", "García de las Nubes de Ensayo"),
        ("Héctor", "Horizonte Demo"),
        ("Irina", "Isla Demo"),
        ("Julián", "Jardín Demo"),
        ("Kira", "Kilómetro Demo"),
        ("León", "Lago Demo"),
        ("Malena", "Marea Demo"),
        ("Nereo", "Niebla Demo"),
        ("Ópalo", "Orilla Demo"),
        ("Paz", "Puente Demo"),
    )
    assignments = (0, 1, 2, 0, 1, 2, 0, 1, 2, 0, 1, 2, 0, 1, 2, 3)
    joined_dates = (date(2019, 3, 1), date(2020, 3, 1), date(2021, 3, 1), date(2022, 3, 1))
    return tuple(
        MemberFixture(
            fixture_key=f"member.g{_GROUPS[index // 4].number}.{index % 4 + 1:02d}",
            institutional_number=770001 + index,
            academic_number=99077001 + index,
            document_number=100077001 + index,
            study_key=1770001 + index,
            email_key=2770001 + index,
            group_key=_GROUPS[index // 4].fixture_key,
            subcommission_key=_SUBCOMMISSIONS[assignments[index]].fixture_key,
            first_name=first_name,
            last_name=last_name,
            email=f"g{_GROUPS[index // 4].number}.{index % 4 + 1:02d}@scrum77.test",
            birth_date=date(1998, 5, index + 1),
            joined_on=joined_dates[index // 4],
            membership_state_code=2 if index in (1, 15) else 1,
        )
        for index, (first_name, last_name) in enumerate(names)
    )


def _junior_members() -> tuple[MemberFixture, ...]:
    """Agrega órdenes nuevos sin alterar las dieciséis identidades ya aprobadas."""
    definitions = (
        (17, 62, 1, "Quimey", "Quimera Demo", "subcommission.computing", date(2024, 3, 1)),
        (18, 62, 2, "Rocío", "Rumbo Demo", "subcommission.people", date(2024, 3, 1)),
        (19, 63, 1, "Sol", "Sendero Demo", "subcommission.relations", date(2025, 3, 1)),
        (20, 63, 2, "Tomás", "Trama Demo", "subcommission.computing", date(2025, 3, 1)),
    )
    return tuple(
        MemberFixture(
            fixture_key=f"member.g{group}.{index:02d}",
            institutional_number=770000 + order,
            academic_number=99077000 + order,
            document_number=100077000 + order,
            study_key=1770000 + order,
            email_key=2770000 + order,
            group_key=f"group.g{group}",
            subcommission_key=subcommission_key,
            first_name=first_name,
            last_name=last_name,
            email=f"g{group}.{index:02d}@scrum77.test",
            birth_date=date(1998, 5, order),
            joined_on=joined_on,
            membership_state_code=1,
        )
        for order, group, index, first_name, last_name, subcommission_key, joined_on in definitions
    )


_MEMBERS = _members() + _junior_members()


def _account(suffix: str, role: str, is_enabled: bool = True) -> AccountFixture:
    member = next(m for m in _MEMBERS if m.fixture_key == f"member.{suffix}")
    return AccountFixture(
        f"account.{suffix}",
        member.fixture_key,
        f"user.{suffix}",
        f"local_socio.{suffix}",
        str(member.academic_number),
        role,
        is_enabled,
    )


def _advanced_scene(
    key: str, stage: str, members: tuple[str, ...], points: str, *, ordinal: int
) -> AdvancedCauseFixture:
    """Fechas constantes del relato sintético; nunca se consulta el reloj."""
    opened = datetime(2026, 9, 1, 12, ordinal, tzinfo=timezone.utc)
    stages = ("revision_resolucion", "espera_resolucion", "pendiente_correos", "emitido")
    index = stages.index(stage)
    return AdvancedCauseFixture(
        key,
        "account.g58.01" if ordinal % 2 else "account.g59.01",
        members,
        stage,
        ("baja", "normal", "urgente")[ordinal % 3],
        Decimal(points),
        opened,
        opened + timedelta(days=1),
        opened + timedelta(days=15),
        opened + timedelta(days=16) if index >= 1 else None,
        opened + timedelta(days=17) if index >= 2 else None,
        opened + timedelta(days=18) if index >= 3 else None,
    )


CATALOG = DemoCatalog(
    profile="scrum77-g57-g60-v1",
    social_cycle=_CYCLE,
    source_reference=_SOURCE,
    recorded_on=date(2026, 10, 12),
    groups=_GROUPS,
    subcommissions=_SUBCOMMISSIONS,
    members=_MEMBERS,
    accounts=(
        _account("g57.01", "SOCIO"),
        _account("g57.02", "SOCIO", False),
        _account("g58.01", "CD"),
        _account("g58.02", "SOCIO"),
        _account("g59.01", "FISCALIZADORA"),
        _account("g60.01", "SOCIO"),
        _account("g62.01", "SOCIO"),
        _account("g62.02", "SOCIO"),
        _account("g63.01", "SOCIO"),
        _account("g63.02", "SOCIO"),
    ),
    preserved_accounts=tuple(
        PreservedAccountFixture(f"preserved.seed-demo.{legajo}", legajo)
        for legajo in ("74907", "85194", "87414", "408917", "403655")
    ),
    conditions=tuple(
        ConditionFixture(
            f"condition.g57.{index:02d}", f"member.g57.{index:02d}", "EX_TRAVELER", _SOURCE, _CYCLE
        )
        for index in range(1, 5)
    ),
    causes=(
        CauseFixture(
            "cause.created.low",
            "account.g58.01",
            ("member.g57.01",),
            "creado",
            "baja",
            Decimal("-1.00"),
        ),
        CauseFixture(
            "cause.created.normal",
            "account.g59.01",
            ("member.g58.02",),
            "creado",
            "normal",
            Decimal("-2.00"),
        ),
        CauseFixture(
            "cause.created.urgent.multi",
            "account.g58.01",
            ("member.g57.01", "member.g60.01"),
            "creado",
            "urgente",
            Decimal("-3.00"),
        ),
    ),
    t01_scenes=(
        T01Fixture("t01.cd.draft", "account.g58.01", (), "DRAFT", None, "normal", Decimal("0.00")),
        T01Fixture(
            "t01.authority.draft",
            "account.g59.01",
            ("member.g60.01",),
            "DRAFT",
            None,
            "normal",
            Decimal("-1.00"),
        ),
        T01Fixture(
            "t01.cd.issued.multi",
            "account.g58.01",
            ("member.g57.01", "member.g58.02"),
            "ISSUED",
            "justificando",
            "urgente",
            Decimal("-2.00"),
        ),
        T01Fixture(
            "t01.authority.issued",
            "account.g59.01",
            ("member.g60.01",),
            "ISSUED",
            "justificando",
            "baja",
            Decimal("-1.00"),
        ),
    ),
    advanced_causes=(
        _advanced_scene(
            "advanced.review.01", "revision_resolucion", ("member.g57.01",), "-1", ordinal=1
        ),
        _advanced_scene(
            "advanced.review.02", "revision_resolucion", ("member.g62.01",), "-2", ordinal=2
        ),
        _advanced_scene(
            "advanced.review.03",
            "revision_resolucion",
            ("member.g63.01", "member.g60.01"),
            "-3",
            ordinal=3,
        ),
        _advanced_scene(
            "advanced.signature.01", "espera_resolucion", ("member.g58.02",), "-1", ordinal=4
        ),
        _advanced_scene(
            "advanced.dispatch.01", "pendiente_correos", ("member.g59.01",), "-2", ordinal=5
        ),
        _advanced_scene(
            "advanced.dispatch.02", "pendiente_correos", ("member.g62.02",), "-1", ordinal=6
        ),
        _advanced_scene("advanced.emitted.01", "emitido", ("member.g62.01",), "2", ordinal=7),
        _advanced_scene("advanced.emitted.02", "emitido", ("member.g62.02",), "-1", ordinal=8),
        _advanced_scene("advanced.emitted.03", "emitido", ("member.g63.01",), "-2", ordinal=9),
        _advanced_scene("advanced.emitted.04", "emitido", ("member.g63.02",), "1", ordinal=10),
    ),
    historical_movements=(
        HistoricalMovementFixture(
            "history.movement.g57-merit",
            "member.g57.01",
            "history.resolution.shared-merit",
            "history.expediente.shared-merit",
            Decimal("2.00"),
        ),
        HistoricalMovementFixture(
            "history.movement.g58-shared-merit",
            "member.g58.02",
            "history.resolution.shared-merit",
            "history.expediente.shared-merit",
            Decimal("1.00"),
        ),
        HistoricalMovementFixture(
            "history.movement.g59-merit",
            "member.g59.01",
            "history.resolution.g59-merit",
            "history.expediente.g59-merit",
            Decimal("2.00"),
        ),
        HistoricalMovementFixture(
            "history.movement.g57-sanction",
            "member.g57.02",
            "history.resolution.g57-sanction",
            "history.expediente.g57-sanction",
            Decimal("-1.00"),
        ),
        HistoricalMovementFixture(
            "history.movement.g58-positive",
            "member.g58.01",
            "history.resolution.g58-positive",
            "history.expediente.g58-positive",
            Decimal("3.00"),
        ),
        HistoricalMovementFixture(
            "history.movement.g58-negative",
            "member.g58.01",
            "history.resolution.g58-negative",
            "history.expediente.g58-negative",
            Decimal("-3.00"),
        ),
        HistoricalMovementFixture(
            "history.movement.g59-sanction",
            "member.g59.02",
            "history.resolution.g59-sanction",
            "history.expediente.g59-sanction",
            Decimal("-4.00"),
        ),
        HistoricalMovementFixture(
            "history.movement.g60-merit",
            "member.g60.01",
            "history.resolution.g60-merit",
            "history.expediente.g60-merit",
            Decimal("1.00"),
        ),
    ),
)


def _text(value: str, limit: int, label: str) -> None:
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise ValueError(f"{label}: texto vacío o fuera del contrato.")


def _key(value: str, prefix: str = "") -> None:
    _text(value, 100, "Clave de catálogo")
    if not re.fullmatch(r"[a-z][a-z0-9._-]*", value) or not value.startswith(prefix):
        raise ValueError("La clave estable no corresponde al namespace del catálogo.")


def _unique(items: tuple[object, ...], field: str) -> None:
    values = [getattr(item, field) for item in items]
    if len(values) != len(set(values)):
        raise ValueError(f"El catálogo contiene un valor duplicado de {field}.")


def _points(value: Decimal, *, nonzero: bool = False) -> None:
    if (
        not isinstance(value, Decimal)
        or not value.is_finite()
        or value != value.to_integral_value()
        or abs(value) > Decimal("99999999")
        or (nonzero and value == 0)
    ):
        raise ValueError("El oráculo requiere puntos enteros finitos dentro de DECIMAL(10,2).")


def validate_catalog(catalog: DemoCatalog) -> None:
    """Valida el conjunto v1 en memoria; no acredita propiedad ni filas destino."""
    _key(catalog.profile)
    _text(catalog.source_reference, 200, "Fuente del corte")
    _text(catalog.social_cycle, 80, "Corte social")
    if type(catalog.recorded_on) is not date:
        raise ValueError("El catálogo requiere su fecha de registro técnico.")
    if catalog.groups != _GROUPS or any(
        g.social_year is not None and type(g.social_year) is not int for g in catalog.groups
    ):
        raise ValueError("El corte de grupos debe coincidir con la respuesta corregida del PO.")
    if catalog.subcommissions != _SUBCOMMISSIONS:
        raise ValueError("Las referencias de subcomisión deben conservar sus códigos fuente.")
    collections = (
        catalog.groups,
        catalog.subcommissions,
        catalog.members,
        catalog.accounts,
        catalog.preserved_accounts,
        catalog.conditions,
        catalog.causes,
        catalog.t01_scenes,
        catalog.historical_movements,
        catalog.advanced_causes,
    )
    for items in collections:
        if not isinstance(items, tuple):
            raise ValueError("El catálogo debe usar colecciones inmutables.")
        _unique(items, "fixture_key")
        for item in items:
            _key(item.fixture_key)
    _unique(tuple(item for items in collections for item in items), "fixture_key")
    for scene in (*catalog.causes, *catalog.t01_scenes, *catalog.advanced_causes):
        presentation = SCENE_PRESENTATIONS.get(scene.fixture_key)
        if presentation is None:
            raise ValueError("La escena requiere un título y relato ficticios aprobados.")
        _text(presentation.title, 255, "Título ficticio")
        for text in (
            presentation.reason,
            presentation.place,
            presentation.witnesses,
            presentation.causal,
        ):
            if not text.strip():
                raise ValueError("La presentación de la escena no puede estar vacía.")
    group_counts = {group.fixture_key: 2 if group.category == "JUNIOR" else 4 for group in _GROUPS}
    if Counter(m.group_key for m in catalog.members) != group_counts:
        raise ValueError("Se requieren cuatro identidades G57–G60 y dos por cada grupo Junior.")
    for field, (lower, upper) in IDENTITY_RANGES.items():
        _unique(catalog.members, field)
        if any(
            type(getattr(m, field)) is not int or not lower <= getattr(m, field) <= upper
            for m in catalog.members
        ):
            raise ValueError(f"{field}: identidad fuera del rango sintético acordado.")
    _unique(catalog.members, "email")
    member_by_key = {m.fixture_key: m for m in catalog.members}
    subcommission_keys = {s.fixture_key for s in catalog.subcommissions}
    for member in catalog.members:
        _key(member.fixture_key, "member.")
        _text(member.first_name, 45, "Nombre ficticio")
        _text(member.last_name, 45, "Apellido ficticio")
        _text(member.email, 45, "Correo ficticio")
        if not re.fullmatch(r"g(?:57|58|59|60|62|63)\.[0-9]{2}@scrum77\.test", member.email):
            raise ValueError("El correo debe pertenecer al dominio y referencia ficticios.")
        if member.fixture_key.removeprefix("member.") != member.email.split("@", 1)[0]:
            raise ValueError("La casilla ficticia debe corresponder a su identidad estable.")
        if not member.fixture_key.startswith(f"member.{member.group_key.removeprefix('group.')}."):
            raise ValueError("La identidad debe conservar su referencia de grupo.")
        if member.subcommission_key not in subcommission_keys:
            raise ValueError("El socio contiene una referencia de subcomisión inexistente.")
        if (
            type(member.birth_date) is not date
            or type(member.joined_on) is not date
            or not member.birth_date < member.joined_on <= catalog.recorded_on
        ):
            raise ValueError("Las fechas de ficha deben ser válidas en el registro técnico.")
        codes = (
            member.document_type_code,
            member.sex_code,
            member.member_type_code,
            member.specialty_code,
            member.change_reason_code,
            member.membership_state_code,
        )
        if (
            any(type(code) is not int for code in codes)
            or codes[:5] != (1, 3, 12, 1, 1)
            or codes[5] not in (1, 2)
        ):
            raise ValueError(
                "Las referencias de ficha deben conservar los códigos fuente declarados."
            )
    if len(catalog.preserved_accounts) != 5 or {a.legajo for a in catalog.preserved_accounts} != {
        "74907",
        "85194",
        "87414",
        "408917",
        "403655",
    }:
        raise ValueError("Las cinco cuentas seed_demo deben conservar sus referencias.")
    if len(catalog.accounts) != 10:
        raise ValueError("El catálogo ampliado declara diez cuentas operativas nuevas.")
    for field in ("member_key", "username", "user_key", "local_socio_key"):
        _unique(catalog.accounts, field)
    for account in catalog.accounts:
        _key(account.fixture_key, "account.")
        suffix = account.fixture_key.removeprefix("account.")
        member = member_by_key.get(account.member_key)
        if (
            member is None
            or account.member_key != f"member.{suffix}"
            or account.user_key != f"user.{suffix}"
            or account.local_socio_key != f"local_socio.{suffix}"
            or account.username != str(member.academic_number)
        ):
            raise ValueError("Las referencias de cuenta y ambos socios deben ser inequívocas.")
        if (
            account.role not in {"SOCIO", "CD", "FISCALIZADORA", "TD", "ADMIN"}
            or type(account.is_enabled) is not bool
        ):
            raise ValueError("La cuenta requiere rol existente y vigencia booleana explícita.")
        if member.group_key in {"group.g62", "group.g63"} and (
            account.role != "SOCIO" or not account.is_enabled
        ):
            raise ValueError("Las cuentas Junior del catálogo son socios comunes habilitados.")
    if {a.username for a in catalog.accounts} & {a.legajo for a in catalog.preserved_accounts}:
        raise ValueError("El conjunto nuevo no puede ocupar una identidad seed_demo.")
    ex_keys = {m.fixture_key for m in catalog.members if m.group_key == "group.g57"}
    _unique(catalog.conditions, "member_key")
    if {c.member_key for c in catalog.conditions} != ex_keys:
        raise ValueError("Cada G57 requiere su condición explícita sin marcar otra cohorte.")
    for condition in catalog.conditions:
        if (
            condition.condition != "EX_TRAVELER"
            or condition.source_reference != catalog.source_reference
            or condition.social_cycle != catalog.social_cycle
        ):
            raise ValueError(
                "La condición institucional debe conservar fuente y corte del catálogo."
            )
    accounts = {a.fixture_key: a for a in catalog.accounts}
    operational_members = {a.member_key for a in catalog.accounts}
    for scene in (*catalog.causes, *catalog.t01_scenes, *catalog.advanced_causes):
        creator = accounts.get(scene.creator_account_key)
        if (
            creator is None
            or not creator.is_enabled
            or creator.role not in {"CD", "TD", "FISCALIZADORA"}
        ):
            raise ValueError("La escena requiere un solicitante operativo habilitado por su rol.")
        if len(set(scene.recipient_member_keys)) != len(scene.recipient_member_keys) or any(
            key not in operational_members for key in scene.recipient_member_keys
        ):
            raise ValueError(
                "Los destinatarios deben referenciar perfiles declarados, sin duplicados."
            )
        if scene.urgency not in {"baja", "normal", "urgente"}:
            raise ValueError("La escena debe usar una urgencia vigente.")
        _points(scene.requested_points)
    if len(catalog.causes) != 3 or any(
        c.stage != "creado" or not c.recipient_member_keys for c in catalog.causes
    ):
        raise ValueError("Las tres causas directas del conjunto se abren en Creado.")
    if Counter(s.status for s in catalog.t01_scenes) != {"DRAFT": 2, "ISSUED": 2}:
        raise ValueError("El catálogo requiere dos borradores y dos solicitudes emitidas.")
    issued = [s for s in catalog.t01_scenes if s.status == "ISSUED"]
    if len({s.creator_account_key for s in issued}) != 2:
        raise ValueError("Las dos solicitudes emitidas deben pertenecer a creadores distintos.")
    for scene in catalog.t01_scenes:
        if (scene.status == "DRAFT" and scene.resulting_stage is not None) or (
            scene.status == "ISSUED"
            and (scene.resulting_stage != "justificando" or not scene.recipient_member_keys)
        ):
            raise ValueError(
                "Los borradores no abren causas; las emitidas llegan a Justificaciones."
            )
    if len(catalog.historical_movements) != 8:
        raise ValueError("El conjunto histórico v1 declara ocho atribuciones individuales.")
    resolution_to_expediente: dict[str, str] = {}
    expediente_to_resolution: dict[str, str] = {}
    for movement in catalog.historical_movements:
        if movement.member_key not in member_by_key:
            raise ValueError("El movimiento debe identificar un destinatario del catálogo.")
        _key(movement.resolution_key, "history.resolution.")
        _key(movement.legacy_expediente_key, "history.expediente.")
        _points(movement.points, nonzero=True)
        previous = resolution_to_expediente.setdefault(
            movement.resolution_key, movement.legacy_expediente_key
        )
        reverse = expediente_to_resolution.setdefault(
            movement.legacy_expediente_key, movement.resolution_key
        )
        if previous != movement.legacy_expediente_key or reverse != movement.resolution_key:
            raise ValueError("Cada respaldo resolutivo debe conservar su expediente legado.")
    if len(resolution_to_expediente) != 7:
        raise ValueError("Los antecedentes v1 declaran siete respaldos resolutivos.")
    # La extensión es opcional para importar y verificar el catálogo previo aprobado.
    # Cuando está presente, debe ser completa: no se aceptan cargas parciales.
    if catalog.advanced_causes and Counter(scene.stage for scene in catalog.advanced_causes) != {
        "revision_resolucion": 3,
        "espera_resolucion": 1,
        "pendiente_correos": 2,
        "emitido": 4,
    }:
        raise ValueError("Las escenas adicionales requieren la distribución autorizada 3/1/2/4.")
    stages = ("revision_resolucion", "espera_resolucion", "pendiente_correos", "emitido")
    for scene in catalog.advanced_causes:
        _key(scene.fixture_key, "advanced.")
        if not scene.recipient_member_keys or scene.source_reference != _ADVANCED_SOURCE:
            raise ValueError(
                "La historia sintética requiere participantes y procedencia explícitos."
            )
        times = (
            scene.opened_at,
            scene.justification_started_at,
            scene.reviewed_at,
            scene.signature_pending_at,
            scene.dispatch_pending_at,
            scene.emitted_at,
        )
        length = 3 + stages.index(scene.stage)
        if any(value is not None for value in times[length:]) or any(
            not isinstance(value, datetime) or value.utcoffset() is None for value in times[:length]
        ):
            raise ValueError(
                "Las fechas de la historia deben ser aware y coincidir con sus etapas."
            )
        ordered = times[:length]
        if any(left >= right for left, right in zip(ordered, ordered[1:], strict=False)) or (
            scene.updated_at.date() >= catalog.recorded_on
        ):
            raise ValueError(
                "La historia sintética debe ser cronológica y anterior al corte técnico."
            )
        _points(scene.requested_points, nonzero=True)
    emissions = [scene for scene in catalog.advanced_causes if scene.stage == "emitido"]
    if catalog.advanced_causes and [
        (scene.recipient_member_keys, scene.requested_points) for scene in emissions
    ] != [
        (("member.g62.01",), Decimal("2")),
        (("member.g62.02",), Decimal("-1")),
        (("member.g63.01",), Decimal("-2")),
        (("member.g63.02",), Decimal("1")),
    ]:
        raise ValueError("Los cuatro emitidos deben conservar su atribución Junior individual.")


def expected_balances(catalog: DemoCatalog) -> dict[str, Decimal]:
    """Suma sólo los antecedentes previstos, sin pedidos pendientes ni escrituras."""
    validate_catalog(catalog)
    balances = {member.fixture_key: Decimal("0.00") for member in catalog.members}
    for movement in catalog.historical_movements:
        balances[movement.member_key] += movement.points
    for scene in catalog.advanced_causes:
        if scene.stage == "emitido":
            balances[scene.recipient_member_keys[0]] += scene.requested_points
    return balances
