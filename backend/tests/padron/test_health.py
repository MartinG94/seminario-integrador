"""Tests de API para el endpoint de observabilidad y healthcheck del padrón institucional.

Cobertura:
  - GET /api/v1/padron/health/ (CA5, H04, MED-003, MED-IT2-001):
    - Acceso público irrestricto sin autenticación JWT ([AllowAny], authentication_classes=[]).
    - HEALTHY -> HTTP 200 OK.
    - DEGRADED -> HTTP 200 OK.
    - UNAVAILABLE -> HTTP 503 Service Unavailable.
    - Métodos no permitidos -> HTTP 405 Method Not Allowed.

Referencia: spec.md §RF-PADRON-05, plan.md §5, tasks.md T5.5.
"""

from unittest.mock import MagicMock, patch

from rest_framework import status
from rest_framework.test import APIClient

from padron.domain import HealthStatusDTO


def _make_health_dto(status_code_str: str, latency_ms: float = 25.0) -> HealthStatusDTO:
    """Helper para construir DTOs de salud para mocks."""
    return HealthStatusDTO(
        status=status_code_str,
        latency_ms=latency_ms,
        source="mysql_institutional",
        record_count=515 if status_code_str == "HEALTHY" else 0,
        last_checked_at="2026-09-22T12:00:00Z",
        message="Diagnóstico de prueba.",
    )


class TestPadronHealthEndpoint:
    """Pruebas para el endpoint /api/v1/padron/health/."""

    def setup_method(self) -> None:
        self.client = APIClient()
        self.url = "/api/v1/padron/health/"

    @patch("padron.views.get_padron_repository")
    def test_public_access_no_auth_required(self, mock_get_repo) -> None:
        """Sondas de infraestructura acceden sin credenciales ni tokens JWT (MED-IT2-001)."""
        mock_repo = MagicMock()
        mock_repo.check_health.return_value = _make_health_dto("HEALTHY")
        mock_get_repo.return_value = mock_repo

        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert response.status_code != status.HTTP_401_UNAUTHORIZED

    @patch("padron.views.get_padron_repository")
    def test_healthy_status_returns_200(self, mock_get_repo) -> None:
        """Estado HEALTHY responde HTTP 200 con los 6 campos canónicos."""
        mock_repo = MagicMock()
        mock_repo.check_health.return_value = _make_health_dto("HEALTHY", latency_ms=15.2)
        mock_get_repo.return_value = mock_repo

        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["status"] == "HEALTHY"
        assert data["latency_ms"] == 15.2
        assert data["source"] == "mysql_institutional"
        assert data["record_count"] == 515
        assert "last_checked_at" in data
        assert "message" in data

    @patch("padron.views.get_padron_repository")
    def test_degraded_status_returns_200(self, mock_get_repo) -> None:
        """Estado DEGRADED responde HTTP 200 alertando latencia o conteo 0 (CA5 / MED-003)."""
        mock_repo = MagicMock()
        mock_repo.check_health.return_value = _make_health_dto("DEGRADED", latency_ms=650.0)
        mock_get_repo.return_value = mock_repo

        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["status"] == "DEGRADED"
        assert data["latency_ms"] == 650.0

    @patch("padron.views.get_padron_repository")
    def test_unavailable_status_returns_503(self, mock_get_repo) -> None:
        """Estado UNAVAILABLE responde HTTP 503 Service Unavailable (CA5 / MED-003)."""
        mock_repo = MagicMock()
        mock_repo.check_health.return_value = _make_health_dto("UNAVAILABLE", latency_ms=3500.0)
        mock_get_repo.return_value = mock_repo

        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

        data = response.json()
        assert data["status"] == "UNAVAILABLE"
        assert data["latency_ms"] == 3500.0

    def test_disallowed_methods_return_405(self) -> None:
        """Métodos de mutación POST, PUT, DELETE son rechazados con HTTP 405."""
        for method in ("post", "put", "patch", "delete"):
            caller = getattr(self.client, method)
            response = caller(self.url)
            assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
