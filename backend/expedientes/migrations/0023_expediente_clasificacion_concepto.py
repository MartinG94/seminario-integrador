# Generated manually for SCRUM-63 TD case concept classification & reports

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("expedientes", "0022_merge_20261103_2119"),
    ]

    operations = [
        migrations.AddField(
            model_name="expediente",
            name="clasificacion",
            field=models.CharField(
                choices=[
                    ("CD", "Comisión Directiva"),
                    ("RRHH", "Recursos Humanos"),
                    ("PRENSA", "Prensa y Difusión"),
                    ("OYE", "Organización y Eventos"),
                    ("GSA", "Gestión Social y Ambiental"),
                    ("RII", "Relaciones Institucionales"),
                    ("COMPUTOS", "Cómputos"),
                    ("TD", "Tribunal de Disciplina"),
                    ("CR", "Comisión Rifaria"),
                    ("MANTENIMIENTO", "Mantenimiento"),
                    ("RC", "Revisores de Cuentas"),
                    ("GVP", "Grupo de Viaje y Permanencia"),
                    ("GENERAL", "General"),
                ],
                db_index=True,
                default="GENERAL",
                help_text="Concepto o subcomisión clasificadora asignada por TD.",
                max_length=50,
            ),
        ),
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
        migrations.AddField(
            model_name="solicitudt01",
            name="clasificacion",
            field=models.CharField(
                choices=[
                    ("CD", "Comisión Directiva"),
                    ("RRHH", "Recursos Humanos"),
                    ("PRENSA", "Prensa y Difusión"),
                    ("OYE", "Organización y Eventos"),
                    ("GSA", "Gestión Social y Ambiental"),
                    ("RII", "Relaciones Institucionales"),
                    ("COMPUTOS", "Cómputos"),
                    ("TD", "Tribunal de Disciplina"),
                    ("CR", "Comisión Rifaria"),
                    ("MANTENIMIENTO", "Mantenimiento"),
                    ("RC", "Revisores de Cuentas"),
                    ("GVP", "Grupo de Viaje y Permanencia"),
                    ("GENERAL", "General"),
                ],
                db_index=True,
                default="GENERAL",
                help_text="Concepto o subcomisión clasificadora asignada por TD.",
                max_length=50,
            ),
        ),
    ]
