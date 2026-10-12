"""Propiedad persistente del catálogo; no modifica tablas ni datos institucionales."""

from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = []

    operations = [
        migrations.CreateModel(
            name="DemoFixtureOwnership",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("profile", models.CharField(db_collation="utf8mb4_bin", max_length=80)),
                ("fixture_key", models.CharField(db_collation="utf8mb4_bin", max_length=160)),
                ("namespace", models.CharField(db_collation="utf8mb4_bin", max_length=100)),
                ("object_key", models.CharField(db_collation="utf8mb4_bin", max_length=80)),
                ("owned", models.BooleanField(default=True)),
            ],
            options={"ordering": ["fixture_key"]},
        ),
        migrations.AddConstraint(
            model_name="demofixtureownership",
            constraint=models.UniqueConstraint(
                fields=("profile", "fixture_key"), name="demo_fixture_profile_key_uq"
            ),
        ),
        migrations.AddConstraint(
            model_name="demofixtureownership",
            constraint=models.UniqueConstraint(
                fields=("namespace", "object_key"), name="demo_fixture_target_uq"
            ),
        ),
    ]
