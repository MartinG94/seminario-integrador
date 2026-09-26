"""
Comando de gestión para procesar y reintentar la cola de correos salientes (Outbox).

Uso:
    python manage.py process_email_queue [--batch-size=50] [--force]
"""

from django.core.management.base import BaseCommand

from notifications.services import EmailDispatcherService


class Command(BaseCommand):
    help = "Procesa los correos pendientes de envío en la cola transaccional Outbox."

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--batch-size",
            type=int,
            default=50,
            help="Cantidad máxima de correos a despachar en esta ejecución (por defecto: 50).",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help=(
                "Forzar el despacho ignorando la ventana de espera del "
                "próximo reintento (next_retry_at)."
            ),
        )

    def handle(self, *args, **options) -> None:
        batch_size = options["batch_size"]
        force = options["force"]

        self.stdout.write(
            self.style.NOTICE(
                f"Iniciando procesamiento Outbox (batch_size={batch_size}, force={force})..."
            )
        )

        result = EmailDispatcherService.process_pending_queue(batch_size=batch_size, force=force)

        self.stdout.write(
            self.style.SUCCESS(
                f"Procesamiento finalizado: "
                f"Procesados={result['processed']}, "
                f"Enviados={result['sent']}, "
                f"Fallidos={result['failed']}, "
                f"Pendientes restantes={result['pending']}"
            )
        )
