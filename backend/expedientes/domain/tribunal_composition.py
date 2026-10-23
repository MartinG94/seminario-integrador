"""Reglas de dominio para constituir el Tribunal de Disciplina de una causa (S4-04).

Dominio puro sin dependencias de Django (Estatuto AVEIT 2026):
- Art. 92: tres titulares y tres suplentes, uno de cada por 4.º, 5.º y 6.º año;
  el suplente reemplaza al titular y nadie puede ocupar otro cargo.
- Art. 93: sin recusación; la única causa voluntaria es el conflicto que declara
  el propio integrante.
- Art. 95: el involucrado se aparta; dos involucrados del mismo año o tres o más
  integran un Tribunal ad hoc designado por Asamblea con socios de los mismos años.
"""

from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from enum import StrEnum

ACTIVE_SOCIAL_YEARS = (4, 5, 6)
MIN_GROUNDS_LENGTH = 20


class Condition(StrEnum):
    TITULAR = "TITULAR"
    SUPLENTE = "SUPLENTE"
    AD_HOC = "AD_HOC"


class SeparationCause(StrEnum):
    INVOLVED = "INVOLUCRADO"
    CONFLICT = "CONFLICTO_INTERES"


class CompositionError(ValueError):
    """La operación no respeta la integración estatutaria del Tribunal."""


@dataclass(frozen=True)
class Member:
    socio_id: int
    social_year: int
    condition: Condition
    label: str = ""
    other_position: str | None = None
    enabled: bool = True


@dataclass(frozen=True)
class Seat:
    social_year: int
    member: Member | None
    replaces: Member | None = None


@dataclass(frozen=True)
class Composition:
    seats: tuple[Seat, ...]
    separations: dict[int, SeparationCause]
    ad_hoc: bool
    pending_replacements: tuple[Member, ...]
    designees: tuple[Member, ...]
    issues: tuple[str, ...]

    @property
    def can_be_constituted(self) -> bool:
        return not self.issues


def _incompatibility_issues(member: Member) -> list[str]:
    issues = []
    if member.other_position:
        issues.append(
            f"{member.label} ocupa otro cargo ({member.other_position}), "
            "incompatible con el Tribunal (Art. 92)."
        )
    if not member.enabled:
        issues.append(f"{member.label} no tiene la cuenta habilitada.")
    return issues


def roster_issues(members: Iterable[Member]) -> list[str]:
    """Observaciones de la nómina: un titular y un suplente Activos por año (CA1/CA5)."""
    members = list(members)
    issues = []
    counts = Counter((m.social_year, m.condition) for m in members)
    for year in ACTIVE_SOCIAL_YEARS:
        for condition, name in ((Condition.TITULAR, "titular"), (Condition.SUPLENTE, "suplente")):
            count = counts[(year, condition)]
            if count == 0:
                issues.append(f"Falta el {name} del {year}.º año.")
            elif count > 1:
                issues.append(f"Hay más de un {name} del {year}.º año.")
    for member in members:
        if member.social_year not in ACTIVE_SOCIAL_YEARS:
            issues.append(f"{member.label} no es socio Activo (4.º a 6.º año).")
        issues.extend(_incompatibility_issues(member))
    return issues


def _by_year(members: Iterable[Member], condition: Condition) -> dict[int, Member]:
    return {m.social_year: m for m in members if m.condition == condition}


