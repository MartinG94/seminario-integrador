"""API del Tribunal de la causa (S4-04): inhibición de involucrados."""

import pytest
from rest_framework import status

from expedientes.models import DecisionCausalDescargo, EstadoExpedienteEnum
from socios.models import Role

pytestmark = pytest.mark.django_db


def url(expediente, suffix: str) -> str:
    return f"/api/v1/expedientes/{expediente.pk}/{suffix}"


DECISION = {
    "decision": "REJECTED",
    "fundamento": "El certificado no acredita la imposibilidad de asistir a la reunión.",
}


class TestConsulta:
    @pytest.mark.parametrize("role", [Role.TD, Role.CD, Role.ADMIN])
    def test_autoridades_consultan(
        self, api_client, causal_expediente, tribunal_nomina, make_socio, role
    ):
        api_client.force_authenticate(make_socio(legajo="77001", role=role).user)
        response = api_client.get(url(causal_expediente, "composicion/"))
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["asientos"]) == 3
        assert response.data["usuario"] == {"esta_involucrado": False}

    def test_socio_imputado_no_consulta(self, api_client, causal_expediente, causal_imputado):
        api_client.force_authenticate(causal_imputado.user)
        response = api_client.get(url(causal_expediente, "composicion/"))
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_anonimo(self, api_client, causal_expediente):
        response = api_client.get(url(causal_expediente, "composicion/"))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_expediente_inexistente(self, api_client, causal_vocal):
        api_client.force_authenticate(causal_vocal.user)
        response = api_client.get("/api/v1/expedientes/999999/composicion/")
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestEndpointsManualesSuprimidos:
    @pytest.mark.parametrize(
        "suffix",
        [
            "composicion/apartamientos/",
            "composicion/designaciones-ad-hoc/",
            "composicion/constituir/",
            # Sin acta en el sistema: la Asamblea designa integrantes con rol TD (PO, 31/10/2026).
            "resolucion-asamblea/",
        ],
    )
    def test_no_existen(self, api_client, causal_expediente, causal_vocal, suffix):
        api_client.force_authenticate(causal_vocal.user)
        response = api_client.post(url(causal_expediente, suffix), {}, format="json")
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestInhibicionDeInvolucrados:
    @pytest.fixture
    def vocal_imputado(self, causal_expediente, tribunal_nomina):
        causal_expediente.socios.add(tribunal_nomina["t5"])
        return tribunal_nomina["t5"]

    def test_imputado_rol_td_puede_evaluar_justificativos(
        self, api_client, causal_descargo, vocal_imputado
    ):
        api_client.force_authenticate(vocal_imputado.user)
        response = api_client.post(
            url(causal_descargo.expediente, f"descargos/{causal_descargo.pk}/decisiones/"),
            DECISION,
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert DecisionCausalDescargo.objects.exists()

    def test_solicitante_rol_td_puede_evaluar_justificativos(
        self, api_client, causal_descargo, tribunal_nomina
    ):
        from expedientes.models import SolicitudT01

        SolicitudT01.objects.create(
            solicitante=tribunal_nomina["t6"],
            tipo_accion=SolicitudT01.TipoAccion.SANCTION,
            expediente=causal_descargo.expediente,
        )
        api_client.force_authenticate(tribunal_nomina["t6"].user)
        response = api_client.post(
            url(causal_descargo.expediente, f"descargos/{causal_descargo.pk}/decisiones/"),
            DECISION,
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED

    def test_miembro_no_involucrado_evalua(self, api_client, causal_descargo, tribunal_nomina):
        api_client.force_authenticate(tribunal_nomina["t4"].user)
        response = api_client.post(
            url(causal_descargo.expediente, f"descargos/{causal_descargo.pk}/decisiones/"),
            DECISION,
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED

    @pytest.mark.parametrize(
        ("suffix", "payload"),
        [
            ("estado/", {"estado": EstadoExpedienteEnum.ESPERA_RESOLUCION, "motivo": "Avance"}),
            ("transicionar/", {"to_status": EstadoExpedienteEnum.ESPERA_RESOLUCION}),
        ],
    )
    def test_imputado_rol_td_puede_transicionar(
        self, api_client, causal_expediente, vocal_imputado, suffix, payload
    ):
        api_client.force_authenticate(vocal_imputado.user)
        response = api_client.post(url(causal_expediente, suffix), payload, format="json")
        assert response.status_code == status.HTTP_200_OK
        causal_expediente.refresh_from_db()
        assert causal_expediente.estado == EstadoExpedienteEnum.ESPERA_RESOLUCION

    def test_imputado_rol_td_puede_emitir_y_firmar(
        self, api_client, causal_expediente, vocal_imputado
    ):
        causal_expediente.estado = EstadoExpedienteEnum.PENDIENTE_CORREOS
        causal_expediente.concepto = "TD"
        causal_expediente.save(update_fields=["estado", "concepto"])
        api_client.force_authenticate(vocal_imputado.user)
        response = api_client.post(
            url(causal_expediente, "transicionar/"),
            {"to_status": EstadoExpedienteEnum.EMITIDO},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK

    def test_miembro_no_involucrado_transiciona(
        self, api_client, causal_expediente, tribunal_nomina
    ):
        api_client.force_authenticate(tribunal_nomina["t4"].user)
        response = api_client.post(
            url(causal_expediente, "transicionar/"),
            {"to_status": EstadoExpedienteEnum.ESPERA_RESOLUCION},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
