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
from expedientes.domain.holiday_provider import DbHolidayProvider

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
    """Evidencia histórica; no configura el calendario operativo."""

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
    """Registro histórico de una versión anterior del calendario."""

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


class Holiday(models.Model):
    """Día inhábil del único calendario institucional operativo."""

    class Origin(models.TextChoices):
        USER = "USER", "Registro por usuario"
        SYSTEM = "SYSTEM", "Carga inicial del sistema"
        LEGACY = "LEGACY", "Registro previo sin autoría registrada"

    date = models.DateField(unique=True)
    description = models.CharField(max_length=200)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="institutional_holidays",
    )
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    origin = models.CharField(max_length=10, choices=Origin.choices, default=Origin.USER)

    class Meta:
        db_table = "expedientes_institutional_holiday"
        verbose_name = "Feriado institucional"
        verbose_name_plural = "Feriados institucionales"
        ordering = ["date"]
        constraints = [
            models.CheckConstraint(
                check=(
                    models.Q(origin="USER", created_by__isnull=False)
                    | models.Q(origin__in=["SYSTEM", "LEGACY"], created_by__isnull=True)
                ),
                name="holiday_requires_creation_audit",
            )
        ]

    def __str__(self) -> str:
        return f"{self.date}: {self.description}"


class UrgenciaExpedienteEnum(models.TextChoices):
    """Niveles de urgencia procesal para expedientes disciplinarios (SCRUM-78)."""

    BAJA = "baja", "Baja"
    NORMAL = "normal", "Normal"
    URGENTE = "urgente", "Urgente"


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
    puntos = models.DecimalField(max_digits=10, decimal_places=2, default=-1.0)
    estado = models.CharField(
        max_length=30,
        choices=EstadoExpedienteEnum.choices,
        default=EstadoExpedienteEnum.CREADO,
        db_index=True,
    )
    urgencia = models.CharField(
        max_length=20,
        choices=UrgenciaExpedienteEnum.choices,
        default=UrgenciaExpedienteEnum.NORMAL,
        db_index=True,
        help_text="Nivel de urgencia procesal (Baja, Normal, Urgente).",
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
        actor: str = "SISTEMA",
    ) -> datetime:
        """
        Calcula y congela el plazo de 5 días hábiles a partir de fecha_hora_inicio.
        Usa el calendario único y conserva la fecha/hora límite persistida (CA3).
        Transiciona al estado JUSTIFICANDO registrando trazabilidad y auditoría.
        """
        if self.plazo_limite_at is not None:
            return self.plazo_limite_at
        provider = holiday_provider if holiday_provider is not None else DbHolidayProvider()

        limite = compute_business_deadline(
            start_at=fecha_hora_inicio,
            business_days=dias_habiles,
            holiday_provider=provider,
        )

        self.plazo_inicio_at = fecha_hora_inicio
        self.plazo_limite_at = limite
        self.save(
            update_fields=[
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
    urgencia = models.CharField(
        max_length=20,
        choices=UrgenciaExpedienteEnum.choices,
        default=UrgenciaExpedienteEnum.NORMAL,
        blank=True,
    )
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


class CategoriaEventoEnum(models.TextChoices):
    """Categoría institucional del evento: espacio deliberativo vs actividad operativa."""

    REUNION = "REUNION", "Reunión Institucional"
    ACTIVIDAD = "ACTIVIDAD", "Actividad Operativa / Voluntariado"


class SubtipoReunionEnum(models.TextChoices):
    """Subtipos reglamentarios para eventos de categoría REUNION."""

    ORDINARIA = "ORDINARIA", "Reunión Ordinaria de Subcomisión"
    EXTRAORDINARIA = "EXTRAORDINARIA", "Reunión Extraordinaria de CD"
    ASAMBLEA = "ASAMBLEA", "Asamblea General (Ordinaria / Extraordinaria)"
    PLENARIO = "PLENARIO", "Plenario Directivo"


class SubtipoActividadEnum(models.TextChoices):
    """Subtipos reglamentarios para eventos de categoría ACTIVIDAD."""

    MANTENIMIENTO = "MANTENIMIENTO", "Mantenimiento y Reparaciones"
    VOLUNTARIADO = "VOLUNTARIADO", "Voluntariado Institucional"
    JORNADA = "JORNADA", "Jornada de Trabajo"
    EVENTO_SOCIAL = "EVENTO_SOCIAL", "Evento Social / Beneficio"
    GUARDIA = "GUARDIA", "Guardia Técnica"


class ModalidadEventoEnum(models.TextChoices):
    """Modalidad de realización de la convocatoria."""

    PRESENCIAL_SEDE = "PRESENCIAL_SEDE", "Presencial en Sede Central"
    PRESENCIAL_EXTERNA = "PRESENCIAL_EXTERNA", "Presencial Fuera de Sede"
    VIRTUAL = "VIRTUAL", "Virtual (Videoconferencia)"


class ModoConvocatoriaEnum(models.TextChoices):
    """Alcance de la convocatoria a socios."""

    GRUPO = "GRUPO", "Por Grupo Social Completo"
    SUBCOMISION = "SUBCOMISION", "Por Subcomisión Completa"
    PERSONALIZADA = "PERSONALIZADA", "Lista Personalizada de Socios"


class EstadoEventoEnum(models.TextChoices):
    """Ciclo de vida del evento institucional."""

    PROGRAMADA = "PROGRAMADA", "Programada"
    EN_CURSO = "EN_CURSO", "En Curso"
    CERRADA = "CERRADA", "Cerrada"


class EstadoAsistenciaEventoEnum(models.TextChoices):
    """Tipificación reglamentaria del estado de asistencia de un socio citado."""

    PRESENTE = "PRESENTE", "Presente"
    TARDE_LEVE = "TARDE_LEVE", "Tardanza Leve (15-30 min)"
    TARDE_GRAVE = "TARDE_GRAVE", "Tardanza Grave (>30 min)"
    RETIRO_ANTICIPADO_LEVE = "RETIRO_ANTICIPADO_LEVE", "Retiro Anticipado Leve (15-30 min)"
    RETIRO_ANTICIPADO_GRAVE = "RETIRO_ANTICIPADO_GRAVE", "Retiro Anticipado Grave (>30 min)"
    AUSENTE = "AUSENTE", "Ausente Injustificado"


class MetodoCapturaAsistenciaEnum(models.TextChoices):
    """Mecanismo de relevamiento de asistencia conforme al patrón Strategy."""

    MANUAL = "MANUAL", "Carga Manual"
    BIOMETRICO = "BIOMETRICO", "Lector Biométrico"


class EstadoRegistroApercibimientoEnum(models.TextChoices):
    """Estado del apercibimiento en el libro mayor."""

    PENDIENTE = "PENDIENTE", "Pendiente de Consolidación"
    CONSOLIDADO = "CONSOLIDADO", "Consolidado en Sanción"


class EventoInstitucional(models.Model):
    """Convocatoria institucional a reunión o actividad presencial/virtual obligatoria.

    Satisface CA1, CA2, CA8, CA9 y CA10.
    """

    titulo = models.CharField(
        max_length=200, help_text="Título o denominación formal de la convocatoria."
    )
    descripcion = models.TextField(blank=True, default="")
    categoria = models.CharField(
        max_length=20,
        choices=CategoriaEventoEnum.choices,
        help_text="Discriminador formal entre Reunión y Actividad.",
    )
    tipo = models.CharField(
        max_length=30,
        help_text="Subtipo reglamentario condicionado según la categoría seleccionada.",
    )
    modalidad = models.CharField(
        max_length=30,
        choices=ModalidadEventoEnum.choices,
        default=ModalidadEventoEnum.PRESENCIAL_SEDE,
        help_text="Modalidad: Sede Central, Fuera de Sede o Virtual.",
    )
    ubicacion = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Dirección física externa o enlace web de videoconferencia (Meet/Zoom).",
    )
    lugar = models.CharField(
        max_length=200,
        default="Sede Central AVEIT",
        help_text="Descripción textual de la sede o locación.",
    )
    fecha_publicacion = models.DateTimeField(
        help_text="Momento en que se publica y notifica formalmente la reunión (Art. 95).",
    )
    fecha_programada = models.DateTimeField(
        help_text="Fecha y hora de inicio fijada para el evento (campo obligatorio mínimo).",
    )
    fecha_fin = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Fecha y hora de finalización prevista (estrictamente opcional).",
    )
    fecha_hora_cierre_efectivo = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Momento real en que concluyó el evento o se cerró la toma de asistencia.",
    )
    fecha_reporte = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Momento en que se eleva el informe a Comisión Directiva (Art. 99).",
    )
    tolerancia_tardanza_minutos = models.PositiveSmallIntegerField(
        default=15,
        help_text="Tolerancia en minutos antes de computar tardanza leve (default: 15 min).",
    )
    tolerancia_retiro_minutos = models.PositiveSmallIntegerField(
        default=15,
        help_text="Tolerancia en minutos de retiro anticipado leve (default: 15 min).",
    )
    estado = models.CharField(
        max_length=30,
        choices=EstadoEventoEnum.choices,
        default=EstadoEventoEnum.PROGRAMADA,
    )
    modo_convocatoria = models.CharField(
        max_length=30,
        choices=ModoConvocatoriaEnum.choices,
        default=ModoConvocatoriaEnum.PERSONALIZADA,
    )
    grupo_convocado = models.CharField(max_length=10, null=True, blank=True)
    es_obligatoria = models.BooleanField(
        default=True,
        help_text="Indica si la asistencia reviste carácter obligatorio estatutario.",
    )
    es_sancionable = models.BooleanField(
        default=False,
        help_text=(
            "Determinado según cumplimiento de preaviso de 2 días hábiles y "
            "reporte en 72 hs hábiles (CA1/CA2)."
        ),
    )
    motivo_no_sancionable = models.TextField(
        null=True,
        blank=True,
        help_text="Fundamento de auditoría si la reunión perdió carácter sancionable.",
    )
    convocante = models.ForeignKey(
        "socios.Socio",
        on_delete=models.PROTECT,
        related_name="eventos_convocados",
    )
    subcomision = models.ForeignKey(
        "socios.Subcomision",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="eventos",
    )
    reportado_por = models.ForeignKey(
        "socios.Socio",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="eventos_reportados",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "expedientes_evento"
        verbose_name = "Evento Institucional"
        verbose_name_plural = "Eventos Institucionales"
        ordering = ["-fecha_programada"]
        indexes = [
            models.Index(
                fields=["fecha_programada", "estado"], name="idx_evento_fecha_prog_estado"
            ),
            models.Index(
                fields=["categoria", "tipo", "es_sancionable"], name="idx_evento_cat_tipo_sanc"
            ),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(fecha_publicacion__lte=models.F("fecha_programada")),
                name="chk_evento_publicacion_previa",
            ),
            models.CheckConstraint(
                check=models.Q(fecha_fin__isnull=True)
                | models.Q(fecha_fin__gte=models.F("fecha_programada")),
                name="chk_evento_fin_coherente",
            ),
        ]

    def __str__(self) -> str:
        return (
            f"[{self.categoria}] {self.titulo} - {self.fecha_programada.strftime('%d/%m/%Y %H:%M')}"
        )

    def clean(self) -> None:
        errors = {}
        if (
            self.fecha_publicacion
            and self.fecha_programada
            and self.fecha_publicacion > self.fecha_programada
        ):
            errors["fecha_publicacion"] = (
                "La fecha de publicación no puede ser posterior a la fecha programada."
            )

        if self.fecha_fin and self.fecha_programada and self.fecha_fin < self.fecha_programada:
            errors["fecha_fin"] = (
                "La fecha de finalización no puede ser anterior a la fecha programada."
            )

        if self.categoria == CategoriaEventoEnum.REUNION:
            if self.tipo not in SubtipoReunionEnum.values:
                errors["tipo"] = (
                    f"El subtipo '{self.tipo}' no corresponde a una REUNION. "
                    f"Opciones: {SubtipoReunionEnum.values}"
                )
        elif self.categoria == CategoriaEventoEnum.ACTIVIDAD:
            if self.tipo not in SubtipoActividadEnum.values:
                errors["tipo"] = (
                    f"El subtipo '{self.tipo}' no corresponde a una ACTIVIDAD. "
                    f"Opciones: {SubtipoActividadEnum.values}"
                )

        if errors:
            raise ValidationError(errors)


