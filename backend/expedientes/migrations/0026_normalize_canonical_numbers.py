"""Normaliza identificadores históricos a n/YYYY de forma transaccional."""

import re

from django.db import migrations


NUMBER_RE = re.compile(r"^(?:EXP-)?0*(\d+)/(\d{4})$")


def canonical(value):
    if not value:
        return value
    match = NUMBER_RE.match(value.strip())
    return f"{int(match.group(1))}/{match.group(2)}" if match else value


def normalize_numbers(apps, schema_editor):
    Expediente = apps.get_model("expedientes", "Expediente")
    SolicitudT01 = apps.get_model("expedientes", "SolicitudT01")
    Sequence = apps.get_model("expedientes", "ExpedienteNumberSequence")

    seen = {}
    original_numbers = {}
    for expediente in Expediente.objects.order_by("pk"):
        original = expediente.numero
        original_numbers[expediente.pk] = original
        numero = canonical(original)
        if numero != expediente.numero:
            other = Expediente.objects.filter(numero=numero).exclude(pk=expediente.pk).first()
            if other:
                raise RuntimeError(
                    f"Colisión histórica de expedientes {expediente.pk} y {other.pk}: {numero}"
                )
            expediente.numero = numero
            expediente.save(update_fields=["numero"])
        if numero:
            if numero in seen and seen[numero] != expediente.pk:
                raise RuntimeError(f"Colisión histórica detectada: {numero}")
            seen[numero] = expediente.pk

    for solicitud in SolicitudT01.objects.select_related("expediente").order_by("pk"):
        if solicitud.estado == "DRAFT":
            if solicitud.numero_expediente is not None:
                SolicitudT01.objects.filter(pk=solicitud.pk).update(
                    numero_expediente=None
                )
            continue
        if not solicitud.expediente_id:
            raise RuntimeError(
                f"Solicitud ISSUED sin expediente asociado: {solicitud.pk}"
            )
        if solicitud.expediente_id:
            raw_numero = original_numbers.get(
                solicitud.expediente_id, solicitud.expediente.numero
            )
            numero = canonical(raw_numero)
            known_number = bool(NUMBER_RE.match((raw_numero or "").strip()))
            legacy_request_number = (solicitud.numero_expediente or "").startswith("T01-")
            if known_number and solicitud.numero_expediente != numero:
                if solicitud.numero_expediente and not legacy_request_number:
                    raise RuntimeError(
                        f"Conflicto de número en solicitud {solicitud.pk}: "
                        f"{solicitud.numero_expediente} != {numero}"
                    )
                SolicitudT01.objects.filter(pk=solicitud.pk).update(
                    numero_expediente=numero
                )

    maxima = {}
    for numero in Expediente.objects.values_list("numero", flat=True):
        match = NUMBER_RE.match(numero or "")
        if match:
            value, year = int(match.group(1)), int(match.group(2))
            maxima[year] = max(maxima.get(year, 0), value)
    for year, last_value in maxima.items():
        Sequence.objects.update_or_create(year=year, defaults={"last_value": last_value})


class Migration(migrations.Migration):
    dependencies = [("expedientes", "0025_resolucion_reglamentos_respaldantes")]
    operations = [migrations.RunPython(normalize_numbers, migrations.RunPython.noop)]
