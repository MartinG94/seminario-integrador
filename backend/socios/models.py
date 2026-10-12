from collections.abc import Iterable

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models.functions import Length
from django.db.models.lookups import Exact

from socios.institutional_conditions import InstitutionalMembershipCondition  # noqa: F401


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
    JUNIOR = "JUNIOR", "Junior"
    SENIOR = "SENIOR", "Senior"
    EX_TRAVELER = "EX_TRAVELER", "Exviajero"


class Role(models.TextChoices):
    """Roles RBAC del sistema. Ver docs/especificaciones/RBAC-SGD-AVEIT.md."""

    SOCIO = "SOCIO", "Socio Ordinario"
    FISCALIZADORA = "FISCALIZADORA", "Autoridad de Subcomisión / Líder de Equipo"
    CD = "CD", "Comisión Directiva"
    TD = "TD", "Tribunal de Disciplina"
    ADMIN = "ADMIN", "Administrador de Cómputos"


class Socio(models.Model):
    """Socio operativo, vinculado 1:1 con sus credenciales y vigencia independiente."""

    FIRST_SENIOR_SOCIAL_YEAR: int = 3

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
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(6)],
    )
    category = models.CharField(max_length=12, choices=SocialCategory.choices)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.SOCIO, db_index=True)
    # Vigencia operativa de la cuenta: independiente de `category` (Constitución, ppio. 8).
    is_enabled = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Socio"
        verbose_name_plural = "Socios"
        ordering = ["last_name", "first_name"]
        constraints = [
            models.CheckConstraint(
                name="socios_category_social_year_ck",
                check=(
                    models.Q(category__regex=r"^EX_TRAVELER$", social_year__isnull=True)
                    & Exact(Length("category"), len(SocialCategory.EX_TRAVELER))
                )
                | (
                    ~models.Q(category=SocialCategory.EX_TRAVELER)
                    & models.Q(social_year__isnull=False, social_year__gte=1, social_year__lte=6)
                ),
            )
        ]

    def __str__(self) -> str:
        return f"{self.last_name}, {self.first_name} ({self.legajo})"

    @classmethod
    def category_for_social_year(cls, social_year: int) -> str:
        """Junior en años 1–2 y Senior en 3–6; el año no determina condición exviajero."""
        if (
            isinstance(social_year, bool)
            or not isinstance(social_year, int)
            or not 1 <= social_year <= 6
        ):
            raise ValidationError({"social_year": "El año social debe ser un entero entre 1 y 6."})
        if social_year >= cls.FIRST_SENIOR_SOCIAL_YEAR:
            return SocialCategory.SENIOR
        return SocialCategory.JUNIOR

    def clean(self) -> None:
        super().clean()
        if self.category == SocialCategory.EX_TRAVELER:
            if self.social_year is not None:
                raise ValidationError({"social_year": "Un socio exviajero no tiene año social."})
        elif self.social_year is None:
            raise ValidationError(
                {"social_year": "El año social es obligatorio salvo condición exviajero explícita."}
            )

    def save(
        self,
        force_insert: bool = False,
        force_update: bool = False,
        using: str | None = None,
        update_fields: Iterable[str] | None = None,
    ) -> None:
        self.full_clean(exclude=["category"])
        if self.category != SocialCategory.EX_TRAVELER:
            self.category = self.category_for_social_year(self.social_year)
        if update_fields is not None:
            update_fields = frozenset(update_fields)
            if update_fields & {"category", "social_year"}:
                update_fields |= {"category", "social_year"}
        super().save(
            force_insert=force_insert,
            force_update=force_update,
            using=using,
            update_fields=update_fields,
        )
