"""Contrato del esquema legado requerido por el seed en una base de pruebas vacía."""

import pytest
from django.db import connection
from django.db.backends.sqlite3.base import DatabaseWrapper

from tests.legacy_schema import create_seed_support_tables, drop_seed_support_tables


@pytest.mark.django_db
def test_seed_catalogues_exist_before_loading_data() -> None:
    required = {
        "socio_tipodocumento",
        "socio_sexo",
        "socio_estadocivil",
        "socio_tipoSocio",
        "socio_motivoCambioEstado",
        "socio_especialidad",
        "grupo_lista",
        "socio_email",
        "socio_estadoHistorial",
        "tribunal_valorsancion",
        "tribunal_expediente",
    }

    assert required <= set(connection.introspection.table_names())


def test_seed_schema_is_empty_idempotent_and_preserves_existing_tables(
    tmp_path, django_db_blocker
) -> None:
    database = DatabaseWrapper(
        {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": str(tmp_path / "seed-schema.sqlite3"),
            "OPTIONS": {},
            "TIME_ZONE": None,
            "AUTOCOMMIT": True,
            "ATOMIC_REQUESTS": False,
            "CONN_MAX_AGE": 0,
            "CONN_HEALTH_CHECKS": False,
        },
        alias="seed_schema",
    )
    with django_db_blocker.unblock():
        try:
            with database.cursor() as cursor:
                cursor.execute("CREATE TABLE socio_tipodocumento (marker TEXT)")
                cursor.execute("INSERT INTO socio_tipodocumento VALUES ('Conservado')")
            created = create_seed_support_tables(database)

            assert "socio_email" in created
            assert "socio_tipodocumento" not in created
            assert "expedientes_evento" not in database.introspection.table_names()
            assert create_seed_support_tables(database) == []
            with database.cursor() as cursor:
                for table in created:
                    cursor.execute(f"SELECT COUNT(*) FROM {database.ops.quote_name(table)}")
                    assert cursor.fetchone()[0] == 0

            drop_seed_support_tables(database, created)

            assert not set(created).intersection(database.introspection.table_names())
            with database.cursor() as cursor:
                cursor.execute("SELECT marker FROM socio_tipodocumento")
                assert cursor.fetchall() == [("Conservado",)]
        finally:
            database.close()
