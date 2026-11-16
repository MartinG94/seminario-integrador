"""Backfill seguro de numero_socio desde el vínculo institucional user_id."""

from django.core.management.base import BaseCommand

from padron.models import Socio as SocioInstitucional
from socios.models import Socio


class Command(BaseCommand):
    help = "Reporta o asigna numero_socio mediante socio_lista.user_id; por defecto simula."

    def add_arguments(self, parser):
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Persiste únicamente correspondencias inequívocas.",
        )

    def handle(self, *args, **options):
        apply_changes = options["apply"]
        assigned = 0
        unchanged = 0
        ambiguous = 0
        unresolved = 0
        conflicts = 0

        for socio in Socio.objects.all().iterator():
            candidates = list(
                SocioInstitucional.objects.filter(user_id=socio.user_id).values_list(
                    "nroSocio", flat=True
                )
            )
            if len(candidates) == 0:
                unresolved += 1
                self.stdout.write(f"SIN CORRESPONDENCIA socio_local={socio.pk}")
                continue
            if len(candidates) > 1:
                ambiguous += 1
                self.stdout.write(
                    f"AMBIGUO socio_local={socio.pk} candidatos={','.join(map(str, candidates))}"
                )
                continue

            numero_socio = candidates[0]
            duplicate = (
                Socio.objects.filter(numero_socio=numero_socio).exclude(pk=socio.pk).exists()
            )
            if duplicate or (socio.numero_socio is not None and socio.numero_socio != numero_socio):
                conflicts += 1
                self.stdout.write(f"CONFLICTO socio_local={socio.pk}")
                continue
            if socio.numero_socio == numero_socio:
                unchanged += 1
                continue
            assigned += 1
            self.stdout.write(
                f"{'ASIGNAR' if apply_changes else 'SIMULAR'} "
                f"socio_local={socio.pk} numero_socio={numero_socio}"
            )
            if apply_changes:
                socio.numero_socio = numero_socio
                socio.save(update_fields=["numero_socio"])

        mode = "aplicado" if apply_changes else "simulación"
        self.stdout.write(
            self.style.SUCCESS(
                f"Backfill {mode}: asignados={assigned}, sin_cambios={unchanged}, "
                f"ambiguos={ambiguous}, sin_correspondencia={unresolved}, "
                f"conflictos={conflicts}."
            )
        )
