"""Pruebas del servicio de valoración extraordinaria T03 (S4-03)."""

from dataclasses import asdict
from datetime import UTC, datetime

import pytest

from expedientes.domain.t03_valuation import TribunalCondition
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
from expedientes.services.t03_valuation_service import (
    T03ValuationForbidden,
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


@pytest.fixture
def make_expediente(t03_descargo):
    """Crea un expediente del mismo imputado en el estado indicado."""

    def _make(numero: str, estado: str = EstadoExpedienteEnum.EMITIDO, **fields) -> Expediente:
        return Expediente.objects.create(
            numero=numero,
            socio=t03_descargo.socio,
            motivo=fields.pop("motivo", f"Causa {numero}"),
            estado=estado,
            **fields,
        )

    return _make


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


class TestAntecedents:
    """RF-11 a RF-14: vínculo a expedientes emitidos, revalidado en el servicio."""

    def test_links_emitted_antecedents_with_number_copy(
        self, t03_descargo, tribunal_member, make_expediente
    ) -> None:
        first = make_expediente("EXP-0702/2026")
        second = make_expediente("EXP-0703/2026")

        valuation = register(t03_descargo, tribunal_member, antecedente_ids=[second.id, first.id])

        links = list(
            ValoracionT03Antecedente.objects.filter(valoracion=valuation).values_list(
                "expediente_antecedente_id", "numero_antecedente"
            )
        )
        assert links == [(second.id, "EXP-0703/2026"), (first.id, "EXP-0702/2026")]

    def test_antecedent_of_same_socio_in_another_case_is_valid(
        self, t03_descargo, tribunal_member, make_expediente
    ) -> None:
        own_history = make_expediente("EXP-0704/2026")

        valuation = register(t03_descargo, tribunal_member, antecedente_ids=[own_history.id])

        assert valuation.antecedentes.get().expediente_antecedente_id == own_history.id

    def test_rejects_unknown_antecedent_without_recording(
        self, t03_descargo, tribunal_member, make_expediente
    ) -> None:
        valid = make_expediente("EXP-0702/2026")

        with pytest.raises(T03ValuationValidationError, match="emitido"):
            register(t03_descargo, tribunal_member, antecedente_ids=[valid.id, 999999])
        assert not ValoracionT03.objects.exists()
        assert not ValoracionT03Antecedente.objects.exists()

    @pytest.mark.parametrize(
        "estado",
        [
            EstadoExpedienteEnum.CREADO,
            EstadoExpedienteEnum.JUSTIFICANDO,
            EstadoExpedienteEnum.REVISION_RESOLUCION,
            EstadoExpedienteEnum.ESPERA_RESOLUCION,
            EstadoExpedienteEnum.PENDIENTE_CORREOS,
        ],
    )
    def test_rejects_antecedent_not_emitted_without_recording(
        self, t03_descargo, tribunal_member, make_expediente, estado
    ) -> None:
        not_emitted = make_expediente("EXP-0705/2026", estado=estado)

        with pytest.raises(T03ValuationValidationError, match="emitido"):
            register(t03_descargo, tribunal_member, antecedente_ids=[not_emitted.id])
        assert not ValoracionT03.objects.exists()
        assert not ValoracionT03Antecedente.objects.exists()

    def test_rejects_repeated_antecedent_without_recording(
        self, t03_descargo, tribunal_member, make_expediente
    ) -> None:
        emitted = make_expediente("EXP-0702/2026")

        with pytest.raises(T03ValuationValidationError, match="repetido"):
            register(t03_descargo, tribunal_member, antecedente_ids=[emitted.id, emitted.id])
        assert not ValoracionT03.objects.exists()

    def test_rejects_own_expediente_without_recording(self, t03_descargo, tribunal_member) -> None:
        with pytest.raises(T03ValuationValidationError, match="mismo expediente"):
            register(t03_descargo, tribunal_member, antecedente_ids=[t03_descargo.expediente_id])
        assert not ValoracionT03.objects.exists()

    def test_link_keeps_only_reference_never_content(
        self, t03_descargo, tribunal_member, make_expediente
    ) -> None:
        emitted = make_expediente("EXP-0702/2026")

        valuation = register(t03_descargo, tribunal_member, antecedente_ids=[emitted.id])

        link = ValoracionT03Antecedente.objects.filter(valoracion=valuation).values().get()
        assert set(link) == {
            "id",
            "valoracion_id",
            "expediente_antecedente_id",
            "numero_antecedente",
        }


class TestInterestedPartyInhibition:
    """RF-26: imputados y solicitante del T01 no valoran (Estatuto Art. 95; RP 2026 Art. 24)."""

    def test_main_imputado_cannot_value(self, t03_descargo) -> None:
        imputado = t03_descargo.socio

        with pytest.raises(T03ValuationForbidden, match="parte interesada"):
            register(t03_descargo, imputado)
        assert not ValoracionT03.objects.exists()

    def test_co_imputado_member_cannot_value(self, t03_descargo, make_socio) -> None:
        member = make_socio(legajo="77020", role=Role.TD)
        t03_descargo.expediente.socios.add(member)

        with pytest.raises(T03ValuationForbidden, match="parte interesada"):
            register(t03_descargo, member)
        assert not ValoracionT03.objects.exists()

    def test_t01_requester_member_cannot_value(self, t03_descargo, make_socio) -> None:
        member = make_socio(legajo="77021", role=Role.TD)
        SolicitudT01.objects.create(
            solicitante=member,
            tipo_accion=SolicitudT01.TipoAccion.SANCTION,
            puntos=-1,
            destinatarios_socios_ids=[t03_descargo.socio_id],
            estado=SolicitudT01.Estado.ISSUED,
            expediente=t03_descargo.expediente,
        )

        with pytest.raises(T03ValuationForbidden, match="parte interesada"):
            register(t03_descargo, member)
        assert not ValoracionT03.objects.exists()

    def test_unrelated_member_can_value(self, t03_descargo, tribunal_member) -> None:
        assert register(t03_descargo, tribunal_member).version == 1


class TestLookupAntecedent:
    """RF-16: el servicio resuelve el expediente emitido y su fecha de emisión (D4 y D6)."""

    @pytest.mark.parametrize("text", ["904/2026", "0904/2026", "EXP-0904/2026", " exp-904/2026 "])
    def test_finds_emitted_case_by_any_accepted_number(self, make_expediente, text) -> None:
        emitted = make_expediente("EXP-0904/2026", motivo="Inasistencia a la reunión plenaria")

        found = T03ValuationService.lookup_antecedent(text)

        assert found.expediente.id == emitted.id
        assert found.expediente.numero == "EXP-0904/2026"

    def test_emission_date_is_last_transition_to_emitido(self, make_expediente) -> None:
        emitted = make_expediente("EXP-0904/2026")
        first = CambioEstadoExpediente.objects.create(
            expediente=emitted,
            estado_anterior=EstadoExpedienteEnum.PENDIENTE_CORREOS,
            estado_nuevo=EstadoExpedienteEnum.EMITIDO,
        )
        last = CambioEstadoExpediente.objects.create(
            expediente=emitted,
            estado_anterior=EstadoExpedienteEnum.PENDIENTE_CORREOS,
            estado_nuevo=EstadoExpedienteEnum.EMITIDO,
        )
        other = CambioEstadoExpediente.objects.create(
            expediente=emitted,
            estado_anterior=EstadoExpedienteEnum.CREADO,
            estado_nuevo=EstadoExpedienteEnum.JUSTIFICANDO,
        )
        CambioEstadoExpediente.objects.filter(pk=first.pk).update(
            fecha_hora=datetime(2026, 9, 1, 12, tzinfo=UTC)
        )
        CambioEstadoExpediente.objects.filter(pk=last.pk).update(
            fecha_hora=datetime(2026, 9, 15, 12, tzinfo=UTC)
        )
        CambioEstadoExpediente.objects.filter(pk=other.pk).update(
            fecha_hora=datetime(2026, 10, 1, 12, tzinfo=UTC)
        )

        card = T03ValuationService.lookup_antecedent("904/2026")

        assert card.fecha_emision == datetime(2026, 9, 15, 12, tzinfo=UTC)

    def test_emission_date_falls_back_to_updated_at(self, make_expediente) -> None:
        emitted = make_expediente("EXP-0904/2026")

        card = T03ValuationService.lookup_antecedent("904/2026")

        assert card.fecha_emision == Expediente.objects.get(pk=emitted.pk).updated_at

    def test_not_emitted_case_is_not_found(self, make_expediente) -> None:
        make_expediente("EXP-0904/2026", estado=EstadoExpedienteEnum.PENDIENTE_CORREOS)

        with pytest.raises(T03ValuationNotFound, match="No hay un expediente emitido"):
            T03ValuationService.lookup_antecedent("904/2026")

    def test_unknown_case_is_not_found(self) -> None:
        with pytest.raises(T03ValuationNotFound, match="No hay un expediente emitido"):
            T03ValuationService.lookup_antecedent("904/2026")

    @pytest.mark.parametrize("text", ["", "   ", "904", "abc/2026"])
    def test_malformed_number_is_rejected(self, text) -> None:
        with pytest.raises(T03ValuationValidationError, match="número de expediente"):
            T03ValuationService.lookup_antecedent(text)

    def test_returns_only_the_case_and_its_emission_date(self, make_expediente) -> None:
        make_expediente("EXP-0904/2026")

        found = T03ValuationService.lookup_antecedent("904/2026")

        assert set(asdict(found)) == {"expediente", "fecha_emision"}
