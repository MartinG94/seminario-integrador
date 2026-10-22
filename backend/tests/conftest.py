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
    sub, _ = Subcomision.objects.get_or_create(name="Cómputos")
    return sub


@pytest.fixture(autouse=True)
def ensure_calendar_seeded(request):
    """Garantiza que el calendario y feriados institucionales canónicos estén sembrados."""
    if not request.node.get_closest_marker("django_db"):
        return
    try:
        from expedientes.models import Holiday

        if not Holiday.objects.exists():
            from importlib import import_module
            from types import SimpleNamespace

            from django.apps import apps
            from django.db import connection

            seed_0008 = import_module(
                "expedientes.migrations.0008_seed_calendario_2026"
            ).seed_calendario_2026
            import_0010 = import_module(
                "expedientes.migrations.0010_import_institutional_holidays"
            ).import_current_holidays

            editor = SimpleNamespace(connection=connection)
            seed_0008(apps, editor)
            import_0010(apps, editor)
    except Exception:
        pass


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


@pytest.fixture(scope="session")
def django_db_setup(django_db_setup, django_db_blocker):
    """Agrega el esquema externo sólo después de crear la base de pruebas."""
    from django.db import connection

    from tests.legacy_schema import (
        create_legacy_tables,
        create_seed_support_tables,
        drop_legacy_tables,
        drop_seed_support_tables,
    )

    with django_db_blocker.unblock():
        created = create_legacy_tables(connection)
        support_tables = create_seed_support_tables(connection)

    yield
    with django_db_blocker.unblock():
        drop_seed_support_tables(connection, support_tables)
        drop_legacy_tables(connection, created)
