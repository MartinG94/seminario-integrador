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


class OperacionDescargoEnum(models.TextChoices):
    """Operaciones registradas en el historial inmutable de un descargo (SCRUM-49)."""

    PRESENTADO = "PRESENTADO", "Descargo presentado"
    CORREGIDO = "CORREGIDO", "Descargo corregido dentro del plazo"
    RETIRADO = "RETIRADO", "Descargo retirado dentro del plazo"


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


class ConceptoExpedienteEnum(models.TextChoices):
    """Catálogo de conceptos institucionales para clasificación por el TD."""

    CD = "CD", "CD — Comisión Directiva"
    TD = "TD", "TD — Tribunal de Disciplina"
    GSA = "GSA", "GSA — Gestión Social y Ambiental"
    GVP = "GVP", "GVP — Grupo de Viaje / Gestión de Viaje"
    COMP = "COMP", "COMP — Cómputos"
    RRHH = "RRHH", "RRHH — Recursos Humanos"
    RRII = "RRII", "RRII — Relaciones Institucionales"
    PRENSA = "PRENSA", "PRENSA — Prensa y Difusión"
    MANT = "MANT", "MANT — Mantenimiento"
    EVENTOS = "EVENTOS", "EVENTOS — Organización y Eventos"
    RIFAS = "RIFAS", "RIFAS — Rifas"
    ASAMBLEA = "ASAMBLEA", "ASAMBLEA — Asamblea General"
    OTROS = "OTROS", "OTROS — Otros Conceptos Institucionales"


