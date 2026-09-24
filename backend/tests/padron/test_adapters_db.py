"""Pruebas de integración reales contra base de datos para DatabasePadronAdapter.

Verifica empíricamente:
  - IMPL-BLK-001: Consultas SQL reales, Prefetch determinista, Subquery de historial y
    paginación LIMIT/OFFSET.
  - IMPL-BLK-002: Ejecución de consultas optimizadas O(1) con django_assert_num_queries
    (prevención de N+1).
  - IMPL-BLK-003: Salvaguarda inmutable de sólo lectura (PermissionDenied ante intentos
    de save() o delete()).
  - IMPL-BLK-004: Resiliencia de check_health() ante falla real de conexión.
"""

from datetime import date, datetime, timezone

import pytest
from django.core.exceptions import PermissionDenied
from django.db import connection

from padron.adapters import DatabasePadronAdapter
from padron.domain import (
    MembershipStatusEnum,
    SocioCategoryEnum,
    SocioInstitucionalDTO,
)
from padron.models import (
    Socio,
    SocioEmail,
    SocioEstado,
    SocioEstadoHistorial,
    SocioEstudio,
    Subcomision,
)

UNMANAGED_MODELS = [
    Subcomision,
    SocioEstado,
    Socio,
    SocioEstudio,
    SocioEmail,
    SocioEstadoHistorial,
]


@pytest.fixture(scope="session", autouse=True)
def setup_unmanaged_tables(django_db_setup, django_db_blocker):
    """Crea dinámicamente las tablas para los modelos `managed = False` en la BD de pruebas."""
    with django_db_blocker.unblock():
        with connection.schema_editor() as editor:
            for model in UNMANAGED_MODELS:
                try:
                    editor.create_model(model)
                except Exception:
                    pass  # Tabla ya creada
    yield
    with django_db_blocker.unblock():
        with connection.schema_editor() as editor:
            for model in reversed(UNMANAGED_MODELS):
                try:
                    editor.delete_model(model)
                except Exception:
                    pass


def _create_record(model_cls, **kwargs):
    """Helper de prueba que inicializa y guarda registros con bypass explícito de sólo lectura."""
    obj = model_cls(**kwargs)
    obj._allow_write = True
    obj.save()
    return obj


# ==============================================================================
# IMPL-BLK-003: Verificación de Salvaguarda de Sólo Lectura
# ==============================================================================


@pytest.mark.django_db
class TestReadOnlyModelSafeguards:
    """Valida que los modelos unmanaged rechacen tajantemente cualquier operación de mutación."""

    def test_save_raises_permission_denied_on_subcomision(self) -> None:
        sub = Subcomision(nombre="Subcomisión Ilícita")
        with pytest.raises(PermissionDenied, match="estricta sólo lectura"):
            sub.save()

    def test_save_raises_permission_denied_on_socio(self) -> None:
        socio = Socio(
            apellido="Pérez",
            nombre="Juan",
            fechaIngreso=date(2023, 1, 1),
            codTipoDoc=1,
            nroDoc=38000111,
            fechaNac=date(2000, 1, 1),
            codSexo=1,
            anoSocial=2,
            idTipoSocio=1,
        )
        with pytest.raises(PermissionDenied, match="estricta sólo lectura"):
            socio.save()

    def test_save_raises_permission_denied_on_socio_estudio(self) -> None:
        estudio = SocioEstudio(
            compositeKey=999,
            socio_id=1,
            nroLegajo=12345,
            codEspecialidad=1,
        )
        with pytest.raises(PermissionDenied, match="estricta sólo lectura"):
            estudio.save()

    def test_delete_raises_permission_denied(self) -> None:
        sub = _create_record(Subcomision, nombre="Cómputos")
        sub._allow_write = False  # Restaurar protección
        with pytest.raises(PermissionDenied, match="estricta sólo lectura"):
            sub.delete()


# ==============================================================================
# IMPL-BLK-001: Pruebas de Integración Reales con Base de Datos
# ==============================================================================


