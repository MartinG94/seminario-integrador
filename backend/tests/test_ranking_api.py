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

    def test_get_ranking_without_trailing_slash_returns_200(
        self, api_client: APIClient, seed_ranking_data
    ) -> None:
        """Endpoints sin barra final (/api/v1/ranking y /api/ranking) responden 200 sin 301."""
        r_v1 = api_client.get("/api/v1/ranking")
        assert r_v1.status_code == status.HTTP_200_OK
        assert len(r_v1.json()) == 4

        r_unv = api_client.get("/api/ranking")
        assert r_unv.status_code == status.HTTP_200_OK
        assert len(r_unv.json()) == 4

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

    def test_empty_query_params_returns_200_no_filter(
        self, api_client: APIClient, seed_ranking_data
    ) -> None:
        """Query params vacíos o sólo espacios se ignoran sin disparar HTTP 400."""
        response = api_client.get(
            "/api/v1/ranking/?categoria=&ordering=&reconciliado=&subcomision=&search="
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()) == 4

        response_spaces = api_client.get(
            "/api/v1/ranking/?categoria=  &ordering=  &reconciliado=  "
        )
        assert response_spaces.status_code == status.HTTP_200_OK
        assert len(response_spaces.json()) == 4

    def test_ordering_merito_alias_descending(
        self, api_client: APIClient, seed_ranking_data
    ) -> None:
        """Alias 'merito' ordena por saldo de mayor a menor (frontend contract)."""
        response = api_client.get("/api/v1/ranking/?ordering=merito")
        assert response.status_code == status.HTTP_200_OK
        saldos = [item["saldo"] for item in response.json()]
        assert saldos == sorted(saldos, reverse=True)

    def test_ordering_sancion_alias_ascending(
        self, api_client: APIClient, seed_ranking_data
    ) -> None:
        """Alias 'sancion' ordena por saldo de menor a mayor (más sancionados primero)."""
        response = api_client.get("/api/v1/ranking/?ordering=sancion")
        assert response.status_code == status.HTTP_200_OK
        saldos = [item["saldo"] for item in response.json()]
        assert saldos == sorted(saldos)

    def test_ordering_by_subcomision(self, api_client: APIClient, seed_ranking_data) -> None:
        """Ordenamiento alfabético por nombre de subcomisión."""
        response = api_client.get("/api/v1/ranking/?ordering=subcomision")
        assert response.status_code == status.HTTP_200_OK
        subcomisiones = [item["subcomision"] for item in response.json()]
        assert subcomisiones == sorted(subcomisiones)

    def test_search_by_full_name_multiword(self, api_client: APIClient, seed_ranking_data) -> None:
        """Búsqueda por nombre y apellido combinados en ambos sentidos."""
        r_direct = api_client.get("/api/v1/ranking/?q=Carlos Alonso")
        assert len(r_direct.json()) == 1
        assert r_direct.json()[0]["id"] == "101"

        r_reverse = api_client.get("/api/v1/ranking/?q=Alonso Carlos")
        assert len(r_reverse.json()) == 1
        assert r_reverse.json()[0]["id"] == "101"

    def test_filter_by_subcomision_id(self, api_client: APIClient, seed_ranking_data) -> None:
        """Filtrado numérico por codSubcomision."""
        response = api_client.get("/api/v1/ranking/?subcomision=1")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 2
        for item in data:
            assert item["subcomision"] == "Cómputos"

    def test_reconciliation_filter_float_precision_tolerance(
        self, api_client: APIClient, seed_ranking_data
    ) -> None:
        """
        Prueba de estrés de tolerancia flotante:
        Un socio cuyos movimientos suman 0.1 + 0.2 (= 0.30000000000000004) y caché 0.3
        debe ser considerado reconciliado en Python y en filtro SQL (?reconciliado=true/false).
        """
        sub = seed_ranking_data["subcomisiones"][0]
        s_float = Socio.objects.create(
            nroSocio=199,
            nombre="Flotante",
            apellido="Prueba",
            anoSocial=4,
            subcomision=sub,
        )
        PuntajeAplicado.objects.create(idPuntajeAplicado=1991, socio=s_float, puntajeAplicado=0.1)
        PuntajeAplicado.objects.create(idPuntajeAplicado=1992, socio=s_float, puntajeAplicado=0.2)
        PuntajeGeneral.objects.create(idPuntajeGeneral=199, socio=s_float, puntos=0.3)

        # Debe aparecer en reconciliado=true
        r_true = api_client.get("/api/v1/ranking/?reconciliado=true")
        assert r_true.status_code == status.HTTP_200_OK
        ids_true = [item["id"] for item in r_true.json()]
        assert "199" in ids_true

        # NO debe aparecer en reconciliado=false
        r_false = api_client.get("/api/v1/ranking/?reconciliado=false")
        assert r_false.status_code == status.HTTP_200_OK
        ids_false = [item["id"] for item in r_false.json()]
        assert "199" not in ids_false

    def test_search_with_multiple_estudios_no_duplicate_rows(
        self, api_client: APIClient, seed_ranking_data
    ) -> None:
        """
        Prueba adversarial: Un socio con múltiples legajos universitarios en socio_estudio
        no debe generar filas duplicadas ni errores al buscar por texto.
        """
        s1 = seed_ranking_data["socios"][0]
        # Agregar un segundo estudio a Carlos Alonso (nroSocio 101)
        SocioEstudio.objects.create(
            compositeKey=10102,
            socio=s1,
            nroLegajo=99887,
            codEspecialidad=2,
        )

        # Búsqueda por el segundo legajo
        response = api_client.get("/api/v1/ranking/?search=99887")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == str(s1.nroSocio)
        assert data[0]["apellido"] == "Alonso"

    def test_missing_or_null_subcomision_handling(
        self, api_client: APIClient, seed_ranking_data
    ) -> None:
        """
        Socio sin subcomisión asignada debe serializarse como 'Sin Subcomisión'
        y responder a los filtros semánticos correspondientes.
        """
        s_orphan = Socio.objects.create(
            nroSocio=299,
            nombre="Sin",
            apellido="SubcomisionSocio",
            anoSocial=1,
            subcomision=None,
        )

        r_all = api_client.get("/api/v1/ranking/?search=SubcomisionSocio")
        assert r_all.status_code == status.HTTP_200_OK
        assert len(r_all.json()) == 1
        assert r_all.json()[0]["subcomision"] == "Sin Subcomisión"

        # Filtrar por "Sin Subcomisión"
        r_filter = api_client.get("/api/v1/ranking/?subcomision=Sin Subcomisión")
        assert r_filter.status_code == status.HTTP_200_OK
        assert len(r_filter.json()) == 1
        assert r_filter.json()[0]["id"] == str(s_orphan.nroSocio)

        # Filtrar por alias "null"
        r_null = api_client.get("/api/v1/ranking/?subcomision=null")
        assert r_null.status_code == status.HTTP_200_OK
        assert len(r_null.json()) == 1
        assert r_null.json()[0]["id"] == str(s_orphan.nroSocio)

    def test_search_by_subcomision_name_aligned_with_frontend(
        self, api_client: APIClient, seed_ranking_data
    ) -> None:
        """La búsqueda textual incluye la subcomisión según el contrato de frontend."""
        # Búsqueda con tilde
        r_accent = api_client.get("/api/v1/ranking/?search=Cómputos")
        assert r_accent.status_code == status.HTTP_200_OK
        data_accent = r_accent.json()
        assert len(data_accent) == 2
        for item in data_accent:
            assert item["subcomision"] == "Cómputos"

        # Búsqueda sin tilde
        r_plain = api_client.get("/api/v1/ranking/?search=computos")
        assert r_plain.status_code == status.HTTP_200_OK
        data_plain = r_plain.json()
        assert len(data_plain) == 2

    def test_search_accent_insensitive_matching(
        self, api_client: APIClient, seed_ranking_data
    ) -> None:
        """Búsqueda insensible a tildes (Díaz con/sin acento)."""
        r_plain = api_client.get("/api/v1/ranking/?search=diaz")
        assert r_plain.status_code == status.HTTP_200_OK
        assert len(r_plain.json()) == 1
        assert r_plain.json()[0]["apellido"] == "Díaz"

        r_accent = api_client.get("/api/v1/ranking/?search=Díaz")
        assert r_accent.status_code == status.HTTP_200_OK
        assert len(r_accent.json()) == 1
        assert r_accent.json()[0]["apellido"] == "Díaz"

    def test_filter_by_subcomision_accent_insensitive(
        self, api_client: APIClient, seed_ranking_data
    ) -> None:
        """El filtro de subcomisión admite nombres sin tildes."""
        r = api_client.get("/api/v1/ranking/?subcomision=computos")
        assert r.status_code == status.HTTP_200_OK
        data = r.json()
        assert len(data) == 2
        for item in data:
            assert item["subcomision"] == "Cómputos"

    def test_frontend_query_param_aliases(self, api_client: APIClient, seed_ranking_data) -> None:
        """Soporta nombres de parámetros directamente ligados al estado de Angular."""
        response = api_client.get(
            "/api/v1/ranking/?filtroCategoria=ACTIVO&criterioOrden=merito&filtroSubcomision=Cómputos"
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 2
        for item in data:
            assert item["categoria"] == "ACTIVO"
            assert item["subcomision"] == "Cómputos"
        assert data[0]["saldo"] >= data[1]["saldo"]

    def test_ordering_case_insensitive(self, api_client: APIClient, seed_ranking_data) -> None:
        """El ordenamiento es insensible a mayúsculas/minúsculas."""
        r_upper = api_client.get("/api/v1/ranking/?ordering=MERITO")
        assert r_upper.status_code == status.HTTP_200_OK
        r_title = api_client.get("/api/v1/ranking/?ordering=Saldo")
        assert r_title.status_code == status.HTTP_200_OK

    def test_ordering_by_id_asc_and_desc(self, api_client: APIClient, seed_ranking_data) -> None:
        """Ordenamiento por id / nroSocio ascendente y descendente."""
        r_asc = api_client.get("/api/v1/ranking/?ordering=id")
        assert r_asc.status_code == status.HTTP_200_OK
        ids_asc = [item["id"] for item in r_asc.json()]
        assert ids_asc == ["101", "102", "103", "104"]

        r_desc = api_client.get("/api/v1/ranking/?ordering=-id")
        assert r_desc.status_code == status.HTTP_200_OK
        ids_desc = [item["id"] for item in r_desc.json()]
        assert ids_desc == ["104", "103", "102", "101"]

    def test_reconciliado_filter_si_with_accent(
        self, api_client: APIClient, seed_ranking_data
    ) -> None:
        """El parámetro reconciliado acepta 'sí' con tilde."""
        r = api_client.get("/api/v1/ranking/?reconciliado=sí")
        assert r.status_code == status.HTTP_200_OK
        data = r.json()
        assert len(data) == 2
        for item in data:
            assert item["reconciliado"] is True

    def test_ordering_by_legajo_with_missing_estudio(
        self, api_client: APIClient, seed_ranking_data
    ) -> None:
        """Un socio sin estudio usa nroSocio como legajo y se ordena consistentemente."""
        sub = seed_ranking_data["subcomisiones"][0]
        Socio.objects.create(
            nroSocio=999,
            nombre="Zacarías",
            apellido="Zárate",
            anoSocial=1,
            subcomision=sub,
        )
        r_asc = api_client.get("/api/v1/ranking/?ordering=legajo")
        assert r_asc.status_code == status.HTTP_200_OK
        legajos = [item["legajo"] for item in r_asc.json()]
        # Todos los legajos son strings no nulos
        assert all(isinstance(leg, str) and leg for leg in legajos)
        assert "999" in legajos

        r_desc = api_client.get("/api/v1/ranking/?ordering=-legajo")
        assert r_desc.status_code == status.HTTP_200_OK
        legajos_desc = [item["legajo"] for item in r_desc.json()]
    def test_search_multi_term_out_of_order_tokens(
        self, api_client: APIClient, seed_ranking_data
    ) -> None:
        """Búsqueda con múltiples términos en cualquier orden (nombre + subcomisión, etc.)."""
        # Carlos (Alonso) en Cómputos
        r1 = api_client.get("/api/v1/ranking/?search=computos carlos")
        assert r1.status_code == status.HTTP_200_OK
        assert len(r1.json()) == 1
        assert r1.json()[0]["id"] == "101"

        # Alonso + legajo 54321
        r2 = api_client.get("/api/v1/ranking/?search=54321 alonso")
        assert r2.status_code == status.HTTP_200_OK
        assert len(r2.json()) == 1
        assert r2.json()[0]["id"] == "101"

    def test_comma_separated_multi_ordering(
        self, api_client: APIClient, seed_ranking_data
    ) -> None:
        """Soporta ordenamiento múltiple separado por coma según estándar REST/DRF."""
        response = api_client.get("/api/v1/ranking/?ordering=-saldo,apellido")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 4
        saldos = [item["saldo"] for item in data]
        assert saldos == sorted(saldos, reverse=True)

        # Ordenamiento por subcomisión y luego saldo ascendente
        r_sub = api_client.get("/api/v1/ranking/?ordering=subcomision,saldo")
        assert r_sub.status_code == status.HTTP_200_OK
        assert len(r_sub.json()) == 4

    def test_ordering_by_diferencia_and_reconciliado(
        self, api_client: APIClient, seed_ranking_data
    ) -> None:
        """Soporta ordenamiento por diferencia de reconciliación y estado."""
        r_diff = api_client.get("/api/v1/ranking/?ordering=-diferencia")
        assert r_diff.status_code == status.HTTP_200_OK
        data = r_diff.json()
        diffs = [abs(item["diferencia"]) for item in data]
        assert diffs == sorted(diffs, reverse=True)

        r_rec = api_client.get("/api/v1/ranking/?ordering=reconciliado")
        assert r_rec.status_code == status.HTTP_200_OK

    def test_django_system_check_reports_zero_warnings(self) -> None:
        """El sistema Django check no debe emitir warnings de URL ni colisiones de namespace."""
        from io import StringIO
        from django.core.management import call_command

        out = StringIO()
        call_command("check", stdout=out)
        output = out.getvalue()
        assert "System check identified no issues" in output



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

    def test_constant_query_count_when_socios_lack_estudio(
        self, api_client: APIClient, seed_ranking_data
    ) -> None:
        """
        Ataque N+1: Verificar que socios sin ningún registro de socio_estudio
        no disparan consultas adicionales por socio en el serializador.
        """
        sub = seed_ranking_data["subcomisiones"][0]
        for i in range(5):
            Socio.objects.create(
                nroSocio=500 + i,
                nombre=f"NoEstudio_{i}",
                apellido=f"Apellido_{i}",
                anoSocial=2,
                subcomision=sub,
            )

        with CaptureQueriesContext(connection) as ctx:
            response = api_client.get("/api/v1/ranking/")

        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()) == 9  # 4 iniciales + 5 nuevos
        # Debe mantenerse estrictamente en 1 única consulta SQL (cero N+1)
        assert len(ctx.captured_queries) == 1
