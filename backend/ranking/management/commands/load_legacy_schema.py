"""Comando de gestión para adaptar y cargar el esquema y datos semilla del sistema legado."""

import re
from pathlib import Path
from typing import Any

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import connection


class Command(BaseCommand):
    help = "Adapta y carga tablas y datos semilla del esquema legado en SQLite/MySQL."

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--path",
            type=str,
            default=None,
            help="Ruta al archivo sistema_actual_legado_schema.sql",
        )
        parser.add_argument(
            "--clean",
            action="store_true",
            help="Limpia y recrea las tablas antes de insertar los datos semilla.",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        sql_path_opt = options.get("path")
        if sql_path_opt:
            file_path = Path(sql_path_opt)
        else:
            file_path = (
                settings.BASE_DIR.parent
                / "docs"
                / "analisis-proceso-actual"
                / "sistema-actual"
                / "sistema_actual_legado_schema.sql"
            )

        if not file_path.exists():
            raise CommandError(f"No se encontró el archivo SQL legado en: {file_path}")

        self.stdout.write(f"Leyendo esquema legado desde: {file_path}")
        with open(file_path, encoding="utf-8") as f:
            raw_sql = f.read()

        is_sqlite = connection.vendor == "sqlite"
        self.stdout.write(f"Motor de base de datos detectado: {connection.vendor}")

        if is_sqlite:
            statements = self._adapt_mysql_to_sqlite(raw_sql, clean=options.get("clean", False))
        else:
            statements = self._clean_mysql_statements(raw_sql, clean=options.get("clean", False))

        self.stdout.write(f"Ejecutando {len(statements)} sentencias SQL...")

        if is_sqlite:
            connection.ensure_connection()
            connection.connection.execute("PRAGMA foreign_keys = OFF;")
        else:
            with connection.cursor() as cursor:
                cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")

        with connection.cursor() as cursor:
            executed_tables = 0
            executed_inserts = 0

            for stmt in statements:
                stmt_clean = stmt.strip()
                if not stmt_clean:
                    continue
                try:
                    cursor.execute(stmt_clean)
                    upper_s = stmt_clean.upper()
                    if upper_s.startswith("CREATE TABLE"):
                        executed_tables += 1
                    elif upper_s.startswith("INSERT"):
                        executed_inserts += 1

                except Exception as exc:
                    warn_msg = (
                        f"Advertencia al ejecutar sentencia: {exc}\nSentencia: {stmt_clean[:90]}..."
                    )
                    self.stderr.write(self.style.WARNING(warn_msg))

            if is_sqlite:
                connection.connection.execute("PRAGMA foreign_keys = ON;")
            else:
                cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")

            # Consultar métricas de verificación
            cursor.execute("SELECT count(*) FROM socio_lista;")
            socios_count = cursor.fetchone()[0]

            cursor.execute("SELECT count(*) FROM socio_tiposubcomision;")
            subcomisiones_count = cursor.fetchone()[0]

            cursor.execute("SELECT count(*) FROM tribunal_puntajegeneral;")
            ptj_gral_count = cursor.fetchone()[0]

            cursor.execute("SELECT count(*) FROM tribunal_puntajeaplicado;")
            ptj_aplicado_count = cursor.fetchone()[0]

        self.stdout.write(
            self.style.SUCCESS(
                f"Carga completada exitosamente:\n"
                f" - Tablas procesadas: {executed_tables}\n"
                f" - Inserciones ejecutadas: {executed_inserts}\n"
                f" - Socios cargados: {socios_count}\n"
                f" - Subcomisiones cargadas: {subcomisiones_count}\n"
                f" - Puntajes Generales (cache): {ptj_gral_count}\n"
                f" - Puntajes Aplicados (libro mayor): {ptj_aplicado_count}"
            )
        )

    def _split_sql_statements(self, sql: str) -> list[str]:
        """Separa sentencias SQL respetando cadenas de texto entre comillas y comentarios."""
        raw_statements = []
        current: list[str] = []
        in_quote = False
        quote_char = ""
        in_line_comment = False
        i = 0
        n = len(sql)

        while i < n:
            c = sql[i]

            if in_line_comment:
                if c == "\n":
                    in_line_comment = False
                i += 1
                continue

            if in_quote:
                current.append(c)
                if c == quote_char:
                    if i + 1 < n and sql[i + 1] == quote_char:
                        current.append(sql[i + 1])
                        i += 1
                    else:
                        in_quote = False
                i += 1
                continue

            if c in ("'", '"', "`"):
                in_quote = True
                quote_char = c
                current.append(c)
                i += 1
                continue

            if c == "-" and i + 1 < n and sql[i + 1] == "-":
                in_line_comment = True
                i += 2
                continue

            if c == ";":
                stmt = "".join(current).strip()
                if stmt:
                    raw_statements.append(stmt)
                current = []
                i += 1
                continue

            current.append(c)
            i += 1

        if current:
            stmt = "".join(current).strip()
            if stmt:
                raw_statements.append(stmt)

        return raw_statements

    def _clean_mysql_statements(self, sql: str, clean: bool = False) -> list[str]:
        """
        Limpia sentencias MySQL manteniendo compatibilidad nativa y preservando
        la base de datos de Django.
        """
        raw_statements = self._split_sql_statements(sql)
        statements = []
        for stmt in raw_statements:
            clean_stmt = stmt.strip()
            upper = clean_stmt.upper()
            if upper.startswith(("SET NAMES", "SET FOREIGN_KEY_CHECKS", "CREATE DATABASE", "USE ")):
                continue
            if upper.startswith("DROP TABLE") and not clean:
                continue
            statements.append(clean_stmt)
        return statements

    def _adapt_mysql_to_sqlite(self, sql: str, clean: bool = False) -> list[str]:
        """Convierte sentencias DDL y DML de MySQL a sintaxis nativa de SQLite."""
        raw_statements = self._split_sql_statements(sql)

        sqlite_stmts = []
        for stmt in raw_statements:
            clean_stmt = stmt.strip()
            upper_stmt = clean_stmt.upper()
            if upper_stmt.startswith("DROP TABLE"):
                if clean:
                    clean_stmt = clean_stmt.replace("`", '"')
                    sqlite_stmts.append(clean_stmt)
            elif upper_stmt.startswith("CREATE TABLE"):
                clean_stmt = re.sub(
                    r"\)\s*ENGINE=.*$", ")", clean_stmt, flags=re.IGNORECASE | re.DOTALL
                )
                clean_stmt = clean_stmt.replace("`", '"')

                match = re.match(
                    r'CREATE TABLE\s+(?:IF NOT EXISTS\s+)?("?\w+"?)\s*\((.*)\)',
                    clean_stmt,
                    flags=re.DOTALL | re.IGNORECASE,
                )
                if not match:
                    continue
                table_name = match.group(1)
                body = match.group(2)

                body_parts = []
                cur_part = []
                paren_depth = 0
                for c in body:
                    if c == "(":
                        paren_depth += 1
                    elif c == ")":
                        paren_depth -= 1
                    if c == "," and paren_depth == 0:
                        body_parts.append("".join(cur_part).strip())
                        cur_part = []
                    else:
                        cur_part.append(c)
                if cur_part:
                    body_parts.append("".join(cur_part).strip())

                new_parts = []
                pk_col = None
                for part in body_parts:
                    pk_match = re.match(
                        r'PRIMARY KEY\s*\(\s*"(\w+)"\s*\)', part, flags=re.IGNORECASE
                    )
                    if pk_match:
                        pk_col = pk_match.group(1)

                for part in body_parts:
                    stripped = part.strip()
                    upper_part = stripped.upper()

                    if (
                        upper_part.startswith("KEY ")
                        or upper_part.startswith('"KEY"')
                        or upper_part.startswith("UNIQUE KEY")
                    ):
                        continue
                    if upper_part.startswith("PRIMARY KEY"):
                        if pk_col:
                            continue

                    if "AUTO_INCREMENT" in upper_part:
                        part = re.sub(
                            r"int\(\d+\)\s+NOT\s+NULL\s+AUTO_INCREMENT",
                            "INTEGER PRIMARY KEY AUTOINCREMENT",
                            part,
                            flags=re.IGNORECASE,
                        )
                        part = re.sub(r"AUTO_INCREMENT", "", part, flags=re.IGNORECASE)

                    part = re.sub(
                        r"ON UPDATE CURRENT_TIMESTAMP\(\d*\)",
                        "",
                        part,
                        flags=re.IGNORECASE,
                    )
                    part = re.sub(
                        r"DEFAULT CURRENT_TIMESTAMP\(\d*\)",
                        "DEFAULT CURRENT_TIMESTAMP",
                        part,
                        flags=re.IGNORECASE,
                    )
                    part = re.sub(r"int\(\d+\)", "INTEGER", part, flags=re.IGNORECASE)
                    part = re.sub(r"tinyint\(\d+\)", "INTEGER", part, flags=re.IGNORECASE)
                    part = re.sub(r"longtext", "TEXT", part, flags=re.IGNORECASE)
                    part = re.sub(r"double", "REAL", part, flags=re.IGNORECASE)

                    if (
                        pk_col
                        and re.match(rf'"{pk_col}"\s+', stripped, flags=re.IGNORECASE)
                        and "PRIMARY KEY" not in part.upper()
                    ):
                        part = re.sub(r"NOT NULL", "PRIMARY KEY", part, flags=re.IGNORECASE)
                        if "PRIMARY KEY" not in part.upper():
                            part = part.strip() + " PRIMARY KEY"

                    if table_name.strip('"').lower() == "socio_lista":
                        if stripped.startswith(('"codSubcomision"', "codSubcomision")):
                            part = re.sub(r"NOT\s+NULL", "DEFAULT NULL", part, flags=re.IGNORECASE)
                        elif stripped.startswith(('"idTipoSocio"', "idTipoSocio")):
                            part = re.sub(r"NOT\s+NULL", "DEFAULT NULL", part, flags=re.IGNORECASE)
                        elif stripped.startswith(('"fechaNac"', "fechaNac")):
                            part = re.sub(r"NOT\s+NULL", "DEFAULT NULL", part, flags=re.IGNORECASE)

                    new_parts.append(part.strip())

                sqlite_stmt = (
                    f"CREATE TABLE IF NOT EXISTS {table_name} (\n  "
                    + ",\n  ".join(new_parts)
                    + "\n)"
                )
                sqlite_stmts.append(sqlite_stmt)
            elif upper_stmt.startswith("INSERT INTO"):
                clean_stmt = clean_stmt.replace("`", '"')
                # Anexar date_joined con CURRENT_TIMESTAMP para auth_user
                if '"auth_user"' in clean_stmt and "date_joined" not in clean_stmt:
                    clean_stmt = clean_stmt.replace('("id",', '("date_joined", "id",')
                    clean_stmt = re.sub(r"\(\s*(\d+)\s*,", r"(datetime('now'), \1,", clean_stmt)
                # Reemplazar con INSERT OR REPLACE INTO para idempotencia
                clean_stmt = re.sub(
                    r"^INSERT INTO", "INSERT OR REPLACE INTO", clean_stmt, flags=re.IGNORECASE
                )
                sqlite_stmts.append(clean_stmt)

        return sqlite_stmts
