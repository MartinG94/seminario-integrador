"""Pruebas unitarias e integración de la API de Reportes e Indicadores (SCRUM-63)."""

from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from expedientes.models import (
    ClasificacionExpedienteEnum,
    EstadoExpedienteEnum,
    Expediente,
)
from socios.models import Role, Socio, Subcomision

User = get_user_model()


@pytest.fixture
def auth_client():
    user = User.objects.create_user(
        username="td_tester",
        email="td@aveit.org.ar",
        password="password123",
    )
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def base_subcomision():
    sub, _ = Subcomision.objects.get_or_create(
        name="Gestión Social y Ambiental",
        defaults={"description": "GSA"},
    )
    return sub


@pytest.fixture
def sample_socio(base_subcomision):
    user = User.objects.create_user(
        username="11779",
        email="diego@aveit.org.ar",
        first_name="Diego Gabriel",
        last_name="Sanchez Turu Michel",
    )
    socio, _ = Socio.objects.get_or_create(
        legajo="87414",
        defaults={
            "user": user,
            "first_name": "Diego Gabriel",
            "last_name": "Sanchez Turu Michel",
            "email": "diego@aveit.org.ar",
            "subcomision": base_subcomision,
            "social_year": 6,
            "role": Role.SOCIO,
            "is_enabled": True,
        },
    )
    return socio


@pytest.fixture
def sample_expediente(sample_socio):
    exp = Expediente.objects.create(
        numero="EXP-TEST-001/2026",
        socio=sample_socio,
        motivo="Reconocimiento por participación destacada en eventos",
        puntos=Decimal("2.00"),
        estado=EstadoExpedienteEnum.EMITIDO,
        clasificacion=ClasificacionExpedienteEnum.GSA,
    )
    return exp


@pytest.mark.django_db
class TestReportesAPI:
    """Verifica los endpoints analíticos de la pantalla de Reportes."""

    def test_reportes_t01_metrics(self, auth_client, sample_expediente):
        url = reverse("expedientes:reportes-t01")
        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        data = response.data

        assert "kpis" in data
        assert "tiempo_vida_promedio_dias" in data["kpis"]
        assert data["kpis"]["tiempo_vida_promedio_dias"] >= 0

        assert "expedientes_por_clasificacion" in data
        assert isinstance(data["expedientes_por_clasificacion"], list)
        assert len(data["expedientes_por_clasificacion"]) > 0

        assert "distribucion_por_grupo" in data
        assert "distribucion_puntos" in data

    def test_reportes_reuniones_metrics(self, auth_client):
        url = reverse("expedientes:reportes-reuniones")
        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        data = response.data

        assert "kpis" in data
        assert "expedientes_por_categoria" in data
        assert "proporcion_aprobacion" in data
        assert "socios_por_grupo" in data

    def test_reportes_subcomisiones_list(self, auth_client, base_subcomision):
        url = reverse("expedientes:reportes-subcomisiones")
        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)
        nombres = [s["nombre"] for s in response.data]
        assert base_subcomision.name in nombres

    def test_reportes_subcomision_detail_and_intra_inter(
        self, auth_client, base_subcomision, sample_expediente
    ):
        url = reverse("expedientes:reportes-subcomision")
        response = auth_client.get(f"{url}?subcomision_id={base_subcomision.id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.data

        assert "subcomision" in data
        assert data["subcomision"]["id"] == base_subcomision.id

        assert "intra_vs_inter" in data
        assert len(data["intra_vs_inter"]) == 2
        # Gráfico de barras acordado: Intra vs Inter
        tipos = [b["tipo"] for b in data["intra_vs_inter"]]
        assert any("Intra-Subcomisión" in t for t in tipos)
        assert any("Inter-Subcomisiones" in t for t in tipos)

        assert "tabla_socios" in data
        assert isinstance(data["tabla_socios"], list)
        assert len(data["tabla_socios"]) > 0

    def test_reportes_historico_records_highscores(self, auth_client):
        url = reverse("expedientes:reportes-historico-records")
        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        data = response.data

        assert "record_absoluto" in data
        rec = data["record_absoluto"]
        # Récord Histórico de Diego Sánchez #11779 con 25 pts
        assert rec["socio_numero"] == 11779
        assert rec["puntaje_maximo"] == 25.0
        assert "Diego" in rec["nombre_completo"]

        assert "top_historico" in data
        assert len(data["top_historico"]) >= 5
        assert data["top_historico"][0]["socio_numero"] == 11779

        assert "serie_anual" in data
        assert "distribucion_historica_puntos" in data

    def test_patch_expediente_clasificacion(self, auth_client, sample_expediente):
        url = reverse(
            "expedientes:expediente-clasificacion-patch",
            kwargs={"pk": sample_expediente.pk},
        )
        response = auth_client.patch(url, {"clasificacion": "CD"}, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["clasificacion"] == "CD"

        sample_expediente.refresh_from_db()
        assert sample_expediente.clasificacion == ClasificacionExpedienteEnum.CD

    def test_patch_expediente_clasificacion_invalida(self, auth_client, sample_expediente):
        url = reverse(
            "expedientes:expediente-clasificacion-patch",
            kwargs={"pk": sample_expediente.pk},
        )
        response = auth_client.patch(
            url, {"clasificacion": "CLASIFICACION_INEXISTENTE"}, format="json"
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
