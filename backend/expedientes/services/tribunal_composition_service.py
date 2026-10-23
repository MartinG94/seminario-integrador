"""Servicio de aplicación para constituir el Tribunal de cada causa (S4-04).

Orquesta la nómina legada, los apartamientos declarados y las designaciones ad hoc
con el dominio puro `tribunal_composition`, y congela el cuerpo antes de resolver.
"""

from dataclasses import dataclass

from django.db import transaction

from expedientes.domain.tribunal_composition import (
    Composition,
    CompositionError,
    Condition,
    Member,
    SeparationCause,
    compose,
    validate_conflict_grounds,
    validate_designation,
)
from expedientes.models import (
    ApartamientoTribunal,
    CausaApartamientoEnum,
    ComposicionTribunal,
    CondicionIntegranteEnum,
    DesignacionAdHoc,
    EstadoExpedienteEnum,
    Expediente,
    IntegranteComposicion,
)
from expedientes.services.tribunal_roster import LegacyTribunalRosterAdapter, Roster, RosterEntry

# La composición se gestiona hasta que se adopta la resolución (CA4).
COMPOSABLE_STATES = (
    EstadoExpedienteEnum.CREADO,
    EstadoExpedienteEnum.JUSTIFICANDO,
    EstadoExpedienteEnum.REVISION_RESOLUCION,
    EstadoExpedienteEnum.ESPERA_RESOLUCION,
)


class TribunalCompositionError(Exception):
    """Error base de la constitución del Tribunal."""


class TribunalCompositionNotFound(TribunalCompositionError):
    pass


class TribunalCompositionStateError(TribunalCompositionError):
    def __init__(self, message: str, observaciones: list[str] | None = None) -> None:
        super().__init__(message)
        self.observaciones = observaciones or []


class TribunalCompositionValidationError(TribunalCompositionError):
    pass


class TribunalCompositionForbidden(TribunalCompositionError):
    pass


@dataclass(frozen=True)
class _LiveState:
    roster: Roster
    composition: Composition
    involved_ids: set[int]
    designees: dict[int, RosterEntry]
    conflicts: dict[int, ApartamientoTribunal]
    issues: list[str]

    def entry(self, socio_id: int) -> RosterEntry | None:
        for entry in self.roster.entries:
            if entry.socio.id == socio_id:
                return entry
        return self.designees.get(socio_id)


def _involved_ids(expediente: Expediente) -> set[int]:
    return {expediente.socio_id, *expediente.socios.values_list("pk", flat=True)}


def _live_state(expediente: Expediente) -> _LiveState:
    adapter = LegacyTribunalRosterAdapter()
    roster = adapter.load()
    involved_ids = _involved_ids(expediente)
    conflicts = {a.socio_id: a for a in expediente.apartamientos_tribunal.all()}

    designees: dict[int, RosterEntry] = {}
    replacements: dict[int, Member] = {}
    issues = list(roster.issues)
    for designacion in expediente.designaciones_ad_hoc.select_related("designado"):
        entry = adapter.entry_for(designacion.designado)
        if entry is None:
            issues.append(
                f"El designado N° {designacion.designado.legajo} ya no figura en el padrón vigente."
            )
            continue
        designees[entry.socio.id] = entry
        replacements[designacion.reemplaza_a_id] = entry.member

    composition = compose(
        roster.members,
        involved_ids=involved_ids,
        conflict_ids=set(conflicts),
        replacements=replacements,
    )
    issues.extend(composition.issues)
    return _LiveState(roster, composition, involved_ids, designees, conflicts, issues)


def _signature(entry: RosterEntry, condition: Condition) -> str:
    return IntegranteComposicion(
        nro_socio=entry.nro_socio,
        nombre_completo=entry.nombre,
        grupo=entry.grupo,
        condicion=condition,
    ).firma


def _separations(state: _LiveState) -> list[dict]:
    rows = []
    for entry in state.roster.entries:
        cause = state.composition.separations.get(entry.socio.id)
        if cause is None:
            continue
        declared = state.conflicts.get(entry.socio.id)
        rows.append(
            {
                "socio_id": entry.socio.id,
                "nro_socio": entry.nro_socio,
                "nombre": entry.nombre,
                "anio_social": entry.member.social_year,
                "condicion": str(entry.member.condition),
                "causa": str(cause),
                "causa_display": CausaApartamientoEnum(str(cause)).label,
                "fundamento": (
                    declared.fundamento
                    if declared and cause == SeparationCause.CONFLICT
                    else "Figura entre los socios involucrados del expediente."
                ),
            }
        )
    return rows


