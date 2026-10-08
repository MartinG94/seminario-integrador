"""Tests para los endpoints del tablero Kanban y transiciones de estado (S2-05)."""

import pytest
from rest_framework import status

from expedientes.models import CambioEstadoExpediente, EstadoExpedienteEnum, Expediente
from socios.models import Role


@pytest.fixture
def td_user(make_socio):
    return make_socio(legajo="10001", role=Role.TD)


@pytest.fixture
def socio_user(make_socio):
    return make_socio(legajo="10002", role=Role.SOCIO)


@pytest.fixture
def cd_user(make_socio):
    return make_socio(legajo="10003", role=Role.CD)


@pytest.fixture
def expediente_creado(db, socio_user):
    return Expediente.objects.create(
        numero="EXP-2026-001",
        socio=socio_user,
        motivo="Inasistencia a asamblea",
        puntos=-1.0,
        estado=EstadoExpedienteEnum.CREADO,
    )


@pytest.mark.django_db
class TestBoardExpedientesView:
    """Pruebas para GET /api/v1/expedientes/board/ (CA1 y CA2)."""

    def test_board_requiere_autenticacion(self, api_client):
        response = api_client.get("/api/v1/expedientes/board/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_socio_ordinario_no_puede_ver_board(self, api_client, authenticate, socio_user):
        client = authenticate(socio_user)
        response = client.get("/api/v1/expedientes/board/")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_td_puede_ver_board_con_seis_columnas(
        self, api_client, authenticate, td_user, expediente_creado
    ):
        client = authenticate(td_user)
        response = client.get("/api/v1/expedientes/board/")
        assert response.status_code == status.HTTP_200_OK

        data = response.data
        assert "columns" in data
        assert len(data["columns"]) == 6

        keys = [col["key"] for col in data["columns"]]
        assert keys == [
            EstadoExpedienteEnum.CREADO,
            EstadoExpedienteEnum.JUSTIFICANDO,
            EstadoExpedienteEnum.REVISION_RESOLUCION,
            EstadoExpedienteEnum.ESPERA_RESOLUCION,
            EstadoExpedienteEnum.PENDIENTE_CORREOS,
            EstadoExpedienteEnum.EMITIDO,
        ]

        # Verificar que el expediente creado está en la primera columna
        col_creado = data["columns"][0]
        assert len(col_creado["cases"]) == 1
        case = col_creado["cases"][0]
        assert case["numero"] == "EXP-2026-001"
        assert case["transiciones_permitidas"] == [EstadoExpedienteEnum.JUSTIFICANDO]

    def test_cd_puede_ver_board(self, api_client, authenticate, cd_user, expediente_creado):
        client = authenticate(cd_user)
        response = client.get("/api/v1/expedientes/board/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["columns"]) == 6

    def test_filtro_por_socio_legajo(
        self, api_client, authenticate, td_user, expediente_creado, make_socio
    ):
        otro_socio = make_socio(legajo="99999", role=Role.SOCIO)
        Expediente.objects.create(
            numero="EXP-2026-002",
            socio=otro_socio,
            motivo="Otro motivo",
            puntos=-2.0,
            estado=EstadoExpedienteEnum.CREADO,
        )

        client = authenticate(td_user)
        response = client.get("/api/v1/expedientes/board/?socio=10002")
        assert response.status_code == status.HTTP_200_OK
        col_creado = response.data["columns"][0]
        assert len(col_creado["cases"]) == 1
        assert col_creado["cases"][0]["numero"] == "EXP-2026-001"

    def test_filtro_por_estado(self, api_client, authenticate, td_user, expediente_creado):
        client = authenticate(td_user)
        response = client.get(
            f"/api/v1/expedientes/board/?estado={EstadoExpedienteEnum.JUSTIFICANDO}"
        )
        assert response.status_code == status.HTTP_200_OK
        # Todas las 6 columnas están presentes, pero CREADO no tendrá casos en el qs
        col_creado = response.data["columns"][0]
        assert len(col_creado["cases"]) == 0

    def test_filtro_por_rango_fechas(self, api_client, authenticate, td_user, expediente_creado):
        from django.utils import timezone

        yesterday = (timezone.localdate() - timezone.timedelta(days=1)).isoformat()
        tomorrow = (timezone.localdate() + timezone.timedelta(days=1)).isoformat()

        client = authenticate(td_user)
        # Rango que incluye hoy: debe devolver el expediente
        response = client.get(
            f"/api/v1/expedientes/board/?fecha_desde={yesterday}&fecha_hasta={tomorrow}"
        )
        assert response.status_code == status.HTTP_200_OK
        col_creado = response.data["columns"][0]
        assert len(col_creado["cases"]) == 1

        # Rango en el pasado que excluye hoy: no debe devolver el expediente
        response_excl = client.get(
            f"/api/v1/expedientes/board/?fecha_desde={yesterday}&fecha_hasta={yesterday}"
        )
        assert response_excl.status_code == status.HTTP_200_OK
        col_excl = response_excl.data["columns"][0]
        assert len(col_excl["cases"]) == 0

    def test_filtro_por_socio_implicado_m2m(
        self, api_client, authenticate, td_user, socio_user, make_socio
    ):
        socio_secundario = make_socio(legajo="55555", role=Role.SOCIO)
        exp = Expediente.objects.create(
            numero="EXP-2026-055",
            socio=socio_user,
            motivo="Causa colectiva",
            estado=EstadoExpedienteEnum.CREADO,
        )
        exp.socios.add(socio_secundario)

        client = authenticate(td_user)
        # Búsqueda por legajo del socio secundario en relación M2M
        response = client.get("/api/v1/expedientes/board/?socio=55555")
        assert response.status_code == status.HTTP_200_OK
        col_creado = response.data["columns"][0]
        numeros = [c["numero"] for c in col_creado["cases"]]
        assert "EXP-2026-055" in numeros
        assert col_creado["cases"][0]["cantidad_socios"] >= 1


@pytest.mark.django_db
class TestTransicionarExpedienteView:
    """Pruebas para POST /api/v1/expedientes/<pk>/transicionar/ (CA3)."""

    def test_transicionar_requiere_autenticacion(self, api_client, expediente_creado):
        response = api_client.post(
            f"/api/v1/expedientes/{expediente_creado.id}/transicionar/",
            {"to_status": EstadoExpedienteEnum.JUSTIFICANDO},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_socio_ordinario_no_puede_transicionar(
        self, api_client, authenticate, socio_user, expediente_creado
    ):
        client = authenticate(socio_user)
        response = client.post(
            f"/api/v1/expedientes/{expediente_creado.id}/transicionar/",
            {"to_status": EstadoExpedienteEnum.JUSTIFICANDO},
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_transicion_valida_creado_a_justificando(
        self, api_client, authenticate, td_user, expediente_creado
    ):
        client = authenticate(td_user)
        response = client.post(
            f"/api/v1/expedientes/{expediente_creado.id}/transicionar/",
            {
                "to_status": EstadoExpedienteEnum.JUSTIFICANDO,
                "justificacion": "Apertura formal de justificaciones",
            },
        )
        assert response.status_code == status.HTTP_200_OK

        expediente_creado.refresh_from_db()
        assert expediente_creado.estado == EstadoExpedienteEnum.JUSTIFICANDO

        # Verificar auditoría
        audit = CambioEstadoExpediente.objects.filter(expediente=expediente_creado).first()
        assert audit is not None
        assert audit.estado_anterior == EstadoExpedienteEnum.CREADO
        assert audit.estado_nuevo == EstadoExpedienteEnum.JUSTIFICANDO
        assert audit.actor == td_user.user.username
        assert audit.motivo == "Apertura formal de justificaciones"

    def test_transicion_invalida_salto_de_estado_rechazada(
        self, api_client, authenticate, td_user, expediente_creado
    ):
        client = authenticate(td_user)
        # Salto de creado a emitido no permitido
        response = client.post(
            f"/api/v1/expedientes/{expediente_creado.id}/transicionar/",
            {"to_status": EstadoExpedienteEnum.EMITIDO},
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert (
            "estado" in response.data or "to_status" in response.data or "detail" in response.data
        )

        expediente_creado.refresh_from_db()
        assert expediente_creado.estado == EstadoExpedienteEnum.CREADO

    def test_transicion_estado_final_emitido_no_permite_mas_transiciones(
        self, api_client, authenticate, td_user, socio_user
    ):
        expediente_emitido = Expediente.objects.create(
            numero="EXP-2026-999",
            socio=socio_user,
            motivo="Finalizado",
            estado=EstadoExpedienteEnum.EMITIDO,
        )
        client = authenticate(td_user)
        response = client.post(
            f"/api/v1/expedientes/{expediente_emitido.id}/transicionar/",
            {"to_status": EstadoExpedienteEnum.CREADO},
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        expediente_emitido.refresh_from_db()
        assert expediente_emitido.estado == EstadoExpedienteEnum.EMITIDO

    def test_expediente_no_encontrado(self, api_client, authenticate, td_user):
        client = authenticate(td_user)
        response = client.post(
            "/api/v1/expedientes/999999/transicionar/",
            {"to_status": EstadoExpedienteEnum.JUSTIFICANDO},
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND
