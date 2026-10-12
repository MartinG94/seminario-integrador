"""Entrada protegida del seed de SCRUM-77; stdout sólo contiene el manifiesto."""

import json
from typing import Any

from django.core.management.base import BaseCommand, CommandError

from core import demo_seed
from socios.demo_catalog import CATALOG


class Command(BaseCommand):
    help = "Carga o verifica el catálogo ficticio SCRUM-77 sin sobrescribir datos existentes."
    requires_system_checks: list[str] = []

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument("--profile", default=CATALOG.profile)

    def handle(self, *args: str, **options: Any) -> None:
        demo_seed.assert_demo_seed_environment(options["profile"])
        demo_seed.preflight._check_mysql()
        demo_seed.preflight._check_http_health()
        try:
            report = demo_seed.run_demo_seed(profile=options["profile"])
        except CommandError:
            raise
        except Exception:
            raise CommandError(
                "La carga no pudo completarse; se revirtieron datos, propiedad y numeración. "
                "Conservá la demo y corregí la causa antes de reintentar."
            ) from None
        self.stdout.write(json.dumps(report, ensure_ascii=False, sort_keys=True))
