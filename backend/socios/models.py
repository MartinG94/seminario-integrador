from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Subcomision(models.Model):
    """Una de las 7 subcomisiones estatutarias de AVEIT."""

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name = "Subcomisión"
        verbose_name_plural = "Subcomisiones"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class SocialCategory(models.TextChoices):
    PASSIVE = "PASSIVE", "Pasivo"
    ACTIVE = "ACTIVE", "Activo"


class Role(models.TextChoices):
    """Roles RBAC del sistema. Ver docs/especificaciones/RBAC-SGD-AVEIT.md."""

    SOCIO = "SOCIO", "Socio Ordinario"
    FISCALIZADORA = "FISCALIZADORA", "Autoridad de Subcomisión / Líder de Equipo"
    CD = "CD", "Comisión Directiva"
    TD = "TD", "Tribunal de Disciplina"
    ADMIN = "ADMIN", "Administrador de Cómputos"


class Socio(models.Model):
    """Socio con membresía vigente, vinculado 1:1 con sus credenciales."""

    FIRST_ACTIVE_SOCIAL_YEAR = 4

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="socio",
    )
    legajo = models.CharField(max_length=20, unique=True, db_index=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(max_length=150, unique=True)
    subcomision = models.ForeignKey(
        Subcomision,
        on_delete=models.PROTECT,
        related_name="socios",
        null=True,
        blank=True,
    )
    social_year = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(6)]
    )
    category = models.CharField(max_length=10, choices=SocialCategory.choices)
    role = models.CharField(
        max_length=20, choices=Role.choices, default=Role.SOCIO, db_index=True
    )
    # Vigencia operativa de la cuenta: independiente de `category` (Constitución, ppio. 8).
    is_enabled = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Socio"
        verbose_name_plural = "Socios"
        ordering = ["last_name", "first_name"]

    def __str__(self) -> str:
        return f"{self.last_name}, {self.first_name} ({self.legajo})"

    @classmethod
    def category_for_social_year(cls, social_year: int) -> str:
        """Años 1-3 => Pasivo; años 4-6 => Activo (Constitución, ppio. 8)."""
        if social_year >= cls.FIRST_ACTIVE_SOCIAL_YEAR:
            return SocialCategory.ACTIVE
        return SocialCategory.PASSIVE

    def save(self, *args, **kwargs):
        self.full_clean(exclude=["category"])
        self.category = self.category_for_social_year(self.social_year)
        super().save(*args, **kwargs)
