"""Registro técnico de propiedad de datos sintéticos, separado del dominio."""

from django.db import models


class DemoFixtureOwnership(models.Model):
    """Vincula una clave estable de catálogo con una identidad física sin secretos."""

    profile = models.CharField(max_length=80, db_collation="utf8mb4_bin")
    fixture_key = models.CharField(max_length=160, db_collation="utf8mb4_bin")
    namespace = models.CharField(max_length=100, db_collation="utf8mb4_bin")
    object_key = models.CharField(max_length=80, db_collation="utf8mb4_bin")
    owned = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["profile", "fixture_key"], name="demo_fixture_profile_key_uq"
            ),
            models.UniqueConstraint(
                fields=["namespace", "object_key"], name="demo_fixture_target_uq"
            ),
        ]
        ordering = ["fixture_key"]

    def __str__(self) -> str:
        return f"{self.profile}: {self.fixture_key}"
