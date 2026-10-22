"""Comando seed_production_data expuesto desde la app expedientes.

Delega la ejecución al comando central de carga en core.management.commands.seed_production_data
garantizando compatibilidad total con invocaciones específicas de la app expedientes.
"""

from typing import Any

from core.management.commands.seed_production_data import Command as CoreSeedCommand


class Command(CoreSeedCommand):
    """Comando seed_production_data accesible desde la app expedientes."""

    help = (
        "Carga datos del padrón, socios de login, expedientes, eventos, "
        "asistencias y apercibimientos."
    )

    def handle(self, *args: Any, **options: Any) -> None:
        super().handle(*args, **options)
