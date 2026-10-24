"""API del Tribunal de la causa (S4-04): inhibición de involucrados y Asamblea."""

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status

from expedientes.models import DecisionCausalDescargo, EstadoExpedienteEnum, ResolucionAsamblea
from socios.models import Role
from tests.expedientes.conftest import PDF_BYTES

pytestmark = pytest.mark.django_db


def url(expediente, suffix: str) -> str:
    return f"/api/v1/expedientes/{expediente.pk}/{suffix}"


DECISION = {
    "decision": "REJECTED",
    "fundamento": "El certificado no acredita la imposibilidad de asistir a la reunión.",
}


def acta(name: str = "acta.pdf", content: bytes = PDF_BYTES) -> SimpleUploadedFile:
    return SimpleUploadedFile(name, content, content_type="application/pdf")


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

    def test_imputado_no_evalua_justificativos(self, api_client, causal_descargo, vocal_imputado):
        api_client.force_authenticate(vocal_imputado.user)
        response = api_client.post(
            url(causal_descargo.expediente, f"descargos/{causal_descargo.pk}/decisiones/"),
            DECISION,
            format="json",
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "Participación restringida" in response.data["detail"]
        assert not DecisionCausalDescargo.objects.exists()

    def test_solicitante_no_evalua_justificativos(
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
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_vocal_no_involucrado_evalua(self, api_client, causal_descargo, tribunal_nomina):
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
    def test_imputado_no_transiciona(
        self, api_client, causal_expediente, vocal_imputado, suffix, payload
    ):
        api_client.force_authenticate(vocal_imputado.user)
        response = api_client.post(url(causal_expediente, suffix), payload, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN
        causal_expediente.refresh_from_db()
        assert causal_expediente.estado == EstadoExpedienteEnum.REVISION_RESOLUCION

    def test_imputado_no_emite_ni_firma(self, api_client, causal_expediente, vocal_imputado):
        causal_expediente.estado = EstadoExpedienteEnum.PENDIENTE_CORREOS
        causal_expediente.save(update_fields=["estado"])
        api_client.force_authenticate(vocal_imputado.user)
        response = api_client.post(
            url(causal_expediente, "transicionar/"),
            {"to_status": EstadoExpedienteEnum.EMITIDO},
            format="json",
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_vocal_no_involucrado_transiciona(self, api_client, causal_expediente, tribunal_nomina):
        api_client.force_authenticate(tribunal_nomina["t4"].user)
        response = api_client.post(
            url(causal_expediente, "transicionar/"),
            {"to_status": EstadoExpedienteEnum.ESPERA_RESOLUCION},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK


class TestResolucionAsamblea:
    @pytest.fixture
    def caso_critico(self, causal_expediente, tribunal_nomina):
        causal_expediente.socios.add(tribunal_nomina["t5"], tribunal_nomina["s5"])
        return causal_expediente

    @pytest.mark.parametrize("role", [Role.CD, Role.ADMIN])
    def test_cd_o_admin_registran_y_emiten(self, api_client, caso_critico, make_socio, role):
        api_client.force_authenticate(make_socio(legajo="77020", role=role).user)
        response = api_client.post(
            url(caso_critico, "resolucion-asamblea/"), {"acta": acta()}, format="multipart"
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["resolucion_asamblea"]["acta_nombre"] == "acta.pdf"
        caso_critico.refresh_from_db()
        assert caso_critico.estado == EstadoExpedienteEnum.EMITIDO

    def test_tribunal_no_registra(self, api_client, caso_critico, tribunal_nomina):
        api_client.force_authenticate(tribunal_nomina["t4"].user)
        response = api_client.post(
            url(caso_critico, "resolucion-asamblea/"), {"acta": acta()}, format="multipart"
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_cd_involucrado_no_registra(self, api_client, caso_critico, make_socio):
        cd = make_socio(legajo="77021", role=Role.CD)
        caso_critico.socios.add(cd)
        api_client.force_authenticate(cd.user)
        response = api_client.post(
            url(caso_critico, "resolucion-asamblea/"), {"acta": acta()}, format="multipart"
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_sin_acta(self, api_client, caso_critico, make_socio):
        api_client.force_authenticate(make_socio(legajo="77022", role=Role.CD).user)
        response = api_client.post(
            url(caso_critico, "resolucion-asamblea/"), {}, format="multipart"
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_acta_que_no_es_pdf(self, api_client, caso_critico, make_socio):
        api_client.force_authenticate(make_socio(legajo="77023", role=Role.CD).user)
        response = api_client.post(
            url(caso_critico, "resolucion-asamblea/"),
            {"acta": acta("acta.png", b"\x89PNG\r\n\x1a\n" + b"0" * 10)},
            format="multipart",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_sin_caso_critico_devuelve_409(
        self, api_client, causal_expediente, tribunal_nomina, make_socio
    ):
        api_client.force_authenticate(make_socio(legajo="77024", role=Role.CD).user)
        response = api_client.post(
            url(causal_expediente, "resolucion-asamblea/"), {"acta": acta()}, format="multipart"
        )
        assert response.status_code == status.HTTP_409_CONFLICT

    def test_descarga_del_acta(self, api_client, caso_critico, make_socio, tribunal_nomina):
        api_client.force_authenticate(make_socio(legajo="77025", role=Role.CD).user)
        api_client.post(
            url(caso_critico, "resolucion-asamblea/"), {"acta": acta()}, format="multipart"
        )
        assert ResolucionAsamblea.objects.filter(expediente=caso_critico).exists()

        api_client.force_authenticate(tribunal_nomina["t4"].user)
        response = api_client.get(url(caso_critico, "resolucion-asamblea/"))
        assert response.status_code == status.HTTP_200_OK
        assert response["Content-Type"] == "application/pdf"
        assert response.content == PDF_BYTES

    def test_descarga_sin_acta(self, api_client, causal_expediente, causal_vocal):
        api_client.force_authenticate(causal_vocal.user)
        response = api_client.get(url(causal_expediente, "resolucion-asamblea/"))
        assert response.status_code == status.HTTP_404_NOT_FOUND
