"""Tests unitarios para el endpoint de salud /api/health/."""

from unittest.mock import patch

from django.db import OperationalError
from django.test import SimpleTestCase
from rest_framework.test import APIClient


class TestHealthCheckEndpoint(SimpleTestCase):
    """Pruebas de verificación de conectividad y resiliencia del endpoint de salud."""

    def setUp(self) -> None:
        """Inicializar cliente de prueba para la API."""
        self.client = APIClient()
        self.url = "/api/health/"

    @patch("django.db.connection.ensure_connection")
    def test_health_check_success(self, mock_ensure_connection) -> None:
        """Validar retorno HTTP 200 cuando la base de datos responde operativamente."""
        mock_ensure_connection.return_value = None

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok", "db": "connected"})
        mock_ensure_connection.assert_called_once()

    @patch("django.db.connection.ensure_connection")
    def test_health_check_db_failure_returns_503(self, mock_ensure_connection) -> None:
        """Validar retorno HTTP 503 cuando la base de datos se encuentra caída o inaccesible."""
        mock_ensure_connection.side_effect = OperationalError("Can't connect to MySQL server")

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 503)
        data = response.json()
        self.assertEqual(data["status"], "error")
        self.assertIn("Can't connect to MySQL server", data["db"])
        mock_ensure_connection.assert_called_once()
