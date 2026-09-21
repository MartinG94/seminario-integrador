import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from socios.models import Role, Socio, Subcomision

UserModel = get_user_model()

VALID_PASSWORD = "Aveit-Test-2026!"


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture
def subcomision(db) -> Subcomision:
    return Subcomision.objects.create(name="Cómputos")


@pytest.fixture
def make_socio(db, subcomision):
    """Crea un Socio con sus credenciales. `legajo` se usa como username."""

    def _make(
        legajo: str = "74907",
        role: str = Role.SOCIO,
        social_year: int = 2,
        is_enabled: bool = True,
        password: str = VALID_PASSWORD,
        email: str | None = None,
    ) -> Socio:
        email = email or f"socio{legajo}@aveit.test"
        user = UserModel.objects.create_user(username=legajo, email=email, password=password)
        return Socio.objects.create(
            user=user,
            legajo=legajo,
            first_name="Nombre",
            last_name=f"Apellido{legajo}",
            email=email,
            subcomision=subcomision,
            social_year=social_year,
            role=role,
            is_enabled=is_enabled,
        )

    return _make


@pytest.fixture
def authenticate(api_client):
    """Devuelve un cliente con el Bearer token de un login real."""

    def _authenticate(socio: Socio, password: str = VALID_PASSWORD) -> APIClient:
        response = api_client.post(
            "/api/v1/auth/login/",
            {"identifier": socio.legajo, "password": password},
            format="json",
        )
        assert response.status_code == 200, response.data
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")
        return api_client

    return _authenticate
