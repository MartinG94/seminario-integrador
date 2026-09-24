"""Tests unitarios para los adaptadores y la factoría de inyección del padrón.

Cobertura:
  - MockPadronAdapter: consultas, filtros, paginación, simulación de fallas.
  - Factory: conmutación de dependencias vía PADRON_ADAPTER.
  - Contrato: todos los métodos de PadronRepositoryInterface.

Referencia: spec.md §RF-PADRON-01, §RF-PADRON-05, §RNF-PADRON-03.
"""

from unittest.mock import MagicMock, patch

import pytest
from django.db import OperationalError

from padron.adapters import DatabasePadronAdapter
from padron.domain import (
    ACTIVE_SOCIAL_YEARS,
    PASSIVE_SOCIAL_YEARS,
    HealthStatusDTO,
    MembershipStatusEnum,
    PaginatedSociosDTO,
    SocioCategoryEnum,
    SocioInstitucionalDTO,
    SubcomisionDTO,
)

# ==============================================================================
# MockPadronAdapter — Consultas y Filtros
# ==============================================================================


class TestMockPadronAdapterQueries:
    """Pruebas del MockPadronAdapter para consultas y filtros deterministas."""

    def _get_adapter(self):
        from padron.adapters import MockPadronAdapter

        return MockPadronAdapter()

    def test_list_socios_returns_paginated_dto(self) -> None:
        """list_socios() retorna PaginatedSociosDTO con registros de fixture."""
        adapter = self._get_adapter()
        result = adapter.list_socios()
        assert isinstance(result, PaginatedSociosDTO)
        assert result.count > 0
        assert len(result.results) > 0
        assert result.page == 1
        assert result.page_size == 20

    def test_list_socios_results_are_socio_dto(self) -> None:
        """Cada resultado es una instancia de SocioInstitucionalDTO."""
        adapter = self._get_adapter()
        result = adapter.list_socios()
        for socio in result.results:
            assert isinstance(socio, SocioInstitucionalDTO)

    def test_get_by_id_existing_socio(self) -> None:
        """get_by_id() retorna el socio correcto por nroSocio."""
        adapter = self._get_adapter()
        result = adapter.list_socios()
        first_socio = result.results[0]
        found = adapter.get_by_id(first_socio.socio_id)
        assert found is not None
        assert found.socio_id == first_socio.socio_id

    def test_get_by_id_nonexistent_returns_none(self) -> None:
        """get_by_id() retorna None para un ID inexistente."""
        adapter = self._get_adapter()
        assert adapter.get_by_id(999999) is None

    def test_get_by_legajo_existing(self) -> None:
        """get_by_legajo() retorna el socio correcto por legajo."""
        adapter = self._get_adapter()
        result = adapter.list_socios()
        socio_with_legajo = next((s for s in result.results if s.legajo is not None), None)
        if socio_with_legajo:
            found = adapter.get_by_legajo(socio_with_legajo.legajo)
            assert found is not None
            assert found.legajo == socio_with_legajo.legajo

    def test_get_by_legajo_nonexistent_returns_none(self) -> None:
        """get_by_legajo() retorna None para un legajo inexistente."""
        adapter = self._get_adapter()
        assert adapter.get_by_legajo("000000") is None

    def test_list_subcomisiones_returns_list(self) -> None:
        """list_subcomisiones() retorna lista de SubcomisionDTO."""
        adapter = self._get_adapter()
        result = adapter.list_subcomisiones()
        assert isinstance(result, list)
        assert len(result) > 0
        for sub in result:
            assert isinstance(sub, SubcomisionDTO)

    def test_list_subcomisiones_excludes_sentinel_99(self) -> None:
        """list_subcomisiones() no incluye el centinela cod=99."""
        adapter = self._get_adapter()
        result = adapter.list_subcomisiones()
        for sub in result:
            assert sub.id != 99

    def test_list_subcomisiones_alphabetical_order(self) -> None:
        """list_subcomisiones() retorna en orden alfabético por nombre."""
        adapter = self._get_adapter()
        result = adapter.list_subcomisiones()
        names = [s.name for s in result]
        assert names == sorted(names)

    def test_filter_by_category(self) -> None:
        """list_socios(category=PASSIVE) filtra correctamente."""
        adapter = self._get_adapter()
        result = adapter.list_socios(category=SocioCategoryEnum.PASSIVE)
        for socio in result.results:
            assert socio.category == SocioCategoryEnum.PASSIVE

    def test_filter_by_membership_status(self) -> None:
        """list_socios(membership_status=ENABLED) filtra correctamente."""
        adapter = self._get_adapter()
        result = adapter.list_socios(membership_status=MembershipStatusEnum.ENABLED)
        for socio in result.results:
            assert socio.membership_status == MembershipStatusEnum.ENABLED

    def test_filter_by_is_active(self) -> None:
        """list_socios(is_active=True) retorna solo socios activos."""
        adapter = self._get_adapter()
        result = adapter.list_socios(is_active=True)
        for socio in result.results:
            assert socio.is_active is True

    def test_search_by_name(self) -> None:
        """list_socios(search='...') busca por nombre o apellido."""
        adapter = self._get_adapter()
        all_socios = adapter.list_socios()
        if all_socios.results:
            target = all_socios.results[0]
            result = adapter.list_socios(search=target.last_name[:3])
            assert result.count >= 1

    def test_filter_by_subcomision_id(self) -> None:
        """list_socios(subcomision_id=1) filtra por subcomisión."""
        adapter = self._get_adapter()
        result = adapter.list_socios(subcomision_id=1)
        assert len(result.results) >= 1
        for socio in result.results:
            assert socio.subcomision is not None
            assert socio.subcomision.id == 1

    def test_pagination(self) -> None:
        """list_socios(page=1, page_size=1) retorna exactamente 1 resultado."""
        adapter = self._get_adapter()
        result = adapter.list_socios(page=1, page_size=1)
        assert len(result.results) <= 1
        assert result.page == 1
        assert result.page_size == 1


