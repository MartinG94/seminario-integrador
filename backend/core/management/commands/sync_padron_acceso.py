"""Comando de gestión para sincronizar acceso exclusivo y año social del padrón oficial."""

from pathlib import Path
from typing import Any

from django.core.management.base import BaseCommand

from core.services.padron_access_sync_service import sync_padron_access


class Command(BaseCommand):
    help = (
        "Sincroniza socios_socio (acceso exclusivo y año social según fórmula por grupo) "
        "a partir de SeniorsActivos.csv y JuniorsPasivos.csv."
    )

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument(
            "--csv-dir",
            type=str,
            default=None,
            help=(
                "Ruta opcional al directorio que contiene SeniorsActivos.csv y JuniorsPasivos.csv."
            ),
        )
        parser.add_argument(
            "--year",
            type=int,
            default=None,
            help="Año calendario de referencia para calcular la edad de cada grupo (ej. 2026).",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        csv_dir = Path(options["csv_dir"]) if options.get("csv_dir") else None
        result = sync_padron_access(csv_dir=csv_dir, reference_year=options.get("year"))
        self.stdout.write(
            self.style.SUCCESS(
                "Sincronización completada: "
                f"autorizados={result['authorized_total']} "
                f"(activos={result['seniors_count']}, pasivos={result['juniors_count']}), "
                f"creados={result['created']}, actualizados={result['updated']}, "
                f"deshabilitados={result['disabled']}, "
                f"excluidos_test={result['excluded_test']}, "
                f"excluidos_historicos={result['excluded_historical']}, "
                f"legacy_actualizados={result['legacy_updated']}."
            )
        )