class ClasificacionExpedienteEnum(models.TextChoices):
    """Clasificación o concepto del expediente asignado o validado por TD (SCRUM-63)."""

    CD = "CD", "Comisión Directiva"
    RRHH = "RRHH", "Recursos Humanos"
    PRENSA = "PRENSA", "Prensa y Difusión"
    OYE = "OYE", "Organización y Eventos"
    GSA = "GSA", "Gestión Social y Ambiental"
    RII = "RII", "Relaciones Institucionales"
    COMPUTOS = "COMPUTOS", "Cómputos"
    TD = "TD", "Tribunal de Disciplina"
    CR = "CR", "Comisión Rifaria"
    MANTENIMIENTO = "MANTENIMIENTO", "Mantenimiento"
    RC = "RC", "Revisores de Cuentas"
    GVP = "GVP", "Grupo de Viaje y Permanencia"
    GENERAL = "GENERAL", "General"
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
    clasificacion = models.CharField(
        max_length=50,
        choices=ClasificacionExpedienteEnum.choices,
        default=ClasificacionExpedienteEnum.GENERAL,
        db_index=True,
        help_text="Concepto o subcomisión clasificadora asignada por TD.",
    )
    urgencia = models.CharField(
        max_length=20,
        choices=UrgenciaExpedienteEnum.choices,
        default=UrgenciaExpedienteEnum.NORMAL,
        db_index=True,
        help_text="Nivel de urgencia procesal (Baja, Normal, Urgente).",
    )
    concepto = models.CharField(
        max_length=20,
        choices=ConceptoExpedienteEnum.choices,
        null=True,
        blank=True,
        default=None,
        db_index=True,
        help_text="Concepto institucional clasificado manualmente por el TD durante la revisión.",
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

        from expedientes.services.t01_appeal_service import T01AppealService

        # En los T01 el plazo de apelación es el parámetro vigente, por socio (PB-02).
        limite = T01AppealService.open_initial_periods(
            self, fecha_hora_inicio
        ) or compute_business_deadline(
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
    es_vigente = models.BooleanField(
        default=True,
        db_index=True,
        help_text="False cuando el socio retiró el descargo dentro del plazo (baja lógica).",
    )

    class Meta:
        db_table = "expedientes_descargo"
        constraints = [
            models.UniqueConstraint(
                fields=["expediente", "socio"],
                name="unique_descargo_per_expediente_socio",
            )
        ]


class EvidenciaDescargo(models.Model):
    """Comprobante probatorio protegido y serializado en base de datos (Directiva PO)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    expediente = models.ForeignKey(
        Expediente,
        on_delete=models.CASCADE,
        related_name="evidencias",
        db_index=True,
    )
    descargo = models.ForeignKey(
        DescargoExpediente,
        on_delete=models.PROTECT,
        related_name="evidencias",
        null=True,
        blank=True,
    )
    socio = models.ForeignKey(
        "socios.Socio",
        on_delete=models.PROTECT,
        related_name="evidencias_aportadas",
        db_index=True,
    )
    contenido_blob = models.BinaryField(
        help_text="Contenido binario serializado del archivo probatorio (hasta 5 MB)."
    )
    nombre_original = models.CharField(max_length=255)
    extension = models.CharField(
        max_length=20, help_text="Extensión original extraída (ej. .pdf, .jpg)"
    )
    mime_type = models.CharField(max_length=100, help_text="Tipo MIME validado por magic bytes")
    tamanio_bytes = models.PositiveIntegerField()
    sha256_hash = models.CharField(max_length=64, db_index=True)
    es_vigente = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "expedientes_evidencia_descargo"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.nombre_original} ({self.expediente.numero})"


class DescargoVersion(models.Model):
    """Versión inmutable de un descargo (solo-inserción).

    La versión vigente es la de mayor ``numero``; si su operación es ``RETIRADO`` el socio
    no tiene descargo vigente. Guarda una copia del contenido y el juego de evidencias de
    ese momento, de modo que ninguna corrección o retiro destruya el rastro del escrito.
    """

    descargo = models.ForeignKey(
        DescargoExpediente,
        on_delete=models.PROTECT,
        related_name="versiones",
    )
    numero = models.PositiveIntegerField()
    operacion = models.CharField(max_length=20, choices=OperacionDescargoEnum.choices)
    tipo = models.CharField(max_length=30, choices=TipoDescargoEnum.choices)
    causal = models.CharField(max_length=255, blank=True)
    archivo = models.CharField(max_length=255, blank=True)
    texto = models.TextField(blank=True)
    evidencias = models.ManyToManyField(
        EvidenciaDescargo,
        related_name="versiones",
        blank=True,
    )
    actor = models.CharField(max_length=150)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "expedientes_descargo_version"
        ordering = ["numero"]
        constraints = [
            models.UniqueConstraint(
                fields=["descargo", "numero"],
                name="unique_version_numero_per_descargo",
            )
        ]

    def save(self, *args, **kwargs) -> None:
        if not self._state.adding:
            raise ValidationError("Las versiones del descargo son inmutables.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Las versiones del descargo no pueden eliminarse.")

    def __str__(self) -> str:
        return f"v{self.numero} {self.operacion} ({self.descargo.expediente.numero})"


class AuditoriaDescargaEvidencia(models.Model):
    """Pista de auditoría inmutable de accesos y descargas de evidencia (CA4)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    evidencia = models.ForeignKey(
        EvidenciaDescargo,
        on_delete=models.CASCADE,
        related_name="descargas_auditadas",
    )
    usuario = models.CharField(max_length=150)
    rol = models.CharField(max_length=50)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=500, blank=True)
    fecha_hora = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "expedientes_auditoria_descarga"
        ordering = ["-fecha_hora"]

    def __str__(self) -> str:
        return f"Descarga {self.evidencia_id} por {self.usuario} ({self.fecha_hora})"


class AuditoriaConsultaExpediente(models.Model):
    """Pista de auditoría inmutable de consultas en el visor autorizado (CA3)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    expediente = models.ForeignKey(
        Expediente,
        on_delete=models.CASCADE,
        related_name="consultas_auditadas",
        db_index=True,
    )
    usuario = models.CharField(max_length=150)
    legajo = models.CharField(max_length=50, blank=True)
    rol = models.CharField(max_length=50)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=500, blank=True)
    fecha_hora = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "expedientes_auditoria_consulta"
        ordering = ["-fecha_hora"]

    def __str__(self) -> str:
        return f"Consulta {self.expediente.numero} por {self.usuario} ({self.fecha_hora})"

    def save(self, *args, **kwargs) -> None:
        if not self._state.adding:
            raise ValidationError("Los registros de auditoría de consulta son inmutables.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Los registros de auditoría de consulta no pueden eliminarse.")


class DecisionCausalEnum(models.TextChoices):
    """Resultado de la valoración de una causal tipificada T02 (S4-02)."""

    ACCEPTED = "ACCEPTED", "Aceptada"
    REJECTED = "REJECTED", "Rechazada"


class DecisionCausalDescargo(models.Model):
    """Decisión inmutable y versionada de un miembro del TD sobre la causal de un descargo T02.

    Cada nueva valoración crea una versión; las anteriores se conservan (CA3).
    Guarda una copia del descargo valorado sin modificar el original (CA4).
    """

    expediente = models.ForeignKey(
        Expediente,
        on_delete=models.PROTECT,
        related_name="decisiones_causal",
    )
    descargo = models.ForeignKey(
        DescargoExpediente,
        on_delete=models.PROTECT,
        related_name="decisiones_causal",
    )
    version = models.PositiveIntegerField()
    decision = models.CharField(max_length=10, choices=DecisionCausalEnum.choices)
    regla_sugerida = models.CharField(max_length=10, choices=DecisionCausalEnum.choices)
    se_aparta_de_regla = models.BooleanField(default=False)
    fundamento = models.TextField(blank=True)
    evidencias_valoradas = models.JSONField(default=list, blank=True)
    descargo_snapshot = models.JSONField(default=dict)
    autor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="decisiones_causal",
    )
    autor_legajo = models.CharField(max_length=20)
    autor_rol = models.CharField(max_length=20)
    created_at = models.DateTimeField(default=timezone.now, editable=False, db_index=True)

    class Meta:
        db_table = "expedientes_decision_causal"
        verbose_name = "Decisión sobre causal T02"
        verbose_name_plural = "Decisiones sobre causales T02"
        ordering = ["descargo_id", "-version"]
        constraints = [
            models.UniqueConstraint(
                fields=["descargo", "version"],
                name="unique_decision_version_per_descargo",
            )
        ]

    def __str__(self) -> str:
        return f"Descargo {self.descargo_id} v{self.version}: {self.get_decision_display()}"

    def save(self, *args, **kwargs) -> None:
        if not self._state.adding:
            raise ValidationError(
                "Una decisión registrada es inmutable; registrá una nueva versión."
            )
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Una decisión registrada no puede eliminarse.")


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
    clasificacion = models.CharField(
        max_length=50,
        choices=ClasificacionExpedienteEnum.choices,
        default=ClasificacionExpedienteEnum.GENERAL,
        db_index=True,
        help_text="Concepto o subcomisión clasificadora asignada por TD.",
    )
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


# --- Apelación y adecuación del T01 (PB-02, Reglamento Procesal 2026, art. 14) ---


class T01HistoryRecord(models.Model):
    """Registro del historial del T01: sólo inserción, sin modificación ni eliminación (CA4)."""

    class Meta:
        abstract = True

    def save(self, *args, **kwargs) -> None:
        if not self._state.adding:
            raise ValidationError("El historial del T01 es inmutable.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("El historial del T01 no puede eliminarse.")


class ParametroPlazoApelacion(T01HistoryRecord):
    """Plazo de apelación del T01 en días hábiles; el vigente es el último registrado."""

    DEFAULT_DIAS_HABILES = 5

    dias_habiles = models.PositiveSmallIntegerField()
    autor = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name="+"
    )
    created_at = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        db_table = "expedientes_parametro_plazo_apelacion"
        ordering = ["-created_at", "-id"]

    @classmethod
    def vigente(cls) -> int:
        ultimo = cls.objects.order_by("-created_at", "-id").first()
        return ultimo.dias_habiles if ultimo else cls.DEFAULT_DIAS_HABILES


class OrigenPeriodoApelacionEnum(models.TextChoices):
    APERTURA = "APERTURA", "Apertura del expediente"
    ADECUACION = "ADECUACION", "Nuevo período por adecuación"


class AdecuacionT01(T01HistoryRecord):
    """Versión de la adecuación de puntos e involucrados decidida en el debate (OP 30)."""

    expediente = models.ForeignKey(
        Expediente, on_delete=models.PROTECT, related_name="adecuaciones_t01"
    )
    version = models.PositiveIntegerField()
    puntos_anteriores = models.DecimalField(max_digits=10, decimal_places=2)
    puntos_nuevos = models.DecimalField(max_digits=10, decimal_places=2)
    socios_anteriores = models.JSONField(default=list)
    socios_nuevos = models.JSONField(default=list)
    motivos = models.TextField()
    reabre_plazo = models.BooleanField(default=False)
    socios_con_nuevo_plazo = models.JSONField(default=list, blank=True)
    autor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    autor_legajo = models.CharField(max_length=20)
    created_at = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        db_table = "expedientes_adecuacion_t01"
        ordering = ["version"]
        constraints = [
            models.UniqueConstraint(
                fields=["expediente", "version"], name="unique_adecuacion_t01_version"
            )
        ]


class PeriodoApelacion(T01HistoryRecord):
    """Período de apelación de un socio, con el plazo congelado al abrirse (CA1/CA5)."""

    expediente = models.ForeignKey(
        Expediente, on_delete=models.PROTECT, related_name="periodos_apelacion"
    )
    socio = models.ForeignKey(
        "socios.Socio", on_delete=models.PROTECT, related_name="periodos_apelacion"
    )
    origen = models.CharField(max_length=12, choices=OrigenPeriodoApelacionEnum.choices)
    adecuacion = models.ForeignKey(
        AdecuacionT01,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="periodos_abiertos",
    )
    dias_habiles = models.PositiveSmallIntegerField()
    inicio_at = models.DateTimeField()
    limite_at = models.DateTimeField(db_index=True)
    created_at = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        db_table = "expedientes_periodo_apelacion"
        ordering = ["created_at", "id"]


class ApelacionT01(T01HistoryRecord):
    """Versión de la apelación de un socio involucrado en un T01 (OP 20)."""

    expediente = models.ForeignKey(
        Expediente, on_delete=models.PROTECT, related_name="apelaciones_t01"
    )
    socio = models.ForeignKey(
        "socios.Socio", on_delete=models.PROTECT, related_name="apelaciones_t01"
    )
    numero = models.PositiveIntegerField()
    texto = models.TextField()
    created_at = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        db_table = "expedientes_apelacion_t01"
        ordering = ["socio_id", "numero"]
        constraints = [
            models.UniqueConstraint(
                fields=["expediente", "socio", "numero"], name="unique_apelacion_t01_version"
            )
        ]


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
    ESTADO_SOCIAL = "ESTADO_SOCIAL", "Por Estado Social (Juniors / Seniors)"
    PERSONALIZADA = "PERSONALIZADA", "Lista Personalizada de Socios"


class EstadoEventoEnum(models.TextChoices):
    """Ciclo de vida del evento institucional."""

    CREADO = "CREADO", "Creado"
    NOTIFICADO = "NOTIFICADO", "Notificado"
    EN_CURSO = "EN_CURSO", "En Curso"
    ABIERTO = "ABIERTO", "Abierto"
    FINALIZADO = "FINALIZADO", "Finalizado"
    ANULADO = "ANULADO", "Anulado"


# Aliases de compatibilidad histórica
EstadoEventoEnum.PROGRAMADA = EstadoEventoEnum.CREADO
EstadoEventoEnum.CERRADA = EstadoEventoEnum.FINALIZADO


class EstadoAsistenciaEventoEnum(models.TextChoices):
    """Tipificación reglamentaria del estado de asistencia de un socio citado."""

    PRESENTE = "PRESENTE", "Presente"
    TARDE_LEVE = "TARDE_LEVE", "Tardanza Leve (15-30 min)"
    TARDE_GRAVE = "TARDE_GRAVE", "Tardanza Grave (>30 min)"
    RETIRO_ANTICIPADO_LEVE = "RETIRO_ANTICIPADO_LEVE", "Retiro Anticipado Leve (15-30 min)"
    RETIRO_ANTICIPADO_GRAVE = "RETIRO_ANTICIPADO_GRAVE", "Retiro Anticipado Grave (>30 min)"
    AUSENTE = "AUSENTE", "Ausente Injustificado"
    JUSTIFICADO = "JUSTIFICADO", "Ausencia Justificada"


class MetodoCapturaAsistenciaEnum(models.TextChoices):
    """Mecanismo de relevamiento de asistencia conforme al patrón Strategy."""

    MANUAL = "MANUAL", "Carga Manual"
    BIOMETRICO = "BIOMETRICO", "Lector Biométrico"


class EstadoRegistroApercibimientoEnum(models.TextChoices):
    """Estado del apercibimiento en el libro mayor."""

    PENDIENTE = "PENDIENTE", "Pendiente de Consolidación"
    CONSOLIDADO = "CONSOLIDADO", "Consolidado en Sanción"


class CategoriaEvento(models.Model):
    """Categoría institucional de eventos (Reunión o Actividad)."""

    id = models.AutoField(primary_key=True, db_column="idCategoria")
    codigo = models.CharField(max_length=20, unique=True)
    nombre = models.CharField(max_length=50)

    class Meta:
        db_table = "tribunal_categoriaevento"
        verbose_name = "Categoría de Evento"
        verbose_name_plural = "Categorías de Eventos"

    def __str__(self) -> str:
        return f"{self.codigo} - {self.nombre}"


class EventoInstitucional(models.Model):
    """Convocatoria institucional a reunión o actividad presencial/virtual obligatoria.

    Satisface CA1, CA2, CA8, CA9 y CA10 reutilizando la entidad preexistente tribunal_evento.
    """

    id = models.AutoField(primary_key=True, db_column="idEvento")
    titulo = models.CharField(
        max_length=128,
        db_column="nombre",
        help_text="Título o denominación formal de la convocatoria.",
    )
    descripcion = models.TextField(blank=True, default="", db_column="descripcion")
    categoria_ref = models.ForeignKey(
        CategoriaEvento,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_column="categoria_id",
        related_name="eventos",
    )
    categoria = models.CharField(
        max_length=20,
        choices=CategoriaEventoEnum.choices,
        default=CategoriaEventoEnum.REUNION,
        db_column="categoria",
        help_text="Discriminador formal entre Reunión y Actividad.",
    )
    tipo = models.CharField(
        max_length=30,
        default="ORDINARIA",
        db_column="tipo",
        help_text="Subtipo reglamentario condicionado según la categoría seleccionada.",
    )
    modalidad = models.CharField(
        max_length=30,
        choices=ModalidadEventoEnum.choices,
        default=ModalidadEventoEnum.PRESENCIAL_SEDE,
        db_column="modalidad",
        help_text="Modalidad: Sede Central, Fuera de Sede o Virtual.",
    )
    ubicacion = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        db_column="ubicacion",
        help_text="Dirección física externa o enlace web de videoconferencia (Meet/Zoom).",
    )
    lugar = models.CharField(
        max_length=200,
        default="Sede Central AVEIT",
        db_column="lugar",
        help_text="Descripción textual de la sede o locación.",
    )
    fecha_publicacion = models.DateTimeField(
        db_column="fecha_publicacion",
        help_text="Momento en que se publica y notifica formalmente la reunión (Art. 95).",
    )
    fecha_programada = models.DateTimeField(
        db_column="fechaHoraInicio",
        help_text="Fecha y hora de inicio fijada para el evento (campo obligatorio mínimo).",
    )
    fecha_fin = models.DateTimeField(
        null=True,
        blank=True,
        db_column="fechaHoraFin",
        help_text="Fecha y hora de finalización prevista (estrictamente opcional).",
    )
    tieneHoraFin = models.BooleanField(
        default=False,
        db_column="tieneHoraFin",
        help_text="Indica si el evento tiene hora de finalización definida.",
    )
    fecha_hora_cierre_efectivo = models.DateTimeField(
        null=True,
        blank=True,
        db_column="fecha_hora_cierre_efectivo",
        help_text="Momento real en que concluyó el evento o se cerró la toma de asistencia.",
    )
    fecha_reporte = models.DateTimeField(
        null=True,
        blank=True,
        db_column="fecha_reporte",
        help_text="Momento en que se eleva el informe a Comisión Directiva (Art. 99).",
    )
    tolerancia_tardanza_minutos = models.PositiveSmallIntegerField(
        default=15,
        db_column="toleranciaLeveMinutos",
        help_text="Tolerancia en minutos antes de computar tardanza leve (default: 15 min).",
    )
    tolerancia_grave_minutos = models.PositiveSmallIntegerField(
        default=30,
        db_column="toleranciaGraveMinutos",
        help_text="Tolerancia en minutos antes de computar tardanza grave (default: 30 min).",
    )
    tolerancia_retiro_minutos = models.PositiveSmallIntegerField(
        default=15,
        db_column="tolerancia_retiro_minutos",
        help_text="Tolerancia en minutos de retiro anticipado leve (default: 15 min).",
    )
    estado = models.CharField(
        max_length=30,
        choices=EstadoEventoEnum.choices,
        default=EstadoEventoEnum.CREADO,
        db_column="estado",
    )
    estadoEvento_id = models.IntegerField(default=1, db_column="estadoEvento_id")
    modo_convocatoria = models.CharField(
        max_length=30,
        choices=ModoConvocatoriaEnum.choices,
        default=ModoConvocatoriaEnum.PERSONALIZADA,
        db_column="modo_convocatoria",
    )
    afectados_id = models.IntegerField(default=20, db_column="afectados_id")
    grupo_convocado = models.CharField(
        max_length=10,
        null=True,
        blank=True,
        db_column="grupo_convocado",
    )
    estado_social_convocado = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        choices=[("JUNIORS", "Juniors"), ("SENIORS", "Seniors")],
        db_column="estado_social_convocado",
        help_text="Filtro de cohorte social cuando modo_convocatoria es ESTADO_SOCIAL.",
    )
    detalle_tarea = models.TextField(
        blank=True,
        default="",
        db_column="detalle_tarea",
        help_text="Instrucciones concretas y especificación de la tarea para Actividades.",
    )
    puntos_sancion = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        null=True,
        blank=True,
        db_column="puntos_sancion",
        help_text=(
            "Puntos de penalidad por inasistencia o incumplimiento personalizables para "
            "Actividades."
        ),
    )
    motivo_cancelacion = models.TextField(
        null=True,
        blank=True,
        db_column="motivo_cancelacion",
        help_text="Fundamento formal de anulación del evento.",
    )
    es_obligatoria = models.BooleanField(
        default=True,
        db_column="es_obligatoria",
        help_text="Indica si la asistencia reviste carácter obligatorio estatutario.",
    )
    es_sancionable = models.BooleanField(
        default=False,
        db_column="es_sancionable",
        help_text=(
            "Determinado según cumplimiento de preaviso de 2 días hábiles y "
            "reporte en 72 hs hábiles (CA1/CA2)."
        ),
    )
    motivo_no_sancionable = models.TextField(
        null=True,
        blank=True,
        db_column="motivo_no_sancionable",
        help_text="Fundamento de auditoría si la reunión perdió carácter sancionable.",
    )
    convocante = models.ForeignKey(
        "socios.Socio",
        on_delete=models.PROTECT,
        db_column="responsable_id",
        related_name="eventos_convocados",
    )
    subcomision = models.ForeignKey(
        "socios.Subcomision",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_column="subcomision_id",
        related_name="eventos",
    )
    reportado_por = models.ForeignKey(
        "socios.Socio",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_column="reportado_por_id",
        related_name="eventos_reportados",
    )
    created_at = models.DateTimeField(auto_now_add=True, db_column="created_at")
    updated_at = models.DateTimeField(auto_now=True, db_column="updated_at")

    @property
    def idEvento(self) -> int:
        return self.id

    @property
    def nombre(self) -> str:
        return self.titulo

    @nombre.setter
    def nombre(self, val: str) -> None:
        self.titulo = val

    @property
    def fechaHoraInicio(self):
        return self.fecha_programada

    @fechaHoraInicio.setter
    def fechaHoraInicio(self, val) -> None:
        self.fecha_programada = val

    @property
    def fechaHoraFin(self):
        return self.fecha_fin

    @fechaHoraFin.setter
    def fechaHoraFin(self, val) -> None:
        self.fecha_fin = val

    @property
    def responsable(self):
        return self.convocante

    @responsable.setter
    def responsable(self, val) -> None:
        self.convocante = val

    @property
    def toleranciaLeveMinutos(self) -> int:
        return self.tolerancia_tardanza_minutos

    @toleranciaLeveMinutos.setter
    def toleranciaLeveMinutos(self, val: int) -> None:
        self.tolerancia_tardanza_minutos = val

    @property
    def toleranciaGraveMinutos(self) -> int:
        return self.tolerancia_grave_minutos

    @toleranciaGraveMinutos.setter
    def toleranciaGraveMinutos(self, val: int) -> None:
        self.tolerancia_grave_minutos = val

    class Meta:
        db_table = "tribunal_evento"
        verbose_name = "Evento Institucional"
        verbose_name_plural = "Eventos Institucionales"
        ordering = ["-fecha_programada"]
        indexes = [
            models.Index(
                fields=["fecha_programada", "estado"], name="idx_evento_fechainicio_estado"
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
            if not (self.detalle_tarea and self.detalle_tarea.strip()):
                errors["detalle_tarea"] = (
                    "Para actividades operativas es obligatorio detallar la tarea asignada."
                )

        if errors:
            raise ValidationError(errors)


class EventoConvocado(models.Model):
    """Nómina de socios formalmente convocados o citados a un evento institucional."""

    id = models.AutoField(primary_key=True, db_column="idConvocado")
    evento = models.ForeignKey(
        EventoInstitucional,
        on_delete=models.CASCADE,
        db_column="evento_id",
        related_name="convocados",
    )
    socio = models.ForeignKey(
        "socios.Socio",
        on_delete=models.CASCADE,
        db_column="socio_id",
        related_name="convocatorias_evento",
    )
    created_at = models.DateTimeField(auto_now_add=True, db_column="created_at")

    class Meta:
        db_table = "tribunal_evento_convocado"
        verbose_name = "Socio Convocado a Evento"
        verbose_name_plural = "Socios Convocados a Eventos"
        constraints = [
            models.UniqueConstraint(
                fields=["evento", "socio"],
                name="unique_convocado_evento_socio",
            )
        ]

    def __str__(self) -> str:
        return f"Convocado {self.socio} a {self.evento}"


class AsistenciaEvento(models.Model):
    """Registro individual de asistencia de un socio a un evento institucional (CA10).

    Mapeado a la tabla legacy tribunal_asistente.
    """

    id = models.AutoField(primary_key=True, db_column="idAsistente")
    evento = models.ForeignKey(
        EventoInstitucional,
        on_delete=models.CASCADE,
        db_column="evento_id",
        related_name="asistencias",
    )
    socio = models.ForeignKey(
        "socios.Socio",
        on_delete=models.PROTECT,
        db_column="socio_id",
        related_name="asistencias_eventos",
    )
    estado_asistencia = models.CharField(
        max_length=30,
        choices=EstadoAsistenciaEventoEnum.choices,
        default=EstadoAsistenciaEventoEnum.PRESENTE,
        db_column="estado_asistencia",
    )
    hora_registro = models.DateTimeField(null=True, blank=True, db_column="fechaHoraLlegada")
    hora_salida = models.DateTimeField(null=True, blank=True, db_column="fechaHoraSalida")
    notificado = models.BooleanField(default=False, db_column="notificado")
    fechaNotificacion = models.DateField(null=True, blank=True, db_column="fechaNotificacion")
    minutos_tardanza = models.PositiveIntegerField(default=0, db_column="minutos_tardanza")
    minutos_retiro_anticipado = models.PositiveIntegerField(
        default=0, db_column="minutos_retiro_anticipado"
    )
    metodo_captura = models.CharField(
        max_length=20,
        choices=MetodoCapturaAsistenciaEnum.choices,
        default=MetodoCapturaAsistenciaEnum.MANUAL,
        db_column="metodo_captura",
    )
    dispositivo_id = models.CharField(
        max_length=100, null=True, blank=True, db_column="dispositivo_id"
    )
    motivo = models.TextField(
        blank=True,
        default="",
        db_column="motivo",
        help_text=(
            "Motivo u observación explicativa circunstanciada registrada por el organizador (CA10)."
        ),
    )
    observaciones = models.TextField(blank=True, default="", db_column="observaciones")
    procesado_disciplinario = models.BooleanField(
        default=False, db_column="procesado_disciplinario"
    )
    expediente_generado = models.ForeignKey(
        "expedientes.Expediente",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        db_column="expediente_generado_id",
        related_name="asistencias_origen",
    )
    created_at = models.DateTimeField(auto_now_add=True, db_column="created_at")

    @property
    def idAsistente(self) -> int:
        return self.id

    @property
    def fechaHoraLlegada(self):
        return self.hora_registro

    @fechaHoraLlegada.setter
    def fechaHoraLlegada(self, val) -> None:
        self.hora_registro = val

    @property
    def fechaHoraSalida(self):
        return self.hora_salida

    @fechaHoraSalida.setter
    def fechaHoraSalida(self, val) -> None:
        self.hora_salida = val

    @property
    def apercibimiento_generado_id(self) -> int | None:
        return 1 if self.notificado else None

    @property
    def apercibimiento_generado(self):
        return None if not self.notificado else 1

    @apercibimiento_generado.setter
    def apercibimiento_generado(self, val) -> None:
        self.notificado = bool(val)

    class Meta:
        db_table = "tribunal_asistente"
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


class AtencionFelicitacion(models.Model):
    """Control de llamados de atención y felicitaciones por socio (atencionFelicitacion).

    Aplica la regla 3:1 inmutable:
    - Cada 3 llamados de atención consolidan en una sanción (-1.00 punto) y descuentan 3 llamados.
    - Cada 3 felicitaciones consolidan en un mérito (+1.00 punto) y descuentan 3 felicitaciones.
    """

    socio = models.OneToOneField(
        "socios.Socio",
        primary_key=True,
        on_delete=models.CASCADE,
        db_column="nroSocio",
        related_name="atencion_felicitacion",
    )
    felicitaciones = models.IntegerField(default=0, db_column="felicitaciones")
    llamadosAtencion = models.IntegerField(default=0, db_column="llamadosAtencion")

    @property
    def nroSocio(self) -> int:
        return self.socio_id

    @property
    def id(self) -> int:
        return self.socio_id

    @property
    def pendientes(self) -> int:
        return self.llamadosAtencion

    @property
    def estado(self) -> str:
        return "PENDIENTE" if self.llamadosAtencion > 0 else "CONSOLIDADO"

    class Meta:
        db_table = "atencionFelicitacion"
        verbose_name = "Atención y Felicitación"
        verbose_name_plural = "Atenciones y Felicitaciones"

    def __str__(self) -> str:
        return (
            f"Socio {self.socio_id}: {self.llamadosAtencion} llamados, "
            f"{self.felicitaciones} felicitaciones"
        )


# Aliases retrocompatibles exigidos por las directivas arquitectónicas y el esquema legacy
Reunion = EventoInstitucional
AsistenciaReunion = AsistenciaEvento
RegistroApercibimiento = AtencionFelicitacion
