"""Pruebas del servicio de decisión por causal T02 (S4-02, CA1 a CA4)."""

import uuid

import pytest

from expedientes.domain.causal_resolution import CausalDecision
from expedientes.models import (
    DescargoExpediente,
    EstadoExpedienteEnum,
    EvidenciaDescargo,
    TipoDescargoEnum,
)
from expedientes.services.causal_resolution_service import (
    CausalResolutionNotFound,
    CausalResolutionService,
    CausalResolutionStateError,
    CausalResolutionValidationError,
)

GROUNDS = "El certificado presentado no acredita la fecha de la inasistencia."


def _decide(descargo, user, decision=CausalDecision.ACCEPTED, fundamento="", evidencia_ids=None):
    return CausalResolutionService.decide(
        expediente_id=descargo.expediente_id,
        descargo_id=descargo.id,
        decision=decision,
        fundamento=fundamento,
        evidencia_ids=evidencia_ids,
        user=user,
    )


@pytest.mark.django_db
class TestDecisionPorCausalYEvidencia:
    def test_accepts_causal_linking_current_evidence(
        self, causal_descargo, causal_evidencia, causal_vocal
    ) -> None:
        decision = _decide(causal_descargo, causal_vocal.user)

        assert decision.decision == CausalDecision.ACCEPTED
        assert decision.regla_sugerida == CausalDecision.ACCEPTED
        assert decision.se_aparta_de_regla is False
        assert decision.evidencias_valoradas == [
            {
                "id": str(causal_evidencia.id),
                "nombre_original": "certificado.pdf",
                "sha256_hash": causal_evidencia.sha256_hash,
            }
        ]

    def test_rejects_evidence_outside_descargo(
        self, causal_descargo, causal_evidencia, causal_vocal
    ) -> None:
        with pytest.raises(CausalResolutionValidationError):
            _decide(causal_descargo, causal_vocal.user, evidencia_ids=[uuid.uuid4()])

    def test_rejects_superseded_evidence(
        self, causal_descargo, causal_evidencia, causal_vocal
    ) -> None:
        EvidenciaDescargo.objects.filter(pk=causal_evidencia.pk).update(es_vigente=False)

        with pytest.raises(CausalResolutionValidationError):
            _decide(causal_descargo, causal_vocal.user, evidencia_ids=[causal_evidencia.id])

    def test_decisions_are_individual_per_socio(
        self, causal_descargo, causal_evidencia, causal_vocal, make_socio
    ) -> None:
        otro = make_socio(legajo="76003")
        causal_descargo.expediente.socios.add(otro)
        otro_descargo = DescargoExpediente.objects.create(
            expediente=causal_descargo.expediente,
            socio=otro,
            tipo=TipoDescargoEnum.T02_CERTIFICADO,
            causal="Examen universitario en UTN FRC",
        )

        aceptada = _decide(causal_descargo, causal_vocal.user)
        rechazada = _decide(
            otro_descargo, causal_vocal.user, CausalDecision.REJECTED, fundamento=GROUNDS
        )

        assert aceptada.decision == CausalDecision.ACCEPTED
        assert rechazada.decision == CausalDecision.REJECTED
        assert rechazada.version == 1


@pytest.mark.django_db
class TestFundamentoObligatorio:
    def test_rejection_without_grounds_fails(
        self, causal_descargo, causal_evidencia, causal_vocal
    ) -> None:
        with pytest.raises(CausalResolutionValidationError):
            _decide(causal_descargo, causal_vocal.user, CausalDecision.REJECTED)

    def test_accepting_without_evidence_departs_from_rule_and_needs_grounds(
        self, causal_descargo, causal_vocal
    ) -> None:
        with pytest.raises(CausalResolutionValidationError):
            _decide(causal_descargo, causal_vocal.user)

        decision = _decide(causal_descargo, causal_vocal.user, fundamento=GROUNDS)
        assert decision.se_aparta_de_regla is True
        assert decision.regla_sugerida == CausalDecision.REJECTED


@pytest.mark.django_db
class TestAutoriaYVersion:
    def test_keeps_author_and_previous_versions(
        self, causal_descargo, causal_evidencia, causal_vocal
    ) -> None:
        primera = _decide(causal_descargo, causal_vocal.user)
        segunda = _decide(
            causal_descargo, causal_vocal.user, CausalDecision.REJECTED, fundamento=GROUNDS
        )

        assert (primera.version, segunda.version) == (1, 2)
        assert segunda.autor == causal_vocal.user
        assert segunda.autor_legajo == "76002"
        assert segunda.autor_rol == "TD"
        primera.refresh_from_db()
        assert primera.decision == CausalDecision.ACCEPTED


@pytest.mark.django_db
class TestDescargoInalterado:
    def test_decision_does_not_modify_descargo_or_evidence(
        self, causal_descargo, causal_evidencia, causal_vocal
    ) -> None:
        antes = DescargoExpediente.objects.filter(pk=causal_descargo.pk).values().get()

        decision = _decide(
            causal_descargo, causal_vocal.user, CausalDecision.REJECTED, fundamento=GROUNDS
        )

        assert DescargoExpediente.objects.filter(pk=causal_descargo.pk).values().get() == antes
        causal_evidencia.refresh_from_db()
        assert causal_evidencia.es_vigente is True
        assert decision.descargo_snapshot["causal"] == causal_descargo.causal
        assert decision.descargo_snapshot["texto"] == causal_descargo.texto


@pytest.mark.django_db
class TestEtapaYTipo:
    @pytest.mark.parametrize(
        "estado",
        [
            EstadoExpedienteEnum.CREADO,
            EstadoExpedienteEnum.JUSTIFICANDO,
            EstadoExpedienteEnum.PENDIENTE_CORREOS,
            EstadoExpedienteEnum.EMITIDO,
        ],
    )
    def test_rejects_outside_review_stage(
        self, estado, causal_descargo, causal_evidencia, causal_vocal
    ) -> None:
        expediente = causal_descargo.expediente
        expediente.estado = estado
        expediente.save(update_fields=["estado"])

        with pytest.raises(CausalResolutionStateError):
            _decide(causal_descargo, causal_vocal.user)

    def test_allows_waiting_for_resolution_stage(
        self, causal_descargo, causal_evidencia, causal_vocal
    ) -> None:
        expediente = causal_descargo.expediente
        expediente.estado = EstadoExpedienteEnum.ESPERA_RESOLUCION
        expediente.save(update_fields=["estado"])

        assert _decide(causal_descargo, causal_vocal.user).version == 1

    def test_rejects_t03_descargo(self, causal_descargo, causal_vocal) -> None:
        DescargoExpediente.objects.filter(pk=causal_descargo.pk).update(
            tipo=TipoDescargoEnum.T03_EXTRAORDINARIO
        )
        causal_descargo.refresh_from_db()

        with pytest.raises(CausalResolutionValidationError):
            _decide(causal_descargo, causal_vocal.user, fundamento=GROUNDS)

    def test_descargo_from_another_expediente_is_not_found(
        self, causal_descargo, causal_vocal
    ) -> None:
        with pytest.raises(CausalResolutionNotFound):
            CausalResolutionService.decide(
                expediente_id=causal_descargo.expediente_id,
                descargo_id=causal_descargo.id + 999,
                decision=CausalDecision.ACCEPTED,
                fundamento=GROUNDS,
                evidencia_ids=None,
                user=causal_vocal.user,
            )
