"""Management command para cerrar automáticamente expedientes vencidos (CA4 / SCRUM-46)."""

from django.core.management.base import BaseCommand
from django.utils import timezone

from expedientes.services.deadline_service import DeadlineEnforcementService


class Command(BaseCommand):
    help = (
        "Cierra de forma idempotente los expedientes en justificación "
        "cuyo plazo perentorio de 5 días hábiles haya vencido sin descargo."
    )

    def handle(self, *args, **options) -> None:
        service = DeadlineEnforcementService()
        ahora = timezone.now()
        self.stdout.write(
            self.style.NOTICE(f"Iniciando evaluación de plazos procesales al instante: {ahora}...")
        )

        total_cerrados = service.close_expired_deadlines(ahora=ahora)

        if total_cerrados > 0:
            self.stdout.write(
                self.style.SUCCESS(f"Se cerraron {total_cerrados} expediente(s) con plazo vencido.")
            )
        else:
            self.stdout.write(
                self.style.NOTICE("No se encontraron expedientes con plazo vencido para cerrar.")
            )
