"""Pruebas de integración para la API REST del Ranking Reconciliado."""

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from rest_framework import status
from rest_framework.test import APIClient

from ranking.models import (
    PuntajeAplicado,
    PuntajeGeneral,
    Socio,
    SocioEstudio,
    Subcomision,
    TipoSocio,
)


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture
def seed_ranking_data(db) -> dict[str, list]:
    """Crea una base de socios con casos balanceados, discrepantes y sin movimientos."""
    sub_computos = Subcomision.objects.create(codSubcomision=1, nombre="Cómputos")
    sub_eventos = Subcomision.objects.create(codSubcomision=7, nombre="Eventos")
    sub_td = Subcomision.objects.create(codSubcomision=10, nombre="Tribunal de Disciplina")

    tipo_ord = TipoSocio.objects.create(idTipoSocio=12, nombre="Socio Ordinario")
    tipo_pres = TipoSocio.objects.create(idTipoSocio=1, nombre="Presidente Subcomisión")

    # 1. Socio Activo Reconciliado (saldo = 10, caché = 10)
    s1 = Socio.objects.create(
        nroSocio=101,
        nombre="Carlos",
        apellido="Alonso",
        anoSocial=5,  # ACTIVO
        subcomision=sub_computos,
        tipoSocio=tipo_pres,
    )
    SocioEstudio.objects.create(compositeKey=10101, socio=s1, nroLegajo=54321, codEspecialidad=1)
    PuntajeAplicado.objects.create(idPuntajeAplicado=1, socio=s1, puntajeAplicado=10.0)
    PuntajeGeneral.objects.create(idPuntajeGeneral=1, socio=s1, puntos=10.0)

    # 2. Socio Pasivo con Discrepancia (saldo = -2.0, caché = -1.5 -> dif = -0.5, no reconciliado)
    s2 = Socio.objects.create(
        nroSocio=102,
        nombre="Beatriz",
        apellido="Bustos",
        anoSocial=2,  # PASIVO
        subcomision=sub_eventos,
        tipoSocio=tipo_ord,
    )
    SocioEstudio.objects.create(compositeKey=10201, socio=s2, nroLegajo=65432, codEspecialidad=1)
    PuntajeAplicado.objects.create(idPuntajeAplicado=2, socio=s2, puntajeAplicado=-2.0)
    PuntajeGeneral.objects.create(idPuntajeGeneral=2, socio=s2, puntos=-1.5)

    # 3. Socio Pasivo Reconciliado sin movimientos (saldo = 0, caché = 0)
    s3 = Socio.objects.create(
        nroSocio=103,
        nombre="Daniel",
        apellido="Castro",
        anoSocial=1,  # PASIVO
        subcomision=sub_td,
        tipoSocio=tipo_ord,
    )
    SocioEstudio.objects.create(compositeKey=10301, socio=s3, nroLegajo=76543, codEspecialidad=1)
    PuntajeGeneral.objects.create(idPuntajeGeneral=3, socio=s3, puntos=0.0)

    # 4. Socio Activo con múltiples movimientos (5.0 + (-1.5) = 3.5, caché = 3.0 -> no reconciliado)
    s4 = Socio.objects.create(
        nroSocio=104,
        nombre="Elena",
        apellido="Díaz",
        anoSocial=4,  # ACTIVO
        subcomision=sub_computos,
        tipoSocio=tipo_ord,
    )
    SocioEstudio.objects.create(compositeKey=10401, socio=s4, nroLegajo=87654, codEspecialidad=1)
    PuntajeAplicado.objects.create(idPuntajeAplicado=3, socio=s4, puntajeAplicado=5.0)
    PuntajeAplicado.objects.create(idPuntajeAplicado=4, socio=s4, puntajeAplicado=-1.5)
    PuntajeGeneral.objects.create(idPuntajeGeneral=4, socio=s4, puntos=3.0)

    return {
        "socios": [s1, s2, s3, s4],
        "subcomisiones": [sub_computos, sub_eventos, sub_td],
    }


