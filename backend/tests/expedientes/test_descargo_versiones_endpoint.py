"""Historial de versiones del descargo por API (SCRUM-49 / S3-05, tarea T8).

``GET /api/v1/expedientes/<id>/descargo/versiones/``:
- Anónimo 401; socio ajeno a la causa 403; expediente inexistente 404.
- El socio imputado ve únicamente sus propias versiones; TD, CD y ADMIN ven las de todos.
- Respuesta ordenada por número, con operación, contenido, evidencias (sin binario) y actor.
"""

from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework import status

from expedientes.models import (
    EstadoExpedienteEnum,
    EvidenciaDescargo,
    Expediente,
    TipoDescargoEnum,
)
from socios.models import Role

T03 = TipoDescargoEnum.T03_EXTRAORDINARIO


@pytest.fixture
def titular(make_socio):
    return make_socio(legajo="74907")


@pytest.fixture
def coimputado(make_socio):
    return make_socio(legajo="85194")


@pytest.fixture
def expediente(titular, coimputado):
    exp = Expediente.objects.create(
        numero="EXP-701/2026",
        socio=titular,
        motivo="Historial de versiones",
        estado=EstadoExpedienteEnum.JUSTIFICANDO,
        plazo_inicio_at=timezone.now() - timedelta(days=1),
        plazo_limite_at=timezone.now() + timedelta(days=3),
    )
    exp.socios.add(titular, coimputado)
    return exp


def _post_descargo(client, user, expediente, **payload) -> None:
    client.force_authenticate(user=user)
    response = client.post(
        f"/api/v1/expedientes/{expediente.id}/descargo/", {"tipo": T03, **payload}, format="json"
    )
    assert response.status_code in (status.HTTP_200_OK, status.HTTP_201_CREATED)


def _get_versiones(client, user, expediente):
    if user is not None:
        client.force_authenticate(user=user)
    return client.get(f"/api/v1/expedientes/{expediente.id}/descargo/versiones/")


@pytest.mark.django_db(transaction=True)
class TestHistorialDeVersiones:
    def test_titular_ve_sus_versiones_ordenadas_con_el_contenido(
        self, api_client, titular, expediente
    ) -> None:
        _post_descargo(api_client, titular.user, expediente, texto="Texto v1.", causal="Otro")
        _post_descargo(api_client, titular.user, expediente, texto="Texto v2.")
        api_client.delete(f"/api/v1/expedientes/{expediente.id}/descargo/")

        response = _get_versiones(api_client, titular.user, expediente)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert [(v["numero"], v["operacion"]) for v in data] == [
            (1, "PRESENTADO"),
            (2, "CORREGIDO"),
            (3, "RETIRADO"),
        ]
        assert data[0]["texto"] == "Texto v1."
        assert data[0]["causal"] == "Otro"
        assert data[0]["tipo"] == T03
        assert data[0]["actor"] == "SOCIO_74907"
        assert data[0]["socio_legajo"] == "74907"
        assert data[0]["operacion_display"] == "Descargo presentado"
        assert data[0]["created_at"]

    def test_incluye_metadatos_de_evidencias_sin_el_contenido_binario(
        self, api_client, titular, expediente
    ) -> None:
        evidencia = EvidenciaDescargo.objects.create(
            expediente=expediente,
            socio=titular,
            contenido_blob=b"%PDF-1.4 secreto",
            nombre_original="prueba.pdf",
            extension=".pdf",
            mime_type="application/pdf",
            tamanio_bytes=16,
            sha256_hash="c" * 64,
        )
        _post_descargo(
            api_client,
            titular.user,
            expediente,
            texto="Con prueba.",
            evidencia_ids=[str(evidencia.id)],
        )

        data = _get_versiones(api_client, titular.user, expediente).json()

        assert [e["nombre_original"] for e in data[0]["evidencias"]] == ["prueba.pdf"]
        assert "contenido_blob" not in data[0]["evidencias"][0]
        assert "secreto" not in str(data)

    def test_socio_imputado_solo_ve_sus_propias_versiones(
        self, api_client, titular, coimputado, expediente
    ) -> None:
        _post_descargo(api_client, titular.user, expediente, texto="Del titular.")
        _post_descargo(api_client, coimputado.user, expediente, texto="Del coimputado.")

        data = _get_versiones(api_client, coimputado.user, expediente).json()

        assert [v["texto"] for v in data] == ["Del coimputado."]

    @pytest.mark.parametrize("rol", [Role.TD, Role.CD, Role.ADMIN])
    def test_autoridades_ven_las_versiones_de_todos_los_socios(
        self, api_client, make_socio, titular, coimputado, expediente, rol
    ) -> None:
        _post_descargo(api_client, titular.user, expediente, texto="Del titular.")
        _post_descargo(api_client, coimputado.user, expediente, texto="Del coimputado.")
        autoridad = make_socio(legajo="80001", role=rol)

        data = _get_versiones(api_client, autoridad.user, expediente).json()

        assert sorted(v["texto"] for v in data) == ["Del coimputado.", "Del titular."]

    def test_anonimo_recibe_401(self, api_client, expediente) -> None:
        response = _get_versiones(api_client, None, expediente)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_socio_ajeno_a_la_causa_recibe_403(self, api_client, make_socio, expediente) -> None:
        ajeno = make_socio(legajo="99999")

        response = _get_versiones(api_client, ajeno.user, expediente)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_expediente_inexistente_devuelve_404(self, api_client, titular) -> None:
        api_client.force_authenticate(user=titular.user)

        response = api_client.get("/api/v1/expedientes/999999/descargo/versiones/")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_sin_descargos_devuelve_lista_vacia(self, api_client, titular, expediente) -> None:
        response = _get_versiones(api_client, titular.user, expediente)

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []
