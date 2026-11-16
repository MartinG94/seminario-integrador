import re

from django.core.management.base import BaseCommand
from django.db import transaction

from expedientes.models import Expediente, SolicitudT01

NUMBER_RE = re.compile(r"^(?:EXP-)?0*(\d+)/(\d{4})$")


def canonical(value):
    match = NUMBER_RE.match((value or "").strip())
    return f"{int(match.group(1))}/{match.group(2)}" if match else value


class Command(BaseCommand):
    help = "Reporta o normaliza identificadores históricos de expedientes."

    def add_arguments(self, parser):
        parser.add_argument("--apply", action="store_true")

    def handle(self, *args, **options):
        changes = []
        conflicts = []
        for expediente in Expediente.objects.order_by("pk"):
            new_number = canonical(expediente.numero)
            if new_number != expediente.numero:
                if Expediente.objects.filter(numero=new_number).exclude(pk=expediente.pk).exists():
                    conflicts.append(f"expediente:{expediente.pk}:{new_number}")
                else:
                    changes.append((expediente, new_number))
        for solicitud in SolicitudT01.objects.select_related("expediente").order_by("pk"):
            if solicitud.estado == SolicitudT01.Estado.DRAFT:
                if solicitud.numero_expediente is not None:
                    changes.append((solicitud, None))
            elif not solicitud.expediente_id:
                conflicts.append(f"solicitud-emitida-sin-expediente:{solicitud.pk}")
            elif solicitud.numero_expediente != solicitud.expediente.numero:
                changes.append((solicitud, solicitud.expediente.numero))
        self.stdout.write(f"cambios={len(changes)} conflictos={len(conflicts)}")
        for conflict in conflicts:
            self.stdout.write(f"CONFLICTO {conflict}")
        if not options["apply"] or conflicts:
            self.stdout.write("simulación; no se modificaron registros")
            return
        with transaction.atomic():
            for instance, value in changes:
                field = "numero" if isinstance(instance, Expediente) else "numero_expediente"
                instance.__class__.objects.filter(pk=instance.pk).update(**{field: value})
        self.stdout.write(self.style.SUCCESS("reconciliación aplicada"))
