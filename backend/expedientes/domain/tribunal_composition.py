"""Reglas de dominio para integrar el Tribunal de Disciplina de una causa (S4-04).

Dominio puro sin dependencias de Django (Estatuto AVEIT 2026 y Reglamento Procesal 2026):
- Art. 92: tres titulares y tres suplentes, uno de cada por 4.º, 5.º y 6.º año;
  el suplente reemplaza automáticamente al titular y nadie puede ocupar otro cargo.
- Art. 95 Estatuto y Art. 24 RPD: el integrante involucrado en la causa (imputado o
  solicitante) se aparta de pleno derecho y lo reemplaza su suplente. Si se involucran
  el titular y el suplente de un mismo año (Caso A) o tres o más integrantes (Caso B),
  el Tribunal ordinario no puede intervenir y la causa requiere Tribunal ad hoc /
  intervención de Asamblea.
"""

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass
from enum import StrEnum

ACTIVE_SOCIAL_YEARS = (4, 5, 6)
AD_HOC_MIN_INVOLVED = 3


class Condition(StrEnum):
    TITULAR = "TITULAR"
    SUPLENTE = "SUPLENTE"


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
    separated: tuple[Member, ...]
    ad_hoc_reasons: tuple[str, ...]
    issues: tuple[str, ...]

    @property
    def requires_ad_hoc(self) -> bool:
        return bool(self.ad_hoc_reasons)


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
        if member.other_position:
            issues.append(
                f"{member.label} ocupa otro cargo ({member.other_position}), "
                "incompatible con el Tribunal (Art. 92)."
            )
        if not member.enabled:
            issues.append(f"{member.label} no tiene la cuenta habilitada.")
    return issues


def compose(members: Iterable[Member], *, involved_ids: set[int]) -> Composition:
    """Integra el cuerpo efectivo: apartamiento automático, suplencia y casos ad hoc."""
    members = list(members)
    titulares = {m.social_year: m for m in members if m.condition == Condition.TITULAR}
    suplentes = {m.social_year: m for m in members if m.condition == Condition.SUPLENTE}
    separated = tuple(m for m in members if m.socio_id in involved_ids)

    seats = []
    reasons = []
    for year in ACTIVE_SOCIAL_YEARS:
        titular, suplente = titulares.get(year), suplentes.get(year)
        titular_free = titular is not None and titular.socio_id not in involved_ids
        suplente_free = suplente is not None and suplente.socio_id not in involved_ids
        if titular_free:
            seats.append(Seat(year, titular))
        elif suplente_free:
            seats.append(Seat(year, suplente, replaces=titular))
        else:
            seats.append(Seat(year, None, replaces=titular))
        if titular and suplente and not titular_free and not suplente_free:
            reasons.append(
                f"El titular y el suplente del {year}.º año están involucrados en la causa "
                "(Art. 95 del Estatuto)."
            )
    if len(separated) >= AD_HOC_MIN_INVOLVED:
        reasons.append(
            f"{len(separated)} integrantes del Tribunal están involucrados en la causa "
            "(Art. 95 del Estatuto)."
        )

    return Composition(
        seats=tuple(seats),
        separated=separated,
        ad_hoc_reasons=tuple(reasons),
        issues=tuple(roster_issues(members)),
    )
