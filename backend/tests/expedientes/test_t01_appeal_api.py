"""API de apelación y adecuación del T01 (PB-02): permisos y códigos HTTP."""

import pytest
from rest_framework import status

from expedientes.models import EstadoExpedienteEnum, Expediente, ParametroPlazoApelacion
from expedientes.services.workflow_service import ExpedienteWorkflowService
from socios.models import Role

pytestmark = pytest.mark.django_db

APELACION = "No estuve presente en el laboratorio ese día; hay testigos."
MOTIVOS = "El debate acreditó que la falta fue compartida con un tercer socio."
PLAZO_URL = "/api/v1/expedientes/parametros/plazo-apelacion/"


@pytest.fixture
def en_apelacion(t01_expediente) -> Expediente:
    return ExpedienteWorkflowService.transition(
        expediente_id=t01_expediente.pk,
        estado_nuevo=EstadoExpedienteEnum.JUSTIFICANDO,
        actor="tribunal",
        motivo="Apertura del período de apelación",
    )


@pytest.fixture
def vocal(make_socio):
    return make_socio(legajo="78100", role=Role.TD, social_year=6)


class TestPlazo:
    def test_tribunal_consulta_y_modifica(self, api_client, vocal):
        api_client.force_authenticate(vocal.user)
        assert api_client.get(PLAZO_URL).data["dias_habiles"] == 5
        response = api_client.put(PLAZO_URL, {"dias_habiles": 7}, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["dias_habiles"] == 7
        assert response.data["actualizado_por"] == "78100"

    def test_valor_invalido(self, api_client, vocal):
        api_client.force_authenticate(vocal.user)
        response = api_client.put(PLAZO_URL, {"dias_habiles": 45}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert not ParametroPlazoApelacion.objects.exists()

    def test_comision_directiva_consulta_pero_no_modifica(self, api_client, make_socio):
        api_client.force_authenticate(make_socio(legajo="78200", role=Role.CD).user)
        assert api_client.get(PLAZO_URL).status_code == status.HTTP_200_OK
        response = api_client.put(PLAZO_URL, {"dias_habiles": 7}, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_socio_no_consulta(self, api_client, causal_imputado):
        api_client.force_authenticate(causal_imputado.user)
        assert api_client.get(PLAZO_URL).status_code == status.HTTP_403_FORBIDDEN

    def test_anonimo(self, api_client):
        assert api_client.get(PLAZO_URL).status_code == status.HTTP_401_UNAUTHORIZED


class TestApelacion:
    def test_socio_apela(self, api_client, en_apelacion, t01_involucrados):
        api_client.force_authenticate(t01_involucrados[0].user)
        response = api_client.post(
            f"/api/v1/expedientes/{en_apelacion.pk}/apelacion/", {"texto": APELACION}, format="json"
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["apelaciones"][0]["texto"] == APELACION

    def test_socio_ajeno(self, api_client, en_apelacion, make_socio):
        api_client.force_authenticate(make_socio(legajo="78999").user)
        response = api_client.post(
            f"/api/v1/expedientes/{en_apelacion.pk}/apelacion/", {"texto": APELACION}, format="json"
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_fuera_de_etapa(self, api_client, t01_expediente, t01_involucrados):
        api_client.force_authenticate(t01_involucrados[0].user)
        response = api_client.post(
            f"/api/v1/expedientes/{t01_expediente.pk}/apelacion/",
            {"texto": APELACION},
            format="json",
        )
        assert response.status_code == status.HTTP_409_CONFLICT

    def test_texto_breve(self, api_client, en_apelacion, t01_involucrados):
        api_client.force_authenticate(t01_involucrados[0].user)
        response = api_client.post(
            f"/api/v1/expedientes/{en_apelacion.pk}/apelacion/", {"texto": "No"}, format="json"
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_t02_rechazado_en_expediente_de_t01(self, api_client, en_apelacion, t01_involucrados):
        api_client.force_authenticate(t01_involucrados[0].user)
        response = api_client.post(
            f"/api/v1/expedientes/{en_apelacion.pk}/descargo/",
            {"tipo": "T02_CERTIFICADO", "causal": "Enfermedad", "texto": "Certificado"},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "apelación" in response.data["detail"]

    def test_expediente_inexistente(self, api_client, t01_involucrados):
        api_client.force_authenticate(t01_involucrados[0].user)
        response = api_client.post(
            "/api/v1/expedientes/999999/apelacion/", {"texto": APELACION}, format="json"
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestAdecuacion:
    def payload(self, expediente, **overrides):
        data = {
            "puntos": "-1.50",
            "socios": list(expediente.socios.values_list("pk", flat=True)),
            "motivos": MOTIVOS,
            "reabrir_plazo": False,
        }
        data.update(overrides)
        return data

    def test_tribunal_adecua(self, api_client, en_apelacion, vocal):
        Expediente.objects.filter(pk=en_apelacion.pk).update(
            estado=EstadoExpedienteEnum.REVISION_RESOLUCION
        )
        api_client.force_authenticate(vocal.user)
        response = api_client.post(
            f"/api/v1/expedientes/{en_apelacion.pk}/adecuaciones/",
            self.payload(en_apelacion),
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["adecuaciones"][0]["puntos_nuevos"] == "-1.50"

    def test_fuera_del_debate(self, api_client, en_apelacion, vocal):
        api_client.force_authenticate(vocal.user)
        response = api_client.post(
            f"/api/v1/expedientes/{en_apelacion.pk}/adecuaciones/",
            self.payload(en_apelacion),
            format="json",
        )
        assert response.status_code == status.HTTP_409_CONFLICT

    @pytest.mark.parametrize("role", [Role.CD, Role.SOCIO, Role.ADMIN])
    def test_solo_el_tribunal_adecua(self, api_client, en_apelacion, make_socio, role):
        api_client.force_authenticate(make_socio(legajo="78300", role=role).user)
        response = api_client.post(
            f"/api/v1/expedientes/{en_apelacion.pk}/adecuaciones/",
            self.payload(en_apelacion),
            format="json",
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestHistorial:
    def test_socio_involucrado(self, api_client, en_apelacion, t01_involucrados):
        api_client.force_authenticate(t01_involucrados[0].user)
        response = api_client.get(f"/api/v1/expedientes/{en_apelacion.pk}/t01/historial/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["es_t01"] is True
        assert len(response.data["periodos"]) == 1

    def test_tercero(self, api_client, en_apelacion, make_socio):
        api_client.force_authenticate(make_socio(legajo="78999").user)
        response = api_client.get(f"/api/v1/expedientes/{en_apelacion.pk}/t01/historial/")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_anonimo(self, api_client, en_apelacion):
        response = api_client.get(f"/api/v1/expedientes/{en_apelacion.pk}/t01/historial/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_mis_expedientes_indica_origen_t01(api_client, en_apelacion, t01_involucrados):
    api_client.force_authenticate(t01_involucrados[0].user)
    (expediente,) = api_client.get("/api/v1/expedientes/mis-expedientes/").data
    assert expediente["es_t01"] is True
