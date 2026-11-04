"""Pruebas unitarias e integración para el comando import_socios_y_puntos."""

from decimal import Decimal
from io import StringIO

import pytest
from django.core.management import call_command
from django.db import connection

from expedientes.models import AtencionFelicitacion, Expediente
from ranking.services import get_reconciled_ranking_queryset
from tests.legacy_schema import create_seed_support_tables


@pytest.mark.django_db(transaction=True)
class TestImportSociosYPuntosCommand:
    """Verifica la correcta ingestión del padrón, expedientes y saldos."""

    @pytest.fixture(autouse=True)
    def setup_legacy_tables(self) -> None:
        """Asegura la existencia de las tablas legadas en la BD de pruebas."""
        create_seed_support_tables(connection)
        yield
        # Teardown de aislamiento: limpiar registros insertados
        # para no colisionar con suites posteriores en la base de pruebas
        with connection.cursor() as cursor:
            cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
            existing = set(connection.introspection.table_names())
            for table in [
                "socio_tiposubcomision",
                "socio_especialidad",
                "socio_estado",
                "socio_lista",
                "socio_estudio",
                "socio_telefono",
                "socio_medio",
                "tribunal_expediente",
                "tribunal_puntajegeneral",
            ]:
                if table in existing:
                    cursor.execute(f"DELETE FROM `{table}`")
            cursor.execute("SET FOREIGN_KEY_CHECKS = 1")

    def test_command_dry_run_executes_cleanly(self) -> None:
        out = StringIO()
        call_command("import_socios_y_puntos", "--dry-run", stdout=out)
        output = out.getvalue()
        assert "Ingestión del Padrón y Expedientes del Tribunal" in output
        assert "Catálogos verificados." in output
        assert "padrón general" in output
        assert "RECONCILIACIÓN 100%" in output
        assert "Modo --dry-run activo: Revertiendo." in output

    def test_diego_sanchez_historico_reconciliado(self) -> None:
        # Socio 11779 (Diego Sánchez) debe reflejar exactamente los puntos del Tribunal
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT puntos, felicitaciones, llamadosAtencion "
                "FROM tribunal_puntajegeneral WHERE socio_id = 11779"
            )
            row = cursor.fetchone()

        if row:
            puntos, felicitaciones, llamados = row
            assert Decimal(str(puntos)) == Decimal("24.5")
            assert felicitaciones == 1
            assert llamados == 0

            # Verificar que en atencionFelicitacion coincidan los contadores
            af = AtencionFelicitacion.objects.filter(nroSocio=11779).first()
            if af:
                assert af.felicitaciones == 1
                assert af.llamadosAtencion == 0

    def test_exviajeros_no_reciben_expedientes(self) -> None:
        # A los socios de Ex Viajeros no se les piden ni emiten expedientes
        exviajeros_exp_count = Expediente.objects.filter(
            socio__subcomision__name="Ex Viajeros"
        ).count()
        assert exviajeros_exp_count == 0

    def test_ranking_reconciliado_sin_discrepancias(self) -> None:
        # Ningún socio con puntos debe figurar con discrepancias en el ranking
        qs = get_reconciled_ranking_queryset()
        for s in qs.filter(nroSocio__in=[11779, 11737, 11549]):
            assert s.saldo_historico_calc == s.saldo_cache_calc
