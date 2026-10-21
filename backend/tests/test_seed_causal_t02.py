"""Escenarios sembrados para revisar S4-02 (decisión por causal T02) de forma manual."""

from decimal import Decimal

import pytest
from django.core.management import call_command

from expedientes.domain.causal_resolution import CausalDecision
from expedientes.models import (
    DecisionCausalDescargo,
    DescargoExpediente,
    EstadoExpedienteEnum,
    EvidenciaDescargo,
    Expediente,
    TipoDescargoEnum,
)
from expedientes.services.causal_resolution_service import suggested_for
from ranking.models import PuntajeGeneral


@pytest.fixture(autouse=True)
def populate_data(db) -> None:
    call_command("seed_production_data")


def _t02(numero: str) -> DescargoExpediente:
    return DescargoExpediente.objects.get(
        expediente__numero=numero, tipo=TipoDescargoEnum.T02_CERTIFICADO
    )


@pytest.mark.django_db
class TestEscenariosCausalT02:
    def test_t02_with_evidence_in_review_suggests_accepting(self) -> None:
        descargo = _t02("EXP-0901/2026")

        assert descargo.expediente.estado == EstadoExpedienteEnum.REVISION_RESOLUCION
        assert suggested_for(descargo) == CausalDecision.ACCEPTED
        assert not descargo.decisiones_causal.exists()

    def test_t02_without_evidence_in_review_suggests_rejecting(self) -> None:
        descargo = _t02("EXP-0902/2026")

        assert descargo.expediente.estado == EstadoExpedienteEnum.REVISION_RESOLUCION
        assert suggested_for(descargo) == CausalDecision.REJECTED

    def test_multiactor_waiting_has_t02_with_two_versions_and_t03(self) -> None:
        expediente = Expediente.objects.get(numero="EXP-0903/2026")
        tipos = set(expediente.descargos.values_list("tipo", flat=True))

        assert expediente.estado == EstadoExpedienteEnum.ESPERA_RESOLUCION
        assert expediente.socios.count() == 3
        assert tipos == {TipoDescargoEnum.T02_CERTIFICADO, TipoDescargoEnum.T03_EXTRAORDINARIO}
        versiones = list(_t02("EXP-0903/2026").decisiones_causal.values_list("version", "decision"))
        assert versiones == [(2, CausalDecision.REJECTED), (1, CausalDecision.ACCEPTED)]

    def test_emitted_keeps_previous_decisions_and_consistent_balance(self) -> None:
        descargo = _t02("EXP-0904/2026")
        expediente = descargo.expediente

        assert expediente.estado == EstadoExpedienteEnum.EMITIDO
        assert descargo.decisiones_causal.exists()
        saldo = PuntajeGeneral.objects.get(socio_id=int(expediente.socio.legajo)).puntos
        assert saldo == expediente.puntos == Decimal("-1.00")

    def test_seed_is_idempotent_for_causal_scenarios(self) -> None:
        counts = (
            DescargoExpediente.objects.count(),
            EvidenciaDescargo.objects.count(),
            DecisionCausalDescargo.objects.count(),
        )

        call_command("seed_production_data")

        assert (
            DescargoExpediente.objects.count(),
            EvidenciaDescargo.objects.count(),
            DecisionCausalDescargo.objects.count(),
        ) == counts
