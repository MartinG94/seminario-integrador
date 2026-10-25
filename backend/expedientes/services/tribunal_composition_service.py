"""Servicio de aplicación del Tribunal que interviene en cada causa (S4-04).

Sin trámites manuales (Notas del PO sobre PR #63):
- Inhibición: ningún socio involucrado (imputado o solicitante) interviene en el
  juzgamiento (Art. 95 Estatuto y Art. 24 RPD).
- Suplencia automática: la composición se calcula en tiempo real y se estampa de forma
  inmutable al adoptar la resolución.
- Casos A y B del Art. 95: se inmoviliza la resolución ordinaria, se avisa a Comisión
  Directiva por Outbox y la causa concluye con la Resolución por Asamblea Extraordinaria.
"""

from dataclasses import dataclass

from django.conf import settings

from expedientes.domain.tribunal_composition import Composition, Condition, compose
from expedientes.models import (
    ComposicionTribunal,
    CondicionIntegranteEnum,
    EstadoExpedienteEnum,
    Expediente,
    IntegranteComposicion,
    ResolucionAsamblea,
    SolicitudT01,
)
from expedientes.services.tribunal_roster import LegacyTribunalRosterAdapter, Roster, RosterEntry
from notifications.models import EmailOutbox
from notifications.services import EmailDispatcherService
from socios.models import Role

# Etapas en las que la causa ya puede resolverse por Asamblea: vencido el período de
# justificaciones, para no cercenar el derecho de defensa.
ASSEMBLY_STATES = (
    EstadoExpedienteEnum.REVISION_RESOLUCION,
    EstadoExpedienteEnum.ESPERA_RESOLUCION,
)
ASSEMBLY_ROLES = (Role.CD, Role.ADMIN)
AD_HOC_NOTICE_KEY = "td-ad-hoc-expediente-{expediente_id}"

INVOLVED_MESSAGE = (
    "Participación restringida: sos parte interesada en este expediente (imputado o "
    "solicitante). Tu lugar lo ocupa automáticamente tu suplente conforme al Art. 95 del "
    "Estatuto y Art. 24 del Reglamento Procesal."
)
AD_HOC_MESSAGE = (
    "La causa requiere Tribunal Ad-Hoc / intervención de Asamblea (Art. 95 del Estatuto): "
    "no puede resolverla el Tribunal ordinario."
)


class TribunalCompositionError(Exception):
    """Error base del Tribunal de la causa."""


class TribunalCompositionNotFound(TribunalCompositionError):
    pass


class TribunalCompositionStateError(TribunalCompositionError):
    def __init__(self, message: str, observaciones: list[str] | None = None) -> None:
        super().__init__(message)
        self.observaciones = observaciones or []


@dataclass(frozen=True)
class _LiveState:
    roster: Roster
    composition: Composition

    @property
    def issues(self) -> list[str]:
        return [*self.roster.issues, *self.composition.issues]

    def entry(self, socio_id: int) -> RosterEntry:
        return next(e for e in self.roster.entries if e.socio.id == socio_id)


def involved_socio_ids(expediente: Expediente) -> set[int]:
    """Partes interesadas: imputados y quien solicitó la apertura o la sanción (Art. 24 RPD)."""
    ids = {expediente.socio_id, *expediente.socios.values_list("pk", flat=True)}
    solicitante_id = (
        SolicitudT01.objects.filter(expediente=expediente)
        .values_list("solicitante_id", flat=True)
        .first()
    )
    if solicitante_id is not None:
        ids.add(solicitante_id)
    return ids


def is_involved(expediente: Expediente, user) -> bool:
    socio = getattr(user, "socio", None)
    return socio is not None and socio.id in involved_socio_ids(expediente)


def _live_state(expediente: Expediente) -> _LiveState:
    roster = LegacyTribunalRosterAdapter().load()
    composition = compose(roster.members, involved_ids=involved_socio_ids(expediente))
    return _LiveState(roster, composition)


def _signature(entry: RosterEntry, condition: Condition) -> str:
    return IntegranteComposicion(
        nro_socio=entry.nro_socio,
        nombre_completo=entry.nombre,
        grupo=entry.grupo,
        condicion=condition,
    ).firma


def _separated(state: _LiveState) -> list[dict]:
    rows = []
    for member in state.composition.separated:
        entry = state.entry(member.socio_id)
        rows.append(
            {
                "socio_id": entry.socio.id,
                "nro_socio": entry.nro_socio,
                "nombre": entry.nombre,
                "anio_social": member.social_year,
                "condicion": str(member.condition),
            }
        )
    return rows


def _expediente_or_404(expediente_id: int) -> Expediente:
    expediente = Expediente.objects.filter(pk=expediente_id).first()
    if expediente is None:
        raise TribunalCompositionNotFound("Expediente no encontrado.")
    return expediente


def _assembly_payload(resolucion: ResolucionAsamblea | None) -> dict | None:
    if resolucion is None:
        return None
    return {
        "acta_nombre": resolucion.acta_nombre,
        "registrada_at": resolucion.created_at,
        "registrada_por_legajo": resolucion.registrada_por_legajo,
    }


