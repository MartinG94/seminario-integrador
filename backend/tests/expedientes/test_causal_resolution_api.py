"""Pruebas de integración de la API de decisiones por causal T02 (S4-02)."""

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from expedientes.models import DecisionCausalDescargo, EstadoExpedienteEnum
from socios.models import Role

GROUNDS = "El certificado presentado no acredita la fecha de la inasistencia."


def _url(descargo) -> str:
    return f"/api/v1/expedientes/{descargo.expediente_id}/descargos/{descargo.id}/decisiones/"


def _client(socio) -> APIClient:
    client = APIClient()
    client.force_authenticate(user=socio.user)
    return client


@pytest.mark.django_db
class TestRegistrarDecisionCausal:
    def test_vocal_registers_decision_201(
        self, causal_descargo, causal_evidencia, causal_vocal
    ) -> None:
        response = _client(causal_vocal).post(
            _url(causal_descargo),
            {"decision": "ACCEPTED", "evidencia_ids": [str(causal_evidencia.id)]},
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED, response.data
        assert response.data["version"] == 1
        assert response.data["decision_display"] == "Aceptada"
        assert response.data["autor"] == causal_vocal.legajo
        assert response.data["evidencias_valoradas"][0]["sha256_hash"] == (
            causal_evidencia.sha256_hash
        )

    def test_rejection_without_grounds_400(
        self, causal_descargo, causal_evidencia, causal_vocal
    ) -> None:
        response = _client(causal_vocal).post(
            _url(causal_descargo), {"decision": "REJECTED"}, format="json"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "fundamento" in response.data["detail"]
        assert not DecisionCausalDescargo.objects.exists()

    def test_invalid_decision_value_400(self, causal_descargo, causal_vocal) -> None:
        response = _client(causal_vocal).post(
            _url(causal_descargo), {"decision": "MAYBE", "fundamento": GROUNDS}, format="json"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_outside_review_stage_409(
        self, causal_descargo, causal_evidencia, causal_vocal
    ) -> None:
        expediente = causal_descargo.expediente
        expediente.estado = EstadoExpedienteEnum.JUSTIFICANDO
        expediente.save(update_fields=["estado"])

        response = _client(causal_vocal).post(
            _url(causal_descargo), {"decision": "ACCEPTED"}, format="json"
        )

        assert response.status_code == status.HTTP_409_CONFLICT

    def test_unknown_descargo_404(self, causal_descargo, causal_vocal) -> None:
        url = f"/api/v1/expedientes/{causal_descargo.expediente_id}/descargos/999999/decisiones/"

        response = _client(causal_vocal).post(url, {"decision": "ACCEPTED"}, format="json")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_anonymous_401(self, causal_descargo) -> None:
        response = APIClient().post(_url(causal_descargo), {"decision": "ACCEPTED"}, format="json")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.parametrize("role", [Role.SOCIO, Role.CD, Role.ADMIN, Role.FISCALIZADORA])
    def test_only_tribunal_can_decide_403(self, role, causal_descargo, make_socio) -> None:
        otro = make_socio(legajo="76009", role=role)

        response = _client(otro).post(
            _url(causal_descargo), {"decision": "ACCEPTED", "fundamento": GROUNDS}, format="json"
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_disabled_vocal_403(self, causal_descargo, make_socio) -> None:
        inhabilitado = make_socio(legajo="76010", role=Role.TD, is_enabled=False)

        response = _client(inhabilitado).post(
            _url(causal_descargo), {"decision": "ACCEPTED", "fundamento": GROUNDS}, format="json"
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestConsultarDecisionesCausal:
    def _registrar_dos_versiones(self, descargo, vocal) -> None:
        client = _client(vocal)
        client.post(_url(descargo), {"decision": "ACCEPTED"}, format="json")
        client.post(_url(descargo), {"decision": "REJECTED", "fundamento": GROUNDS}, format="json")

    def test_history_lists_versions_newest_first(
        self, causal_descargo, causal_evidencia, causal_vocal, make_socio
    ) -> None:
        self._registrar_dos_versiones(causal_descargo, causal_vocal)
        directiva = make_socio(legajo="76011", role=Role.CD)

        response = _client(directiva).get(_url(causal_descargo))

        assert response.status_code == status.HTTP_200_OK
        assert [d["version"] for d in response.data] == [2, 1]
        assert response.data[0]["fundamento"] == GROUNDS

    def test_imputado_cannot_read_history_403(
        self, causal_descargo, causal_evidencia, causal_vocal, causal_imputado
    ) -> None:
        self._registrar_dos_versiones(causal_descargo, causal_vocal)

        response = _client(causal_imputado).get(_url(causal_descargo))

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_detail_shows_decisions_to_tribunal_only(
        self, causal_descargo, causal_evidencia, causal_vocal, causal_imputado
    ) -> None:
        self._registrar_dos_versiones(causal_descargo, causal_vocal)
        url = f"/api/v1/expedientes/{causal_descargo.expediente_id}/"

        vocal_data = _client(causal_vocal).get(url).data["descargos"][0]
        imputado_data = _client(causal_imputado).get(url).data["descargos"][0]

        assert vocal_data["regla_sugerida"] == "ACCEPTED"
        assert [d["version"] for d in vocal_data["decisiones_causal"]] == [2, 1]
        assert "decisiones_causal" not in imputado_data
        assert "regla_sugerida" not in imputado_data
