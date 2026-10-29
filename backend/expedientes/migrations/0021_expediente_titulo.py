# Generated for Expediente.titulo

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("expedientes", "0020_expediente_concepto"),
    ]

    operations = [
        migrations.AddField(
            model_name="expediente",
            name="titulo",
            field=models.CharField(
                blank=True,
                default="",
                help_text="Título breve institucional del expediente.",
                max_length=255,
            ),
        ),
    ]
