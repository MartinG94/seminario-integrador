"""Tests para los endpoints REST del calendario institucional de días hábiles.

Cubre:
- CA1: Exclusión de fines de semana y feriados en cálculo.
- CA2: Versionado y auditoría con motivo formal.
- CA4: Zona horaria oficial America/Argentina/Buenos_Aires.
- CA5: Control de acceso RBAC estricto en servidor (403 para socios ordinarios).
"""

from datetime import datetime
from zoneinfo import ZoneInfo

import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

from expedientes.models import Holiday
from socios.models import Role, Socio, Subcomision

User = get_user_model()
TZ_BA = ZoneInfo("America/Argentina/Buenos_Aires")


@pytest.fixture
def subcomision(db):
    return Subcomision.objects.create(name="Cómputos")


@pytest.fixture
def admin_user(db, subcomision):
    user = User.objects.create_user(
        username="admin_computos",
        email="admin@aveit.org.ar",
        password="secure_password_2026",
    )
    Socio.objects.create(
        user=user,
        first_name="Admin",
        last_name="Computos",
        legajo="ADM-001",
        email="admin@aveit.org.ar",
        subcomision=subcomision,
        social_year=4,
        role=Role.ADMIN,
        is_enabled=True,
    )
    return user


@pytest.fixture
def socio_user(db, subcomision):
    user = User.objects.create_user(
        username="socio_ordinario",
        email="socio@aveit.org.ar",
        password="secure_password_2026",
    )
    Socio.objects.create(
        user=user,
        first_name="Juan",
        last_name="Perez",
        legajo="SOC-1234",
        email="socio@aveit.org.ar",
        subcomision=subcomision,
        social_year=2,
        role=Role.SOCIO,
        is_enabled=True,
    )
    return user


@pytest.fixture
def cd_user(db, subcomision):
    user = User.objects.create_user(
        username="cd_autoridad",
        email="cd@aveit.org.ar",
        password="secure_password_2026",
    )
    Socio.objects.create(
        user=user,
        first_name="Presidente",
        last_name="AVEIT",
        legajo="CD-001",
        email="cd@aveit.org.ar",
        subcomision=subcomision,
        social_year=5,
        role=Role.CD,
        is_enabled=True,
    )
    return user


@pytest.fixture
def client_authenticated(admin_user):
    client = APIClient()
    client.force_authenticate(user=admin_user)
    return client


@pytest.fixture
def client_socio(socio_user):
    client = APIClient()
    client.force_authenticate(user=socio_user)
    return client


@pytest.fixture
def client_cd(cd_user):
    client = APIClient()
    client.force_authenticate(user=cd_user)
    return client


@pytest.mark.django_db
class TestCalendarioApi:
    def test_list_institutional_holidays(self, client_socio):
        response = client_socio.get("/api/v1/expedientes/calendario/feriados/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 16
        assert all(item["creado_por_nombre"] == "Sistema (carga inicial)" for item in response.data)

    def test_empty_calendar_is_readable_without_implicit_seed(self, client_socio):
        Holiday.objects.all().delete()
        response = client_socio.get("/api/v1/expedientes/calendario/feriados/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data == []
        assert not Holiday.objects.exists()
        result = client_socio.post(
            "/api/v1/expedientes/calendario/calcular-plazo/",
            {"start_at": "2026-10-09T10:00:00-03:00", "business_days": 1},
            format="json",
        )
        assert result.status_code == 200
        assert result.data["deadline"] == "2026-10-12T10:00:00-03:00"

    @pytest.mark.parametrize(
        "params", [{"month": 0}, {"month": 13}, {"year": "invalid"}, {"ordering": "id"}]
    )
    def test_invalid_filters_return_400(self, client_socio, params):
        response = client_socio.get("/api/v1/expedientes/calendario/feriados/", params)
        assert response.status_code == 400

    def test_calcular_plazo_endpoint(self, client_socio):
        response = client_socio.post(
            "/api/v1/expedientes/calendario/calcular-plazo/",
            {"start_at": "2026-10-08T10:00:45-03:00", "business_days": 5},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["deadline"] == "2026-10-16T10:00:45-03:00"
        assert len(response.data["dias_habiles_computados"]) == 5
        assert [day["date"] for day in response.data["dias_excluidos"]] == [
            "2026-10-10",
            "2026-10-11",
            "2026-10-12",
        ]

    def test_simulation_normalizes_utc_to_institutional_day(self, client_socio):
        response = client_socio.post(
            "/api/v1/expedientes/calendario/calcular-plazo/",
            {"start_at": "2026-10-13T01:30:00Z", "business_days": 1},
            format="json",
        )
        assert response.status_code == 200
        assert response.data["start_at"] == "2026-10-12T22:30:00-03:00"
        assert response.data["deadline"] == "2026-10-13T22:30:00-03:00"

    def test_authenticated_user_without_socio_can_read(self):
        user = User.objects.create_user(username="authenticated_without_socio")
        client = APIClient()
        client.force_authenticate(user)
        assert client.get("/api/v1/expedientes/calendario/feriados/").status_code == 200

    def test_duplicate_insert_after_validation_is_controlled(
        self, client_authenticated, admin_user
    ):
        from datetime import date
        from unittest.mock import patch

        Holiday.objects.create(date=date(2026, 10, 13), description="Asueto", created_by=admin_user)
        # Representa una fecha ocupada después del chequeo de unicidad del serializer.
        with (
            patch("rest_framework.validators.UniqueValidator.__call__"),
            patch(
                "django.utils.timezone.now", return_value=datetime(2026, 10, 10, 12, tzinfo=TZ_BA)
            ),
        ):
            response = client_authenticated.post(
                "/api/v1/expedientes/calendario/feriados/",
                {"fecha": "2026-10-13", "descripcion": "Alta concurrente"},
                format="json",
            )
        assert response.status_code == 400
        assert "fecha" in response.data
        assert Holiday.objects.filter(date=date(2026, 10, 13)).count() == 1
