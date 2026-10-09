"""Tests para el clasificador de urgencia en expedientes (SCRUM-78 / S3-07).

Cubre:
1. Atributo `urgencia` en Expediente con valores Baja, Normal, Urgente (default Normal).
2. Apertura mediante ExpedienteWorkflowService con urgencia.
3. Exposición en BoardExpedienteSerializer y ExpedienteListSerializer.
4. Filtrado en ExpedienteFilter y BoardExpedientesView.
5. Actualización de urgencia vía PATCH protegido para integrantes del TD.
"""

import pytest
from rest_framework import status

from expedientes.models import (
    EstadoExpedienteEnum,
    Expediente,
    UrgenciaExpedienteEnum,
)
from expedientes.serializers import BoardExpedienteSerializer, ExpedienteListSerializer
from expedientes.services.workflow_service import ExpedienteWorkflowService
from socios.models import Role


@pytest.fixture
def td_socio(make_socio):
    """Socio con rol TD."""
    return make_socio(legajo="11239", role=Role.TD, email="td_giuliano@aveit.test")


@pytest.fixture
def regular_socio(make_socio):
    """Socio ordinario sin facultades de TD."""
    return make_socio(legajo="12999", role=Role.SOCIO, email="socio_juan@aveit.test")


@pytest.mark.django_db
class TestExpedienteUrgenciaModel:
    """Pruebas unitarias de dominio y persistencia para urgencia."""

    def test_default_urgencia_is_normal(self, regular_socio):
        exp = Expediente.objects.create(
            numero="EXP-101/2026",
            socio=regular_socio,
            motivo="Causa general",
            estado=EstadoExpedienteEnum.CREADO,
        )
        assert exp.urgencia == UrgenciaExpedienteEnum.NORMAL
        assert exp.get_urgencia_display() == "Normal"

    def test_explicit_urgencia_values_accepted(self, regular_socio):
        exp_baja = Expediente.objects.create(
            numero="EXP-102/2026",
            socio=regular_socio,
            motivo="Causa leve",
            urgencia=UrgenciaExpedienteEnum.BAJA,
        )
        exp_urgente = Expediente.objects.create(
            numero="EXP-103/2026",
            socio=regular_socio,
            motivo="Causa grave institucional",
            urgencia=UrgenciaExpedienteEnum.URGENTE,
        )
        assert exp_baja.urgencia == "baja"
        assert exp_baja.get_urgencia_display() == "Baja"
        assert exp_urgente.urgencia == "urgente"
        assert exp_urgente.get_urgencia_display() == "Urgente"

    def test_workflow_service_open_expediente_with_urgencia(self, regular_socio):
        exp = ExpedienteWorkflowService.open_expediente(
            motivo="Apertura con urgencia crítica",
            socio_ids=[regular_socio.pk],
            actor="SOLICITANTE_CD",
            urgencia=UrgenciaExpedienteEnum.URGENTE,
        )
        assert exp.urgencia == UrgenciaExpedienteEnum.URGENTE

        exp_default = ExpedienteWorkflowService.open_expediente(
            motivo="Apertura estándar",
            socio_ids=[regular_socio.pk],
            actor="SOLICITANTE_CD",
        )
        assert exp_default.urgencia == UrgenciaExpedienteEnum.NORMAL


@pytest.mark.django_db
class TestExpedienteUrgenciaSerializers:
    """Pruebas de serialización de urgencia para listado y tablero."""

    def test_board_serializer_exposes_urgencia(self, regular_socio):
        exp = Expediente.objects.create(
            numero="EXP-201/2026",
            socio=regular_socio,
            motivo="Prueba serializer",
            urgencia=UrgenciaExpedienteEnum.URGENTE,
        )
        data = BoardExpedienteSerializer(exp).data
        assert "urgencia" in data
        assert data["urgencia"] == "urgente"
        assert data["urgencia_display"] == "Urgente"

    def test_list_serializer_exposes_urgencia(self, regular_socio):
        exp = Expediente.objects.create(
            numero="EXP-202/2026",
            socio=regular_socio,
            motivo="Prueba serializer list",
            urgencia=UrgenciaExpedienteEnum.BAJA,
        )
        data = ExpedienteListSerializer(exp).data
        assert "urgencia" in data
        assert data["urgencia"] == "baja"
        assert data["urgencia_display"] == "Baja"


@pytest.mark.django_db
class TestExpedienteUrgenciaApi:
    """Pruebas de endpoints para filtrado y actualización de urgencia."""

    def test_board_filtering_by_urgencia(self, td_socio, regular_socio, authenticate):
        Expediente.objects.create(
            numero="EXP-301/2026",
            socio=regular_socio,
            motivo="Causa normal",
            urgencia=UrgenciaExpedienteEnum.NORMAL,
        )
        Expediente.objects.create(
            numero="EXP-302/2026",
            socio=regular_socio,
            motivo="Causa urgente",
            urgencia=UrgenciaExpedienteEnum.URGENTE,
        )

        client = authenticate(td_socio)
        response = client.get("/api/v1/expedientes/board/?urgencia=urgente")
        assert response.status_code == status.HTTP_200_OK

        columns = response.data["columns"]
        all_cases = [c for col in columns for c in col["cases"]]
        numeros = [c["numero"] for c in all_cases]
        assert "EXP-302/2026" in numeros
        assert "EXP-301/2026" not in numeros

    def test_patch_urgencia_authorized_td(self, td_socio, regular_socio, authenticate):
        exp = Expediente.objects.create(
            numero="EXP-401/2026",
            socio=regular_socio,
            motivo="Causa inicial normal",
            urgencia=UrgenciaExpedienteEnum.NORMAL,
        )

        client = authenticate(td_socio)
        response = client.patch(
            f"/api/v1/expedientes/{exp.id}/",
            {"urgencia": "urgente"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["urgencia"] == "urgente"
        assert response.data["urgencia_display"] == "Urgente"

        exp.refresh_from_db()
        assert exp.urgencia == UrgenciaExpedienteEnum.URGENTE

    def test_patch_urgencia_forbidden_for_regular_socio(self, regular_socio, authenticate):
        exp = Expediente.objects.create(
            numero="EXP-402/2026",
            socio=regular_socio,
            motivo="Causa",
            urgencia=UrgenciaExpedienteEnum.NORMAL,
        )

        client = authenticate(regular_socio)
        response = client.patch(
            f"/api/v1/expedientes/{exp.id}/",
            {"urgencia": "urgente"},
            format="json",
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_patch_urgencia_invalid_choice_rejected(self, td_socio, regular_socio, authenticate):
        exp = Expediente.objects.create(
            numero="EXP-403/2026",
            socio=regular_socio,
            motivo="Causa",
            urgencia=UrgenciaExpedienteEnum.NORMAL,
        )

        client = authenticate(td_socio)
        response = client.patch(
            f"/api/v1/expedientes/{exp.id}/",
            {"urgencia": "critica_maxima"},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "urgencia" in response.data