def _expediente_or_404(expediente_id: int, *, lock: bool = False) -> Expediente:
    queryset = Expediente.objects.select_for_update() if lock else Expediente.objects
    expediente = queryset.filter(pk=expediente_id).first()
    if expediente is None:
        raise TribunalCompositionNotFound("Expediente no encontrado.")
    return expediente


def _ensure_mutable(expediente: Expediente) -> None:
    if ComposicionTribunal.objects.filter(expediente=expediente).exists():
        raise TribunalCompositionStateError(
            "El cuerpo del Tribunal ya está constituido; su composición es inmutable."
        )
    if expediente.estado not in COMPOSABLE_STATES:
        raise TribunalCompositionStateError(
            f"El expediente está en '{expediente.get_estado_display()}' "
            "y ya no admite cambios en la composición del Tribunal."
        )


def _ensure_not_separated(state: _LiveState, user) -> None:
    socio = getattr(user, "socio", None)
    if socio is not None and socio.id in state.composition.separations:
        raise TribunalCompositionForbidden(
            "Estás apartado de esta causa y no podés intervenir en la integración del Tribunal."
        )


class TribunalCompositionService:
    @staticmethod
    def describe(expediente_id: int, user=None) -> dict:
        """Composición de la causa; con `user`, indica si integra la nómina o está apartado."""
        socio_id = getattr(getattr(user, "socio", None), "id", None)
        expediente = _expediente_or_404(expediente_id)
        composicion = (
            ComposicionTribunal.objects.filter(expediente=expediente)
            .prefetch_related("integrantes")
            .first()
        )
        if composicion is not None:
            return {
                "constituida": True,
                "constituida_at": composicion.created_at,
                "constituida_por_legajo": composicion.constituida_por_legajo,
                "es_ad_hoc": composicion.es_ad_hoc,
                "asientos": [
                    {
                        "anio_social": integrante.anio_social,
                        "socio_id": integrante.socio_id,
                        "nro_socio": integrante.nro_socio,
                        "nombre": integrante.nombre_completo,
                        "grupo": integrante.grupo,
                        "condicion": integrante.condicion,
                        "firma": integrante.firma,
                        "reemplaza_a": integrante.reemplaza_a,
                    }
                    for integrante in composicion.integrantes.all()
                ],
                "nomina": [],
                "apartamientos": composicion.apartamientos,
                "designaciones_ad_hoc": [],
                "pendientes_ad_hoc": [],
                "observaciones": [],
                "puede_constituirse": False,
                "usuario": {
                    "es_integrante": any(
                        i.socio_id == socio_id for i in composicion.integrantes.all()
                    ),
                    "esta_apartado": any(
                        a.get("socio_id") == socio_id for a in composicion.apartamientos
                    ),
                },
            }

        state = _live_state(expediente)
        seats = []
        for seat in state.composition.seats:
            entry = state.entry(seat.member.socio_id) if seat.member else None
            replaced = state.entry(seat.replaces.socio_id) if seat.replaces else None
            seats.append(
                {
                    "anio_social": seat.social_year,
                    "socio_id": entry.socio.id if entry else None,
                    "nro_socio": entry.nro_socio if entry else None,
                    "nombre": entry.nombre if entry else "",
                    "grupo": entry.grupo if entry else "",
                    "condicion": str(seat.member.condition) if seat.member else "",
                    "firma": _signature(entry, seat.member.condition) if entry else "",
                    "reemplaza_a": replaced.member.label if replaced else "",
                }
            )
        separated = state.composition.separations
        return {
            "constituida": False,
            "constituida_at": None,
            "constituida_por_legajo": "",
            "es_ad_hoc": state.composition.ad_hoc,
            "asientos": seats,
            "nomina": [
                {
                    "socio_id": entry.socio.id,
                    "nro_socio": entry.nro_socio,
                    "nombre": entry.nombre,
                    "grupo": entry.grupo,
                    "anio_social": entry.member.social_year,
                    "condicion": str(entry.member.condition),
                    "apartado": entry.socio.id in separated,
                }
                for entry in state.roster.entries
            ],
            "apartamientos": _separations(state),
            "designaciones_ad_hoc": [
                {
                    "reemplaza_a_id": designacion.reemplaza_a_id,
                    "designado_id": designacion.designado_id,
                    "designado": (
                        state.designees[designacion.designado_id].member.label
                        if designacion.designado_id in state.designees
                        else designacion.designado.legajo
                    ),
                    "anio_social": designacion.anio_social,
                    "acta_asamblea": designacion.acta_asamblea,
                    "created_at": designacion.created_at,
                }
                for designacion in expediente.designaciones_ad_hoc.all()
            ],
            "pendientes_ad_hoc": [
                {"socio_id": m.socio_id, "nombre": m.label, "anio_social": m.social_year}
                for m in state.composition.pending_replacements
            ],
            "observaciones": state.issues,
            "puede_constituirse": not state.issues and expediente.estado in COMPOSABLE_STATES,
            "usuario": {
                "es_integrante": any(e.socio.id == socio_id for e in state.roster.entries),
                "esta_apartado": socio_id in separated,
            },
        }

    @staticmethod
    @transaction.atomic
    def declare_conflict(*, expediente_id: int, user, fundamento: str) -> ApartamientoTribunal:
        """Apartamiento voluntario del propio integrante; no existe la recusación (Art. 93)."""
        expediente = _expediente_or_404(expediente_id, lock=True)
        _ensure_mutable(expediente)
        state = _live_state(expediente)
        socio = getattr(user, "socio", None)
        if socio is None or not any(e.socio.id == socio.id for e in state.roster.entries):
            raise TribunalCompositionValidationError(
                "Sólo un integrante de la nómina del Tribunal puede apartarse a sí mismo; "
                "no existe la recusación (Art. 93 del Estatuto)."
            )
        if socio.id in state.involved_ids:
            raise TribunalCompositionValidationError(
                "Ya estás apartado de la causa por estar involucrado en ella (Art. 95)."
            )
        if socio.id in state.conflicts:
            raise TribunalCompositionValidationError(
                "Ya registraste tu apartamiento en esta causa."
            )
        fundamento = fundamento.strip()
        try:
            validate_conflict_grounds(fundamento)
        except CompositionError as exc:
            raise TribunalCompositionValidationError(str(exc)) from exc
        return ApartamientoTribunal.objects.create(
            expediente=expediente,
            socio=socio,
            causa=CausaApartamientoEnum.CONFLICTO_INTERES,
            fundamento=fundamento,
            autor=user,
        )

    @staticmethod
    @transaction.atomic
    def designate_ad_hoc(
        *,
        expediente_id: int,
        user,
        reemplaza_a_id: int,
        designado_nro_socio: int,
        acta_asamblea: str,
    ) -> DesignacionAdHoc:
        """Registra el integrante ad hoc designado por Asamblea (Art. 95)."""
        expediente = _expediente_or_404(expediente_id, lock=True)
        _ensure_mutable(expediente)
        state = _live_state(expediente)
        _ensure_not_separated(state, user)

        replaced = next((e for e in state.roster.entries if e.socio.id == reemplaza_a_id), None)
        if replaced is None:
            raise TribunalCompositionValidationError(
                "El socio a reemplazar no integra la nómina del Tribunal."
            )
        designee = LegacyTribunalRosterAdapter().entry_for_nro_socio(designado_nro_socio)
        if designee is None:
            raise TribunalCompositionValidationError(
                "El socio designado no figura en el padrón institucional vigente "
                "o no tiene cuenta en el sistema."
            )
        try:
            validate_designation(
                composition=state.composition,
                replaced=replaced.member,
                designee=designee.member,
                roster=state.roster.members,
                involved_ids=state.involved_ids,
            )
        except CompositionError as exc:
            raise TribunalCompositionValidationError(str(exc)) from exc
        return DesignacionAdHoc.objects.create(
            expediente=expediente,
            reemplaza_a=replaced.socio,
            designado=designee.socio,
            anio_social=replaced.member.social_year,
            acta_asamblea=acta_asamblea.strip(),
            autor=user,
        )

    @staticmethod
    @transaction.atomic
    def constitute(*, expediente_id: int, user) -> ComposicionTribunal:
        """Congela el cuerpo efectivo y las causas de apartamiento (CA4)."""
        expediente = _expediente_or_404(expediente_id, lock=True)
        _ensure_mutable(expediente)
        state = _live_state(expediente)
        _ensure_not_separated(state, user)
        if state.issues:
            raise TribunalCompositionStateError(
                "No se puede constituir el cuerpo del Tribunal: " + state.issues[0],
                observaciones=state.issues,
            )

        socio = getattr(user, "socio", None)
        composicion = ComposicionTribunal.objects.create(
            expediente=expediente,
            es_ad_hoc=state.composition.ad_hoc,
            apartamientos=_separations(state),
            constituida_por=user,
            constituida_por_legajo=socio.legajo if socio else user.get_username(),
        )
        for seat in state.composition.seats:
            entry = state.entry(seat.member.socio_id)
            replaced = state.entry(seat.replaces.socio_id) if seat.replaces else None
            IntegranteComposicion.objects.create(
                composicion=composicion,
                anio_social=seat.social_year,
                socio=entry.socio,
                condicion=CondicionIntegranteEnum(str(seat.member.condition)),
                nro_socio=entry.nro_socio,
                nombre_completo=entry.nombre,
                grupo=entry.grupo,
                reemplaza_a=replaced.member.label if replaced else "",
            )
        return composicion
