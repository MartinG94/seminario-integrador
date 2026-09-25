"""Pruebas del loader en una conexión SQLite temporal, ajena a ranking/padron."""

from io import StringIO

import pytest
from django.core.management import call_command
from django.db.backends.sqlite3.base import DatabaseWrapper

from ranking.management.commands import load_legacy_schema


@pytest.fixture
def isolated_loader(tmp_path, monkeypatch, django_db_blocker):
    """El DDL del loader nunca alcanza la conexión default de la suite."""
    database = DatabaseWrapper(
        {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": str(tmp_path / "legacy-loader.sqlite3"),
            "OPTIONS": {},
            "TIME_ZONE": None,
            "AUTOCOMMIT": True,
            "ATOMIC_REQUESTS": False,
            "CONN_MAX_AGE": 0,
            "CONN_HEALTH_CHECKS": False,
        },
        alias="legacy_loader",
    )
    monkeypatch.setattr(load_legacy_schema, "connection", database)
    with django_db_blocker.unblock():
        try:
            yield database
        finally:
            database.close()


class TestLoadLegacySchemaCommand:
    """Conserva las verificaciones de carga e idempotencia sin contaminar la suite."""

    def test_load_legacy_schema_populates_tables(self, isolated_loader) -> None:
        out = StringIO()
        call_command("load_legacy_schema", stdout=out)
        output = out.getvalue()
        assert "Carga completada exitosamente" in output
        assert "Socios cargados: 3" in output
        assert "Subcomisiones cargadas: 12" in output

        with isolated_loader.cursor() as cursor:
            for table, expected in (
                ("socio_lista", 3),
                ("socio_tiposubcomision", 12),
                ("tribunal_puntajegeneral", 3),
                ("tribunal_puntajeaplicado", 1),
            ):
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                assert cursor.fetchone()[0] == expected
            cursor.execute(
                "SELECT s.apellido, s.nombre, s.anoSocial, sub.nombre "
                "FROM socio_lista s JOIN socio_tiposubcomision sub "
                "ON s.codSubcomision = sub.codSubcomision WHERE s.nroSocio = 1001"
            )
            apellido, nombre, ano_social, subcomision = cursor.fetchone()
            assert apellido == "Pérez"
            assert nombre == "Esteban"
            assert ano_social >= 4
            assert subcomision == "Tribunal de Disciplina"

    def test_load_legacy_schema_is_idempotent(self, isolated_loader) -> None:
        for _ in range(2):
            call_command("load_legacy_schema", stdout=StringIO())
        with isolated_loader.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM socio_lista")
            assert cursor.fetchone()[0] == 3
            cursor.execute("SELECT COUNT(*) FROM tribunal_puntajegeneral")
            assert cursor.fetchone()[0] == 3
