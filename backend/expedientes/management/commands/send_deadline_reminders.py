"""Management command para despachar recordatorios 24h antes del vencimiento de plazo (Evento 7)."""

from django.core.management.base import BaseCommand
from django.utils import timezone

from expedientes.services.deadline_service import DeadlineEnforcementService


class Command(BaseCommand):
    help = (
        "Encola recordatorios en EmailOutbox para expedientes en justificación cuyo plazo "
        "vence dentro de las próximas 24 horas."
    )

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--hours",
            type=int,
            default=24,
            help="Ventana horaria previa al vencimiento (por defecto: 24).",
        )

    def handle(self, *args, **options) -> None:
        hours = options["hours"]
        service = DeadlineEnforcementService()
        total = service.send_imminent_deadline_reminders(ahora=timezone.now(), window_hours=hours)
        self.stdout.write(self.style.SUCCESS(f"Recordatorios de vencimiento procesados: {total}."))
