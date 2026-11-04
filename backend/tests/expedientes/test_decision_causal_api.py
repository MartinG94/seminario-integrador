"""Pruebas del endpoint HTTP de decisión por causal (POST /descargos/<id>/decisiones/)."""

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from expedientes.domain.causal_resolution import CausalDecision

pytestmark = pytest.mark.django_db


def _decision_url(descargo) -> str:
    return f"/api/v1/expedientes/{descargo.expediente_id}/descargos/{descargo.id}/decisiones/"


class TestDecisionCausalAPI:
    def test_post_decision_same_score_without_grounds_success(
        self, causal_descargo, causal_vocal
    ) -> None:
        causal_descargo.expediente.puntos = -1
        causal_descargo.expediente.save(update_fields=["puntos"])

        client = APIClient()
        client.force_authenticate(user=causal_vocal.user)

        response = client.post(
            _decision_url(causal_descargo),
            {
                "decision": CausalDecision.REJECTED.value,
                "fundamento": "",
                "puntaje_final": -1,
            },
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["decision"] == CausalDecision.REJECTED.value
        assert data["fundamento"] == ""
        assert data["descargo_snapshot"]["puntaje_final"] == -1.0
        assert data["se_aparta_de_regla"] is False

    def test_post_decision_favorable_score_without_grounds_success(
        self, causal_descargo, causal_vocal
    ) -> None:
        causal_descargo.expediente.puntos = -1
        causal_descargo.expediente.save(update_fields=["puntos"])

        client = APIClient()
        client.force_authenticate(user=causal_vocal.user)

        response = client.post(
            _decision_url(causal_descargo),
            {
                "decision": CausalDecision.ACCEPTED.value,
                "fundamento": "",
                "puntaje_final": 0,
            },
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["decision"] == CausalDecision.ACCEPTED.value
        assert data["fundamento"] == ""
        assert data["descargo_snapshot"]["puntaje_final"] == 0.0
        assert data["se_aparta_de_regla"] is True

    def test_post_decision_unfavorable_score_without_grounds_fails_400(
        self, causal_descargo, causal_vocal
    ) -> None:
        causal_descargo.expediente.puntos = -1
        causal_descargo.expediente.save(update_fields=["puntos"])

        client = APIClient()
        client.force_authenticate(user=causal_vocal.user)

        response = client.post(
            _decision_url(causal_descargo),
            {
                "decision": CausalDecision.REJECTED.value,
                "fundamento": "",
                "puntaje_final": -2,
            },
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "fundamentación escrita es obligatoria" in data["detail"]

    def test_post_decision_unfavorable_score_with_grounds_success(
        self, causal_descargo, causal_vocal
    ) -> None:
        causal_descargo.expediente.puntos = -1
        causal_descargo.expediente.save(update_fields=["puntos"])

        client = APIClient()
        client.force_authenticate(user=causal_vocal.user)

        response = client.post(
            _decision_url(causal_descargo),
            {
                "decision": CausalDecision.REJECTED.value,
                "fundamento": "Agravamiento fundamentado por reiteración en el período.",
                "puntaje_final": -2,
            },
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["descargo_snapshot"]["puntaje_final"] == -2.0
        assert data["fundamento"] == "Agravamiento fundamentado por reiteración en el período."
