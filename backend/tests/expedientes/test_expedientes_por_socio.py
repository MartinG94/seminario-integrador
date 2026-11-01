"""Pruebas para el endpoint público/autenticado GET /api/v1/expedientes/por-socio/ (Milestone 2).

Cubre:
- R2.1: Requerimiento de autenticación (401 para usuarios anónimos).
- R2.2: Validación de parámetro 'legajo' (400 si falta o está en blanco).
- R2.3: Consulta permitida para socio regular (Role.SOCIO con 200 OK).
- R2.4: Aislamiento estricto: /gestion/ sigue respondiendo 403 para Role.SOCIO.
- R2.5: Serializador acotado (ExpedienteResumenSerializer) con campos autorizados.
- R2.6: Manejo de socios sin expedientes (retorna lista vacía [] con 200 OK).
- R2.7: Ordenamiento por fecha de creación descendente (-created_at).
- R2.8: Coincidencia tanto para socio titular como para socios implicados.
"""

from decimal import Decimal

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from expedientes.models import (
    EstadoExpedienteEnum,
    Expediente,
    SolicitudT01,
    UrgenciaExpedienteEnum,
)
from socios.models import Role


@pytest.mark.django_db
class TestExpedientesPorSocioEndpoint:
    """Suite de integración para el endpoint GET /api/v1/expedientes/por-socio/."""

    def test_unauthenticated_request_returns_401(self, api_client: APIClient) -> None:
        """Petición anónima debe ser rechazada con HTTP 401 Unauthorized."""
        response = api_client.get("/api/v1/expedientes/por-socio/?legajo=74907")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_missing_legajo_returns_400(self, make_socio, authenticate) -> None:
        """Omitir el query param 'legajo' responde HTTP 400 Bad Request."""
        socio = make_socio(legajo="74907", role=Role.SOCIO)
        client = authenticate(socio)

        response = client.get("/api/v1/expedientes/por-socio/")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "error" in response.json()
        assert "legajo" in response.json()["error"].lower()

    def test_empty_or_whitespace_legajo_returns_400(self, make_socio, authenticate) -> None:
        """Enviar un legajo vacío o solo con espacios responde HTTP 400 Bad Request."""
        socio = make_socio(legajo="74907", role=Role.SOCIO)
        client = authenticate(socio)

        response = client.get("/api/v1/expedientes/por-socio/?legajo=   ")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "error" in response.json()

    def test_regular_socio_can_query_expedientes_returns_200(
        self, make_socio, authenticate
    ) -> None:
        """Un usuario con rol estándar (Role.SOCIO) puede consultar expedientes por legajo."""
        socio_consultor = make_socio(legajo="74907", role=Role.SOCIO)
        socio_imputado = make_socio(legajo="85123", role=Role.SOCIO)

        exp = Expediente.objects.create(
            numero="EXP-2026-001",
            socio=socio_imputado,
            motivo="Incumplimiento de tareas asignadas en subcomisión",
            puntos=Decimal("-2.00"),
            estado=EstadoExpedienteEnum.CREADO,
            urgencia=UrgenciaExpedienteEnum.NORMAL,
        )

        client = authenticate(socio_consultor)
        response = client.get(f"/api/v1/expedientes/por-socio/?legajo={socio_imputado.legajo}")
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == exp.id
        assert data[0]["numero"] == "EXP-2026-001"
        assert data[0]["motivo"] == "Incumplimiento de tareas asignadas en subcomisión"
        assert Decimal(str(data[0]["puntos"])) == Decimal("-2.00")
        assert data[0]["estado"] == EstadoExpedienteEnum.CREADO
        assert data[0]["urgencia"] == UrgenciaExpedienteEnum.NORMAL
        assert data[0]["urgencia_display"] == "Normal"

    def test_gestion_endpoint_still_forbids_regular_socio_403(
        self, make_socio, authenticate
    ) -> None:
        """Verifica el aislamiento de seguridad: /gestion/ sigue bloqueado para Role.SOCIO."""
        socio = make_socio(legajo="74907", role=Role.SOCIO)
        client = authenticate(socio)

        response = client.get(f"/api/v1/expedientes/gestion/?legajo={socio.legajo}")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_scoped_serializer_fields_and_no_confidential_leak(
        self, make_socio, authenticate
    ) -> None:
        """Garantiza que la respuesta contenga estrictamente los campos autorizados del contrato."""
        socio = make_socio(legajo="74907", role=Role.SOCIO)
        exp = Expediente.objects.create(
            numero="EXP-2026-002",
            socio=socio,
            motivo="Demora en entrega de informe",
            puntos=Decimal("-1.00"),
            estado=EstadoExpedienteEnum.JUSTIFICANDO,
            urgencia=UrgenciaExpedienteEnum.URGENTE,
        )

        client = authenticate(socio)
        response = client.get(f"/api/v1/expedientes/por-socio/?legajo={socio.legajo}")
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert len(data) == 1
        item = data[0]
        assert item["id"] == exp.id

        expected_fields = {
            "id",
            "numero",
            "titulo",
            "motivo",
            "puntos",
            "estado",
            "urgencia",
            "urgencia_display",
            "created_at",
        }
        assert set(item.keys()) == expected_fields

        # Campos internos confidenciales prohibidos para consulta pública
        forbidden_fields = [
            "historial",
            "evidencias",
            "descargos",
            "votos",
            "decisiones",
            "solicitante",
            "creador",
            "socios",
        ]
        for field in forbidden_fields:
            assert field not in item

    def test_socio_without_expedientes_returns_empty_list(self, make_socio, authenticate) -> None:
        """Consultar un legajo sin expedientes responde HTTP 200 con lista vacía []."""
        socio = make_socio(legajo="74907", role=Role.SOCIO)
        client = authenticate(socio)

        response = client.get("/api/v1/expedientes/por-socio/?legajo=99999")
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []

    def test_ordering_newest_first(self, make_socio, authenticate) -> None:
        """Los expedientes se ordenan por fecha de creación más reciente primero (-created_at)."""
        socio = make_socio(legajo="74907", role=Role.SOCIO)
        exp1 = Expediente.objects.create(
            numero="EXP-2026-010",
            socio=socio,
            motivo="Primer caso",
        )
        exp2 = Expediente.objects.create(
            numero="EXP-2026-020",
            socio=socio,
            motivo="Segundo caso posterior",
        )

        client = authenticate(socio)
        response = client.get(f"/api/v1/expedientes/por-socio/?legajo={socio.legajo}")
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert len(data) == 2
        # El segundo creado debe figurar primero
        assert data[0]["id"] == exp2.id
        assert data[1]["id"] == exp1.id

    def test_matches_socio_as_implicado_in_m2m(self, make_socio, authenticate) -> None:
        """Captura expedientes donde el legajo corresponde a un socio implicado adicional."""
        socio_principal = make_socio(legajo="74001", role=Role.SOCIO)
        socio_implicado = make_socio(legajo="74002", role=Role.SOCIO)

        exp = Expediente.objects.create(
            numero="EXP-2026-050",
            socio=socio_principal,
            motivo="Infracción colectiva",
        )
        exp.socios.add(socio_implicado)

        client = authenticate(socio_implicado)
        response = client.get(f"/api/v1/expedientes/por-socio/?legajo={socio_implicado.legajo}")
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == exp.id

    def test_titulo_derived_from_solicitud_t01_or_fallback(self, make_socio, authenticate) -> None:
        """El campo 'titulo' utiliza el título de la Solicitud T01 o hace fallback a motivo."""
        autoridad = make_socio(legajo="61001", role=Role.CD)
        socio = make_socio(legajo="74907", role=Role.SOCIO)

        exp_con_t01 = Expediente.objects.create(
            numero="EXP-2026-090",
            socio=socio,
            motivo="Motivo fallback de respaldo",
        )
        SolicitudT01.objects.create(
            expediente=exp_con_t01,
            solicitante=autoridad,
            destinatario_socio_id=socio.id,
            destinatarios_socios_ids=[socio.id],
            titulo="Título descriptivo de Solicitud T01",
            motivo="Motivo T01",
            tipo_accion=SolicitudT01.TipoAccion.SANCTION,
            puntos=Decimal("-1.00"),
            estado=SolicitudT01.Estado.ISSUED,
        )

        exp_sin_t01 = Expediente.objects.create(
            numero="EXP-2026-091",
            socio=socio,
            motivo="Motivo directo sin solicitud T01",
        )

        client = authenticate(socio)
        response = client.get(f"/api/v1/expedientes/por-socio/?legajo={socio.legajo}")
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        items_by_id = {item["id"]: item for item in data}
        assert items_by_id[exp_con_t01.id]["titulo"] == "Título descriptivo de Solicitud T01"
        assert items_by_id[exp_sin_t01.id]["titulo"] == "Motivo directo sin solicitud T01"
