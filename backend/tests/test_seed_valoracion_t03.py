"""Escenarios sembrados para revisar S4-03 (valoración T03 con antecedentes) de forma manual."""

from decimal import Decimal

import pytest
from django.core.management import call_command

from expedientes.domain.t03_valuation import TribunalCondition
from expedientes.models import (
    DescargoExpediente,
    EstadoExpedienteEnum,
    Expediente,
    TipoDescargoEnum,
    ValoracionT03,
)
from expedientes.services.t03_valuation_service import T03ValuationService
from ranking.models import PuntajeGeneral
from socios.models import Role, Socio


class _Titular:
    def condition_for_user(self, user_id: int) -> TribunalCondition:
        return TribunalCondition.TITULAR


@pytest.fixture(autouse=True)
def populate_data(db) -> None:
    call_command("seed_production_data")


@pytest.mark.django_db
class TestEscenariosValoracionT03:
    def test_case_in_review_has_a_current_t03_without_valuations(self) -> None:
        expediente = Expediente.objects.get(numero="EXP-0905/2026")
        descargo = DescargoExpediente.objects.get(expediente=expediente)

        assert expediente.estado == EstadoExpedienteEnum.REVISION_RESOLUCION
        assert descargo.tipo == TipoDescargoEnum.T03_EXTRAORDINARIO
        assert descargo.es_vigente
        assert descargo.socio.legajo == "770010"
        assert not descargo.valoraciones_t03.exists()

    def test_seeded_tribunal_member_can_value_the_t03(self) -> None:
        member = Socio.objects.get(legajo="408917")
        descargo = DescargoExpediente.objects.get(expediente__numero="EXP-0905/2026")

        valuation = T03ValuationService.register(
            expediente_id=descargo.expediente_id,
            descargo_id=descargo.id,
            resultado="ACCEPTED",
            fundamento="El corte de ruta está acreditado y fue ajeno a la voluntad del socio.",
            antecedente_ids=[Expediente.objects.get(numero="EXP-0906/2026").id],
            user=member.user,
            condition_provider=_Titular(),
        )

        assert member.role == Role.TD
        assert valuation.antecedentes.get().numero_antecedente == "EXP-0906/2026"

    @pytest.mark.parametrize("numero", ["906/2026", "904/2026"])
    def test_emitted_antecedents_are_found_by_number(self, numero) -> None:
        found = T03ValuationService.lookup_antecedent(numero)

        assert found.expediente.estado == EstadoExpedienteEnum.EMITIDO
        assert found.fecha_emision is not None

    def test_emitted_antecedent_keeps_balance_consistent(self) -> None:
        expediente = Expediente.objects.get(numero="EXP-0906/2026")

        saldo = PuntajeGeneral.objects.get(socio_id=int(expediente.socio.legajo)).puntos
        assert expediente.socio.legajo == "770011"
        assert saldo == expediente.puntos == Decimal("-1.00")

    def test_seed_is_idempotent_for_t03_scenarios(self) -> None:
        counts = (
            Expediente.objects.count(),
            DescargoExpediente.objects.count(),
            ValoracionT03.objects.count(),
        )

        call_command("seed_production_data")

        assert (
            Expediente.objects.count(),
            DescargoExpediente.objects.count(),
            ValoracionT03.objects.count(),
        ) == counts
