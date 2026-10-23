"""API de composición del Tribunal por causa (S4-04): permisos y códigos HTTP."""

import pytest
from rest_framework import status

from expedientes.models import ApartamientoTribunal, ComposicionTribunal, EstadoExpedienteEnum
from socios.models import Role

pytestmark = pytest.mark.django_db

FUNDAMENTO = "Comparto vivienda con el socio imputado en la causa."


def url(expediente, suffix: str = "") -> str:
    return f"/api/v1/expedientes/{expediente.pk}/composicion/{suffix}"


class TestConsulta:
    @pytest.mark.parametrize("role", [Role.TD, Role.CD, Role.ADMIN])
    def test_autoridades_consultan(
        self, api_client, causal_expediente, tribunal_nomina, make_socio, role
    ):
        api_client.force_authenticate(make_socio(legajo="77001", role=role).user)
        response = api_client.get(url(causal_expediente))
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["asientos"]) == 3
        assert response.data["puede_constituirse"] is True

    def test_socio_imputado_no_consulta(self, api_client, causal_expediente, causal_imputado):
        api_client.force_authenticate(causal_imputado.user)
        assert api_client.get(url(causal_expediente)).status_code == status.HTTP_403_FORBIDDEN

    def test_anonimo(self, api_client, causal_expediente):
        assert api_client.get(url(causal_expediente)).status_code == status.HTTP_401_UNAUTHORIZED

    def test_expediente_inexistente(self, api_client, causal_vocal):
        api_client.force_authenticate(causal_vocal.user)
        response = api_client.get("/api/v1/expedientes/999999/composicion/")
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestApartamiento:
    def test_integrante_se_aparta(self, api_client, causal_expediente, tribunal_nomina):
        api_client.force_authenticate(tribunal_nomina["t6"].user)
        response = api_client.post(
            url(causal_expediente, "apartamientos/"), {"fundamento": FUNDAMENTO}, format="json"
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["apartamientos"][0]["causa"] == "CONFLICTO_INTERES"
        assert response.data["asientos"][2]["socio_id"] == tribunal_nomina["s6"].id

    def test_recusacion_no_existe_el_socio_imputado_no_aparta(
        self, api_client, causal_expediente, causal_imputado, tribunal_nomina
    ):
        api_client.force_authenticate(causal_imputado.user)
        response = api_client.post(
            url(causal_expediente, "apartamientos/"),
            {"fundamento": FUNDAMENTO, "socio": tribunal_nomina["t4"].id},
            format="json",
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert not ApartamientoTribunal.objects.exists()

    def test_un_integrante_no_aparta_a_otro(self, api_client, causal_expediente, tribunal_nomina):
        api_client.force_authenticate(tribunal_nomina["t4"].user)
        api_client.post(
            url(causal_expediente, "apartamientos/"),
            {"fundamento": FUNDAMENTO, "socio": tribunal_nomina["t5"].id},
            format="json",
        )
        (apartamiento,) = ApartamientoTribunal.objects.all()
        assert apartamiento.socio == tribunal_nomina["t4"]

    def test_comision_directiva_no_aparta(
        self, api_client, causal_expediente, tribunal_nomina, make_socio
    ):
        api_client.force_authenticate(make_socio(legajo="77002", role=Role.CD).user)
        response = api_client.post(
            url(causal_expediente, "apartamientos/"), {"fundamento": FUNDAMENTO}, format="json"
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_fundamento_breve(self, api_client, causal_expediente, tribunal_nomina):
        api_client.force_authenticate(tribunal_nomina["t6"].user)
        response = api_client.post(
            url(causal_expediente, "apartamientos/"), {"fundamento": "Breve"}, format="json"
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestDesignacionAdHoc:
    def test_comision_directiva_registra_designacion(
        self, api_client, causal_expediente, tribunal_nomina, make_legacy_socio, make_socio
    ):
        causal_expediente.socios.add(tribunal_nomina["t4"], tribunal_nomina["s4"])
        designado = make_legacy_socio(90041, 4)
        api_client.force_authenticate(make_socio(legajo="77003", role=Role.CD).user)
        response = api_client.post(
            url(causal_expediente, "designaciones-ad-hoc/"),
            {
                "reemplaza_a": tribunal_nomina["t4"].id,
                "designado_nro_socio": int(designado.legajo),
                "acta_asamblea": "Acta de Asamblea N° 3/2026",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["es_ad_hoc"] is True
        assert response.data["asientos"][0]["socio_id"] == designado.id

    def test_designacion_invalida(self, api_client, causal_expediente, tribunal_nomina):
        api_client.force_authenticate(tribunal_nomina["t5"].user)
        response = api_client.post(
            url(causal_expediente, "designaciones-ad-hoc/"),
            {
                "reemplaza_a": tribunal_nomina["t4"].id,
                "designado_nro_socio": 999999,
                "acta_asamblea": "x",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_socio_no_designa(self, api_client, causal_expediente, causal_imputado):
        api_client.force_authenticate(causal_imputado.user)
        response = api_client.post(
            url(causal_expediente, "designaciones-ad-hoc/"), {}, format="json"
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_apartado_no_designa(
        self, api_client, causal_expediente, tribunal_nomina, make_legacy_socio
    ):
        causal_expediente.socios.add(tribunal_nomina["t4"], tribunal_nomina["s4"])
        designado = make_legacy_socio(90041, 4)
        api_client.force_authenticate(tribunal_nomina["t4"].user)
        response = api_client.post(
            url(causal_expediente, "designaciones-ad-hoc/"),
            {
                "reemplaza_a": tribunal_nomina["s4"].id,
                "designado_nro_socio": int(designado.legajo),
                "acta_asamblea": "Acta de Asamblea N° 3/2026",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestConstitucion:
    def test_tribunal_constituye(self, api_client, causal_expediente, tribunal_nomina):
        api_client.force_authenticate(tribunal_nomina["t4"].user)
        response = api_client.post(url(causal_expediente, "constituir/"))
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["constituida"] is True
        assert [s["condicion"] for s in response.data["asientos"]] == ["TITULAR"] * 3

        segunda = api_client.post(url(causal_expediente, "constituir/"))
        assert segunda.status_code == status.HTTP_409_CONFLICT
        apartamiento = api_client.post(
            url(causal_expediente, "apartamientos/"), {"fundamento": FUNDAMENTO}, format="json"
        )
        assert apartamiento.status_code == status.HTTP_409_CONFLICT

    def test_constitucion_con_observaciones(self, api_client, causal_expediente, tribunal_nomina):
        causal_expediente.socios.add(tribunal_nomina["t4"], tribunal_nomina["s4"])
        api_client.force_authenticate(tribunal_nomina["t5"].user)
        response = api_client.post(url(causal_expediente, "constituir/"))
        assert response.status_code == status.HTTP_409_CONFLICT
        assert len(response.data["observaciones"]) == 2
        assert not ComposicionTribunal.objects.exists()

    def test_comision_directiva_no_constituye(
        self, api_client, causal_expediente, tribunal_nomina, make_socio
    ):
        api_client.force_authenticate(make_socio(legajo="77004", role=Role.CD).user)
        response = api_client.post(url(causal_expediente, "constituir/"))
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_resolucion_sin_cuerpo_constituido(self, api_client, causal_expediente, causal_vocal):
        causal_expediente.estado = EstadoExpedienteEnum.ESPERA_RESOLUCION
        causal_expediente.save(update_fields=["estado"])
        api_client.force_authenticate(causal_vocal.user)
        response = api_client.post(
            f"/api/v1/expedientes/{causal_expediente.pk}/estado/",
            {"estado": EstadoExpedienteEnum.PENDIENTE_CORREOS, "motivo": "Resolución adoptada"},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Constituí el cuerpo" in str(response.data)
