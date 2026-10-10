"""Importa el calendario vigente sin modificar evidencia ni vencimientos previos."""

from datetime import date

from django.apps.registry import Apps
from django.db import migrations
from django.db.backends.base.schema import BaseDatabaseSchemaEditor

# Pares exactos de la migración 0008, para no atribuir altas humanas al sistema.
SEED_HOLIDAYS = {
    date(2026, 1, 1): "Año Nuevo",
    date(2026, 2, 16): "Carnaval (Lunes)",
    date(2026, 2, 17): "Carnaval (Martes)",
    date(2026, 3, 24): "Día Nacional de la Memoria por la Verdad y la Justicia",
    date(2026, 4, 2): "Día del Veterano y de los Caídos en la Guerra de Malvinas",
    date(2026, 4, 3): "Viernes Santo",
    date(2026, 5, 1): "Día del Trabajador",
    date(2026, 5, 25): "Día de la Revolución de Mayo",
    date(2026, 6, 17): "Paso a la Inmortalidad del Gral. Don Martín Miguel de Güemes",
    date(2026, 6, 20): "Paso a la Inmortalidad del Gral. Manuel Belgrano",
    date(2026, 7, 9): "Día de la Independencia",
    date(2026, 8, 17): "Paso a la Inmortalidad del Gral. José de San Martín",
    date(2026, 10, 12): "Día del Respeto a la Diversidad Cultural",
    date(2026, 11, 20): "Día de la Soberanía Nacional",
    date(2026, 12, 8): "Inmaculada Concepción de María",
    date(2026, 12, 25): "Navidad",
}

# Fechas trasladadas verificadas con Cancillería; corrección aprobada por usuario.
# https://clond.cancilleria.gob.ar/es/node/1986
OFFICIAL_TRANSFERS = {date(2026, 6, 17): date(2026, 6, 15), date(2026, 11, 20): date(2026, 11, 23)}


def import_current_holidays(apps: Apps, schema_editor: BaseDatabaseSchemaEditor) -> None:
    alias = schema_editor.connection.alias
    calendar_model = apps.get_model("expedientes", "CalendarioVersion")
    legacy_model = apps.get_model("expedientes", "FeriadoExcepcion")
    holiday_model = apps.get_model("expedientes", "Holiday")
    active = calendar_model.objects.using(alias).filter(activa=True).order_by("-version").first()
    if active is None:
        return

    current = list(
        legacy_model.objects.using(alias)
        .filter(calendario_version_id=active.pk, es_laborable=False)
        .order_by("fecha", "pk")
    )
    imported = {}
    for previous in current:
        matches_seed = (
            active.version == 1 and SEED_HOLIDAYS.get(previous.fecha) == previous.descripcion
        )
        target_date = (
            OFFICIAL_TRANSFERS.get(previous.fecha, previous.fecha)
            if matches_seed
            else previous.fecha
        )
        origin = "SYSTEM" if matches_seed and active.version == 1 else "LEGACY"
        # Ante coincidencia, conservar el registro ya situado en la fecha correcta.
        if target_date not in imported or previous.fecha == target_date:
            imported[target_date] = holiday_model(
                date=target_date,
                description=previous.descripcion,
                created_by_id=None,
                created_at=previous.created_at,
                origin=origin,
            )
    holiday_model.objects.using(alias).bulk_create(imported.values())


class Migration(migrations.Migration):
    dependencies = [("expedientes", "0009_institutional_calendar")]
    operations = [migrations.RunPython(import_current_holidays, migrations.RunPython.noop)]