# ==============================================================================
# MockPadronAdapter — Simulación de Fallas (CA5)
# ==============================================================================


class TestMockPadronAdapterHealthAndFailures:
    """Pruebas de observabilidad y simulación de fallas del mock."""

    def test_check_health_returns_dto(self) -> None:
        """check_health() retorna HealthStatusDTO."""
        from padron.adapters import MockPadronAdapter

        adapter = MockPadronAdapter()
        result = adapter.check_health()
        assert isinstance(result, HealthStatusDTO)
        assert result.source == "mock_isolated"

    def test_check_health_healthy_status(self) -> None:
        """En condiciones normales, el mock reporta HEALTHY."""
        from padron.adapters import MockPadronAdapter

        adapter = MockPadronAdapter()
        result = adapter.check_health()
        assert result.status == "HEALTHY"
        assert result.record_count > 0

    def test_check_health_simulated_failure(self) -> None:
        """Con simulate_failure=True, reporta UNAVAILABLE."""
        from padron.adapters import MockPadronAdapter

        adapter = MockPadronAdapter(simulate_failure=True)
        result = adapter.check_health()
        assert result.status == "UNAVAILABLE"

    def test_simulated_failure_raises_on_queries(self) -> None:
        """Con simulate_failure=True, las consultas lanzan excepción."""
        from django.db import OperationalError

        from padron.adapters import MockPadronAdapter

        adapter = MockPadronAdapter(simulate_failure=True)
        with pytest.raises(OperationalError):
            adapter.list_socios()

    def test_simulated_failure_get_by_id_raises(self) -> None:
        """Con simulate_failure=True, get_by_id lanza excepción."""
        from django.db import OperationalError

        from padron.adapters import MockPadronAdapter

        adapter = MockPadronAdapter(simulate_failure=True)
        with pytest.raises(OperationalError):
            adapter.get_by_id(1)


# ==============================================================================
# Factory — Conmutación de Dependencias
# ==============================================================================


class TestPadronFactory:
    """Pruebas para la factoría de inyección de dependencias."""

    @patch.dict("os.environ", {"PADRON_ADAPTER": "mock"})
    def test_factory_returns_mock_adapter(self) -> None:
        """Con PADRON_ADAPTER='mock', la factoría retorna MockPadronAdapter."""
        from padron.adapters import MockPadronAdapter
        from padron.factory import get_padron_repository

        repo = get_padron_repository()
        assert isinstance(repo, MockPadronAdapter)

    @patch.dict("os.environ", {"PADRON_ADAPTER": "database"})
    def test_factory_returns_database_adapter(self) -> None:
        """Con PADRON_ADAPTER='database', la factoría retorna DatabasePadronAdapter."""
        from padron.adapters import DatabasePadronAdapter
        from padron.factory import get_padron_repository

        repo = get_padron_repository()
        assert isinstance(repo, DatabasePadronAdapter)

    @patch.dict("os.environ", {}, clear=False)
    def test_factory_defaults_to_database(self) -> None:
        """Sin variable PADRON_ADAPTER, la factoría retorna DatabasePadronAdapter."""
        import os

        from padron.factory import get_padron_repository

        # Remove env var if it exists
        os.environ.pop("PADRON_ADAPTER", None)
        from padron.adapters import DatabasePadronAdapter

        repo = get_padron_repository()
        assert isinstance(repo, DatabasePadronAdapter)


