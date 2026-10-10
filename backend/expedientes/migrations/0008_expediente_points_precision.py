from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("expedientes", "0007_expediente_urgencia"),
    ]

    operations = [
        migrations.AlterField(
            model_name="expediente",
            name="puntos",
            field=models.DecimalField(decimal_places=2, default=-1.0, max_digits=10),
        ),
    ]