def compose(
    members: Iterable[Member],
    *,
    involved_ids: set[int],
    conflict_ids: set[int],
    replacements: Mapping[int, Member],
) -> Composition:
    """Integra el cuerpo efectivo de la causa: apartamiento, suplencia y caso ad hoc.

    `replacements` asocia el socio apartado con el integrante ad hoc designado por
    Asamblea; sólo se considera cuando el caso es ad hoc.
    """
    members = list(members)
    roster_ids = {m.socio_id for m in members}
    separations = {socio_id: SeparationCause.CONFLICT for socio_id in conflict_ids & roster_ids} | {
        socio_id: SeparationCause.INVOLVED for socio_id in involved_ids & roster_ids
    }

    titulares = _by_year(members, Condition.TITULAR)
    suplentes = _by_year(members, Condition.SUPLENTE)
    involved = [m for m in members if m.socio_id in involved_ids]
    involved_per_year = Counter(m.social_year for m in involved)
    # Año con integrantes pero todos apartados: imposibilidad de integrar (Art. 92).
    vacant_years = set()
    for year in ACTIVE_SOCIAL_YEARS:
        candidates = [c for c in (titulares.get(year), suplentes.get(year)) if c is not None]
        if candidates and all(c.socio_id in separations for c in candidates):
            vacant_years.add(year)
    is_ad_hoc = (
        len(involved) >= 3
        or any(count >= 2 for count in involved_per_year.values())
        or bool(vacant_years)
    )

    required = [
        m
        for m in members
        if m.socio_id in separations
        and (separations[m.socio_id] == SeparationCause.INVOLVED or m.social_year in vacant_years)
    ]
    active_replacements = dict(replacements) if is_ad_hoc else {}

    seats = []
    for year in ACTIVE_SOCIAL_YEARS:
        seat = Seat(social_year=year, member=None)
        for candidate in (titulares.get(year), suplentes.get(year)):
            if candidate is None:
                continue
            if candidate.socio_id not in separations:
                titular = titulares.get(year)
                seat = Seat(year, candidate, replaces=None if candidate is titular else titular)
                break
            if candidate.socio_id in active_replacements:
                seat = Seat(year, active_replacements[candidate.socio_id], replaces=candidate)
                break
        seats.append(seat)

    pending = (
        tuple(m for m in required if m.socio_id not in active_replacements) if is_ad_hoc else ()
    )
    issues = roster_issues(members)
    issues.extend(
        f"Falta designar por Asamblea el reemplazo ad hoc de {m.label} ({m.social_year}.º año)."
        for m in pending
    )
    issues.extend(
        f"No hay integrante habilitado para el {seat.social_year}.º año."
        for seat in seats
        if seat.member is None and not any(m.social_year == seat.social_year for m in pending)
    )
    return Composition(
        seats=tuple(seats),
        separations=separations,
        ad_hoc=is_ad_hoc,
        pending_replacements=pending,
        designees=tuple(active_replacements.values()),
        issues=tuple(issues),
    )


def validate_conflict_grounds(grounds: str) -> None:
    if len(grounds.strip()) < MIN_GROUNDS_LENGTH:
        raise CompositionError(
            f"Indicá un fundamento de al menos {MIN_GROUNDS_LENGTH} caracteres "
            "para apartarte por conflicto de interés."
        )


def validate_designation(
    *,
    composition: Composition,
    replaced: Member,
    designee: Member,
    roster: Iterable[Member],
    involved_ids: set[int],
) -> None:
    """Valida la designación ad hoc de Asamblea (Art. 95) y la incompatibilidad (CA5)."""
    if not composition.ad_hoc:
        raise CompositionError(
            "Sólo se designan integrantes ad hoc cuando lo exige el Art. 95 del Estatuto."
        )
    if replaced.socio_id not in {m.socio_id for m in composition.pending_replacements}:
        raise CompositionError(f"{replaced.label} no requiere reemplazo ad hoc en esta causa.")
    if designee.social_year != replaced.social_year:
        raise CompositionError(
            "El designado debe pertenecer al mismo año social "
            f"({replaced.social_year}.º) que el integrante reemplazado."
        )
    if designee.socio_id in involved_ids:
        raise CompositionError(f"{designee.label} está involucrado en la causa.")
    current = {m.socio_id for m in roster} | {m.socio_id for m in composition.designees}
    if designee.socio_id in current:
        raise CompositionError(f"{designee.label} ya integra el Tribunal en esta causa.")
    issues = _incompatibility_issues(designee)
    if issues:
        raise CompositionError(issues[0])