class AsistenciaEvento(models.Model):
    """Registro individual de asistencia de un socio a un evento institucional (CA10)."""

    evento = models.ForeignKey(
        EventoInstitucional,
        on_delete=models.CASCADE,
        related_name="asistencias",
    )
    socio = models.ForeignKey(
        "socios.Socio",
        on_delete=models.PROTECT,
        related_name="asistencias_eventos",
    )
    estado_asistencia = models.CharField(
        max_length=30,
        choices=EstadoAsistenciaEventoEnum.choices,
    )
    hora_registro = models.DateTimeField(null=True, blank=True)
    hora_salida = models.DateTimeField(null=True, blank=True)
    minutos_tardanza = models.PositiveIntegerField(default=0)
    minutos_retiro_anticipado = models.PositiveIntegerField(default=0)
    metodo_captura = models.CharField(
        max_length=20,
        choices=MetodoCapturaAsistenciaEnum.choices,
        default=MetodoCapturaAsistenciaEnum.MANUAL,
    )
    dispositivo_id = models.CharField(max_length=100, null=True, blank=True)
    motivo = models.TextField(
        blank=True,
        default="",
        help_text=(
            "Motivo u observación explicativa circunstanciada registrada por el organizador (CA10)."
        ),
    )
    observaciones = models.TextField(blank=True, default="")
    procesado_disciplinario = models.BooleanField(default=False)
    expediente_generado = models.ForeignKey(
        "expedientes.Expediente",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="asistencias_origen",
    )
    apercibimiento_generado = models.ForeignKey(
        "expedientes.RegistroApercibimiento",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="asistencias_origen",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "expedientes_asistencia_evento"
        verbose_name = "Asistencia a Evento"
        verbose_name_plural = "Asistencias a Eventos"
        constraints = [
            models.UniqueConstraint(
                fields=["evento", "socio"],
                name="unique_asistencia_per_evento_socio",
            )
        ]

    def __str__(self) -> str:
        return f"Asistencia {self.socio} - {self.evento.titulo}: {self.estado_asistencia}"

    def clean(self) -> None:
        if self.evento_id and self.socio_id:
            qs = AsistenciaEvento.objects.filter(evento_id=self.evento_id, socio_id=self.socio_id)
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if qs.exists():
                raise ValidationError(
                    "Ya existe un registro de asistencia para este socio en este evento."
                )


class RegistroApercibimiento(models.Model):
    """Libro mayor independiente de apercibimientos y llamados de atención.

    Aplica la regla 3:1 de consolidación (CA4).
    """

    socio = models.ForeignKey(
        "socios.Socio",
        on_delete=models.PROTECT,
        related_name="apercibimientos",
    )
    origen_tipo = models.CharField(
        max_length=50,
        help_text=(
            "Causal reglamentaria (ej. REUNION_TARDANZA_LEVE, SOLICITUD_T01, LLAMADO_ATENCION)."
        ),
    )
    asistencia = models.ForeignKey(
        AsistenciaEvento,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="apercibimientos_derivados",
    )
    expediente_origen = models.ForeignKey(
        "expedientes.Expediente",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="apercibimientos_declarados",
    )
    solicitud_t01 = models.ForeignKey(
        SolicitudT01,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="apercibimientos_originados",
    )
    fecha_hecho = models.DateField(
        help_text="Fecha en que aconteció el hecho sancionado.",
    )
    motivo = models.TextField(
        help_text="Descripción o circunstanciación del apercibimiento.",
    )
    articulo_reglamento = models.CharField(
        max_length=50,
        default="Art. 83",
        help_text="Artículo normativo respaldante.",
    )
    estado = models.CharField(
        max_length=20,
        choices=EstadoRegistroApercibimientoEnum.choices,
        default=EstadoRegistroApercibimientoEnum.PENDIENTE,
    )
    lote_consolidacion = models.UUIDField(
        null=True,
        blank=True,
        help_text="UUID del lote de consolidación de la terna de 3 apercibimientos (CA4).",
    )
    expediente_sancion = models.ForeignKey(
        "expedientes.Expediente",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="apercibimientos_consolidados",
        help_text="Expediente formal por -1.0 punto originado al consolidar la terna.",
    )
    fecha_consolidacion = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp del momento en que se consolidó la terna.",
    )
    actor_registro = models.CharField(
        max_length=150,
        default="SISTEMA",
        help_text="Usuario o subsistema que asienta el apercibimiento.",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "expedientes_registro_apercibimiento"
        verbose_name = "Registro de Apercibimiento"
        verbose_name_plural = "Libro Mayor de Apercibimientos"
        ordering = ["created_at"]
        indexes = [
            models.Index(
                fields=["socio", "estado", "created_at"],
                name="idx_aperc_socio_est_created",
            ),
        ]

    def __str__(self) -> str:
        return f"Apercibimiento #{self.id or 'N/A'} - {self.socio} [{self.estado}]"

    def clean(self) -> None:
        errors = {}
        if self.estado == EstadoRegistroApercibimientoEnum.CONSOLIDADO:
            if not self.lote_consolidacion:
                errors["lote_consolidacion"] = (
                    "Un apercibimiento consolidado debe contener el UUID del lote de consolidación."
                )
            if not self.expediente_sancion_id and not getattr(self, "expediente_sancion", None):
                errors["expediente_sancion"] = (
                    "Un apercibimiento consolidado debe estar vinculado a un expediente de sanción."
                )
        elif self.estado == EstadoRegistroApercibimientoEnum.PENDIENTE:
            if self.lote_consolidacion:
                errors["lote_consolidacion"] = (
                    "Un apercibimiento en estado PENDIENTE no debe poseer lote de consolidación."
                )
            if self.expediente_sancion_id or getattr(self, "expediente_sancion", None):
                errors["expediente_sancion"] = (
                    "Un apercibimiento en estado PENDIENTE no debe estar vinculado "
                    "a un expediente de sanción."
                )

        if errors:
            raise ValidationError(errors)


# Aliases retrocompatibles exigidos por las directivas arquitectónicas
Reunion = EventoInstitucional
AsistenciaReunion = AsistenciaEvento
