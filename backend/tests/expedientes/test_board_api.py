"""Tests para los endpoints del tablero Kanban y transiciones de estado (S2-05)."""

from datetime import timedelta
from decimal import Decimal

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone
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
        assert case["reglamento_asociado"] == "Reglamento Procesal Disciplinario 2026"
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
        assert case["reglamento_asociado"] == "Reglamento Procesal Disciplinario 2026"

    def test_board_reglamento_asociado_custom_y_fallback(
        self, api_client, authenticate, td_user, make_socio
    ):
        socio = make_socio(legajo="30001", role=Role.SOCIO)
        exp_con_causal = Expediente.objects.create(
            numero="EXP-2026-301",
            socio=socio,
            motivo="Causa con causal específica",
            puntos=-1.0,
            estado=EstadoExpedienteEnum.CREADO,
        )
        SolicitudT01.objects.create(
            solicitante=td_user,
            destinatarios_socios_ids=[socio.id],
            tipo_accion=SolicitudT01.TipoAccion.SANCTION,
            causal="Reglamento Interno de Becas y Ayudas 2025",
            expediente=exp_con_causal,
        )

        client = authenticate(td_user)
        response = client.get("/api/v1/expedientes/board/")
        assert response.status_code == status.HTTP_200_OK

        col = response.data["columns"][0]
        case_causal = next(c for c in col["cases"] if c["numero"] == "EXP-2026-301")
        assert case_causal["reglamento_asociado"] == "Reglamento Interno de Becas y Ayudas 2025"

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

    @pytest.mark.parametrize("texto", ["0007/2026", "plenaria"])
    def test_busqueda_de_antecedentes_solo_entre_causas_emitidas(
        self, api_client, authenticate, td_user, socio_user, texto
    ):
        """S4-03, RF-15: estado emitido más palabras clave sobre número o motivo (S-8)."""
        Expediente.objects.create(
            numero="EXP-0007/2026",
            socio=socio_user,
            motivo="Inasistencia a la reunión plenaria",
            estado=EstadoExpedienteEnum.EMITIDO,
        )
        Expediente.objects.create(
            numero="EXP-0008/2026",
            socio=socio_user,
            motivo="Daño al mobiliario de la sede",
            estado=EstadoExpedienteEnum.EMITIDO,
        )
        Expediente.objects.create(
            numero="EXP-1007/2026",
            socio=socio_user,
            motivo="Inasistencia a la reunión plenaria de octubre",
            estado=EstadoExpedienteEnum.REVISION_RESOLUCION,
        )

        client = authenticate(td_user)
        response = client.get(
            "/api/v1/expedientes/board/",
            {"estado": EstadoExpedienteEnum.EMITIDO, "socio": texto},
        )

        assert response.status_code == status.HTTP_200_OK
        cases = [case for column in response.data["columns"] for case in column["cases"]]
        assert [case["numero"] for case in cases] == ["EXP-0007/2026"]

    def test_board_preview_limit_caps_cases_and_preserves_totals_and_ordering(
        self, api_client, authenticate, td_user, socio_user
    ):
        """Valida /board/?preview_limit=2 con total_count, has_more y orden -created_at,-id."""
        base_time = timezone.now() - timedelta(days=5)
        emitidos = []
        for idx in range(5):
            exp = Expediente.objects.create(
                numero=f"EXP-EM-{idx:03d}/2026",
                socio=socio_user,
                motivo=f"Emitido {idx}",
                estado=EstadoExpedienteEnum.EMITIDO,
            )
            Expediente.objects.filter(pk=exp.id).update(
                created_at=base_time + timedelta(minutes=idx)
            )
            emitidos.append(exp)

        creados = []
        for idx in range(3):
            exp = Expediente.objects.create(
                numero=f"EXP-CR-{idx:03d}/2026",
                socio=socio_user,
                motivo=f"Creado {idx}",
                estado=EstadoExpedienteEnum.CREADO,
            )
            Expediente.objects.filter(pk=exp.id).update(
                created_at=base_time + timedelta(minutes=10)
            )
            creados.append(exp)

        justif = Expediente.objects.create(
            numero="EXP-JU-000/2026",
            socio=socio_user,
            motivo="Unico justificando",
            estado=EstadoExpedienteEnum.JUSTIFICANDO,
        )

        client = authenticate(td_user)
        response = client.get("/api/v1/expedientes/board/?preview_limit=2")
        assert response.status_code == status.HTTP_200_OK

        cols = {col["key"]: col for col in response.data["columns"]}
        assert len(cols) == 6

        assert cols[EstadoExpedienteEnum.EMITIDO]["total_count"] == 5
        assert cols[EstadoExpedienteEnum.EMITIDO]["has_more"] is True
        assert [c["id"] for c in cols[EstadoExpedienteEnum.EMITIDO]["cases"]] == [
            emitidos[4].id,
            emitidos[3].id,
        ]

        assert cols[EstadoExpedienteEnum.CREADO]["total_count"] == 3
        assert cols[EstadoExpedienteEnum.CREADO]["has_more"] is True
        # Mismo created_at: desempate determinístico por -id
        assert [c["id"] for c in cols[EstadoExpedienteEnum.CREADO]["cases"]] == [
            creados[2].id,
            creados[1].id,
        ]

        assert cols[EstadoExpedienteEnum.JUSTIFICANDO]["total_count"] == 1
        assert cols[EstadoExpedienteEnum.JUSTIFICANDO]["has_more"] is False
        assert [c["id"] for c in cols[EstadoExpedienteEnum.JUSTIFICANDO]["cases"]] == [justif.id]

        assert cols[EstadoExpedienteEnum.ESPERA_RESOLUCION]["total_count"] == 0
        assert cols[EstadoExpedienteEnum.ESPERA_RESOLUCION]["has_more"] is False
        assert cols[EstadoExpedienteEnum.ESPERA_RESOLUCION]["cases"] == []

        # Sin preview_limit preserva comportamiento histórico completo
        full_response = client.get("/api/v1/expedientes/board/")
        assert full_response.status_code == status.HTTP_200_OK
        full_cols = {col["key"]: col for col in full_response.data["columns"]}
        assert len(full_cols[EstadoExpedienteEnum.EMITIDO]["cases"]) == 5
        assert full_cols[EstadoExpedienteEnum.EMITIDO]["total_count"] == 5
        assert full_cols[EstadoExpedienteEnum.EMITIDO]["has_more"] is False

    def test_board_preview_limit_respects_filters_and_m2m_distinct_counts(
        self, api_client, authenticate, td_user, socio_user, make_socio
    ):
        """Asegura que total_count use DISTINCT sobre M2M socios y respete filtros activos."""
        co_socio = make_socio(legajo="55888", role=Role.SOCIO)
        other_socio = make_socio(legajo="55999", role=Role.SOCIO)

        for idx in range(3):
            exp = Expediente.objects.create(
                numero=f"EXP-M2M-{idx:03d}/2026",
                socio=socio_user,
                motivo="Causa colectiva",
                estado=EstadoExpedienteEnum.EMITIDO,
            )
            exp.socios.add(socio_user, co_socio)

        Expediente.objects.create(
            numero="EXP-OTRO-001/2026",
            socio=other_socio,
            motivo="No debe contar",
            estado=EstadoExpedienteEnum.EMITIDO,
        )

        client = authenticate(td_user)
        response = client.get("/api/v1/expedientes/board/?socio=55888&preview_limit=1")
        assert response.status_code == status.HTTP_200_OK
        cols = {col["key"]: col for col in response.data["columns"]}
        assert cols[EstadoExpedienteEnum.EMITIDO]["total_count"] == 3
        assert cols[EstadoExpedienteEnum.EMITIDO]["has_more"] is True
        assert len(cols[EstadoExpedienteEnum.EMITIDO]["cases"]) == 1

    @pytest.mark.parametrize("raw_limit", ["0", "-2", "51", "abc"])
    def test_board_preview_limit_invalido_retorna_400(
        self, api_client, authenticate, td_user, raw_limit
    ):
        client = authenticate(td_user)
        response = client.get(f"/api/v1/expedientes/board/?preview_limit={raw_limit}")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_board_preview_limit_mantiene_queries_acotadas_con_muchos_emitidos(
        self, api_client, authenticate, td_user, socio_user
    ):
        """Evita hidratar miles de emitidos en RAM/ORM cuando preview_limit está activo."""
        for idx in range(20):
            Expediente.objects.create(
                numero=f"EXP-VOL-{idx:03d}/2026",
                socio=socio_user,
                motivo=f"Emitido masivo {idx}",
                estado=EstadoExpedienteEnum.EMITIDO,
            )

        client = authenticate(td_user)
        with CaptureQueriesContext(connection) as ctx:
            response = client.get("/api/v1/expedientes/board/?preview_limit=2")

        assert response.status_code == status.HTTP_200_OK
        assert len(ctx) <= 18
        cols = {col["key"]: col for col in response.data["columns"]}
        assert len(cols[EstadoExpedienteEnum.EMITIDO]["cases"]) == 2
        assert cols[EstadoExpedienteEnum.EMITIDO]["total_count"] == 20
        assert cols[EstadoExpedienteEnum.EMITIDO]["has_more"] is True

    def test_board_cards_expose_es_llamado_and_es_felicitacion(
        self, api_client, authenticate, td_user, socio_user
    ):
        """BoardExpedienteSerializer expone es_llamado y es_felicitacion con ±0.25, T01 y ±0.33."""
        e_llamado = Expediente.objects.create(
            numero="EXP-B-LL-1/2026",
            socio=socio_user,
            motivo="Llamado canon",
            puntos=Decimal("-0.25"),
            estado=EstadoExpedienteEnum.CREADO,
        )
        e_felic_t01 = Expediente.objects.create(
            numero="EXP-B-FE-2/2026",
            socio=socio_user,
            motivo="Felicitacion T01",
            puntos=Decimal("0.00"),
            estado=EstadoExpedienteEnum.CREADO,
        )
        SolicitudT01.objects.create(
            solicitante=td_user,
            destinatarios_socios_ids=[socio_user.id],
            tipo_accion=SolicitudT01.TipoAccion.MERIT,
            puntaje_especial=SolicitudT01.PuntajeEspecial.FELICITACION,
            puntos=Decimal("0.25"),
            causal="Mérito destacado",
            expediente=e_felic_t01,
        )
        e_hist = Expediente.objects.create(
            numero="EXP-B-LL-3/2026",
            socio=socio_user,
            motivo="Llamado histórico",
            puntos=Decimal("-0.33"),
            estado=EstadoExpedienteEnum.CREADO,
        )
        e_std = Expediente.objects.create(
            numero="EXP-B-STD-4/2026",
            socio=socio_user,
            motivo="Puntos estándar",
            puntos=Decimal("-1.00"),
            estado=EstadoExpedienteEnum.CREADO,
        )

        client = authenticate(td_user)
        response = client.get("/api/v1/expedientes/board/")
        assert response.status_code == status.HTTP_200_OK
        cards = {
            c["id"]: c
            for c in next(
                col["cases"]
                for col in response.data["columns"]
                if col["key"] == EstadoExpedienteEnum.CREADO
            )
        }

        assert cards[e_llamado.id]["es_llamado"] is True
        assert cards[e_llamado.id]["es_felicitacion"] is False
        assert cards[e_felic_t01.id]["es_felicitacion"] is True
        assert cards[e_felic_t01.id]["es_llamado"] is False
        assert cards[e_hist.id]["es_llamado"] is True
        assert cards[e_hist.id]["es_felicitacion"] is False
        assert cards[e_std.id]["es_llamado"] is False
        assert cards[e_std.id]["es_felicitacion"] is False


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
