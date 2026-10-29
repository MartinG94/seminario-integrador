# Generated manually for SCRUM-63 TD case concept classification

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("expedientes", "0019_expediente_clasificacion_solicitudt01_clasificacion"),
    ]

    operations = [
        migrations.AddField(
            model_name="expediente",
            name="concepto",
            field=models.CharField(
                blank=True,
                choices=[
                    ("CD", "CD — Comisión Directiva"),
                    ("TD", "TD — Tribunal de Disciplina"),
                    ("GSA", "GSA — Gestión Social y Ambiental"),
                    ("GVP", "GVP — Grupo de Viaje / Gestión de Viaje"),
                    ("COMP", "COMP — Cómputos"),
                    ("RRHH", "RRHH — Recursos Humanos"),
                    ("RRII", "RRII — Relaciones Institucionales"),
                    ("PRENSA", "PRENSA — Prensa y Difusión"),
                    ("MANT", "MANT — Mantenimiento"),
                    ("EVENTOS", "EVENTOS — Organización y Eventos"),
                    ("RIFAS", "RIFAS — Rifas"),
                    ("ASAMBLEA", "ASAMBLEA — Asamblea General"),
                    ("OTROS", "OTROS — Otros Conceptos Institucionales"),
                ],
                db_index=True,
                default=None,
                help_text="Concepto institucional clasificado manualmente por el TD durante la revisión.",
                max_length=20,
                null=True,
            ),
        ),
    ]
