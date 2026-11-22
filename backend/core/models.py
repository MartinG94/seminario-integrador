"""Modelos de administración del sistema (Spec 011): sólo inserción, nunca se editan."""

from __future__ import annotations

from typing import Any, NoReturn

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

IMMUTABLE_MESSAGE = "Los registros de auditoría son inmutables."
UNDELETABLE_MESSAGE = "Los registros de auditoría no pueden eliminarse."


class AppendOnlyQuerySet(models.QuerySet):
    """Bloquea las modificaciones y bajas masivas que eluden `Model.save()`/`delete()`."""

    def update(self, **kwargs: Any) -> NoReturn:
        raise ValidationError(IMMUTABLE_MESSAGE)

    def delete(self) -> NoReturn:
        raise ValidationError(UNDELETABLE_MESSAGE)

    def bulk_update(self, objs: Any, fields: Any, batch_size: int | None = None) -> NoReturn:
        raise ValidationError(IMMUTABLE_MESSAGE)

    def bulk_create(self, objs: Any, *args: Any, **kwargs: Any) -> list[Any]:
        if kwargs.get("update_conflicts") or kwargs.get("ignore_conflicts"):
            raise ValidationError(IMMUTABLE_MESSAGE)
        return super().bulk_create(objs, *args, **kwargs)

    def update_or_create(self, *args: Any, **kwargs: Any) -> NoReturn:
        raise ValidationError(IMMUTABLE_MESSAGE)


class AppendOnlyModel(models.Model):
    """Registro de auditoría: se inserta una vez y no admite cambios ni bajas."""

    objects = AppendOnlyQuerySet.as_manager()

    class Meta:
        abstract = True

    def save(self, *args: Any, **kwargs: Any) -> None:
        if not self._state.adding or kwargs.get("force_update") or kwargs.get("update_fields"):
            raise ValidationError(IMMUTABLE_MESSAGE)
        if self.pk is not None and type(self).objects.filter(pk=self.pk).exists():
            raise ValidationError(IMMUTABLE_MESSAGE)
        kwargs["force_insert"] = True
        super().save(*args, **kwargs)

    def delete(self, *args: Any, **kwargs: Any) -> NoReturn:
        raise ValidationError(UNDELETABLE_MESSAGE)


class SystemParameterChange(AppendOnlyModel):
    """Cambio de un parámetro del sistema; el valor vigente es el último de cada clave."""

    key = models.CharField(max_length=50)
    value = models.JSONField()
    previous_value = models.JSONField(null=True, blank=True)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name="+"
    )
    created_at = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        db_table = "core_parametro_sistema"
        ordering = ["-created_at", "-id"]
        indexes = [models.Index(fields=["key", "created_at"], name="core_param_clave_fecha")]
        verbose_name = "Parámetro del sistema"
        verbose_name_plural = "Parámetros del sistema"

    def __str__(self) -> str:
        return f"{self.key} = {self.value}"


class TribunalRoleAction(models.TextChoices):
    GRANT = "ALTA", "Alta en el Tribunal"
    REVOKE = "BAJA", "Baja del Tribunal"


class TribunalRoleChange(AppendOnlyModel):
    """Alta o baja del rol TD de un socio, con su autoría."""

    socio = models.ForeignKey(
        "socios.Socio", on_delete=models.PROTECT, related_name="tribunal_role_changes"
    )
    action = models.CharField(max_length=10, choices=TribunalRoleAction.choices)
    previous_role = models.CharField(max_length=20)
    new_role = models.CharField(max_length=20)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    created_at = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        db_table = "core_cambio_rol_tribunal"
        ordering = ["-created_at", "-id"]
        verbose_name = "Cambio de rol del Tribunal"
        verbose_name_plural = "Cambios de rol del Tribunal"

    def __str__(self) -> str:
        return f"{self.action} {self.socio_id}"