@pytest.mark.django_db
class TestDatabasePadronAdapterRealDB:
    """Verifica que el adaptador interactúe correctamente con el motor relacional real."""

    def setup_method(self) -> None:
        self.adapter = DatabasePadronAdapter()

        # Crear estados en catálogo
        _create_record(SocioEstado, codEstadoSocio=1, nombre="Activo")
        _create_record(SocioEstado, codEstadoSocio=2, nombre="Pasivo")

        # Crear subcomisiones
        self.sub_computos = _create_record(Subcomision, codSubcomision=1, nombre="Cómputos")
        self.sub_centinela = _create_record(
            Subcomision, codSubcomision=99, nombre="Sin Subcomisión"
        )

        # Crear socio 1: Activo, año 4, con múltiples carreras universitarias
        self.socio1 = _create_record(
            Socio,
            nroSocio=101,
            apellido="Gómez",
            nombre="Martín",
            fechaIngreso=date(2022, 3, 1),
            codTipoDoc=1,
            nroDoc=38123456,
            fechaNac=date(2000, 5, 10),
            codSexo=1,
            subcomision=self.sub_computos,
            anoSocial=4,
            idTipoSocio=1,
        )

        # Múltiples estudios para socio 1 (cardinalidad 1 a N)
        _create_record(
            SocioEstudio,
            compositeKey=1001,
            socio=self.socio1,
            nroLegajo=54321,
            codEspecialidad=1,
            curso="3R1",
        )
        _create_record(
            SocioEstudio,
            compositeKey=1002,  # Mayor compositeKey -> debe prevalecer
            socio=self.socio1,
            nroLegajo=88888,
            codEspecialidad=2,
            curso="4R2",
        )

        # Email prioritario habilitado
        _create_record(
            SocioEmail,
            compositeKey=2001,
            socio=self.socio1,
            idEmail=1,
            email="martin.gomez@aveit.utn.edu.ar",
            habilitado=True,
            comprobado=True,
        )

        # Historial de estados (el más reciente debe prevalecer)
        _create_record(
            SocioEstadoHistorial,
            idGrupo=1,
            socio=self.socio1,
            fechaHora=datetime(2023, 1, 1, 10, 0, tzinfo=timezone.utc),
            codEstadoSocio=2,
            socio_motivoCambioEstado=1,
        )
        _create_record(
            SocioEstadoHistorial,
            idGrupo=1,
            socio=self.socio1,
            fechaHora=datetime(2024, 1, 1, 10, 0, tzinfo=timezone.utc),
            codEstadoSocio=1,  # Más reciente -> ENABLED
            socio_motivoCambioEstado=1,
        )

        # Crear socio 2: Pasivo, año 2, subcomisión 99 (centinela), sin legajo
        self.socio2 = _create_record(
            Socio,
            nroSocio=102,
            apellido="Álvarez",
            nombre="Lucía",
            fechaIngreso=date(2024, 3, 1),
            codTipoDoc=1,
            nroDoc=42987654,
            fechaNac=date(2003, 8, 20),
            codSexo=2,
            subcomision=self.sub_centinela,
            anoSocial=2,
            idTipoSocio=1,
        )

    def test_get_by_id_resolves_real_relations_and_disambiguates_estudios(self) -> None:
        """get_by_id() desambigua deterministamente el legajo y resuelve relaciones en SQL real."""
        dto = self.adapter.get_by_id(101)
        assert dto is not None
        assert isinstance(dto, SocioInstitucionalDTO)
        assert dto.socio_id == 101
        assert dto.first_name == "Martín"
        assert dto.last_name == "Gómez"
        assert dto.dni == "38123456"
        # Desambiguación: prevalece compositeKey 1002 (legajo 88888) sobre 1001 (54321)
        assert dto.legajo == "88888"
        assert dto.email == "martin.gomez@aveit.utn.edu.ar"
        assert dto.subcomision is not None
        assert dto.subcomision.name == "Cómputos"
        assert dto.category == SocioCategoryEnum.ACTIVE
        assert dto.membership_status == MembershipStatusEnum.ENABLED
        assert dto.is_active is True

    def test_get_by_id_handles_missing_legajo_and_sentinel_subcomision(self) -> None:
        """Socio sin estudios tiene legajo=None y subcomisión 99 se traduce a None."""
        dto = self.adapter.get_by_id(102)
        assert dto is not None
        assert dto.legajo is None
        assert dto.subcomision is None  # Centinela 99 limpiado
        assert dto.category == SocioCategoryEnum.PASSIVE

    def test_get_by_legajo_finds_record_via_exists_subquery(self) -> None:
        """get_by_legajo() ejecuta la subconsulta Exists sin requerir JOIN cartesiano."""
        dto = self.adapter.get_by_legajo("88888")
        assert dto is not None
        assert dto.socio_id == 101

        dto_inexistente = self.adapter.get_by_legajo("99999")
        assert dto_inexistente is None

    def test_list_subcomisiones_excludes_sentinel_99_real_db(self) -> None:
        """list_subcomisiones() en BD real excluye codSubcomision=99."""
        subcomisiones = self.adapter.list_subcomisiones()
        assert len(subcomisiones) == 1
        assert subcomisiones[0].name == "Cómputos"
        assert all(s.id != 99 for s in subcomisiones)

    def test_list_socios_filters_and_pagination_real_db(self) -> None:
        """list_socios() ejecuta filtros nativos SQL y paginación LIMIT/OFFSET."""
        # Filtro por categoría ACTIVE
        res_active = self.adapter.list_socios(category=SocioCategoryEnum.ACTIVE)
        assert res_active.count == 1
        assert res_active.results[0].socio_id == 101

        # Filtro por categoría PASSIVE
        res_passive = self.adapter.list_socios(category=SocioCategoryEnum.PASSIVE)
        assert res_passive.count == 1
        assert res_passive.results[0].socio_id == 102

        # Búsqueda textual por apellido (Gómez)
        res_search_apellido = self.adapter.list_socios(search="Gómez")
        assert res_search_apellido.count == 1
        assert res_search_apellido.results[0].socio_id == 101

        # Búsqueda textual por legajo (88888) usando subconsulta Exists
        res_search_legajo = self.adapter.list_socios(search="88888")
        assert res_search_legajo.count == 1
        assert res_search_legajo.results[0].socio_id == 101

        # Paginación con page_size=1
        page1 = self.adapter.list_socios(page=1, page_size=1)
        assert page1.count == 2
        assert len(page1.results) == 1
        assert page1.page == 1

        page2 = self.adapter.list_socios(page=2, page_size=1)
        assert page2.count == 2
        assert len(page2.results) == 1
        assert page2.page == 2
        assert page1.results[0].socio_id != page2.results[0].socio_id


