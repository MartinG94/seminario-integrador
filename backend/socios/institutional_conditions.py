"""Condición confirmada del padrón; no altera su ficha ni las facultades del socio."""

from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING, Any

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import connections, models, router, transaction
from django.db.models.functions import Length, Trim
from django.db.models.lookups import Exact

if TYPE_CHECKING:
    from padron.models import Socio as InstitutionalSocio


class InstitutionalConditionQuerySet(models.QuerySet):
    """Las escrituras masivas no pueden omitir la validación de asociación."""

    def update(self, **kwargs: Any) -> int:
        raise ValidationError("La condición institucional no admite modificaciones masivas.")

    def bulk_create(
        self,
        objs: Iterable[InstitutionalMembershipCondition],
        batch_size: int | None = None,
        ignore_conflicts: bool = False,
        update_conflicts: bool = False,
        update_fields: Iterable[str] | None = None,
        unique_fields: Iterable[str] | None = None,
    ) -> list[InstitutionalMembershipCondition]:
        raise ValidationError("Registrá cada condición con su asociación institucional validada.")

    def bulk_update(
        self,
        objs: Iterable[InstitutionalMembershipCondition],
        fields: Iterable[str],
        batch_size: int | None = None,
    ) -> int:
        raise ValidationError("La condición institucional no admite modificaciones masivas.")

    def delete(self) -> tuple[int, dict[str, int]]:
        raise ValidationError("La condición confirmada se conserva con su fuente y corte.")


class InstitutionalMembershipCondition(models.Model):
    """Referencia explícita por nroSocio; sin FK hacia una tabla ajena a migrate."""

    institutional_number = models.IntegerField(
        primary_key=True,
        validators=[MinValueValidator(1), MaxValueValidator(2147483647)],
    )
    condition = models.CharField(
        max_length=12,
        choices=[("EX_TRAVELER", "Exviajero")],
        db_collation="utf8mb4_bin",
    )
    source_reference = models.CharField(max_length=200)
    social_cycle = models.CharField(max_length=80)
    objects = InstitutionalConditionQuerySet.as_manager()

    class Meta:
        constraints = [
            models.CheckConstraint(
                name="institutional_condition_values_ck",
                check=models.Q(institutional_number__gte=1, condition="EX_TRAVELER")
                & Exact(Length("condition"), len("EX_TRAVELER"))
                & ~Exact(Length(Trim("source_reference")), 0)
                & ~Exact(Length(Trim("social_cycle")), 0),
            )
        ]

    def _validate_values(self) -> None:
        if (
            isinstance(self.institutional_number, bool)
            or not isinstance(self.institutional_number, int)
            or not 1 <= self.institutional_number <= 2147483647
        ):
            raise ValidationError({"institutional_number": "El número institucional no es válido."})
        if self.condition != "EX_TRAVELER":
            raise ValidationError({"condition": "La condición debe confirmarse explícitamente."})
        for field in ("source_reference", "social_cycle"):
            value = getattr(self, field)
            if not isinstance(value, str) or not value.strip():
                raise ValidationError({field: "La fuente y el corte social son obligatorios."})

    def _validate_reference(self, alias: str, *, lock: bool = False) -> None:
        from padron.models import Socio as InstitutionalSocio

        queryset = InstitutionalSocio.objects.using(alias).filter(nroSocio=self.pk)
        if lock:
            queryset = queryset.select_for_update()
        reference = queryset.values("anoSocial").first()
        if reference is None:
            raise ValidationError({"institutional_number": "No existe el socio institucional."})
        if reference["anoSocial"] is not None:
            raise ValidationError({"condition": "Un socio exviajero no tiene año social."})

    def clean(self) -> None:
        super().clean()
        self._validate_values()
        alias = self._state.db or router.db_for_write(type(self), instance=self)
        self._validate_reference(alias)

    def save(
        self,
        force_insert: bool = False,
        force_update: bool = False,
        using: str | None = None,
        update_fields: Iterable[str] | None = None,
    ) -> None:
        alias = using or self._state.db or router.db_for_write(type(self), instance=self)
        if self._state.db is not None and self._state.db != alias:
            raise ValidationError("La referencia pertenece a otra conexión institucional.")
        self._validate_values()
        self._state.db = alias
        with transaction.atomic(using=alias):
            self._validate_reference(alias, lock=True)
            self.full_clean(validate_unique=False, validate_constraints=False)
            existing = (
                type(self).objects.using(alias).select_for_update().filter(pk=self.pk).first()
            )
            if existing is not None:
                if force_insert or self._state.adding:
                    raise ValidationError(
                        {"institutional_number": "La identidad ya está registrada."}
                    )
                if any(
                    getattr(existing, field) != getattr(self, field)
                    for field in ("condition", "source_reference", "social_cycle")
                ):
                    raise ValidationError("No se sobrescribe una condición de otra fuente o corte.")
                return
            if force_update or update_fields is not None or not self._state.adding:
                raise ValidationError("No se puede modificar una condición ausente.")
            super().save(force_insert=True, using=alias)

    def delete(self, using: str | None = None, keep_parents: bool = False) -> None:
        raise ValidationError("La condición confirmada se conserva con su fuente y corte.")


def register_ex_traveler(
    *,
    institutional_member: InstitutionalSocio,
    source_reference: str,
    social_cycle: str,
    using: str | None = None,
) -> InstitutionalMembershipCondition:
    """Registro idempotente con asociación validada y rollback junto a su llamador.

    La propiedad del catálogo/grupo se acredita en el seed posterior; esta API no
    deduce condición desde ID, cargo, baja o año inválido, ni escribe en el padrón.
    """
    from padron.models import Socio as InstitutionalSocio

    if (
        not isinstance(institutional_member, InstitutionalSocio)
        or institutional_member._state.adding
    ):
        raise ValidationError("Se requiere una referencia institucional persistida.")
    alias = using or institutional_member._state.db or "default"
    if alias not in connections.databases or institutional_member._state.db != alias:
        raise ValidationError("La referencia pertenece a otra conexión institucional.")
    candidate = InstitutionalMembershipCondition(
        institutional_number=institutional_member.nroSocio,
        condition="EX_TRAVELER",
        source_reference=source_reference,
        social_cycle=social_cycle,
    )
    candidate._state.db = alias
    candidate._validate_values()
    with transaction.atomic(using=alias):
        candidate._validate_reference(alias, lock=True)
        candidate.full_clean(validate_unique=False, validate_constraints=False)
        existing = (
            InstitutionalMembershipCondition.objects.using(alias)
            .select_for_update()
            .filter(pk=candidate.pk)
            .first()
        )
        if existing is not None:
            if any(
                getattr(existing, field) != getattr(candidate, field)
                for field in ("condition", "source_reference", "social_cycle")
            ):
                raise ValidationError("No se sobrescribe una condición de otra fuente o corte.")
            return existing
        candidate.save(force_insert=True, using=alias)
        return candidate
