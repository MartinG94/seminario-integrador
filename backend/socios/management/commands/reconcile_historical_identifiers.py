"""Reconciliación histórica segura; simula por defecto."""

from django.core.management.base import BaseCommand
from django.db import transaction


class Command(BaseCommand):
    help = "Reporta y completa metadatos históricos con numero_socio verificado."

    def add_arguments(self, parser):
        parser.add_argument("--apply", action="store_true")

    def handle(self, *args, **options):
        from expedientes.models import EstadoResolucionEnum, Resolucion
        from notifications.models import EmailOutbox
        from socios.models import Socio

        apply_changes = options["apply"]
        socios = {
            socio.pk: socio.numero_socio
            for socio in Socio.objects.exclude(numero_socio__isnull=True).only("pk", "numero_socio")
        }
        counts = {
            "outbox": 0,
            "sent": 0,
            "draft": 0,
            "issued": 0,
            "unresolved": 0,
            "conflicts": 0,
        }

        with transaction.atomic():
            for item in EmailOutbox.objects.all().iterator():
                metadata = item.metadata if isinstance(item.metadata, dict) else {}
                try:
                    socio_id = int(metadata.get("socio_id"))
                except (TypeError, ValueError):
                    socio_id = None
                numero_socio = socios.get(socio_id)
                if numero_socio is None:
                    counts["unresolved"] += 1
                    continue
                if metadata.get("numero_socio") == numero_socio:
                    continue
                if metadata.get("numero_socio") is not None:
                    counts["conflicts"] += 1
                    self.stdout.write(f"CONFLICTO correo={item.pk}")
                    continue
                if item.sent_at is not None:
                    counts["sent"] += 1
                    self.stdout.write(f"BLOQUEADO correo_enviado={item.pk}")
                    continue
                counts["outbox"] += 1
                if apply_changes:
                    metadata["numero_socio"] = numero_socio
                    item.metadata = metadata
                    item.save(update_fields=["metadata"])

        for resolucion in Resolucion.objects.all().iterator():
            if resolucion.estado == EstadoResolucionEnum.ISSUED:
                counts["issued"] += 1
                self.stdout.write(f"BLOQUEADO resolucion_emitida={resolucion.pk}")
                continue
            firmantes = resolucion.firmantes or []
            changed = False
            for firmante in firmantes:
                socio = Socio.objects.filter(user_id=firmante.get("user_id")).first()
                if socio is None or socio.numero_socio is None:
                    counts["unresolved"] += 1
                    continue
                if firmante.get("numero_socio") != socio.numero_socio:
                    firmante["numero_socio"] = socio.numero_socio
                    changed = True
            if not changed:
                continue
            counts["draft"] += 1
            if apply_changes:
                resolucion.firmantes = firmantes
                resolucion.save(update_fields=["firmantes", "updated_at"])

        mode = "aplicada" if apply_changes else "simulada"
        self.stdout.write(
            self.style.SUCCESS(
                f"Reconciliación {mode}: outbox={counts['outbox']}, "
                f"enviados_bloqueados={counts['sent']}, drafts={counts['draft']}, "
                f"emitidas_bloqueadas={counts['issued']}, conflictos={counts['conflicts']}, "
                f"sin_correspondencia={counts['unresolved']}."
            )
        )