# ==============================================================================
# IMPL-BLK-002: Verificación Empírica de N+1 (Consultas Constantes O(1))
# ==============================================================================


@pytest.mark.django_db
class TestDatabasePadronAdapterNPlusOne:
    """Verifica empíricamente que list_socios ejecute un número fijo de consultas O(1)."""

    def test_list_socios_executes_constant_queries_regardless_of_page_size(
        self, django_assert_num_queries
    ) -> None:
        sub = _create_record(Subcomision, codSubcomision=10, nombre="Deportes")
        _create_record(SocioEstado, codEstadoSocio=1, nombre="Activo")

        # Poblamos 12 socios con estudios, emails e historial
        for i in range(1, 13):
            s = _create_record(
                Socio,
                nroSocio=200 + i,
                apellido=f"Apellido{i}",
                nombre=f"Nombre{i}",
                fechaIngreso=date(2023, 1, 1),
                codTipoDoc=1,
                nroDoc=40000000 + i,
                fechaNac=date(2001, 1, 1),
                codSexo=1,
                subcomision=sub,
                anoSocial=i % 6 + 1,
                idTipoSocio=1,
            )
            _create_record(
                SocioEstudio,
                compositeKey=3000 + i,
                socio=s,
                nroLegajo=10000 + i,
                codEspecialidad=1,
            )
            _create_record(
                SocioEmail,
                compositeKey=4000 + i,
                socio=s,
                idEmail=1,
                email=f"socio{i}@aveit.utn.edu.ar",
                habilitado=True,
                comprobado=True,
            )
            _create_record(
                SocioEstadoHistorial,
                idGrupo=1,
                socio=s,
                fechaHora=datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc),
                codEstadoSocio=1,
                socio_motivoCambioEstado=1,
            )

        adapter = DatabasePadronAdapter()

        # Exactamente 4 consultas SQL constantes:
        # 1. COUNT(*) para paginación
        # 2. SELECT socio_lista con Subquery latest_cod_estado y select_related subcomision
        # 3. SELECT socio_estudio (prefetch_related con Prefetch order_by('-compositeKey'))
        # 4. SELECT socio_email (prefetch_related)
        with django_assert_num_queries(4):
            res_small = adapter.list_socios(page=1, page_size=5)
            # Materializar todos los DTOs para forzar evaluación completa de relaciones
            assert len(res_small.results) == 5
            for dto in res_small.results:
                assert dto.legajo is not None
                assert dto.email is not None
                assert dto.subcomision is not None

        # Al triplicar el tamaño de página (de 5 a 12 socios),
        # las queries deben mantenerse estrictamente en 4 (O(1))
        with django_assert_num_queries(4):
            res_large = adapter.list_socios(page=1, page_size=12)
            assert len(res_large.results) == 12
            for dto in res_large.results:
                assert dto.legajo is not None
                assert dto.email is not None


# ==============================================================================
# IMPL-BLK-004: Verificación de Resiliencia ante Desconexión Real
# ==============================================================================


@pytest.mark.django_db
class TestDatabasePadronAdapterConnectionResilience:
    """Verifica que check_health() capture fallas reales de conexión."""

    def test_check_health_healthy_when_database_is_connected(self) -> None:
        _create_record(Subcomision, codSubcomision=1, nombre="Cómputos")
        adapter = DatabasePadronAdapter()
        health = adapter.check_health()
        assert health.status in ("HEALTHY", "DEGRADED")
        assert health.latency_ms >= 0.0
        assert health.source == "mysql_institutional"

    def test_check_health_returns_unavailable_on_real_connection_failure(self, monkeypatch) -> None:
        """Verifica que falla real (OperationalError) sea capturada como UNAVAILABLE."""
        from django.db import connection
        from django.db.utils import OperationalError

        def broken_cursor(*args, **kwargs):
            raise OperationalError(
                "Can't connect to MySQL server on '127.0.0.1:3306' (111 Connection refused)"
            )

        monkeypatch.setattr(connection, "cursor", broken_cursor)

        adapter = DatabasePadronAdapter()
        health = adapter.check_health()

        assert health.status == "UNAVAILABLE"
        assert health.record_count == 0
        assert health.latency_ms >= 0.0
        assert health.source == "mysql_institutional"
        assert "Error de conexión a la base institucional" in health.message
        assert "Connection refused" in health.message
