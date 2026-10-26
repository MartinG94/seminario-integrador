from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("expedientes", "0016_merge_20261021_0916")]
    operations = [
        migrations.CreateModel(
            name="Resolucion",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("version", models.PositiveIntegerField(default=1)),
                ("plantilla_version", models.CharField(max_length=50)),
                ("estado", models.CharField(choices=[("DRAFT", "Borrador"), ("ISSUED", "Emitida")], default="DRAFT", max_length=10)),
                ("numero_expediente_snapshot", models.CharField(max_length=50)),
                ("vistos", models.TextField(blank=True, default="")),
                ("considerandos", models.TextField(blank=True, default="")),
                ("articulos_resolutivos", models.TextField(blank=True, default="")),
                ("puntos_finales", models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ("medidas", models.JSONField(blank=True, default=list)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("issued_at", models.DateTimeField(blank=True, null=True)),
                ("contenido_hash", models.CharField(blank=True, default="", max_length=64)),
                ("created_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="resoluciones_creadas", to=settings.AUTH_USER_MODEL)),
                ("expediente", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="resoluciones", to="expedientes.expediente")),
                ("issued_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="resoluciones_emitidas", to=settings.AUTH_USER_MODEL)),
            ],
            options={"db_table": "expedientes_resolucion"},
        ),
        migrations.AddConstraint(model_name="resolucion", constraint=models.UniqueConstraint(fields=("expediente", "version"), name="unique_resolucion_version")),
    ]
