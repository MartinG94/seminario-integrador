"""Pruebas del servicio de valoración extraordinaria T03 (S4-03)."""

import pytest

from expedientes.domain.t03_valuation import TribunalCondition
from expedientes.models import (
    DescargoExpediente,
    EstadoExpedienteEnum,
    TipoDescargoEnum,
    ValoracionT03,
)
from expedientes.services.t03_valuation_service import (
    T03ValuationNotFound,
    T03ValuationService,
    T03ValuationStateError,
    T03ValuationValidationError,
)
from socios.models import Role

pytestmark = pytest.mark.django_db

GROUNDS = "El Tribunal considera acreditada la causa extraordinaria invocada."


class FixedCondition:
    """Doble del puerto `TribunalConditionPort` con una condición fija."""

    def __init__(self, condition: TribunalCondition) -> None:
        self.condition = condition
        self.calls: list[int] = []

    def condition_for_user(self, user_id: int) -> TribunalCondition:
        self.calls.append(user_id)
        return self.condition


def register(descargo: DescargoExpediente, member, **overrides) -> ValoracionT03:
    params = {
        "expediente_id": descargo.expediente_id,
        "descargo_id": descargo.id,
        "resultado": "ACCEPTED",
        "fundamento": GROUNDS,
        "antecedente_ids": [],
        "user": member.user,
        "condition_provider": FixedCondition(TribunalCondition.TITULAR),
    }
    params.update(overrides)
    return T03ValuationService.register(**params)


