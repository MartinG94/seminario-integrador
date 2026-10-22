"""Comando de gestión específico para sembrar eventos, asistencias y apercibimientos.

Permite ejecutar de forma independiente el seed de la Spec 005 (SCRUM-50 / S3-06)
sin necesidad de recargar todo el padrón o esquema legado.
"""

from typing import Any

from django.core.management.base import BaseCommand

from core.management.commands.seed_production_data import Command as CoreSeedCommand
from socios.models import Subcomision


class Command(BaseCommand):
    """Siembra exclusivamente eventos institucionales, asistencias y apercibimientos de prueba."""

    help = (
        "Siembra reuniones, actividades institucionales, asistencias y "
        "apercibimientos representativos."
    )

    def handle(self, *args: Any, **options: Any) -> None:
        self.stdout.write(
            self.style.NOTICE("=== Sembrando eventos institucionales y asistencias (Spec 005) ===")
        )
        core_cmd = CoreSeedCommand()
        core_cmd.stdout = self.stdout
        core_cmd.stderr = self.stderr
        core_cmd.style = self.style

        subcomisiones = {sub.name: sub for sub in Subcomision.objects.all()}
        for name in [
            "Cómputos",
            "Recursos Humanos",
            "Relaciones Institucionales",
            "Prensa",
            "Mantenimiento",
            "Gestión Social y Ambiental",
            "Eventos",
            "Rifas",
            "Comisión Directiva",
            "Tribunal de Disciplina",
        ]:
            if name not in subcomisiones:
                sub, _ = Subcomision.objects.get_or_create(name=name)
                subcomisiones[name] = sub

        core_cmd._sembrar_eventos_y_asistencias(subcomisiones)
        self.stdout.write(
            self.style.SUCCESS("✓ Eventos, asistencias y apercibimientos sembrados con éxito.")
        )
