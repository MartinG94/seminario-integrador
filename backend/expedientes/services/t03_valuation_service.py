"""Servicio de aplicación para valorar descargos T03 con fundamento y antecedentes (S4-03)."""

from collections.abc import Sequence

from django.db import transaction
from django.db.models import Max

from expedientes.domain.ports import TribunalConditionPort
from expedientes.domain.t03_valuation import T03ValuationError, validate_valuation
from expedientes.models import (
    DescargoExpediente,
    EstadoExpedienteEnum,
    Expediente,
    TipoDescargoEnum,
    ValoracionT03,
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


def _default_condition_provider() -> TribunalConditionPort:
    from padron.adapters import DbTribunalConditionProvider

    return DbTribunalConditionProvider()


class T03ValuationService:
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
        except T03ValuationError as exc:
            raise T03ValuationValidationError(str(exc)) from exc

        last_version = (
            ValoracionT03.objects.filter(descargo=descargo).aggregate(last=Max("version"))["last"]
            or 0
        )
        provider = condition_provider or _default_condition_provider()
        socio = getattr(user, "socio", None)
        return ValoracionT03.objects.create(
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
