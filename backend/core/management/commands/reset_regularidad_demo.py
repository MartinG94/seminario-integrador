"""Comando de gestión para reiniciar la base de datos demo de la rama regularidad."""

from typing import Any

from django.core.management.base import BaseCommand

from core.services.demo_reset_service import reset_regularidad_database


class Command(BaseCommand):
    help = "Restaura la base de datos al snapshot SQL inicial de la rama Regularidad."

    def handle(self, *args: Any, **options: Any) -> None:
        result = reset_regularidad_database()
        expedientes = ", ".join(result["expedientes"])
        self.stdout.write(
            self.style.SUCCESS(
                f"Base de datos restaurada al snapshot de Regularidad. "
                f"Expedientes activos: {expedientes}."
            )
        )
