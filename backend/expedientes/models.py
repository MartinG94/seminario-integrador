import uuid

from django.core.exceptions import ValidationError
from django.db import models

from socios.models import Socio


class SolicitudT01(models.Model):
    class Estado(models.TextChoices):
        DRAFT = "DRAFT", "Borrador"
        ISSUED = "ISSUED", "Emitida"

    class TipoAccion(models.TextChoices):
        SANCTION = "SANCTION", "Sanción"
        MERIT = "MERIT", "Mérito"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    estado = models.CharField(max_length=10, choices=Estado.choices, default=Estado.DRAFT)
    solicitante = models.ForeignKey(Socio, on_delete=models.PROTECT)
    destinatario_socio_id = models.PositiveBigIntegerField(null=True, blank=True)
    tipo_accion = models.CharField(max_length=10, choices=TipoAccion.choices)
    causal = models.CharField(max_length=255, blank=True)
    puntos = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    motivo = models.TextField(blank=True)
    anexo_fecha = models.DateField(null=True, blank=True)
    anexo_lugar = models.CharField(max_length=255, blank=True)
    anexo_relato = models.TextField(blank=True)
    anexo_testigos = models.TextField(blank=True)
    snapshot_destinatario = models.JSONField(null=True, blank=True)
    snapshot_emitido = models.JSONField(null=True, blank=True)
    numero_expediente = models.CharField(max_length=40, null=True, blank=True, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    issued_at = models.DateTimeField(null=True, blank=True)

    def clean(self):
        if self.estado == self.Estado.ISSUED and self.puntos is None:
            raise ValidationError({"puntos": "Los puntos son obligatorios al emitir."})
        if self.puntos is not None and self.tipo_accion:
            if self.tipo_accion == self.TipoAccion.SANCTION and self.puntos >= 0:
                raise ValidationError({"puntos": "Una sanción debe tener puntos negativos."})
            if self.tipo_accion == self.TipoAccion.MERIT and self.puntos <= 0:
                raise ValidationError({"puntos": "Un mérito debe tener puntos positivos."})

    def save(self, *args, **kwargs):
        if self.pk and not self._state.adding:
            previous = type(self).objects.filter(pk=self.pk).values("estado").first()
            if previous and previous["estado"] == self.Estado.ISSUED:
                raise ValidationError("Una solicitud emitida es inmutable.")
        self.full_clean()
        return super().save(*args, **kwargs)
