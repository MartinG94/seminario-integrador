"""Modelos de persistencia para expedientes disciplinarios y plazos procesales.

Implementa:
- Expediente con los 6 estados canónicos (Art. 12 Reglamento Procesal 2026).
- Congelamiento inmutable de plazo_limite_at.
- Auditoría estricta de cambios de estado mediante CambioEstadoExpediente.
- Integración transaccional con libro mayor.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import IntegrityError, models, transaction
from django.utils import timezone

from expedientes.domain.calendar import compute_business_deadline
from expedientes.domain.holiday_provider import Argentina2026HolidayProvider, DbHolidayProvider

if TYPE_CHECKING:
    from expedientes.domain.ports import HolidayProviderPort


class EstadoExpedienteEnum(models.TextChoices):
    """Los 6 estados oficiales del expediente conforme al Art. 12 del Reglamento Procesal 2026."""

    CREADO = "creado", "Expediente Creado"
    JUSTIFICANDO = "justificando", "En período de justificaciones"
    REVISION_RESOLUCION = "revision_resolucion", "Justificaciones en revisión"
    ESPERA_RESOLUCION = "espera_resolucion", "En espera de resolución"
    PENDIENTE_CORREOS = "pendiente_correos", "Pendiente de firma y envío"
    EMITIDO = "emitido", "Expedientes ya emitidos"


class TipoDescargoEnum(models.TextChoices):
    """Tipos de formularios de justificación y descargos admitidos."""

    T02_CERTIFICADO = "T02_CERTIFICADO", "Formulario T02 - Causal con Certificado"
    T03_EXTRAORDINARIO = "T03_EXTRAORDINARIO", "Formulario T03 - Extraordinario"


class TipoFeriadoEnum(models.TextChoices):
    """Tipos de feriados y días inhábiles procesales."""

    NACIONAL = "NACIONAL", "Feriado Nacional"
    PROVINCIAL = "PROVINCIAL", "Feriado Provincial"
    INSTITUCIONAL = "INSTITUCIONAL", "Asueto Institucional"
    EXCEPCION = "EXCEPCION", "Día Inhábil Excepcional"


class CalendarioVersion(models.Model):
    """Versión auditable del calendario institucional de días hábiles (CA2/CA3)."""

    version = models.PositiveIntegerField(unique=True, db_index=True)
    nombre = models.CharField(max_length=150)
    vigencia_desde = models.DateField(db_index=True)
    vigencia_hasta = models.DateField(null=True, blank=True)
    activa = models.BooleanField(default=True, db_index=True)
    motivo_cambio = models.TextField(
        help_text="Justificación formal de auditoría para la creación/modificación de la versión."
    )
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="calendarios_creados",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "expedientes_calendario_version"
        verbose_name = "Versión de Calendario Institucional"
        verbose_name_plural = "Versiones de Calendario Institucional"
        ordering = ["-version"]

    def __str__(self) -> str:
        return f"v{self.version} - {self.nombre} ({'Activa' if self.activa else 'Inactiva'})"


class FeriadoExcepcion(models.Model):
    """Feriado, asueto o día inhábil dentro de una versión específica de calendario (CA1/CA2)."""

    calendario_version = models.ForeignKey(
        CalendarioVersion,
        on_delete=models.CASCADE,
        related_name="feriados",
    )
    fecha = models.DateField(db_index=True)
    descripcion = models.CharField(max_length=200)
    tipo = models.CharField(
        max_length=30,
        choices=TipoFeriadoEnum.choices,
        default=TipoFeriadoEnum.NACIONAL,
    )
    es_laborable = models.BooleanField(
        default=False,
        help_text="False indica día inhábil (feriado/asueto); True para excepciones laborables.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "expedientes_feriado_excepcion"
        verbose_name = "Feriado o Excepción de Calendario"
        verbose_name_plural = "Feriados y Excepciones de Calendario"
        ordering = ["fecha"]
        constraints = [
            models.UniqueConstraint(
                fields=["calendario_version", "fecha"],
                name="unique_fecha_per_calendario_version",
            )
        ]

    def __str__(self) -> str:
        return f"{self.fecha}: {self.descripcion} ({self.get_tipo_display()})"


class ExpedienteNumberSequence(models.Model):
    """Contador correlativo anual de expedientes (CA1/CA4): EXP-NNNN/YYYY.

    Una fila por año bloqueada con SELECT ... FOR UPDATE serializa la asignación:
    a diferencia del AUTO_INCREMENT de InnoDB, un rollback devuelve el número y
    la secuencia no deja huecos. El contador se reinicia con cada año calendario.
    """

    year = models.PositiveSmallIntegerField(unique=True)
    last_value = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "expedientes_numero_secuencia"

    @classmethod
    def next_value(cls, year: int) -> int:
        """Reserva el próximo número del año. Debe invocarse dentro de una transacción.

        La migración 0005 siembra la fila del año en curso; la primera apertura de cada
        año nuevo crea la suya. Ante una creación simultánea, la restricción única de
        `year` hace que sólo una inserción prospere y el resto relea la fila bloqueada.
        """
        with transaction.atomic():
            sequence = cls.objects.select_for_update().filter(year=year).first()
            if sequence is None:
                try:
                    with transaction.atomic():
                        cls.objects.create(year=year)
                except IntegrityError:
                    pass
                sequence = cls.objects.select_for_update().get(year=year)
            sequence.last_value += 1
            sequence.save(update_fields=["last_value"])
            return sequence.last_value


class Expediente(models.Model):
    """Expediente disciplinario o mérito institucional."""

    numero = models.CharField(max_length=50, unique=True, db_index=True)
    socio = models.ForeignKey(
        "socios.Socio",
        on_delete=models.PROTECT,
        related_name="expedientes",
        db_index=True,
    )
    socios = models.ManyToManyField(
        "socios.Socio",
        related_name="expedientes_implicados",
        blank=True,
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
    calendario_version = models.ForeignKey(
        CalendarioVersion,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="expedientes_congelados",
        help_text="Versión del calendario institucional aplicada al congelar el plazo (CA3).",
    )
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
        calendario_version: "CalendarioVersion | None" = None,
        actor: str = "SISTEMA",
    ) -> datetime:
        """
        Calcula y congela el plazo de 5 días hábiles a partir de fecha_hora_inicio.
        Conserva inmutablemente la versión del calendario aplicada (CA3).
        Transiciona al estado JUSTIFICANDO registrando trazabilidad y auditoría.
        """
        version = calendario_version
        if version is None and holiday_provider is None:
            version = CalendarioVersion.objects.filter(activa=True).order_by("-version").first()
            if version is not None:
                provider = DbHolidayProvider(version=version)
            else:
                provider = Argentina2026HolidayProvider()
        elif holiday_provider is not None:
            provider = holiday_provider
        else:
            provider = DbHolidayProvider(version=version)

        limite = compute_business_deadline(
            start_at=fecha_hora_inicio,
            business_days=dias_habiles,
            holiday_provider=provider,
        )

        self.calendario_version = version
        self.plazo_inicio_at = fecha_hora_inicio
        self.plazo_limite_at = limite
        self.save(
            update_fields=[
                "calendario_version",
                "plazo_inicio_at",
                "plazo_limite_at",
                "updated_at",
            ]
        )

        from expedientes.services.workflow_service import ExpedienteWorkflowService

        ExpedienteWorkflowService.transition(
            expediente_id=self.pk,
            estado_nuevo=EstadoExpedienteEnum.JUSTIFICANDO,
            actor=actor,
            motivo=f"Apertura de plazo perentorio de {dias_habiles} días hábiles (Art. 12 Inc. 2).",
        )
        self.estado = EstadoExpedienteEnum.JUSTIFICANDO
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


class DescargoExpediente(models.Model):
    """Descargo individual de un socio implicado en un expediente compartido."""

    expediente = models.ForeignKey(
        Expediente,
        on_delete=models.CASCADE,
        related_name="descargos",
    )
    socio = models.ForeignKey(
        "socios.Socio",
        on_delete=models.PROTECT,
        related_name="descargos_expedientes",
    )
    tipo = models.CharField(max_length=30, choices=TipoDescargoEnum.choices)
    causal = models.CharField(max_length=255, blank=True)
    archivo = models.CharField(max_length=255, blank=True)
    texto = models.TextField(blank=True)
    presentado_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "expedientes_descargo"
        constraints = [
            models.UniqueConstraint(
                fields=["expediente", "socio"],
                name="unique_descargo_per_expediente_socio",
            )
        ]


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
    destinatarios_socios_ids = models.JSONField(default=list, blank=True)
    tipo_accion = models.CharField(max_length=10, choices=TipoAccion.choices)
    titulo = models.CharField(max_length=255, blank=True, default="")
    causal = models.CharField(max_length=255, blank=True)
    puntos = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    motivo = models.TextField(blank=True)
    razon = models.TextField(blank=True, default="")
    reglamentos_respaldantes = models.JSONField(default=list, blank=True)
    anexo_fecha = models.DateField(null=True, blank=True)
    anexo_lugar = models.CharField(max_length=255, blank=True)
    anexo_relato = models.TextField(blank=True)
    anexo_testigos = models.TextField(blank=True)
    snapshot_destinatario = models.JSONField(null=True, blank=True)
    snapshots_destinatarios = models.JSONField(default=list, blank=True)
    snapshot_emitido = models.JSONField(null=True, blank=True)
    numero_expediente = models.CharField(max_length=40, null=True, blank=True, unique=True)
    expediente = models.OneToOneField(
        "Expediente",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="solicitud_t01",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    issued_at = models.DateTimeField(null=True, blank=True)

    def clean(self):
        if self.estado == self.Estado.ISSUED:
            if self.puntos is None:
                raise ValidationError({"puntos": "Los puntos son obligatorios al emitir."})
            if not self.destinatarios_socios_ids and not self.destinatario_socio_id:
                raise ValidationError(
                    {
                        "destinatarios_socios_ids": (
                            "Debe incluir al menos un socio destinatario al emitir."
                        )
                    }
                )
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
        # Sincronización bidireccional retrocompatible
        if self.destinatarios_socios_ids and not self.destinatario_socio_id:
            self.destinatario_socio_id = self.destinatarios_socios_ids[0]
        elif self.destinatario_socio_id and not self.destinatarios_socios_ids:
            self.destinatarios_socios_ids = [self.destinatario_socio_id]
        if self.snapshots_destinatarios and not self.snapshot_destinatario:
            self.snapshot_destinatario = self.snapshots_destinatarios[0]
        elif self.snapshot_destinatario and not self.snapshots_destinatarios:
            self.snapshots_destinatarios = [self.snapshot_destinatario]
        self.full_clean()
        return super().save(*args, **kwargs)
