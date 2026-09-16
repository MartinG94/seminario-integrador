"""Pruebas para el comando de gestión load_legacy_schema."""

from io import StringIO

import pytest
from django.core.management import call_command

from ranking.models import PuntajeAplicado, PuntajeGeneral, Socio, Subcomision


@pytest.mark.django_db
class TestLoadLegacySchemaCommand:
    """Pruebas de ingesta y reproducibilidad del esquema legado en SQLite."""

    def test_load_legacy_schema_populates_tables(self) -> None:
        """Verifica que el comando ejecuta DDL y DML y puebla las tablas de socios y puntajes."""
        out = StringIO()
        call_command("load_legacy_schema", stdout=out)

        output = out.getvalue()
        assert "Carga completada exitosamente" in output
        assert "Socios cargados: 3" in output
        assert "Subcomisiones cargadas: 12" in output

        # Validar en el ORM que los registros existen y se pueden consultar
        assert Socio.objects.count() == 3
        assert Subcomision.objects.count() == 12
        assert PuntajeGeneral.objects.count() == 3
        assert PuntajeAplicado.objects.count() == 1

        # Verificar socio emblemático del seed (Esteban Pérez N° 1001)
        socio_1001 = Socio.objects.get(nroSocio=1001)
        assert socio_1001.apellido == "Pérez"
        assert socio_1001.nombre == "Esteban"
        assert socio_1001.categoria == "ACTIVO"
        assert socio_1001.subcomision.nombre == "Tribunal de Disciplina"

    def test_load_legacy_schema_is_idempotent(self) -> None:
        """Verifica que ejecutar el comando varias veces no duplica claves ni rompe integridad."""

        out1 = StringIO()
        call_command("load_legacy_schema", stdout=out1)

        out2 = StringIO()
        call_command("load_legacy_schema", stdout=out2)

        assert Socio.objects.count() == 3
        assert PuntajeGeneral.objects.count() == 3
