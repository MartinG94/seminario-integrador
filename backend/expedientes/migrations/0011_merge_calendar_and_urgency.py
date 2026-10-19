"""Une los historiales publicados del calendario institucional y la urgencia."""

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("expedientes", "0010_import_institutional_holidays"),
        ("expedientes", "0008_expediente_points_precision"),
    ]

    operations = []
