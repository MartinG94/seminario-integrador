"""Modelos de persistencia para expedientes disciplinarios y plazos procesales.

Implementa:
- Expediente con los 6 estados canónicos (Art. 12 Reglamento Procesal 2026).
- Congelamiento inmutable de plazo_limite_at.
- Auditoría estricta de cambios de estado mediante CambioEstadoExpediente.
- Integración transaccional con libro mayor.
"""

from datetime import datetime
from typing import TYPE_CHECKING
import uuid

from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils import timezone

from expedientes.domain.calendar import compute_business_deadline
from expedientes.domain.holiday_provider import Argentina2026HolidayProvider

if TYPE_CHECKING:
    from expedientes.domain.ports import HolidayProviderPort


class EstadoExpedienteEnum(models.TextChoices):
    """Los 6 estados oficiales del expediente conforme al Art. 12 del Reglamento Procesal 2026."""

    CREADO = "creado", "Expediente Creado"
    JUSTIFICANDO = "justificando", "En período de justificaciones"
    REVISION_RESOLUCION = "revision_resolucion", "Justificaciones en revisión"
    ESPERA_RESOLUCION = "espera_resolucion", "Espera de resolución"
    PENDIENTE_CORREOS = "pendiente_correos", "Pendiente de correos"
    EMITIDO = "emitido", "Expedientes ya emitidos"


class TipoDescargoEnum(models.TextChoices):
    """Tipos de formularios de justificación y descargos admitidos."""

    T02_CERTIFICADO = "T02_CERTIFICADO", "Formulario T02 - Causal con Certificado"
    T03_EXTRAORDINARIO = "T03_EXTRAORDINARIO", "Formulario T03 - Extraordinario"


class Expediente(models.Model):
    """Expediente disciplinario o mérito institucional."""

    numero = models.CharField(max_length=50, unique=True, db_index=True)
    socio = models.ForeignKey(
        "socios.Socio",
        on_delete=models.PROTECT,
        related_name="expedientes",
        db_index=True,
    )
    motivo = models.TextField()
    puntos = models.DecimalField(max_digits=5, decimal_places=2, default=-1.0)
    estado = models.CharField(
        max_length=30,
        choices=EstadoExpedienteEnum.choices,
        default=EstadoExpedienteEnum.CREADO,
        db_index=True,
    )
    # Plazos procesales perentorios (CA1 y CA2)
    plazo_inicio_at = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Timestamp inmutable de notificación/apertura del acuse de sanción (S2-04).",
    )
    plazo_limite_at = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Deadline congelado computado en días hábiles.",
    )
    descargo_presentado = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Indica si el socio ya presentó su descargo reglamentario.",
    )
    descargo_tipo = models.CharField(
        max_length=30,
        choices=TipoDescargoEnum.choices,
        blank=True,
        null=True,
    )
    descargo_causal = models.CharField(max_length=255, blank=True, null=True)
    descargo_archivo = models.CharField(max_length=255, blank=True, null=True)
    descargo_texto = models.TextField(blank=True, null=True)
    descargo_presentado_at = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "expedientes_expediente"
        verbose_name = "Expediente Disciplinario"
        verbose_name_plural = "Expedientes Disciplinarios"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.numero} - {self.socio.last_name} ({self.get_estado_display()})"

    @transaction.atomic
    def iniciar_plazo_descargo(
        self,
        fecha_hora_inicio: datetime,
        dias_habiles: int = 5,
        holiday_provider: "HolidayProviderPort | None" = None,
        actor: str = "SISTEMA",
    ) -> datetime:
        """
        Calcula y congela el plazo de 5 días hábiles a partir de fecha_hora_inicio.
        Transiciona al estado JUSTIFICANDO registrando trazabilidad y auditoría.
        """
        provider = holiday_provider or Argentina2026HolidayProvider()
        limite = compute_business_deadline(
            start_at=fecha_hora_inicio,
            business_days=dias_habiles,
            holiday_provider=provider,
        )

        estado_anterior = self.estado
        self.plazo_inicio_at = fecha_hora_inicio
        self.plazo_limite_at = limite
        self.estado = EstadoExpedienteEnum.JUSTIFICANDO
        self.save(update_fields=["plazo_inicio_at", "plazo_limite_at", "estado", "updated_at"])

        CambioEstadoExpediente.objects.create(
            expediente=self,
            estado_anterior=estado_anterior,
            estado_nuevo=EstadoExpedienteEnum.JUSTIFICANDO,
            actor=actor,
            motivo=f"Apertura de plazo perentorio de {dias_habiles} días hábiles (Art. 12 Inc. 2).",
        )
        return limite

    def esta_en_plazo(self, ahora: datetime | None = None) -> bool:
        """
        Evalúa si la presentación está en plazo bajo la regla:
        ahora <= plazo_limite_at (límite inclusivo).
        """
        if not self.plazo_limite_at:
            return False
        momento = ahora or timezone.now()
        return momento <= self.plazo_limite_at


class CambioEstadoExpediente(models.Model):
    """Registro inmutable de trazabilidad y auditoría del ciclo de vida del expediente."""

    expediente = models.ForeignKey(
        Expediente,
        on_delete=models.CASCADE,
        related_name="cambios_estado",
    )
    estado_anterior = models.CharField(max_length=30, choices=EstadoExpedienteEnum.choices)
    estado_nuevo = models.CharField(max_length=30, choices=EstadoExpedienteEnum.choices)
    fecha_hora = models.DateTimeField(auto_now_add=True, db_index=True)
    actor = models.CharField(
        max_length=150,
        default="SISTEMA",
        help_text="Usuario, rol o job responsable de la transición.",
    )
    motivo = models.TextField(blank=True)

    class Meta:
        db_table = "expedientes_cambio_estado"
        verbose_name = "Cambio de Estado de Expediente"
        verbose_name_plural = "Cambios de Estado de Expedientes"
        ordering = ["-fecha_hora"]

    def __str__(self) -> str:
        return (
            f"[{self.fecha_hora}] {self.expediente.numero}: "
            f"{self.estado_anterior} -> {self.estado_nuevo} ({self.actor})"
        )


class SolicitudT01(models.Model):
    class Estado(models.TextChoices):
        DRAFT = "DRAFT", "Borrador"
        ISSUED = "ISSUED", "Emitido"

    class TipoAccion(models.TextChoices):
        SANCTION = "SANCTION", "Sanción"
        MERIT = "MERIT", "Mérito"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    estado = models.CharField(max_length=10, choices=Estado.choices, default=Estado.DRAFT)
    solicitante = models.ForeignKey("socios.Socio", on_delete=models.PROTECT)
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

    def delete(self, *args, **kwargs):
        if self.estado == self.Estado.ISSUED:
            raise ValidationError("Una solicitud emitida es inmutable y no puede eliminarse.")
        return super().delete(*args, **kwargs)

    def save(self, *args, **kwargs):
        if self.pk and not self._state.adding:
            previous = type(self).objects.filter(pk=self.pk).values("estado").first()
            if previous and previous["estado"] == self.Estado.ISSUED:
                raise ValidationError("Una solicitud emitida es inmutable.")
        self.full_clean()
        return super().save(*args, **kwargs)