class TribunalCompositionService:
    @staticmethod
    def describe(expediente_id: int, user=None) -> dict:
        """Responsables de la causa: estampados si ya se resolvió, o calculados en vivo."""
        expediente = _expediente_or_404(expediente_id)
        involved = is_involved(expediente, user)
        resolucion = ResolucionAsamblea.objects.filter(expediente=expediente).first()
        composicion = (
            ComposicionTribunal.objects.filter(expediente=expediente)
            .prefetch_related("integrantes")
            .first()
        )
        if composicion is not None:
            return {
                "estampada": True,
                "estampada_at": composicion.created_at,
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
                "apartados": composicion.apartados,
                "requiere_ad_hoc": False,
                "motivos_ad_hoc": [],
                "observaciones": [],
                "resolucion_asamblea": None,
                "puede_registrar_asamblea": False,
                "usuario": {"esta_involucrado": involved},
            }

        state = _live_state(expediente)
        seats = []
        for seat in state.composition.seats:
            entry = state.entry(seat.member.socio_id) if seat.member else None
            seats.append(
                {
                    "anio_social": seat.social_year,
                    "socio_id": entry.socio.id if entry else None,
                    "nro_socio": entry.nro_socio if entry else None,
                    "nombre": entry.nombre if entry else "",
                    "grupo": entry.grupo if entry else "",
                    "condicion": str(seat.member.condition) if seat.member else "",
                    "firma": _signature(entry, seat.member.condition) if entry else "",
                    "reemplaza_a": seat.replaces.label if seat.replaces else "",
                }
            )
        role = getattr(getattr(user, "socio", None), "role", None)
        return {
            "estampada": False,
            "estampada_at": None,
            "asientos": seats,
            "apartados": _separated(state),
            "requiere_ad_hoc": state.composition.requires_ad_hoc,
            "motivos_ad_hoc": list(state.composition.ad_hoc_reasons),
            "observaciones": state.issues,
            "resolucion_asamblea": _assembly_payload(resolucion),
            "puede_registrar_asamblea": (
                state.composition.requires_ad_hoc
                and resolucion is None
                and expediente.estado in ASSEMBLY_STATES
                and role in ASSEMBLY_ROLES
                and not involved
            ),
            "usuario": {"esta_involucrado": involved},
        }

    @staticmethod
    def requires_ad_hoc(expediente: Expediente) -> bool:
        return _live_state(expediente).composition.requires_ad_hoc

    @staticmethod
    def stamp_for_resolution(expediente: Expediente) -> ComposicionTribunal | None:
        """Congela los responsables al adoptar la resolución ordinaria (CA4).

        Se invoca dentro de la transacción del pase a `Pendiente de firma y envío`. Si la
        causa la resolvió la Asamblea, no hay cuerpo ordinario que estampar.
        """
        if ResolucionAsamblea.objects.filter(expediente=expediente).exists():
            return None
        existing = ComposicionTribunal.objects.filter(expediente=expediente).first()
        if existing is not None:
            return existing
        state = _live_state(expediente)
        if state.composition.requires_ad_hoc:
            raise TribunalCompositionStateError(
                AD_HOC_MESSAGE, observaciones=list(state.composition.ad_hoc_reasons)
            )
        if state.issues:
            raise TribunalCompositionStateError(
                "No se puede resolver: el Tribunal no está integrado conforme al Estatuto. "
                + state.issues[0],
                observaciones=state.issues,
            )

        composicion = ComposicionTribunal.objects.create(
            expediente=expediente, apartados=_separated(state)
        )
        for seat in state.composition.seats:
            entry = state.entry(seat.member.socio_id)
            IntegranteComposicion.objects.create(
                composicion=composicion,
                anio_social=seat.social_year,
                socio=entry.socio,
                condicion=CondicionIntegranteEnum(str(seat.member.condition)),
                nro_socio=entry.nro_socio,
                nombre_completo=entry.nombre,
                grupo=entry.grupo,
                reemplaza_a=seat.replaces.label if seat.replaces else "",
            )
        return composicion

    @staticmethod
    def notify_if_ad_hoc(expediente: Expediente) -> EmailOutbox | None:
        """Encola, una sola vez, el aviso a Comisión Directiva para convocar a Asamblea."""
        state = _live_state(expediente)
        if not state.composition.requires_ad_hoc:
            return None
        apartados = "\n".join(
            f"- {state.entry(m.socio_id).member.label}, {m.social_year}.º año "
            f"({'Titular' if m.condition == Condition.TITULAR else 'Suplente'})"
            for m in state.composition.separated
        )
        motivos = "\n".join(f"- {motivo}" for motivo in state.composition.ad_hoc_reasons)
        outbox, _ = EmailDispatcherService.create_or_get_outbox(
            {
                "to": [settings.COMISION_DIRECTIVA_EMAIL],
                "subject": (
                    f"Expediente {expediente.numero}: requiere Tribunal Ad-Hoc / "
                    "convocatoria a Asamblea (Art. 95)"
                ),
                "body_text": (
                    "Estimada Comisión Directiva:\n\n"
                    f"El expediente {expediente.numero} no puede ser resuelto por el Tribunal "
                    "de Disciplina ordinario porque:\n"
                    f"{motivos}\n\n"
                    f"Integrantes del Tribunal involucrados en la causa:\n{apartados}\n\n"
                    "Conforme al Art. 95 del Estatuto, corresponde convocar de inmediato a "
                    "Asamblea General. Los imputados conservan su plazo para presentar los "
                    "formularios T02/T03. Concluida la Asamblea, registrá en el sistema la "
                    "Resolución por Asamblea Extraordinaria con el PDF del acta.\n\n"
                    "Sistema de Gestión Disciplinaria A.V.E.I.T."
                ),
                "idempotency_key": AD_HOC_NOTICE_KEY.format(expediente_id=expediente.pk),
                "metadata": {
                    "tipo": "AVISO_TRIBUNAL_AD_HOC",
                    "expediente_id": expediente.pk,
                    "expediente_numero": expediente.numero,
                },
            }
        )
        return outbox
