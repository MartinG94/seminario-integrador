"""Preparación no destructiva del esquema de demostración SCRUM-77."""

import json
from typing import Any

from django.core.management.base import BaseCommand, CommandError
from django.db import DatabaseError, connection

from core.demo_schema import prepare_schema
from core.management.commands import check_demo_mysql as preflight


class Command(BaseCommand):
    help = "Prepara y verifica el esquema MySQL demo; conserva tablas y datos compatibles."
    requires_system_checks: list[str] = []

    def handle(self, *args: str, **options: Any) -> None:
        preflight._check_configuration()
        preflight._check_mysql()
        preflight._check_http_health()
        try:
            report = prepare_schema(connection)
        except DatabaseError:
            raise CommandError(
                "No se pudo completar el esquema demo. El DDL puede haber quedado parcial; "
                "conservá la base y corregí la causa antes de reintentar."
            ) from None
        self.stdout.write(
            json.dumps({"status": "ok", **report}, ensure_ascii=False, sort_keys=True)
        )
