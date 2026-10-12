"""Transición explícita de anoSocial al contrato demo nullable de SCRUM-77."""

import json
from typing import Any

from django.core.management.base import BaseCommand, CommandError
from django.db import DatabaseError, connection

from core.demo_schema import transition_social_year_schema
from core.management.commands import check_demo_mysql as preflight


class Command(BaseCommand):
    help = "Transiciona sólo anoSocial de una demo preparada; verifica datos y contrato íntegro."
    requires_system_checks: list[str] = []

    def handle(self, *args: str, **options: Any) -> None:
        preflight._check_configuration()
        preflight._check_mysql()
        preflight._check_http_health()
        try:
            report = transition_social_year_schema(connection)
        except DatabaseError:
            raise CommandError(
                "No se pudo verificar la transición demo. El DDL puede estar aplicado; "
                "conservá la base y corregí la causa antes de reintentar."
            ) from None
        self.stdout.write(
            json.dumps({"status": "ok", **report}, ensure_ascii=False, sort_keys=True)
        )
