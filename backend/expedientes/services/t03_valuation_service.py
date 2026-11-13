"""Servicio de aplicación para valorar descargos T03 con fundamento y antecedentes (S4-03)."""

import logging
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime

from django.db import DatabaseError, transaction
from django.db.models import F, Max, OuterRef, Q, Subquery
from django.db.models.functions import Coalesce

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

logger = logging.getLogger(__name__)

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


class T03ValuationUnavailable(T03ValuationServiceError):
    pass


INTERESTED_PARTY_MESSAGE = (
    "Participación restringida: sos parte interesada en este expediente (imputado o "
    "solicitante) y no podés valorar el descargo, conforme al Art. 95 del Estatuto y "
    "al Art. 24 del Reglamento Procesal."
)


IMPUTADO_RESERVE_MESSAGE = (
    "Acceso restringido: sos imputado en este expediente y no podés consultar la "
    "valoración del Tribunal."
)


PADRON_UNAVAILABLE_MESSAGE = (
    "No se pudo confirmar tu condición de Miembro en el padrón, por lo que la valoración "
    "no se registró. Intentá nuevamente en unos minutos."
)


def imputado_socio_ids(expediente: Expediente) -> set[int]:
    """Imputados de la causa: socio principal y coimputados (RF-24)."""
    return {expediente.socio_id, *(socio.pk for socio in expediente.socios.all())}


def is_imputado(expediente: Expediente, user) -> bool:
    socio = getattr(user, "socio", None)
    return socio is not None and socio.id in imputado_socio_ids(expediente)


def interested_socio_ids(expediente: Expediente) -> set[int]:
    """Partes interesadas: imputados y solicitante del T01 (mismo criterio que el PR #63)."""
    ids = imputado_socio_ids(expediente)
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
class AntecedentLookup:
    """Expediente emitido encontrado por número y su fecha de emisión (RF-16, D6).

    La presentación arma la ficha con una lista blanca de campos (RF-20).
    """

    expediente: Expediente
    fecha_emision: datetime


def _emission_date(expediente: Expediente) -> datetime:
    """Último cambio de estado hacia `emitido`; si no hay, la última actualización (D6)."""
    fecha_calc = getattr(expediente, "fecha_emision_calc", None)
    if fecha_calc is not None:
        return fecha_calc
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
    def lookup_antecedent(numero: str) -> AntecedentLookup:
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
        return AntecedentLookup(expediente=expediente, fecha_emision=_emission_date(expediente))

    @staticmethod
    def list_emitted_antecedents(
        *,
        search: str = "",
        tipo: str = "TODOS",
        exclude_id: int | None = None,
    ) -> list[AntecedentLookup]:
        subquery_emision = Subquery(
            CambioEstadoExpediente.objects.filter(
                expediente=OuterRef("pk"),
                estado_nuevo=EstadoExpedienteEnum.EMITIDO,
            )
            .order_by("-fecha_hora", "-id")
            .values("fecha_hora")[:1]
        )

        qs = (
            Expediente.objects.select_related("solicitud_t01", "socio")
            .filter(estado=EstadoExpedienteEnum.EMITIDO)
            .annotate(fecha_emision_calc=Coalesce(subquery_emision, F("updated_at")))
        )
        if exclude_id is not None:
            qs = qs.exclude(pk=exclude_id)

        if tipo == "SANCTION":
            qs = qs.filter(Q(solicitud_t01__tipo_accion="SANCTION") | Q(puntos__lt=0))
        elif tipo == "MERIT":
            qs = qs.filter(Q(solicitud_t01__tipo_accion="MERIT") | Q(puntos__gt=0))

        search_clean = search.strip()
        if search_clean:
            qs = qs.filter(
                Q(numero__icontains=search_clean)
                | Q(titulo__icontains=search_clean)
                | Q(motivo__icontains=search_clean)
                | Q(socio__first_name__icontains=search_clean)
                | Q(socio__last_name__icontains=search_clean)
                | Q(socio__legajo__icontains=search_clean)
                | Q(socios__first_name__icontains=search_clean)
                | Q(socios__last_name__icontains=search_clean)
                | Q(socios__legajo__icontains=search_clean)
            ).distinct()

        qs = qs.order_by("-updated_at", "-id")[:100]
        results = []
        for exp in qs:
            exp._resolucion_cache = None
            fecha = getattr(exp, "fecha_emision_calc", None) or _emission_date(exp)
            results.append(AntecedentLookup(expediente=exp, fecha_emision=fecha))
        return results

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
        puntaje_final: str | float | int | None = None,
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
        try:
            condition = provider.condition_for_user(user.id)
        except DatabaseError as exc:
            # No se degrada a NO_INFORMADA: quedaría un dato falso en un registro inmutable.
            logger.exception("No se pudo leer la condición del Tribunal en el padrón.")
            raise T03ValuationUnavailable(PADRON_UNAVAILABLE_MESSAGE) from exc
        socio = getattr(user, "socio", None)
        valuation = ValoracionT03.objects.create(
            expediente=expediente,
            descargo=descargo,
            version=last_version + 1,
            resultado=result,
            fundamento=fundamento.strip(),
            puntaje_final=str(puntaje_final) if puntaje_final is not None else None,
            descargo_snapshot=_descargo_snapshot(descargo),
            autor=user,
            autor_legajo=socio.legajo if socio else user.get_username(),
            autor_rol=socio.role if socio else "",
            autor_condicion=condition,
        )
        for antecedent in antecedents:
            ValoracionT03Antecedente.objects.create(
                valoracion=valuation,
                expediente_antecedente=antecedent,
                numero_antecedente=antecedent.numero,
            )
        return valuation


def build_expedientes_referenciados_detalle(ids: list[int] | None) -> list[dict]:
    """Serializa fichas de antecedentes emitidos manteniendo el orden y lista blanca."""
    if not ids:
        return []
    from expedientes.serializers import AntecedenteT03Serializer

    subquery_emision = Subquery(
        CambioEstadoExpediente.objects.filter(
            expediente=OuterRef("pk"),
            estado_nuevo=EstadoExpedienteEnum.EMITIDO,
        )
        .order_by("-fecha_hora", "-id")
        .values("fecha_hora")[:1]
    )

    qs = (
        Expediente.objects.select_related("solicitud_t01")
        .filter(pk__in=ids, estado=EstadoExpedienteEnum.EMITIDO)
        .annotate(fecha_emision_calc=Coalesce(subquery_emision, F("updated_at")))
    )
    found_map = {}
    for exp in qs:
        exp._resolucion_cache = None
        found_map[exp.id] = exp

    ordered_items = []
    for pk in ids:
        if pk in found_map:
            exp = found_map[pk]
            fecha = getattr(exp, "fecha_emision_calc", None) or _emission_date(exp)
            lookup = AntecedentLookup(expediente=exp, fecha_emision=fecha)
            ordered_items.append(lookup)
    return AntecedenteT03Serializer(ordered_items, many=True).data
