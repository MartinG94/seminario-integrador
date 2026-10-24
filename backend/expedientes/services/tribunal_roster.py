"""Nómina del Tribunal de Disciplina desde el padrón legado `socio_lista` (S4-04).

El legado no tiene tabla de autoridades: el cargo reside en `socio_lista.idTipoSocio`
(10 = Titular TD, 11 = Suplente TD) y el año social en `anoSocial`. La ficha se
vincula con la cuenta local por `socio_lista.user_id`.
"""

from dataclasses import dataclass, field
from typing import Final

from expedientes.domain.tribunal_composition import Condition, Member
from padron.models import Socio as LegacySocio
from padron.models import SocioEstadoHistorial
from socios.models import Role, Socio

CARGO_TITULAR_TD: Final = 10
CARGO_SUPLENTE_TD: Final = 11

# Roles RBAC que revelan un cargo en otro órgano (Art. 92) o funciones técnicas
# sin facultad de juzgar (Notas del PO, 07/10/2026).
INCOMPATIBLE_ROLES: Final[dict[str, str]] = {
    Role.CD: "Comisión Directiva",
    Role.FISCALIZADORA: "Autoridad de Subcomisión",
    Role.ADMIN: "Administrador de Cómputos",
}

ROSTER_CONDITIONS: Final[dict[int, Condition]] = {
    CARGO_TITULAR_TD: Condition.TITULAR,
    CARGO_SUPLENTE_TD: Condition.SUPLENTE,
}


@dataclass(frozen=True)
class RosterEntry:
    member: Member
    socio: Socio
    nro_socio: int
    nombre: str
    grupo: str


@dataclass(frozen=True)
class Roster:
    entries: list[RosterEntry]
    issues: list[str] = field(default_factory=list)

    @property
    def members(self) -> list[Member]:
        return [entry.member for entry in self.entries]


def _grupos(nro_socios: list[int]) -> dict[int, str]:
    """Último grupo (Gxx) registrado en el historial de estados de cada socio."""
    grupos: dict[int, str] = {}
    historial = SocioEstadoHistorial.objects.filter(socio_id__in=nro_socios).order_by(
        "-fechaHora", "-idEstadoHistorial"
    )
    for fila in historial.values("socio_id", "idGrupo"):
        grupos.setdefault(fila["socio_id"], f"G{fila['idGrupo']}")
    return grupos


def _entry(legacy: LegacySocio, socio: Socio, condition: Condition, grupo: str) -> RosterEntry:
    nombre = f"{legacy.nombre} {legacy.apellido}".strip()
    return RosterEntry(
        member=Member(
            socio_id=socio.id,
            social_year=legacy.anoSocial,
            condition=condition,
            label=f"{nombre} (N° {legacy.nroSocio})",
            other_position=INCOMPATIBLE_ROLES.get(socio.role),
            enabled=socio.is_enabled,
        ),
        socio=socio,
        nro_socio=legacy.nroSocio,
        nombre=nombre,
        grupo=grupo,
    )


class LegacyTribunalRosterAdapter:
    """Lectura de sólo consulta de la nómina vigente del Tribunal."""

    def load(self) -> Roster:
        legacy_rows = list(
            LegacySocio.objects.filter(
                idTipoSocio__in=ROSTER_CONDITIONS, fechaBaja__isnull=True
            ).order_by("anoSocial", "idTipoSocio", "nroSocio")
        )
        user_ids = [row.user_id for row in legacy_rows if row.user_id]
        socios = {s.user_id: s for s in Socio.objects.filter(user_id__in=user_ids)}
        grupos = _grupos([row.nroSocio for row in legacy_rows])

        entries, issues = [], []
        for row in legacy_rows:
            socio = socios.get(row.user_id)
            if socio is None:
                issues.append(
                    f"El integrante N° {row.nroSocio} del padrón no tiene cuenta "
                    "habilitada en el sistema."
                )
                continue
            entries.append(
                _entry(row, socio, ROSTER_CONDITIONS[row.idTipoSocio], grupos.get(row.nroSocio, ""))
            )
        return Roster(entries=entries, issues=issues)