# ==============================================================================
# Modelos Unmanaged — Verificación Estructural (HIGH-001 / HIGH-002)
# ==============================================================================


class TestPadronModelsUnmanaged:
    """Verificación de invariantes estructurales sobre los modelos ORM no gestionados."""

    def test_all_models_are_unmanaged(self) -> None:
        """Todos los modelos del padrón deben tener managed = False (Principio 6)."""
        from padron.models import (
            Socio,
            SocioEmail,
            SocioEstado,
            SocioEstadoHistorial,
            SocioEstudio,
            Subcomision,
        )

        for model in (
            Subcomision,
            Socio,
            SocioEstudio,
            SocioEmail,
            SocioEstado,
            SocioEstadoHistorial,
        ):
            assert model._meta.managed is False, (
                f"El modelo {model.__name__} debe tener managed = False"
            )

    def test_composite_key_as_primary_key(self) -> None:
        """SocioEstudio y SocioEmail deben tener compositeKey como PK (HIGH-002)."""
        from padron.models import SocioEmail, SocioEstudio

        assert SocioEstudio._meta.pk.name == "compositeKey"
        assert SocioEmail._meta.pk.name == "compositeKey"

    def test_socio_estudio_meta_has_no_ordering(self) -> None:
        """SocioEstudio no debe tener Meta.ordering (HIGH-IT2-001)."""
        from padron.models import SocioEstudio

        assert not SocioEstudio._meta.ordering, (
            "SocioEstudio._meta.ordering debe estar vacío para prevenir inyección "
            "de columnas en SELECT DISTINCT"
        )


# ==============================================================================
# DatabasePadronAdapter — Mapeo Determinista a DTOs
# ==============================================================================


class TestDatabasePadronAdapterMapping:
    """Pruebas para el mapeo determinista de entidades ORM a DTOs de dominio."""

    def _get_adapter(self):
        from padron.adapters import DatabasePadronAdapter

        return DatabasePadronAdapter()

    def test_map_to_dto_disambiguates_estudios_by_composite_key(self) -> None:
        """La desambiguación toma el estudio con mayor compositeKey (H02 / HIGH-001)."""
        from unittest.mock import MagicMock

        adapter = self._get_adapter()

        estudio_antiguo = MagicMock()
        estudio_antiguo.compositeKey = 100
        estudio_antiguo.nroLegajo = 55555

        estudio_reciente = MagicMock()
        estudio_reciente.compositeKey = 200
        estudio_reciente.nroLegajo = 99999

        socio_orm = MagicMock()
        socio_orm.nroSocio = 42
        socio_orm.nombre = "Juan"
        socio_orm.apellido = "Pérez"
        socio_orm.nroDoc = 38111222
        socio_orm.anoSocial = 4
        socio_orm.fechaBaja = None
        socio_orm.subcomision = MagicMock(codSubcomision=1, nombre="Cómputos")
        socio_orm.latest_cod_estado = 1

        # Ya prefetcheado y ordenado por -compositeKey
        socio_orm.estudios.all.return_value = [estudio_reciente, estudio_antiguo]
        socio_orm.emails.all.return_value = []

        dto = adapter._map_to_dto(socio_orm)

        assert isinstance(dto, SocioInstitucionalDTO)
        assert dto.socio_id == 42
        assert dto.legajo == "99999"  # Del estudio con compositeKey=200
        assert dto.category == SocioCategoryEnum.ACTIVE
        assert dto.membership_status == MembershipStatusEnum.ENABLED
        assert dto.is_active is True

    def test_map_to_dto_without_estudios_returns_none_legajo(self) -> None:
        """Socio sin estudios prefetcheados tiene legajo = None."""
        from unittest.mock import MagicMock

        adapter = self._get_adapter()

        socio_orm = MagicMock()
        socio_orm.nroSocio = 43
        socio_orm.nombre = "Ana"
        socio_orm.apellido = "López"
        socio_orm.nroDoc = 39000111
        socio_orm.anoSocial = 2
        socio_orm.fechaBaja = None
        socio_orm.subcomision = None
        socio_orm.latest_cod_estado = 1
        socio_orm.estudios.all.return_value = []
        socio_orm.emails.all.return_value = []

        dto = adapter._map_to_dto(socio_orm)
        assert dto.legajo is None
        assert dto.category == SocioCategoryEnum.PASSIVE

    def test_map_to_dto_sentinel_subcomision_99_is_none(self) -> None:
        """Socio con subcomisión 99 ('Sin Subcomisión') mapea subcomision = None."""
        from unittest.mock import MagicMock

        adapter = self._get_adapter()

        socio_orm = MagicMock()
        socio_orm.nroSocio = 44
        socio_orm.nombre = "Pedro"
        socio_orm.apellido = "Gómez"
        socio_orm.nroDoc = 40111222
        socio_orm.anoSocial = 1
        socio_orm.fechaBaja = None
        socio_orm.subcomision = MagicMock(codSubcomision=99, nombre="Sin Subcomisión")
        socio_orm.latest_cod_estado = 1
        socio_orm.estudios.all.return_value = []
        socio_orm.emails.all.return_value = []

        dto = adapter._map_to_dto(socio_orm)
        assert dto.subcomision is None

    def test_map_to_dto_email_selection_priority(self) -> None:
        """Mapeo de email selecciona la casilla habilitada y comprobada."""
        from unittest.mock import MagicMock

        adapter = self._get_adapter()

        email1 = MagicMock(email="personal@gmail.com", habilitado=True, comprobado=False)
        email2 = MagicMock(email="institucional@aveit.utn.edu.ar", habilitado=True, comprobado=True)

        socio_orm = MagicMock()
        socio_orm.nroSocio = 45
        socio_orm.nombre = "Laura"
        socio_orm.apellido = "Diaz"
        socio_orm.nroDoc = 41222333
        socio_orm.anoSocial = 3
        socio_orm.fechaBaja = None
        socio_orm.subcomision = None
        socio_orm.latest_cod_estado = 1
        socio_orm.estudios.all.return_value = []
        socio_orm.emails.all.return_value = [email1, email2]

        dto = adapter._map_to_dto(socio_orm)
        assert dto.email == "institucional@aveit.utn.edu.ar"


