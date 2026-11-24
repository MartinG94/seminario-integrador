"""Servicio para restaurar la base de datos al snapshot SQL de la rama Regularidad."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from django.conf import settings
from django.db import connection

from expedientes.models import Expediente


def get_snapshot_path() -> Path:
    """Devuelve la ruta al archivo dump SQL de snapshot de Regularidad."""
    configured = getattr(settings, "REGULARIDAD_SNAPSHOT_PATH", None) or os.getenv(
        "REGULARIDAD_SNAPSHOT_PATH"
    )
    if configured:
        return Path(configured)
    return Path(settings.BASE_DIR).parent / "database" / "snapshot_regularidad.sql"


def split_sql_statements(raw_sql: bytes) -> list[bytes]:
    """Separa sentencias SQL en bytes preservando strings, escapes, binarios y comentarios."""
    statements: list[bytes] = []
    start = 0
    i = 0
    n = len(raw_sql)
    in_quote = 0
    in_line_comment = False
    in_block_comment = False

    while i < n:
        b = raw_sql[i]

        if in_line_comment:
            if b == 10:  # \n
                in_line_comment = False
            i += 1
            continue

        if in_block_comment:
            if b == 42 and i + 1 < n and raw_sql[i + 1] == 47:  # */
                in_block_comment = False
                i += 2
            else:
                i += 1
            continue

        if in_quote:
            if b == 92 and in_quote != 96:  # \ escape (no aplica dentro de backticks)
                i += 2
                continue
            if b == in_quote:
                if i + 1 < n and raw_sql[i + 1] == in_quote:
                    i += 2
                    continue
                in_quote = 0
            i += 1
            continue

        if b in (39, 34, 96):  # ', ", `
            in_quote = b
            i += 1
            continue

        if b == 45 and i + 2 < n and raw_sql[i + 1] == 45 and raw_sql[i + 2] in (32, 9, 10, 13):
            in_line_comment = True
            i += 3
            continue

        if b == 35:  # #
            in_line_comment = True
            i += 1
            continue

        if b == 47 and i + 1 < n and raw_sql[i + 1] == 42:  # /*
            in_block_comment = True
            i += 2
            continue

        if b == 59:  # ;
            stmt = raw_sql[start:i].strip()
            if stmt:
                statements.append(stmt)
            start = i + 1

        i += 1

    tail = raw_sql[start:].strip()
    if tail:
        statements.append(tail)

    return statements


def _strip_leading_line_comments(stmt: bytes) -> bytes:
    """Elimina comentarios de línea iniciales (`--` o `#`) para inspeccionar el verbo SQL."""
    lines = stmt.splitlines()
    idx = 0
    while idx < len(lines):
        stripped = lines[idx].strip()
        if not stripped or stripped.startswith((b"--", b"#")):
            idx += 1
            continue
        break
    return b"\n".join(lines[idx:]).strip()


def _should_skip_statement(stmt: bytes) -> bool:
    """Omite comentarios vacíos, CREATE DATABASE y USE para restaurar en la BD activa."""
    effective = _strip_leading_line_comments(stmt)
    if not effective:
        return True
    upper = effective.upper()
    return upper.startswith((b"CREATE DATABASE", b"USE "))


def reset_regularidad_database(snapshot_path: Path | None = None) -> dict[str, Any]:
    """Restaura la base de datos MySQL activa desde el snapshot SQL de Regularidad."""
    path = snapshot_path or get_snapshot_path()
    if not path.is_file():
        raise FileNotFoundError(f"No se encontró el archivo snapshot SQL en: {path}")

    if connection.vendor != "mysql":
        raise RuntimeError(
            "La restauración desde snapshot SQL requiere conexión a MySQL "
            f"(motor actual: {connection.vendor})."
        )

    raw_sql = path.read_bytes()
    statements = split_sql_statements(raw_sql)

    executed = 0
    with connection.cursor() as cursor:
        try:
            for stmt in statements:
                if _should_skip_statement(stmt):
                    continue
                cursor.execute(stmt)
                executed += 1
        finally:
            cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")

    expedientes = list(Expediente.objects.order_by("numero").values_list("numero", flat=True))
    return {
        "snapshot": str(path),
        "statements_executed": executed,
        "expedientes": expedientes,
    }
