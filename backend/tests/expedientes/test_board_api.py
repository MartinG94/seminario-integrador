"""Tests para los endpoints del tablero Kanban y transiciones de estado (S2-05)."""

import pytest
from rest_framework import status

from expedientes.models import (
    CambioEstadoExpediente,
    EstadoExpedienteEnum,
    Expediente,
    SolicitudT01,
)
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
        self, api_client, authenticate, td_user, socio_user, expediente_creado
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
        assert case["cantidad_socios"] == 1
        assert "socios" in case
        assert len(case["socios"]) == 1
        assert case["socios"][0]["id"] == socio_user.id
        assert case["socios"][0]["legajo"] == "10002"
        assert case["titulo"] == "Inasistencia a asamblea"
        assert case["motivo"] == "Inasistencia a asamblea"
        assert case["razon"] == "Inasistencia a asamblea"
        assert case["creador"] == ""

    def test_board_con_multiples_socios_involucrados(
        self, api_client, authenticate, td_user, make_socio
    ):
        socio_1 = make_socio(legajo="20001", role=Role.SOCIO)
        socio_2 = make_socio(legajo="20002", role=Role.SOCIO)
        exp = Expediente.objects.create(
            numero="EXP-2026-099",
            socio=socio_1,
            motivo="Expediente grupal",
            puntos=-2.0,
            estado=EstadoExpedienteEnum.CREADO,
        )
        exp.socios.set([socio_1, socio_2])

        client = authenticate(td_user)
        response = client.get("/api/v1/expedientes/board/")
        assert response.status_code == status.HTTP_200_OK

        col_creado = response.data["columns"][0]
        case = next(c for c in col_creado["cases"] if c["numero"] == "EXP-2026-099")
        assert case["cantidad_socios"] == 2
        assert len(case["socios"]) == 2
        legajos = [s["legajo"] for s in case["socios"]]
        assert "20001" in legajos
        assert "20002" in legajos
        for s in case["socios"]:
            assert "id" in s
            assert "legajo" in s
            assert "nombre" in s
            assert "grupo" in s
            assert str(s["grupo"]).isdigit()
            assert s["estado"] in ("Activo", "Pasivo", "Inactivo")

    def test_board_con_solicitud_t01_creador_razon_titulo(
        self, api_client, authenticate, td_user, make_socio
    ):
        solicitante = make_socio(legajo="74907", role=Role.CD)
        solicitante.first_name = "Lucas"
        solicitante.last_name = "Gastiaburu"
        solicitante.save(update_fields=["first_name", "last_name"])

        involucrado_1 = make_socio(legajo="85194", role=Role.SOCIO)
        involucrado_1.first_name = "Lucas"
        involucrado_1.last_name = "Guillén"
        involucrado_1.save(update_fields=["first_name", "last_name"])

        involucrado_2 = make_socio(legajo="87414", role=Role.SOCIO)
        involucrado_2.first_name = "Diego"
        involucrado_2.last_name = "Sánchez"
        involucrado_2.save(update_fields=["first_name", "last_name"])

        exp = Expediente.objects.create(
            numero="EXP-2026-101",
            socio=involucrado_1,
            motivo="Motivo base del expediente",
            puntos=-1.5,
            estado=EstadoExpedienteEnum.CREADO,
        )
        exp.socios.set([involucrado_1, involucrado_2])

        SolicitudT01.objects.create(
            solicitante=solicitante,
            destinatarios_socios_ids=[involucrado_1.id, involucrado_2.id],
            tipo_accion=SolicitudT01.TipoAccion.SANCTION,
            titulo="Inconducta grave en asamblea",
            motivo="Motivo expresado en T01",
            razon="Violación del Art. 14 del Estatuto Social",
            puntos=-1.5,
            expediente=exp,
        )

        client = authenticate(td_user)
        response = client.get("/api/v1/expedientes/board/")
        assert response.status_code == status.HTTP_200_OK

        col_creado = response.data["columns"][0]
        case = next(c for c in col_creado["cases"] if c["numero"] == "EXP-2026-101")
        assert case["creador"] == "Gastiaburu, Lucas (74907)"
        assert case["titulo"] == "Inconducta grave en asamblea"
        assert case["razon"] == "Violación del Art. 14 del Estatuto Social"
        assert case["cantidad_socios"] == 2
        assert len(case["socios"]) == 2

        # Verificar filtrado por creador y título en ?socio=
        resp_creador = client.get("/api/v1/expedientes/board/?socio=Gastiaburu")
        assert resp_creador.status_code == status.HTTP_200_OK
        assert len(resp_creador.data["columns"][0]["cases"]) == 1

        resp_titulo = client.get("/api/v1/expedientes/board/?socio=Inconducta")
        assert resp_titulo.status_code == status.HTTP_200_OK
        assert len(resp_titulo.data["columns"][0]["cases"]) == 1

    def test_board_creador_fallback_cambios_estado(
        self, api_client, authenticate, td_user, make_socio
    ):
        autoridad = make_socio(legajo="99001", role=Role.TD)
        autoridad.first_name = "Autoridad"
        autoridad.last_name = "Tribunal"
        autoridad.save(update_fields=["first_name", "last_name"])

        involucrado = make_socio(legajo="99002", role=Role.SOCIO)

        exp = Expediente.objects.create(
            numero="EXP-2026-102",
            socio=involucrado,
            motivo="Apertura por oficio",
            puntos=-1.0,
            estado=EstadoExpedienteEnum.CREADO,
        )
        CambioEstadoExpediente.objects.create(
            expediente=exp,
            estado_anterior=EstadoExpedienteEnum.CREADO,
            estado_nuevo=EstadoExpedienteEnum.CREADO,
            actor=f"SOLICITANTE_{autoridad.legajo}",
            motivo="Apertura inicial",
        )

        client = authenticate(td_user)
        response = client.get("/api/v1/expedientes/board/")
        assert response.status_code == status.HTTP_200_OK

        col_creado = response.data["columns"][0]
        case = next(c for c in col_creado["cases"] if c["numero"] == "EXP-2026-102")
        assert case["creador"] == "Tribunal, Autoridad (99001)"
        assert case["titulo"] == "Apertura por oficio"
        assert case["razon"] == "Apertura por oficio"

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
