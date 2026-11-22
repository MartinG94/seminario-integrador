"""Pruebas de API REST para la exclusión fundada de socios involucrados (SCRUM-102)."""

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from expedientes.models import EstadoExpedienteEnum
from socios.models import Role, Socio

VALID_GROUNDS = "El socio no fue notificado oportunamente de la citación a la reunión plenaria."


def _url(exp_id: int, socio_id: int) -> str:
    return f"/api/v1/expedientes/{exp_id}/involucrados/{socio_id}/excluir/"


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture
def imputado_secundario(make_socio) -> Socio:
    return make_socio(legajo="76010", role=Role.SOCIO)


@pytest.mark.django_db
class TestExclusionInvolucradoAPI:
    def test_api_excluir_involucrado_td_exitoso(
        self, api_client, causal_expediente, causal_imputado, imputado_secundario, causal_vocal
    ) -> None:
        """Un vocal TD puede excluir a un socio mediante POST a la API REST."""
        causal_expediente.socios.add(imputado_secundario)
        api_client.force_authenticate(user=causal_vocal.user)

        response = api_client.post(
            _url(causal_expediente.id, causal_imputado.id),
            {"motivo": VALID_GROUNDS},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["esta_excluido"] is True
        assert data["motivo_exclusion"] == VALID_GROUNDS
        assert data["expediente_archivado"] is False
        assert data["activos_restantes_count"] == 1

    def test_api_excluir_involucrado_socio_comun_forbidden(
        self, api_client, causal_expediente, causal_imputado, imputado_secundario
    ) -> None:
        """Un usuario sin rol TD recibe 403 Forbidden."""
        api_client.force_authenticate(user=imputado_secundario.user)

        response = api_client.post(
            _url(causal_expediente.id, causal_imputado.id),
            {"motivo": VALID_GROUNDS},
            format="json",
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_api_excluir_involucrado_motivo_corto_bad_request(
        self, api_client, causal_expediente, causal_imputado, causal_vocal
    ) -> None:
        """Un motivo de menos de 10 caracteres responde 400 Bad Request."""
        api_client.force_authenticate(user=causal_vocal.user)

        response = api_client.post(
            _url(causal_expediente.id, causal_imputado.id),
            {"motivo": "error"},
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "al menos 10 caracteres" in response.json()["detail"]

    def test_api_excluir_ultimo_involucrado_archiva_expediente(
        self, api_client, causal_expediente, causal_imputado, causal_vocal
    ) -> None:
        """Al excluir al único o último involucrado, la API reporta el cierre a EMITIDO."""
        api_client.force_authenticate(user=causal_vocal.user)

        response = api_client.post(
            _url(causal_expediente.id, causal_imputado.id),
            {"motivo": VALID_GROUNDS},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["expediente_archivado"] is True
        assert data["expediente_estado"] == EstadoExpedienteEnum.EMITIDO
        assert data["activos_restantes_count"] == 0