class TestRegisterValuation:
    def test_registers_first_version_with_author_and_snapshot(
        self, t03_descargo, tribunal_member
    ) -> None:
        provider = FixedCondition(TribunalCondition.SUPLENTE)

        valuation = register(
            t03_descargo, tribunal_member, fundamento=f"  {GROUNDS}  ", condition_provider=provider
        )

        stored = ValoracionT03.objects.get(pk=valuation.pk)
        assert stored.version == 1
        assert stored.resultado == "ACCEPTED"
        assert stored.fundamento == GROUNDS
        assert stored.expediente_id == t03_descargo.expediente_id
        assert stored.autor_id == tribunal_member.user_id
        assert stored.autor_legajo == "77002"
        assert stored.autor_rol == Role.TD
        assert stored.autor_condicion == "SUPLENTE"
        assert provider.calls == [tribunal_member.user_id]
        assert stored.descargo_snapshot["tipo"] == TipoDescargoEnum.T03_EXTRAORDINARIO
        assert stored.descargo_snapshot["texto"] == t03_descargo.texto
        assert stored.descargo_snapshot["causal"] == t03_descargo.causal
        assert stored.descargo_snapshot["socio_legajo"] == "77001"

    def test_does_not_modify_the_descargo(self, t03_descargo, tribunal_member) -> None:
        before = DescargoExpediente.objects.filter(pk=t03_descargo.pk).values().get()

        register(t03_descargo, tribunal_member, resultado="REJECTED")

        assert DescargoExpediente.objects.filter(pk=t03_descargo.pk).values().get() == before

    def test_valuation_without_antecedents_is_valid(self, t03_descargo, tribunal_member) -> None:
        valuation = register(t03_descargo, tribunal_member, antecedente_ids=[])

        assert valuation.antecedentes.count() == 0

    def test_successive_valuations_create_new_versions(self, t03_descargo, tribunal_member) -> None:
        first = register(t03_descargo, tribunal_member, resultado="ACCEPTED")
        second = register(
            t03_descargo,
            tribunal_member,
            resultado="REJECTED",
            fundamento="Nuevo criterio: la causa no fue acreditada con suficiencia.",
        )

        assert (first.version, second.version) == (1, 2)
        kept = ValoracionT03.objects.get(pk=first.pk)
        assert kept.resultado == "ACCEPTED"
        assert kept.fundamento == GROUNDS

    def test_each_socio_is_valued_individually(
        self, t03_descargo, tribunal_member, make_socio
    ) -> None:
        expediente = t03_descargo.expediente
        otro = make_socio(legajo="77003")
        expediente.socios.add(otro)
        otro_descargo = DescargoExpediente.objects.create(
            expediente=expediente,
            socio=otro,
            tipo=TipoDescargoEnum.T03_EXTRAORDINARIO,
            texto="Otro motivo extraordinario distinto.",
        )

        register(t03_descargo, tribunal_member, resultado="ACCEPTED")
        register(t03_descargo, tribunal_member, resultado="ACCEPTED")
        other = register(otro_descargo, tribunal_member, resultado="REJECTED")

        assert other.version == 1
        assert other.descargo_snapshot["socio_legajo"] == "77003"
        assert ValoracionT03.objects.filter(descargo=t03_descargo).count() == 2
        assert ValoracionT03.objects.filter(descargo=otro_descargo).count() == 1

    def test_member_without_padron_condition_is_recorded_as_not_informed(
        self, t03_descargo, tribunal_member
    ) -> None:
        valuation = register(
            t03_descargo,
            tribunal_member,
            condition_provider=FixedCondition(TribunalCondition.NO_INFORMADA),
        )

        assert ValoracionT03.objects.get(pk=valuation.pk).autor_condicion == "NO_INFORMADA"

    @pytest.mark.parametrize(
        "estado", [EstadoExpedienteEnum.REVISION_RESOLUCION, EstadoExpedienteEnum.ESPERA_RESOLUCION]
    )
    def test_allowed_states(self, t03_descargo, tribunal_member, estado) -> None:
        t03_descargo.expediente.estado = estado
        t03_descargo.expediente.save()

        assert register(t03_descargo, tribunal_member).version == 1

    @pytest.mark.parametrize(
        "estado",
        [
            EstadoExpedienteEnum.CREADO,
            EstadoExpedienteEnum.JUSTIFICANDO,
            EstadoExpedienteEnum.PENDIENTE_CORREOS,
            EstadoExpedienteEnum.EMITIDO,
        ],
    )
    def test_rejects_states_outside_valuation_stage(
        self, t03_descargo, tribunal_member, estado
    ) -> None:
        t03_descargo.expediente.estado = estado
        t03_descargo.expediente.save()

        with pytest.raises(T03ValuationStateError):
            register(t03_descargo, tribunal_member)
        assert not ValoracionT03.objects.exists()

    def test_rejects_t02_descargo(self, causal_descargo, tribunal_member) -> None:
        with pytest.raises(T03ValuationValidationError, match="T03"):
            register(causal_descargo, tribunal_member)
        assert not ValoracionT03.objects.exists()

    def test_rejects_withdrawn_descargo(self, t03_descargo, tribunal_member) -> None:
        DescargoExpediente.objects.filter(pk=t03_descargo.pk).update(es_vigente=False)

        with pytest.raises(T03ValuationValidationError, match="vigente"):
            register(t03_descargo, tribunal_member)
        assert not ValoracionT03.objects.exists()

    @pytest.mark.parametrize("fundamento", ["", "   ", "Muy corto", "x" * 5001])
    def test_rejects_invalid_grounds_without_recording(
        self, t03_descargo, tribunal_member, fundamento
    ) -> None:
        with pytest.raises(T03ValuationValidationError, match="fundamento"):
            register(t03_descargo, tribunal_member, fundamento=fundamento)
        assert not ValoracionT03.objects.exists()

    def test_rejects_invalid_result(self, t03_descargo, tribunal_member) -> None:
        with pytest.raises(T03ValuationValidationError, match="resultado"):
            register(t03_descargo, tribunal_member, resultado="PARTIAL")
        assert not ValoracionT03.objects.exists()

    def test_unknown_expediente_is_not_found(self, t03_descargo, tribunal_member) -> None:
        with pytest.raises(T03ValuationNotFound):
            register(t03_descargo, tribunal_member, expediente_id=999999)

    def test_descargo_of_another_expediente_is_not_found(
        self, t03_descargo, causal_descargo, tribunal_member
    ) -> None:
        with pytest.raises(T03ValuationNotFound):
            register(t03_descargo, tribunal_member, descargo_id=causal_descargo.id)
        assert not ValoracionT03.objects.exists()
