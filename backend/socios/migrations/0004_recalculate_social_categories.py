"""TS77.33: recálculo histórico local, transaccional y sin modificar otros datos."""

from django.db import migrations, transaction
from django.db.backends.base.schema import BaseDatabaseSchemaEditor
from django.db.migrations.state import StateApps


def _rewrite_categories(
    apps: StateApps, schema_editor: BaseDatabaseSchemaEditor, *, legacy: bool
) -> None:
    """Validar todo el historial bloqueado antes de escribir sólo categorías."""
    socio = apps.get_model("socios", "Socio")
    alias = schema_editor.connection.alias
    # Regla congelada en la migración: no depender del modelo/clasificador vivo.
    first_category, second_category, threshold = (
        ("PASSIVE", "ACTIVE", 4) if legacy else ("JUNIOR", "SENIOR", 3)
    )
    changes: dict[str, list[int]] = {first_category: [], second_category: []}
    with transaction.atomic(using=alias):
        rows = (
            socio.objects.using(alias)
            .select_for_update()
            .order_by("pk")
            .values_list("pk", "social_year", "category")
        )
        for pk, year, category in rows:
            if category == "EX_TRAVELER" and year is None:
                continue
            if (
                category not in {"PASSIVE", "ACTIVE", "JUNIOR", "SENIOR"}
                or isinstance(year, bool)
                or not isinstance(year, int)
                or not 1 <= year <= 6
            ):
                raise RuntimeError(
                    "Hay socios con categoría o año social incompatibles; "
                    "se requiere revisar esos datos antes de recategorizar el historial."
                )
            expected_category = second_category if year >= threshold else first_category
            if category != expected_category:
                changes[expected_category].append(pk)
        for category, identifiers in changes.items():
            if identifiers:
                socio.objects.using(alias).filter(pk__in=identifiers).update(category=category)


def recalculate_categories(apps: StateApps, schema_editor: BaseDatabaseSchemaEditor) -> None:
    _rewrite_categories(apps, schema_editor, legacy=False)


def restore_legacy_categories(apps: StateApps, schema_editor: BaseDatabaseSchemaEditor) -> None:
    """Restaurar el corte 4 del baseline por año; conservar EX_TRAVELER/null.

    Reversión semántica: no recupera etiquetas arbitrarias ni ediciones posteriores.
    La migración predecesora ya admite exviajeros y el año social se conserva.
    """
    _rewrite_categories(apps, schema_editor, legacy=True)


class Migration(migrations.Migration):
    dependencies = [
        ("socios", "0003_local_social_categories"),
    ]

    operations = [
        # El cuerpo define su transacción también al ensayarse directamente.
        migrations.RunPython(recalculate_categories, restore_legacy_categories, atomic=False),
    ]