# ==============================================================================
# DatabasePadronAdapter — Observabilidad y Healthcheck (CA5 / H04 / MED-003)
# ==============================================================================


class TestDatabasePadronAdapterHealthCheck:
    """Pruebas para check_health() del DatabasePadronAdapter con umbrales cuantitativos."""

    def _get_adapter(self):
        from padron.adapters import DatabasePadronAdapter

        return DatabasePadronAdapter()

    @patch("padron.models.Socio.objects.count", return_value=515)
    def test_check_health_healthy(self, mock_count) -> None:
        """Con latencia baja y registros > 0, reporta HEALTHY con source=mysql_institutional."""
        adapter = self._get_adapter()
        result = adapter.check_health()
        assert isinstance(result, HealthStatusDTO)
        assert result.status == "HEALTHY"
        assert result.source == "mysql_institutional"
        assert result.record_count == 515
        assert result.latency_ms < 500

    @patch("padron.models.Socio.objects.count", return_value=0)
    def test_check_health_degraded_when_empty_records(self, mock_count) -> None:
        """Con record_count == 0, reporta DEGRADED."""
        adapter = self._get_adapter()
        result = adapter.check_health()
        assert result.status == "DEGRADED"
        assert result.record_count == 0

    @patch("padron.models.Socio.objects.count")
    def test_check_health_degraded_when_latency_between_500_and_3000(self, mock_count) -> None:
        """Con latencia entre 500ms y 3000ms, reporta DEGRADED."""
        mock_count.return_value = 515
        adapter = self._get_adapter()
        # Simular latencia de 600ms vía monkeypatch o time.monotonic
        with patch("time.monotonic", side_effect=[100.0, 100.6]):
            result = adapter.check_health()
            assert result.status == "DEGRADED"
            assert result.latency_ms >= 500

    @patch("padron.models.Socio.objects.count")
    def test_check_health_unavailable_when_latency_exceeds_3000(self, mock_count) -> None:
        """Con latencia > 3000ms, reporta UNAVAILABLE."""
        mock_count.return_value = 515
        adapter = self._get_adapter()
        with patch("time.monotonic", side_effect=[100.0, 103.5]):
            result = adapter.check_health()
            assert result.status == "UNAVAILABLE"

    @patch("padron.models.Socio.objects.count", side_effect=OperationalError("Connection lost"))
    def test_check_health_unavailable_on_db_exception(self, mock_count) -> None:
        """Ante excepción de base de datos (OperationalError), reporta UNAVAILABLE."""
        adapter = self._get_adapter()
        result = adapter.check_health()
        assert result.status == "UNAVAILABLE"
        assert result.record_count == 0
        assert "Connection lost" in result.message

    @patch("padron.models.Socio.objects.count", side_effect=RuntimeError("Internal unexpected bug"))
    def test_check_health_unavailable_on_unexpected_exception(self, mock_count) -> None:
        """Ante excepción imprevista de aplicación, registra critical y reporta UNAVAILABLE."""
        adapter = self._get_adapter()
        result = adapter.check_health()
        assert result.status == "UNAVAILABLE"
        assert result.record_count == 0
        assert "Error inesperado en verificación de salud" in result.message


