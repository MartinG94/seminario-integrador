"""Une los historiales de la decisión por causal T02 y las versiones de descargo."""

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("expedientes", "0013_decision_causal_descargo"),
        ("expedientes", "0014_backfill_descargo_version_inicial"),
    ]

    operations = []
