"""Pruebas de integración para el endpoint seguro de detalle de expediente (CA4).

Valida:
- GET /api/v1/expedientes/{id}/
- 401 Unauthorized para usuarios anónimos (sin JWT).
- 403 Forbidden para socios ordinarios ajenos a la causa.
- 200 OK para el socio imputado titular de la causa.
- 200 OK para autoridades del Tribunal de Disciplina (TD), Directiva (CD) o Administrador.
- 404 Not Found para expedientes inexistentes.
"""

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from expedientes.models import EstadoExpedienteEnum, Expediente
from socios.models import Role, Socio, Subcomision


@pytest.fixture
def subcomision_test(db) -> Subcomision:
    return Subcomision.objects.create(name="Subcomisión de Cómputos")


@pytest.fixture
def socio_imputado(db, subcomision_test, django_user_model) -> Socio:
    user = django_user_model.objects.create_user(
        username="74301",
        email="socio.imputado@aveit.utn.edu.ar",
        password="Test-Password-2026!",
    )
    return Socio.objects.create(
        user=user,
        legajo="74301",
        first_name="Martín",
        last_name="Guillén",
        email="socio.imputado@aveit.utn.edu.ar",
        subcomision=subcomision_test,
        social_year=3,
        role=Role.SOCIO,
        is_enabled=True,
    )


@pytest.fixture
def socio_ajeno(db, subcomision_test, django_user_model) -> Socio:
    user = django_user_model.objects.create_user(
        username="74302",
        email="ajeno@aveit.utn.edu.ar",
        password="Test-Password-2026!",
    )
    return Socio.objects.create(
        user=user,
        legajo="74302",
        first_name="Lucas",
        last_name="Alvarez",
        email="ajeno@aveit.utn.edu.ar",
        subcomision=subcomision_test,
        social_year=2,
        role=Role.SOCIO,
        is_enabled=True,
    )


@pytest.fixture
def vocal_td(db, subcomision_test, django_user_model) -> Socio:
    user = django_user_model.objects.create_user(
        username="74303",
        email="vocal.td@aveit.utn.edu.ar",
        password="Test-Password-2026!",
    )
    return Socio.objects.create(
        user=user,
        legajo="74303",
        first_name="Valeria",
        last_name="Gómez",
        email="vocal.td@aveit.utn.edu.ar",
        subcomision=subcomision_test,
        social_year=4,
        role=Role.TD,
        is_enabled=True,
    )


@pytest.fixture
def directiva_cd(db, subcomision_test, django_user_model) -> Socio:
    user = django_user_model.objects.create_user(
        username="74304",
        email="cd@aveit.utn.edu.ar",
        password="Test-Password-2026!",
    )
    return Socio.objects.create(
        user=user,
        legajo="74304",
        first_name="Diego",
        last_name="Pérez",
        email="cd@aveit.utn.edu.ar",
        subcomision=subcomision_test,
        social_year=5,
        role=Role.CD,
        is_enabled=True,
    )


@pytest.fixture
def expediente_caso(db, socio_imputado) -> Expediente:
    return Expediente.objects.create(
        numero="EXP-2026-0888",
        socio=socio_imputado,
        motivo="Inasistencia injustificada a reuniones plenarias",
        puntos=-1.0,
        estado=EstadoExpedienteEnum.JUSTIFICANDO,
    )


@pytest.mark.django_db
class TestExpedienteDetailAPI:
    """Pruebas del endpoint GET /api/v1/expedientes/<id>/ con protección RBAC."""

    def test_api_detail_anonymous_unauthorized_401(self, expediente_caso) -> None:
        client = APIClient()
        url = f"/api/v1/expedientes/{expediente_caso.id}/"
        response = client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_api_detail_imputado_authorized_200(self, socio_imputado, expediente_caso) -> None:
        client = APIClient()
        client.force_authenticate(user=socio_imputado.user)

        url = f"/api/v1/expedientes/{expediente_caso.id}/"
        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == expediente_caso.id
        assert data["numero"] == "EXP-2026-0888"
        assert data["estado"] == "justificando"
        assert data["socio_legajo"] == "74301"

    def test_api_detail_other_socio_forbidden_403(self, socio_ajeno, expediente_caso) -> None:
        client = APIClient()
        client.force_authenticate(user=socio_ajeno.user)

        url = f"/api/v1/expedientes/{expediente_caso.id}/"
        response = client.get(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_api_detail_td_authorized_200(self, vocal_td, expediente_caso) -> None:
        client = APIClient()
        client.force_authenticate(user=vocal_td.user)

        url = f"/api/v1/expedientes/{expediente_caso.id}/"
        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["numero"] == "EXP-2026-0888"

    def test_api_detail_cd_authorized_200(self, directiva_cd, expediente_caso) -> None:
        client = APIClient()
        client.force_authenticate(user=directiva_cd.user)

        url = f"/api/v1/expedientes/{expediente_caso.id}/"
        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["numero"] == "EXP-2026-0888"

    def test_api_detail_not_found_404(self, vocal_td) -> None:
        client = APIClient()
        client.force_authenticate(user=vocal_td.user)

        url = "/api/v1/expedientes/99999/"
        response = client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND
