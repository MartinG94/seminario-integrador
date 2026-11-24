from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from django.core.management import call_command

from core.services.demo_reset_service import (
    get_snapshot_path,
    reset_regularidad_database,
    split_sql_statements,
)


def test_split_sql_statements_maneja_binarios_escapes_y_comentarios():
    raw = (
        b"-- Comentario con ; punto y coma\n"
        b"/*!40101 SET NAMES utf8mb4 */;\n"
        b"INSERT INTO docs VALUES ('texto; con \\'escape\\'; y \\\\', "
        b"_binary '%PDF-1.5\\r\\n%\xb5\xb5');\n"
        b"/* comentario bloque ; */\n"
        b"UNLOCK TABLES;\n"
        b"-- Dump completed\n"
    )
    stmts = split_sql_statements(raw)
    assert len(stmts) == 4
    assert stmts[0].endswith(b"/*!40101 SET NAMES utf8mb4 */")
    assert b"_binary '%PDF-1.5\\r\\n%\xb5\xb5'" in stmts[1]
    assert stmts[2] == b"/* comentario bloque ; */\nUNLOCK TABLES"
    assert stmts[3] == b"-- Dump completed"


def test_reset_regularidad_database_falla_si_no_existe_snapshot(tmp_path):
    missing = tmp_path / "inexistente.sql"
    with pytest.raises(FileNotFoundError):
        reset_regularidad_database(snapshot_path=missing)


def test_reset_regularidad_database_omite_use_y_create_database_y_restaura_en_mysql(tmp_path):
    dump_file = tmp_path / "snapshot.sql"
    dump_file.write_bytes(
        b"-- Header\n"
        b"CREATE DATABASE `aveit_tribunal_dev`;\n"
        b"USE `aveit_tribunal_dev`;\n"
        b"DROP TABLE IF EXISTS `t`;\n"
        b"CREATE TABLE `t` (`id` INT PRIMARY KEY);\n"
        b"INSERT INTO `t` VALUES (1);\n"
        b"-- Dump completed\n"
    )

    mock_cursor = MagicMock()
    mock_cm = MagicMock()
    mock_cm.__enter__.return_value = mock_cursor
    mock_cm.__exit__.return_value = False

    with (
        patch("core.services.demo_reset_service.connection") as mock_conn,
        patch("core.services.demo_reset_service.Expediente") as mock_exp,
    ):
        mock_conn.vendor = "mysql"
        mock_conn.cursor.return_value = mock_cm
        mock_exp.objects.order_by.return_value.values_list.return_value = [
            "EXP-0001/2026",
            "EXP-0002/2026",
        ]

        result = reset_regularidad_database(snapshot_path=dump_file)

    executed_sqls = [call.args[0] for call in mock_cursor.execute.call_args_list]
    assert executed_sqls == [
        b"DROP TABLE IF EXISTS `t`",
        b"CREATE TABLE `t` (`id` INT PRIMARY KEY)",
        b"INSERT INTO `t` VALUES (1)",
        "SET FOREIGN_KEY_CHECKS = 1;",
    ]
    assert result["statements_executed"] == 3
    assert result["expedientes"] == ["EXP-0001/2026", "EXP-0002/2026"]


@pytest.mark.django_db
def test_endpoint_reset_demo_db_respeta_debug_y_retorna_snapshot_regularidad(api_client, settings):
    settings.DEBUG = False
    resp_forbidden = api_client.post("/api/v1/auth/reset-demo-db/", {}, format="json")
    assert resp_forbidden.status_code == 403

    settings.DEBUG = True
    with patch(
        "accounts.views.reset_regularidad_database",
        return_value={
            "snapshot": "/database/snapshot_regularidad.sql",
            "statements_executed": 944,
            "expedientes": ["EXP-0001/2026", "EXP-0002/2026"],
        },
    ) as mock_reset:
        resp_ok = api_client.post("/api/v1/auth/reset-demo-db/", {}, format="json")

    assert resp_ok.status_code == 200
    assert resp_ok.data["detail"] == "Base de datos restaurada al snapshot inicial de Regularidad."
    assert resp_ok.data["expedientes"] == ["EXP-0001/2026", "EXP-0002/2026"]
    mock_reset.assert_called_once_with()


def test_comando_reset_regularidad_demo(capsys):
    with patch(
        "core.management.commands.reset_regularidad_demo.reset_regularidad_database",
        return_value={
            "snapshot": "/database/snapshot_regularidad.sql",
            "statements_executed": 944,
            "expedientes": ["EXP-0001/2026", "EXP-0002/2026"],
        },
    ):
        call_command("reset_regularidad_demo")

    out = capsys.readouterr().out
    assert "Base de datos restaurada al snapshot de Regularidad." in out
    assert "EXP-0001/2026, EXP-0002/2026" in out


def test_get_snapshot_path_apunta_a_database_snapshot_regularidad(settings):
    path = get_snapshot_path()
    assert path == Path(settings.BASE_DIR).parent / "database" / "snapshot_regularidad.sql"
