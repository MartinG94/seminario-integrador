"""Regresión del nombre de la base temporal y los permisos de MySQL en CI."""

import os
from pathlib import Path
from runpy import run_path
from unittest.mock import patch

import pytest
from django.db.utils import ConnectionHandler


@pytest.mark.parametrize(
    ("database_env", "expected_name"),
    [
        ({}, "test_aveit_tribunal_dev"),
        ({"DATABASE_NAME": "aveit_tribunal_test"}, "test_aveit_tribunal_test"),
        ({"MYSQL_DATABASE": "aveit_custom"}, "test_aveit_custom"),
        (
            {"DATABASE_NAME": "aveit_ci", "MYSQL_DATABASE": "aveit_legacy"},
            "test_aveit_ci",
        ),
        (
            {"DATABASE_NAME": "aveit_ci", "TEST_DATABASE_NAME": "aveit_isolated_test"},
            "aveit_isolated_test",
        ),
    ],
    ids=["local-default", "ci", "mysql-alias", "database-name-priority", "explicit-override"],
)
def test_mysql_test_database_name(database_env: dict[str, str], expected_name: str) -> None:
    settings_path = Path(__file__).resolve().parents[1] / "core" / "settings.py"
    with patch.dict(os.environ, database_env, clear=True), patch("dotenv.load_dotenv"):
        configuration = run_path(str(settings_path))

    connection = ConnectionHandler(configuration["DATABASES"])["default"]

    # Django calcula el nombre real sin abrir una conexión ni crear bases.
    assert connection.creation._get_test_db_name() == expected_name
