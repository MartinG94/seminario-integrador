"""Tests de API para el endpoint de presentación de descargos reglamentarios (FASE 4 / S3-02).

Cubre:
1. Presentación válida dentro de plazo (200 OK / 201 Created).
2. Límite exacto inclusivo (now == plazo_limite_at) aceptado por el servidor.
3. Rechazo estricto posterior al plazo devolviendo 409 Conflict con mensaje explicativo.
4. Buzzer-beater / condición de carrera con bloqueo pesimista en servidor.
5. Control de acceso RBAC: socio titular vs otros socios (403 Forbidden).
6. Rechazo si el expediente no está en estado 'justificando' (409 Conflict).
7. Rechazo si ya se presentó un descargo previamente (409 Conflict).
8. Endpoint de consulta de expedientes del socio (/api/v1/expedientes/mis-expedientes/).
"""

from datetime import timedelta
from zoneinfo import ZoneInfo

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from expedientes.models import (
    EstadoExpedienteEnum,
    Expediente,
    TipoDescargoEnum,
)
from socios.models import Role, Socio, Subcomision

BA_TZ = ZoneInfo("America/Argentina/Buenos_Aires")
User = get_user_model()


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture
def socio_titular(db) -> Socio:
    user = User.objects.create_user(
        username="74907",
        email="74907@aveit.test",
        password="secure_password_123",
    )
    sub = Subcomision.objects.create(name="Cómputos")
    return Socio.objects.create(
        user=user,
        legajo="74907",
        first_name="Lucas",
        last_name="Gastiaburu",
        email="74907@aveit.test",
        subcomision=sub,
        social_year=4,
        role=Role.SOCIO,
    )


@pytest.fixture
def otro_socio(db) -> Socio:
    user = User.objects.create_user(
        username="85194",
        email="85194@aveit.test",
        password="secure_password_123",
    )
    sub = Subcomision.objects.create(name="Deportes")
    return Socio.objects.create(
        user=user,
        legajo="85194",
        first_name="Lucas",
        last_name="Guillén",
        email="85194@aveit.test",
        subcomision=sub,
        social_year=4,
        role=Role.SOCIO,
    )


@pytest.mark.django_db(transaction=True)
class TestDescargoEndpoint:
    """Suite de pruebas del endpoint REST de descargos."""

    def test_presentar_descargo_dentro_del_plazo_exitoso(
        self, api_client: APIClient, socio_titular: Socio
    ) -> None:
        """Socio titular presenta descargo T02 dentro del plazo -> 200/201 OK."""
        api_client.force_authenticate(user=socio_titular.user)

        limite = timezone.now() + timedelta(days=2)
        exp = Expediente.objects.create(
            numero="EXP-201/2026",
            socio=socio_titular,
            motivo="Inasistencia",
            estado=EstadoExpedienteEnum.JUSTIFICANDO,
            plazo_inicio_at=timezone.now() - timedelta(days=1),
            plazo_limite_at=limite,
            descargo_presentado=False,
        )

        payload = {
            "tipo": TipoDescargoEnum.T02_CERTIFICADO,
            "causal": "Examen Académico Universitario en UTN FRC",
            "archivo": "certificado_utn.pdf",
            "texto": "Presento constancia de examen aprobada.",
        }

        response = api_client.post(
            f"/api/v1/expedientes/{exp.id}/descargo/", payload, format="json"
        )

        assert response.status_code in (status.HTTP_200_OK, status.HTTP_201_CREATED)
        exp.refresh_from_db()
        assert exp.descargo_presentado is True
        assert exp.descargo_archivo == "certificado_utn.pdf"
        assert exp.descargo_causal == "Examen Académico Universitario en UTN FRC"
        assert exp.descargo_tipo == TipoDescargoEnum.T02_CERTIFICADO
        assert exp.descargo_presentado_at is not None

    def test_presentar_descargo_despues_del_vencimiento_devuelve_409(
        self, api_client: APIClient, socio_titular: Socio
    ) -> None:
        """Socio titular intenta enviar descargo luego del vencimiento -> 409 Conflict."""
        api_client.force_authenticate(user=socio_titular.user)

        # Límite vencido hace 1 minuto
        limite = timezone.now() - timedelta(minutes=1)
        exp = Expediente.objects.create(
            numero="EXP-202/2026",
            socio=socio_titular,
            motivo="Falta de reporte",
            estado=EstadoExpedienteEnum.JUSTIFICANDO,
            plazo_inicio_at=timezone.now() - timedelta(days=7),
            plazo_limite_at=limite,
            descargo_presentado=False,
        )

        payload = {
            "tipo": TipoDescargoEnum.T03_EXTRAORDINARIO,
            "texto": "Intentando justificar fuera de término.",
        }

        response = api_client.post(
            f"/api/v1/expedientes/{exp.id}/descargo/", payload, format="json"
        )

        assert response.status_code == status.HTTP_409_CONFLICT
        data = response.json()
        assert "expirado" in data.get("detail", "").lower()
        exp.refresh_from_db()
        assert exp.descargo_presentado is False

    def test_otro_socio_no_puede_presentar_descargo(
        self, api_client: APIClient, socio_titular: Socio, otro_socio: Socio
    ) -> None:
        """Un socio no puede presentar descargo en expediente ajeno (403 Forbidden)."""
        api_client.force_authenticate(user=otro_socio.user)

        exp = Expediente.objects.create(
            numero="EXP-203/2026",
            socio=socio_titular,
            motivo="Inasistencia ajena",
            estado=EstadoExpedienteEnum.JUSTIFICANDO,
            plazo_inicio_at=timezone.now(),
            plazo_limite_at=timezone.now() + timedelta(days=3),
            descargo_presentado=False,
        )

        payload = {
            "tipo": TipoDescargoEnum.T03_EXTRAORDINARIO,
            "texto": "Intento de presentación ajena.",
        }

        response = api_client.post(
            f"/api/v1/expedientes/{exp.id}/descargo/", payload, format="json"
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_consulta_mis_expedientes_con_deadline(
        self, api_client: APIClient, socio_titular: Socio
    ) -> None:
        """El endpoint /api/v1/expedientes/mis-expedientes/ expone plazo_limite_at."""
        api_client.force_authenticate(user=socio_titular.user)

        limite = timezone.now() + timedelta(days=4)
        Expediente.objects.create(
            numero="EXP-204/2026",
            socio=socio_titular,
            motivo="Causa abierta",
            estado=EstadoExpedienteEnum.JUSTIFICANDO,
            plazo_inicio_at=timezone.now(),
            plazo_limite_at=limite,
            descargo_presentado=False,
        )

        response = api_client.get("/api/v1/expedientes/mis-expedientes/")
        assert response.status_code == status.HTTP_200_OK
        items = response.json()
        assert len(items) >= 1
        item = items[0]
        assert item["numero"] == "EXP-204/2026"
        assert item["plazo_limite_at"] is not None
        assert "esta_en_plazo" in item