@pytest.mark.django_db
class TestRankingAPIEndpoints:
    """Pruebas funcionales de endpoints GET /api/v1/ranking/ y /api/ranking/."""

    def test_get_ranking_v1_returns_200(self, api_client: APIClient, seed_ranking_data) -> None:
        """Endpoint oficial versionado responde HTTP 200 con listado."""
        response = api_client.get("/api/v1/ranking/")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 4

    def test_get_ranking_unversioned_returns_200(
        self, api_client: APIClient, seed_ranking_data
    ) -> None:
        """Endpoint directo /api/ranking/ responde HTTP 200 con listado coincidente."""
        response = api_client.get("/api/ranking/")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 4

    def test_ranking_item_matches_contract_rankingsocio(
        self, api_client: APIClient, seed_ranking_data
    ) -> None:
        """Verifica que cada objeto cumple el contrato RankingSocio de TypeScript."""

        response = api_client.get("/api/v1/ranking/")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        item = data[0]
        required_fields = {
            "id",
            "legajo",
            "nombre",
            "apellido",
            "categoria",
            "subcomision",
            "saldo",
            "saldoHistorico",
            "saldoPuntajeGeneral",
            "diferencia",
            "reconciliado",
        }
        assert required_fields.issubset(item.keys())

        # Validar tipos
        assert isinstance(item["id"], str)
        assert isinstance(item["legajo"], str)
        assert isinstance(item["nombre"], str)
        assert isinstance(item["apellido"], str)
        assert item["categoria"] in ("ACTIVO", "PASIVO")
        assert isinstance(item["subcomision"], str)
        assert isinstance(item["saldo"], (int, float))
        assert isinstance(item["saldoHistorico"], (int, float))
        assert isinstance(item["saldoPuntajeGeneral"], (int, float))
        assert isinstance(item["diferencia"], (int, float))
        assert isinstance(item["reconciliado"], bool)

    def test_reconciliation_values_precision(
        self, api_client: APIClient, seed_ranking_data
    ) -> None:
        """Verifica la fidelidad de los campos de reconciliación según los movimientos cargados."""
        response = api_client.get("/api/v1/ranking/?search=Elena")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        elena = data[0]

        # Elena: 5.0 + (-1.5) = 3.5 histórico, 3.0 general, diferencia = 0.5, reconciliado = False
        assert elena["saldoHistorico"] == 3.5
        assert elena["saldoPuntajeGeneral"] == 3.0
        assert elena["diferencia"] == 0.5
        assert elena["reconciliado"] is False


@pytest.mark.django_db
class TestRankingFilteringAndOrdering:
    """Pruebas de filtros por query params y ordenamiento."""

    def test_filter_by_categoria_activo(self, api_client: APIClient, seed_ranking_data) -> None:
        response = api_client.get("/api/v1/ranking/?categoria=ACTIVO")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 2
        for item in data:
            assert item["categoria"] == "ACTIVO"

    def test_filter_by_categoria_pasivo(self, api_client: APIClient, seed_ranking_data) -> None:
        response = api_client.get("/api/v1/ranking/?categoria=PASIVO")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 2
        for item in data:
            assert item["categoria"] == "PASIVO"

    def test_filter_by_categoria_invalid_returns_400(
        self, api_client: APIClient, seed_ranking_data
    ) -> None:
        response = api_client.get("/api/v1/ranking/?categoria=HONORARIO")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        error_data = response.json()
        assert "error" in error_data
        assert "HONORARIO" in error_data["error"]

    def test_filter_by_subcomision_name(self, api_client: APIClient, seed_ranking_data) -> None:
        response = api_client.get("/api/v1/ranking/?subcomision=Cómputos")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 2
        for item in data:
            assert item["subcomision"] == "Cómputos"

    def test_search_by_text(self, api_client: APIClient, seed_ranking_data) -> None:
        # Búsqueda por apellido
        r_ape = api_client.get("/api/v1/ranking/?q=alonso")
        assert len(r_ape.json()) == 1
        assert r_ape.json()[0]["apellido"] == "Alonso"

        # Búsqueda por legajo
        r_leg = api_client.get("/api/v1/ranking/?search=65432")
        assert len(r_leg.json()) == 1
        assert r_leg.json()[0]["legajo"] == "65432"

    def test_ordering_saldo_descending_default(
        self, api_client: APIClient, seed_ranking_data
    ) -> None:
        response = api_client.get("/api/v1/ranking/")
        data = response.json()
        saldos = [item["saldo"] for item in data]
        # Esperado: 10.0, 3.5, 0.0, -2.0
        assert saldos == sorted(saldos, reverse=True)

    def test_ordering_saldo_ascending(self, api_client: APIClient, seed_ranking_data) -> None:
        response = api_client.get("/api/v1/ranking/?ordering=saldo")
        data = response.json()
        saldos = [item["saldo"] for item in data]
        assert saldos == sorted(saldos)

    def test_ordering_invalid_returns_400(self, api_client: APIClient, seed_ranking_data) -> None:
        response = api_client.get("/api/v1/ranking/?ordering=hack_column")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "error" in response.json()

    def test_filter_by_reconciliado(self, api_client: APIClient, seed_ranking_data) -> None:
        # Reconciliados (2 socios: Alonso y Castro)
        r_rec = api_client.get("/api/v1/ranking/?reconciliado=true")
        assert len(r_rec.json()) == 2
        for item in r_rec.json():
            assert item["reconciliado"] is True

        # Discrepancias (2 socios: Bustos y Díaz)
        r_no_rec = api_client.get("/api/v1/ranking/?reconciliado=false")
        assert len(r_no_rec.json()) == 2
        for item in r_no_rec.json():
            assert item["reconciliado"] is False


@pytest.mark.django_db
class TestRankingQueryPerformance:
    """Verificación de optimización de persistencia y ausencia de problemas N+1."""

    def test_constant_query_count_no_n_plus_one(
        self, api_client: APIClient, seed_ranking_data
    ) -> None:
        """
        El endpoint debe resolver toda la información (socios, subcomisiones, legajos,
        saldos históricos y caché) en exactamente UNA (1) consulta SQL.
        """
        with CaptureQueriesContext(connection) as ctx:
            response = api_client.get("/api/v1/ranking/")

        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()) == 4
        # Exactamente 1 consulta SQL para el listado completo
        assert len(ctx.captured_queries) == 1
