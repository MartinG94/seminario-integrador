"""Modelos de administración del sistema (Spec 010): sólo inserción, nunca se editan."""

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class AppendOnlyModel(models.Model):
    """Registro de auditoría: se inserta una vez y no admite cambios ni bajas."""

    class Meta:
        abstract = True

    def save(self, *args, **kwargs) -> None:
        if not self._state.adding:
            raise ValidationError("Los registros de auditoría son inmutables.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Los registros de auditoría no pueden eliminarse.")


class ParametroSistema(AppendOnlyModel):
    """Cambio de un parámetro del sistema; el valor vigente es el último de cada clave."""

    clave = models.CharField(max_length=50)
    valor = models.JSONField()
    valor_anterior = models.JSONField(null=True, blank=True)
    autor = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name="+"
    )
    created_at = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        db_table = "core_parametro_sistema"
        ordering = ["-created_at", "-id"]
        indexes = [models.Index(fields=["clave", "created_at"], name="core_param_clave_fecha")]
        verbose_name = "Parámetro del sistema"
        verbose_name_plural = "Parámetros del sistema"

    def __str__(self) -> str:
        return f"{self.clave} = {self.valor}"


class AccionRolTribunal(models.TextChoices):
    ALTA = "ALTA", "Alta en el Tribunal"
    BAJA = "BAJA", "Baja del Tribunal"


class CambioRolTribunal(AppendOnlyModel):
    """Alta o baja del rol TD de un socio, con su autoría."""

    socio = models.ForeignKey(
        "socios.Socio", on_delete=models.PROTECT, related_name="cambios_rol_tribunal"
    )
    accion = models.CharField(max_length=10, choices=AccionRolTribunal.choices)
    rol_anterior = models.CharField(max_length=20)
    rol_nuevo = models.CharField(max_length=20)
    autor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    created_at = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        db_table = "core_cambio_rol_tribunal"
        ordering = ["-created_at", "-id"]
        verbose_name = "Cambio de rol del Tribunal"
        verbose_name_plural = "Cambios de rol del Tribunal"

    def __str__(self) -> str:
        return f"{self.accion} {self.socio_id}"
