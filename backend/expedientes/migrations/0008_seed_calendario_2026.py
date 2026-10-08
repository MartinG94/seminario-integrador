# Generated manually for seeding initial 2026 institutional calendar

from datetime import date
from django.db import migrations


def seed_calendario_2026(apps, schema_editor):
    CalendarioVersion = apps.get_model("expedientes", "CalendarioVersion")
    FeriadoExcepcion = apps.get_model("expedientes", "FeriadoExcepcion")

    # Si ya existe una versión 1, no duplicar
    cal_version, created = CalendarioVersion.objects.get_or_create(
        version=1,
        defaults={
            "nombre": "Calendario Oficial AVEIT 2026",
            "vigencia_desde": date(2026, 1, 1),
            "vigencia_hasta": None,
            "activa": True,
            "motivo_cambio": "Carga inicial del calendario institucional con los feriados nacionales oficiales de Argentina para el ciclo lectivo 2026 (CA2).",
        },
    )

    holidays = [
        (date(2026, 1, 1), "Año Nuevo", "NACIONAL"),
        (date(2026, 2, 16), "Carnaval (Lunes)", "NACIONAL"),
        (date(2026, 2, 17), "Carnaval (Martes)", "NACIONAL"),
        (date(2026, 3, 24), "Día Nacional de la Memoria por la Verdad y la Justicia", "NACIONAL"),
        (date(2026, 4, 2), "Día del Veterano y de los Caídos en la Guerra de Malvinas", "NACIONAL"),
        (date(2026, 4, 3), "Viernes Santo", "NACIONAL"),
        (date(2026, 5, 1), "Día del Trabajador", "NACIONAL"),
        (date(2026, 5, 25), "Día de la Revolución de Mayo", "NACIONAL"),
        (date(2026, 6, 17), "Paso a la Inmortalidad del Gral. Don Martín Miguel de Güemes", "NACIONAL"),
        (date(2026, 6, 20), "Paso a la Inmortalidad del Gral. Manuel Belgrano", "NACIONAL"),
        (date(2026, 7, 9), "Día de la Independencia", "NACIONAL"),
        (date(2026, 8, 17), "Paso a la Inmortalidad del Gral. José de San Martín", "NACIONAL"),
        (date(2026, 10, 12), "Día del Respeto a la Diversidad Cultural", "NACIONAL"),
        (date(2026, 11, 20), "Día de la Soberanía Nacional", "NACIONAL"),
        (date(2026, 12, 8), "Inmaculada Concepción de María", "NACIONAL"),
        (date(2026, 12, 25), "Navidad", "NACIONAL"),
    ]

    for f_date, desc, tipo in holidays:
        FeriadoExcepcion.objects.get_or_create(
            calendario_version=cal_version,
            fecha=f_date,
            defaults={
                "descripcion": desc,
                "tipo": tipo,
                "es_laborable": False,
            },
        )


def reverse_seed_calendario_2026(apps, schema_editor):
    CalendarioVersion = apps.get_model("expedientes", "CalendarioVersion")
    CalendarioVersion.objects.filter(version=1).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("expedientes", "0007_calendarioversion_feriadoexcepcion_and_more"),
    ]

    operations = [
        migrations.RunPython(seed_calendario_2026, reverse_seed_calendario_2026),
    ]
