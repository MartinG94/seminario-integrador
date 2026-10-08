"""Tests para los endpoints REST del calendario institucional de días hábiles.

Cubre:
- CA1: Exclusión de fines de semana y feriados en cálculo.
- CA2: Versionado y auditoría con motivo formal.
- CA4: Zona horaria oficial America/Argentina/Buenos_Aires.
- CA5: Control de acceso RBAC estricto en servidor (403 para socios ordinarios).
"""

from zoneinfo import ZoneInfo

import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

from expedientes.models import (
    CalendarioVersion,
    TipoFeriadoEnum,
)
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
    def test_list_versiones_authenticated(self, client_socio):
        """Cualquier usuario autenticado puede consultar las versiones de calendario."""
        response = client_socio.get("/api/v1/expedientes/calendario/versiones/")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1  # Versión 1 sembrada por migración

    def test_create_version_forbidden_for_socio(self, client_socio):
        """CA5: Un socio ordinario no puede crear una nueva versión de calendario (403)."""
        payload = {
            "nombre": "Nueva versión no autorizada",
            "vigencia_desde": "2026-11-01",
            "motivo_cambio": "Intento no autorizado",
        }
        response = client_socio.post(
            "/api/v1/expedientes/calendario/versiones/", payload, format="json"
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_version_allowed_for_admin_and_cd(self, client_authenticated, admin_user):
        """CA2/CA5: Administrador puede crear una nueva versión auditada de calendario."""
        payload = {
            "nombre": "Calendario AVEIT 2026 - Modificación Primavera",
            "vigencia_desde": "2026-09-21",
            "motivo_cambio": "Incorporación de asueto institucional por Día del Estudiante.",
            "activa": True,
            "clonar_de_version_id": 1,
            "feriados": [
                {
                    "fecha": "2026-09-21",
                    "descripcion": "Día del Estudiante / Asueto AVEIT",
                    "tipo": TipoFeriadoEnum.INSTITUCIONAL,
                    "es_laborable": False,
                }
            ],
        }
        response = client_authenticated.post(
            "/api/v1/expedientes/calendario/versiones/", payload, format="json"
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["version"] == 2
        assert data["nombre"] == payload["nombre"]
        assert data["activa"] is True
        assert data["feriados_count"] == 17  # 16 clonados + 1 nuevo

        # Verificar que la versión 1 fue desactivada
        v1 = CalendarioVersion.objects.get(version=1)
        assert v1.activa is False

    def test_get_version_detail_with_feriados(self, client_socio):
        """Detalle de versión incluye el listado completo de feriados."""
        response = client_socio.get("/api/v1/expedientes/calendario/versiones/1/")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["version"] == 1
        assert "feriados" in data
        assert len(data["feriados"]) >= 16

    def test_list_feriados_activos(self, client_socio):
        """Listar feriados de la versión activa."""
        response = client_socio.get("/api/v1/expedientes/calendario/feriados/")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 16

    def test_calcular_plazo_endpoint(self, client_socio):
        """CA1/CA4: Endpoint de cálculo de plazo devuelve fecha límite y desglose de exclusiones."""
        payload = {
            "start_at": "2026-10-08T10:00:00-03:00",
            "business_days": 5,
        }
        response = client_socio.post(
            "/api/v1/expedientes/calendario/calcular-plazo/", payload, format="json"
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "deadline" in data
        assert "dias_excluidos" in data
        assert "dias_habiles_computados" in data
        assert len(data["dias_habiles_computados"]) == 5

        # 08/10 (Jueves) + 5 días hábiles considerando 10/10 (Sáb), 11/10 (Dom) y 12/10 (Feriado)
        # -> Vence Viernes 16/10 a las 10:00 hs
        assert "2026-10-16T10:00:00" in data["deadline"]

        # Comprobar que en días excluidos figuran sábado, domingo y el feriado del 12/10
        excluded_dates = [d["date"] for d in data["dias_excluidos"]]
        assert "2026-10-10" in excluded_dates
        assert "2026-10-11" in excluded_dates
        assert "2026-10-12" in excluded_dates

    def test_add_feriado_as_admin_success(self, client_authenticated):
        """ADMIN puede registrar un nuevo feriado o excepción en la versión activa."""
        payload = {
            "fecha": "2026-11-09",
            "descripcion": "Feriado Visita del Papa",
            "tipo": "NACIONAL",
            "es_laborable": False,
        }
        response = client_authenticated.post(
            "/api/v1/expedientes/calendario/feriados/", payload, format="json"
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["fecha"] == "2026-11-09"
        assert data["descripcion"] == "Feriado Visita del Papa"
        assert data["tipo"] == "NACIONAL"
        assert data["es_laborable"] is False

    def test_add_feriado_duplicate_rejected(self, client_authenticated):
        """No se permite duplicar una fecha de feriado en la misma versión (400)."""
        payload = {
            "fecha": "2026-01-01",  # Ya existe en versión 1
            "descripcion": "Año Nuevo duplicado",
            "tipo": "NACIONAL",
            "es_laborable": False,
        }
        response = client_authenticated.post(
            "/api/v1/expedientes/calendario/feriados/", payload, format="json"
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "fecha" in response.json()

    def test_add_feriado_forbidden_for_socio(self, client_socio):
        """Un socio ordinario no puede agregar feriados ni excepciones (403)."""
        payload = {
            "fecha": "2026-11-10",
            "descripcion": "Feriado no autorizado",
            "tipo": "ASUETO",
            "es_laborable": False,
        }
        response = client_socio.post(
            "/api/v1/expedientes/calendario/feriados/", payload, format="json"
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