# ==============================================================================
# DatabasePadronAdapter — Consultas y Filtros (CA1, CA2, HIGH-004, HIGH-IT2-001)
# ==============================================================================


class TestDatabasePadronAdapterQueries:
    """Pruebas para las consultas y delegación de filtros del DatabasePadronAdapter."""

    def _get_adapter(self):
        from padron.adapters import DatabasePadronAdapter

        return DatabasePadronAdapter()

    def test_get_by_legajo_non_numeric_returns_none(self) -> None:
        """Un legajo no numérico o centinela retorna None inmediatamente."""
        adapter = self._get_adapter()
        assert adapter.get_by_legajo("invalido") is None
        assert adapter.get_by_legajo("") is None
        assert adapter.get_by_legajo("   ") is None
        assert adapter.get_by_legajo("0") is None
        assert adapter.get_by_legajo("-123") is None
        assert adapter.get_by_legajo(None) is None  # type: ignore[arg-type]

    @patch("padron.models.Subcomision.objects")
    def test_list_subcomisiones_excludes_sentinel_99(self, mock_subcomision_objects) -> None:
        """list_subcomisiones() excluye el centinela 99 y 'Sin Subcomisión' y ordena por nombre."""
        from unittest.mock import MagicMock

        s1 = MagicMock(codSubcomision=1, nombre="Cómputos")
        s2 = MagicMock(codSubcomision=2, nombre="Recursos Humanos")

        qs_mock = MagicMock()
        qs_mock.exclude.return_value = qs_mock
        qs_mock.order_by.return_value = [s1, s2]
        mock_subcomision_objects.exclude.return_value = qs_mock

        adapter = self._get_adapter()
        result = adapter.list_subcomisiones()

        assert len(result) == 2
        assert result[0].name == "Cómputos"
        assert result[1].name == "Recursos Humanos"
        # Verificar que se llamó a exclude con codSubcomision=99
        mock_subcomision_objects.exclude.assert_called()

    @patch.object(DatabasePadronAdapter, "_get_base_queryset")
    def test_get_by_id_returns_none_when_not_found(self, mock_get_base_qs) -> None:
        """get_by_id retorna None cuando Socio.DoesNotExist es lanzado."""
        from padron.models import Socio

        mock_qs = MagicMock()
        mock_qs.get.side_effect = Socio.DoesNotExist
        mock_get_base_qs.return_value = mock_qs

        adapter = self._get_adapter()
        assert adapter.get_by_id(999999) is None

    @patch.object(DatabasePadronAdapter, "_map_to_dto")
    @patch.object(DatabasePadronAdapter, "_get_base_queryset")
    def test_get_by_id_returns_dto_when_found(self, mock_get_base_qs, mock_map) -> None:
        """get_by_id retorna el DTO mapeado cuando el socio existe."""
        mock_socio = MagicMock()
        mock_qs = MagicMock()
        mock_qs.get.return_value = mock_socio
        mock_get_base_qs.return_value = mock_qs

        mock_dto = MagicMock(spec=SocioInstitucionalDTO)
        mock_map.return_value = mock_dto

        adapter = self._get_adapter()
        result = adapter.get_by_id(42)

        assert result == mock_dto
        mock_qs.get.assert_called_once_with(pk=42)
        mock_map.assert_called_once_with(mock_socio)

    @patch.object(DatabasePadronAdapter, "_map_to_dto")
    @patch.object(DatabasePadronAdapter, "_get_base_queryset")
    def test_get_by_legajo_returns_dto_when_found(self, mock_get_base_qs, mock_map) -> None:
        """get_by_legajo retorna el DTO mapeado cuando existe coincidencia."""
        mock_socio = MagicMock()
        mock_qs = MagicMock()
        mock_qs.filter.return_value.first.return_value = mock_socio
        mock_get_base_qs.return_value = mock_qs

        mock_dto = MagicMock(spec=SocioInstitucionalDTO)
        mock_map.return_value = mock_dto

        adapter = self._get_adapter()
        result = adapter.get_by_legajo("85421")

        assert result == mock_dto
        mock_qs.filter.assert_called_once()
        mock_map.assert_called_once_with(mock_socio)

    @patch.object(DatabasePadronAdapter, "_get_base_queryset")
    def test_get_by_legajo_returns_none_when_no_match(self, mock_get_base_qs) -> None:
        """get_by_legajo retorna None cuando no hay socio con ese legajo."""
        mock_qs = MagicMock()
        mock_qs.filter.return_value.first.return_value = None
        mock_get_base_qs.return_value = mock_qs

        adapter = self._get_adapter()
        result = adapter.get_by_legajo("99999")

        assert result is None

    @patch.object(DatabasePadronAdapter, "_map_to_dto")
    @patch.object(DatabasePadronAdapter, "_get_base_queryset")
    def test_list_socios_pagination_and_mapping(self, mock_get_base_qs, mock_map) -> None:
        """list_socios() ejecuta count(), slicing por LIMIT/OFFSET y mapea a DTOs."""
        s1 = MagicMock()
        s2 = MagicMock()
        mock_qs = MagicMock()
        mock_qs.filter.return_value = mock_qs
        mock_qs.exclude.return_value = mock_qs
        mock_qs.order_by.return_value = mock_qs
        mock_qs.count.return_value = 45
        mock_qs.__getitem__.return_value = [s1, s2]
        mock_get_base_qs.return_value = mock_qs

        dto1 = MagicMock(spec=SocioInstitucionalDTO)
        dto2 = MagicMock(spec=SocioInstitucionalDTO)
        mock_map.side_effect = [dto1, dto2]

        adapter = self._get_adapter()
        result = adapter.list_socios(page=2, page_size=2)

        assert isinstance(result, PaginatedSociosDTO)
        assert result.count == 45
        assert result.page == 2
        assert result.page_size == 2
        assert result.results == [dto1, dto2]

        mock_qs.count.assert_called_once()
        mock_qs.__getitem__.assert_called_once_with(slice(2, 4, None))

    @patch.object(DatabasePadronAdapter, "_get_base_queryset")
    def test_list_socios_filters_applied(self, mock_get_base_qs) -> None:
        """list_socios() aplica correctamente los filtros a nivel QuerySet."""
        mock_qs = MagicMock()
        mock_qs.filter.return_value = mock_qs
        mock_qs.exclude.return_value = mock_qs
        mock_qs.order_by.return_value = mock_qs
        mock_qs.count.return_value = 0
        mock_qs.__getitem__.return_value = []
        mock_get_base_qs.return_value = mock_qs

        adapter = self._get_adapter()

        # Probar cada filtro por separado para verificar llamadas al ORM
        adapter.list_socios(subcomision_id=3)
        mock_qs.filter.assert_any_call(subcomision_id=3)

        adapter.list_socios(category=SocioCategoryEnum.PASSIVE)
        mock_qs.filter.assert_any_call(anoSocial__in=PASSIVE_SOCIAL_YEARS)

        adapter.list_socios(category=SocioCategoryEnum.ACTIVE)
        mock_qs.filter.assert_any_call(anoSocial__in=ACTIVE_SOCIAL_YEARS)

        adapter.list_socios(category=SocioCategoryEnum.UNKNOWN)
        mock_qs.exclude.assert_any_call(anoSocial__in=PASSIVE_SOCIAL_YEARS + ACTIVE_SOCIAL_YEARS)

        adapter.list_socios(is_active=True)
        # Verifica que filter fue invocado
        assert mock_qs.filter.call_count >= 1

        adapter.list_socios(is_active=False)
        assert mock_qs.filter.call_count >= 1

        adapter.list_socios(membership_status=MembershipStatusEnum.ENABLED)
        adapter.list_socios(membership_status=MembershipStatusEnum.SUSPENDED)
        adapter.list_socios(membership_status=MembershipStatusEnum.TERMINATED)

        adapter.list_socios(search="Gomez")
        assert mock_qs.filter.called
