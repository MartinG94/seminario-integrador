"""Servicio de aplicación para valorar descargos T03 con fundamento y antecedentes (S4-03)."""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime

from django.db import transaction
from django.db.models import Max

from expedientes.domain.ports import TribunalConditionPort
from expedientes.domain.t03_valuation import (
    T03ValuationError,
    normalize_case_number,
    validate_antecedent_ids,
    validate_valuation,
)
from expedientes.models import (
    CambioEstadoExpediente,
    DescargoExpediente,
    EstadoExpedienteEnum,
    Expediente,
    SolicitudT01,
    TipoDescargoEnum,
    ValoracionT03,
    ValoracionT03Antecedente,
)
from expedientes.services.causal_resolution_service import _descargo_snapshot

VALUABLE_STATES = (
    EstadoExpedienteEnum.REVISION_RESOLUCION,
    EstadoExpedienteEnum.ESPERA_RESOLUCION,
)


class T03ValuationServiceError(Exception):
    """Error base del servicio de valoración T03."""


class T03ValuationNotFound(T03ValuationServiceError):
    pass


class T03ValuationStateError(T03ValuationServiceError):
    pass


class T03ValuationValidationError(T03ValuationServiceError):
    pass


class T03ValuationForbidden(T03ValuationServiceError):
    pass


INTERESTED_PARTY_MESSAGE = (
    "Participación restringida: sos parte interesada en este expediente (imputado o "
    "solicitante) y no podés valorar el descargo, conforme al Art. 95 del Estatuto y "
    "al Art. 24 del Reglamento Procesal."
)


def interested_socio_ids(expediente: Expediente) -> set[int]:
    """Partes interesadas: imputados y solicitante del T01 (mismo criterio que el PR #63)."""
    ids = {expediente.socio_id, *expediente.socios.values_list("pk", flat=True)}
    solicitante_id = (
        SolicitudT01.objects.filter(expediente=expediente)
        .values_list("solicitante_id", flat=True)
        .first()
    )
    if solicitante_id is not None:
        ids.add(solicitante_id)
    return ids


def is_interested_party(expediente: Expediente, user) -> bool:
    socio = getattr(user, "socio", None)
    return socio is not None and socio.id in interested_socio_ids(expediente)


@dataclass(frozen=True)
class AntecedentCard:
    """Ficha mínima de un antecedente: nunca texto, causal ni evidencia del descargo (RF-20)."""

    id: int
    numero: str
    fecha_emision: datetime
    motivo: str
    reglamento_invocado: str


def _emission_date(expediente: Expediente) -> datetime:
    """Último cambio de estado hacia `emitido`; si no hay, la última actualización (D6)."""
    last_emission = (
        CambioEstadoExpediente.objects.filter(
            expediente=expediente, estado_nuevo=EstadoExpedienteEnum.EMITIDO
        )
        .order_by("-fecha_hora", "-id")
        .values_list("fecha_hora", flat=True)
        .first()
    )
    return last_emission or expediente.updated_at


def _emitted_antecedents(antecedent_ids: list[int]) -> list[Expediente]:
    """Revalida que cada antecedente exista y esté emitido (RF-13); conserva el orden."""
    found = Expediente.objects.filter(
        pk__in=antecedent_ids, estado=EstadoExpedienteEnum.EMITIDO
    ).in_bulk()
    if len(found) != len(antecedent_ids):
        raise T03ValuationValidationError(
            "Uno o más antecedentes no corresponden a un expediente emitido."
        )
    return [found[pk] for pk in antecedent_ids]


def _default_condition_provider() -> TribunalConditionPort:
    from padron.adapters import DbTribunalConditionProvider

    return DbTribunalConditionProvider()


class T03ValuationService:
    @staticmethod
    def lookup_antecedent(numero: str) -> AntecedentCard:
        from expedientes.serializers import _obtener_reglamento_asociado

        try:
            normalized = normalize_case_number(numero)
        except T03ValuationError as exc:
            raise T03ValuationValidationError(str(exc)) from exc
        expediente = (
            Expediente.objects.select_related("solicitud_t01")
            .filter(numero=normalized, estado=EstadoExpedienteEnum.EMITIDO)
            .first()
        )
        if expediente is None:
            raise T03ValuationNotFound("No hay un expediente emitido con ese número.")
        return AntecedentCard(
            id=expediente.id,
            numero=expediente.numero,
            fecha_emision=_emission_date(expediente),
            motivo=expediente.motivo,
            reglamento_invocado=_obtener_reglamento_asociado(expediente),
        )

    @staticmethod
    def get_descargo(expediente_id: int, descargo_id: int) -> DescargoExpediente:
        descargo = (
            DescargoExpediente.objects.select_related("socio")
            .filter(pk=descargo_id, expediente_id=expediente_id)
            .first()
        )
        if descargo is None:
            raise T03ValuationNotFound("Descargo no encontrado en este expediente.")
        return descargo

    @staticmethod
    @transaction.atomic
    def register(
        *,
        expediente_id: int,
        descargo_id: int,
        resultado: str,
        fundamento: str,
        antecedente_ids: Sequence[int] | None,
        user,
        condition_provider: TribunalConditionPort | None = None,
    ) -> ValoracionT03:
        expediente = Expediente.objects.select_for_update().filter(pk=expediente_id).first()
        if expediente is None:
            raise T03ValuationNotFound("Expediente no encontrado.")
        if is_interested_party(expediente, user):
            raise T03ValuationForbidden(INTERESTED_PARTY_MESSAGE)
        if expediente.estado not in VALUABLE_STATES:
            raise T03ValuationStateError(
                f"El expediente está en '{expediente.get_estado_display()}' "
                "y no admite valoraciones del T03."
            )

        descargo = T03ValuationService.get_descargo(expediente_id, descargo_id)
        if descargo.tipo != TipoDescargoEnum.T03_EXTRAORDINARIO:
            raise T03ValuationValidationError(
                "Sólo se valoran acá los descargos extraordinarios del Formulario T03."
            )
        if not descargo.es_vigente:
            raise T03ValuationValidationError("El descargo T03 no está vigente.")

        try:
            result = validate_valuation(resultado, fundamento)
            ids = validate_antecedent_ids(list(antecedente_ids or []), expediente.id)
        except T03ValuationError as exc:
            raise T03ValuationValidationError(str(exc)) from exc
        antecedents = _emitted_antecedents(ids)

        last_version = (
            ValoracionT03.objects.filter(descargo=descargo).aggregate(last=Max("version"))["last"]
            or 0
        )
        provider = condition_provider or _default_condition_provider()
        socio = getattr(user, "socio", None)
        valuation = ValoracionT03.objects.create(
            expediente=expediente,
            descargo=descargo,
            version=last_version + 1,
            resultado=result,
            fundamento=fundamento.strip(),
            descargo_snapshot=_descargo_snapshot(descargo),
            autor=user,
            autor_legajo=socio.legajo if socio else user.get_username(),
            autor_rol=socio.role if socio else "",
            autor_condicion=provider.condition_for_user(user.id),
        )
        for antecedent in antecedents:
            ValoracionT03Antecedente.objects.create(
                valoracion=valuation,
                expediente_antecedente=antecedent,
                numero_antecedente=antecedent.numero,
            )
        return valuation
