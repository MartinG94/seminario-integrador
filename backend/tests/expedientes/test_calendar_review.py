"""Regresiones observables de la revisión del PO del PR #49."""

from datetime import datetime
from datetime import timezone as dt_timezone
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from expedientes.models import CalendarioVersion
from socios.models import Role, Socio

URL = "/api/v1/expedientes/calendario/feriados/"
CALCULATE_URL = "/api/v1/expedientes/calendario/calcular-plazo/"
NOW = datetime(2026, 10, 10, 15, tzinfo=dt_timezone.utc)


@pytest.fixture
def calendar_client(db):
    user = get_user_model().objects.create_user(username="calendar_admin")
    Socio.objects.create(
        user=user,
        first_name="Ana",
        last_name="Pérez",
        legajo="CAL-01",
        email="calendar@example.test",
        social_year=4,
        role=Role.ADMIN,
    )
    client = APIClient()
    client.force_authenticate(user)
    return client, user


@pytest.mark.django_db
class TestCalendarReview:
    @pytest.mark.parametrize("role", [Role.SOCIO, Role.TD, Role.CD, Role.ADMIN])
    def test_any_authenticated_role_can_read(self, calendar_client, role):
        client, user = calendar_client
        user.socio.role = role
        user.socio.save()
        response = client.get(URL)
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        assert len(response.json()) >= 16

    def test_anonymous_cannot_read(self):
        assert APIClient().get(URL).status_code == 401

    @pytest.mark.parametrize("role", [Role.ADMIN, Role.CD, Role.TD])
    def test_create_without_type_records_server_audit(self, calendar_client, role):
        client, user = calendar_client
        user.socio.role = role
        user.socio.save()
        with patch("django.utils.timezone.now", return_value=NOW):
            response = client.post(
                URL,
                {
                    "fecha": "2026-10-13",
                    "descripcion": "Asueto institucional",
                    "creado_por": 99999,
                    "created_at": "2000-01-01T00:00:00Z",
                },
                format="json",
            )
        assert response.status_code == 201, response.data
        data = response.json()
        assert data["creado_por"] == user.pk
        assert "Ana Pérez" in data["creado_por_nombre"]
        assert datetime.fromisoformat(data["created_at"].replace("Z", "+00:00")) == NOW
        assert not {"tipo", "es_laborable", "calendario_version"} & data.keys()
        listed = client.get(URL).json()
        assert next(item for item in listed if item["id"] == data["id"]) == data

    def test_socio_cannot_create(self, calendar_client):
        client, user = calendar_client
        user.socio.role = Role.SOCIO
        user.socio.save()
        response = client.post(URL, {"fecha": "2026-10-13", "descripcion": "Asueto"}, format="json")
        assert response.status_code == 403

    @pytest.mark.parametrize("date_value, expected", [("2026-10-09", 400), ("2026-10-10", 201)])
    def test_retroactive_boundary(self, calendar_client, date_value, expected):
        client, _ = calendar_client
        with patch("django.utils.timezone.now", return_value=NOW):
            response = client.post(
                URL, {"fecha": date_value, "descripcion": "Asueto"}, format="json"
            )
        assert response.status_code == expected, response.data
        if expected == 400:
            assert "fecha" in response.data

    def test_today_uses_institutional_date_near_utc_midnight(self, calendar_client):
        client, _ = calendar_client
        midnight = datetime(2026, 10, 11, 0, 30, tzinfo=dt_timezone.utc)
        with patch("django.utils.timezone.now", return_value=midnight):
            response = client.post(
                URL, {"fecha": "2026-10-10", "descripcion": "Asueto"}, format="json"
            )
        assert response.status_code == 201

    def test_duplicate_date_is_rejected(self, calendar_client):
        client, _ = calendar_client
        payload = {"fecha": "2026-10-13", "descripcion": "Asueto"}
        with patch("django.utils.timezone.now", return_value=NOW):
            assert client.post(URL, payload, format="json").status_code == 201
            response = client.post(URL, payload, format="json")
        assert response.status_code == 400
        assert "fecha" in response.data

    def test_create_does_not_require_initialized_versions(self, calendar_client):
        client, _ = calendar_client
        CalendarioVersion.objects.all().delete()
        assert client.get(URL).status_code == 200
        with patch("django.utils.timezone.now", return_value=NOW):
            response = client.post(
                URL, {"fecha": "2026-10-13", "descripcion": "Asueto"}, format="json"
            )
        assert response.status_code == 201

    def test_new_holiday_immediately_changes_simulation(self, calendar_client):
        client, _ = calendar_client
        payload = {"start_at": "2026-10-12T14:30:45-03:00", "business_days": 1}
        assert client.post(CALCULATE_URL, payload, format="json").json()["deadline"] == (
            "2026-10-13T14:30:45-03:00"
        )
        with patch("django.utils.timezone.now", return_value=NOW):
            assert (
                client.post(
                    URL, {"fecha": "2026-10-13", "descripcion": "Asueto nuevo"}, format="json"
                ).status_code
                == 201
            )
        response = client.post(CALCULATE_URL, payload, format="json")
        assert response.status_code == 200
        assert response.data["deadline"] == "2026-10-14T14:30:45-03:00"
        assert response.data["dias_excluidos"] == [
            {"date": "2026-10-13", "reason": "Feriado: Asueto nuevo"}
        ]
        assert "calendario_version" not in response.data

    def test_filters_only_year_month_and_date_order(self, calendar_client):
        client, _ = calendar_client
        response = client.get(URL, {"year": 2026, "month": 2, "ordering": "-fecha"})
        assert response.status_code == 200
        assert [item["fecha"] for item in response.data] == ["2026-02-17", "2026-02-16"]

    def test_version_creation_is_no_longer_available(self, calendar_client):
        client, _ = calendar_client
        assert client.post("/api/v1/expedientes/calendario/versiones/", {}).status_code == 404
