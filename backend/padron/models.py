"""Modelos ORM de sólo lectura mapeados contra el esquema institucional legado (MySQL).

Todos los modelos declaran `managed = False` para garantizar inmutabilidad
y prevenir cualquier modificación de esquema por parte del SGD-AVEIT.

Referencia:
  - ADR-001, Sección 4.
  - plan.md, Sección 4.1.
  - DDL: sistema_actual_legado_schema.sql.
"""

from django.core.exceptions import PermissionDenied
from django.db import models


class ReadOnlyQuerySet(models.QuerySet):
    """QuerySet inmutable para salvaguardar el padrón institucional contra mutaciones masivas.

    Bloquea las operaciones DML masivas de Django ORM que omiten los métodos save() y delete()
    del ciclo de vida de instancia del modelo.
    """

    def update(self, **kwargs):
        raise PermissionDenied(
            "Operación denegada: No se permiten actualizaciones masivas en modelos de sólo lectura."
        )

    def delete(self):
        raise PermissionDenied(
            "Operación denegada: No se permiten eliminaciones masivas en modelos de sólo lectura."
        )

    def bulk_create(self, objs, **kwargs):
        raise PermissionDenied(
            "Operación denegada: No se permite creación masiva en modelos de sólo lectura."
        )

    def bulk_update(self, objs, fields, **kwargs):
        raise PermissionDenied(
            "Operación denegada: No se permiten modificaciones masivas en modelos de sólo lectura."
        )


class ReadOnlyModel(models.Model):
    """Modelo base abstracto de estricta sólo lectura para el padrón institucional.

    Garantiza el cumplimiento innegociable de RF-PADRON-01 y RNF-PADRON-02 impidiendo cualquier
    mutación (save/delete/update masivo) originada desde el código de la aplicación.
    Permite sobreescritura controlada exclusiva para fixtures de testing
    mediante `_allow_write = True`.
    """

    objects = ReadOnlyQuerySet.as_manager()

    class Meta:
        abstract = True
        managed = False

    def save(self, *args, **kwargs):
        if getattr(self, "_allow_write", False):
            return super().save(*args, **kwargs)
        raise PermissionDenied(
            "Operación denegada: Los modelos del padrón institucional son de estricta sólo lectura."
        )

    def delete(self, *args, **kwargs):
        if getattr(self, "_allow_write", False):
            return super().delete(*args, **kwargs)
        raise PermissionDenied(
            "Operación denegada: Los modelos del padrón institucional son de estricta sólo lectura."
        )


class Subcomision(ReadOnlyModel):
    """Subcomisión institucional preexistente (`socio_tiposubcomision`)."""

    codSubcomision = models.AutoField(primary_key=True, db_column="codSubcomision")
    nombre = models.CharField(max_length=45)

    class Meta:
        managed = False
        db_table = "socio_tiposubcomision"
        verbose_name = "Subcomisión Institucional"
        verbose_name_plural = "Subcomisiones Institucionales"

    def __str__(self) -> str:
        return self.nombre


class Socio(ReadOnlyModel):
    """Ficha central de socio institucional (`socio_lista`)."""

    nroSocio = models.AutoField(primary_key=True, db_column="nroSocio")
    apellido = models.CharField(max_length=45)
    nombre = models.CharField(max_length=45)
    fechaIngreso = models.DateField()
    codTipoDoc = models.IntegerField(db_column="codTipoDoc")
    nroDoc = models.IntegerField(db_column="nroDoc")
    fechaNac = models.DateField(blank=True)
    codSexo = models.IntegerField(db_column="codSexo")
    subcomision = models.ForeignKey(
        Subcomision,
        on_delete=models.DO_NOTHING,
        db_column="codSubcomision",
        blank=True,
    )
    codEstadoCivil = models.IntegerField(null=True, blank=True, db_column="codEstadoCivil")
    fechaBaja = models.DateField(null=True, blank=True, db_column="fechaBaja")
    anoSocial = models.IntegerField(db_column="anoSocial")
    ingresante = models.BooleanField(default=False)
    idTipoSocio = models.IntegerField(db_column="idTipoSocio")
    user_id = models.IntegerField(null=True, blank=True, db_column="user_id")
    forzarCambioClave = models.BooleanField(default=False, db_column="forzarCambioClave")

    class Meta:
        managed = False
        db_table = "socio_lista"
        verbose_name = "Socio Institucional"
        verbose_name_plural = "Socios Institucionales"

    def __str__(self) -> str:
        return f"{self.apellido}, {self.nombre} (#{self.nroSocio})"


class SocioEstudio(ReadOnlyModel):
    """Registro académico y de legajo universitario (`socio_estudio`).

    IMPORTANTE (HIGH-002 / HIGH-IT2-001):
    - Clave primaria física explícita `compositeKey`.
    - Sin `ordering` en `Meta` para evitar inyección de columnas en `SELECT DISTINCT`.
    """

    compositeKey = models.IntegerField(primary_key=True, db_column="compositeKey")
    socio = models.ForeignKey(
        Socio, on_delete=models.DO_NOTHING, db_column="nroSocio", related_name="estudios"
    )
    nroLegajo = models.IntegerField(db_column="nroLegajo")
    codEspecialidad = models.IntegerField(db_column="codEspecialidad")
    curso = models.CharField(max_length=10, null=True, blank=True)
    aula = models.CharField(max_length=10, null=True, blank=True)
    codTurno = models.IntegerField(null=True, blank=True, db_column="codTurno")

    class Meta:
        managed = False
        db_table = "socio_estudio"
        verbose_name = "Estudio del Socio"
        verbose_name_plural = "Estudios del Socio"

    def __str__(self) -> str:
        return f"Legajo {self.nroLegajo} (Socio {self.socio_id})"


class SocioEmail(ReadOnlyModel):
    """Casilla de correo electrónico satélite (`socio_email`).

    IMPORTANTE (HIGH-002):
    - Clave primaria física explícita `compositeKey`.
    """

    compositeKey = models.IntegerField(primary_key=True, db_column="compositeKey")
    socio = models.ForeignKey(
        Socio, on_delete=models.DO_NOTHING, db_column="nroSocio", related_name="emails"
    )
    idEmail = models.IntegerField(db_column="idEmail")
    email = models.CharField(max_length=45)
    comprobado = models.BooleanField(default=False)
    habilitado = models.BooleanField(default=False)

    class Meta:
        managed = False
        db_table = "socio_email"
        verbose_name = "Email del Socio"
        verbose_name_plural = "Emails del Socio"

    def __str__(self) -> str:
        return self.email


class SocioEstado(ReadOnlyModel):
    """Catálogo de estados de membresía del sistema legado (`socio_estado`)."""

    codEstadoSocio = models.AutoField(primary_key=True, db_column="codEstadoSocio")
    nombre = models.CharField(max_length=45)
    descripcion = models.CharField(max_length=45, null=True, blank=True)

    class Meta:
        managed = False
        db_table = "socio_estado"
        verbose_name = "Estado de Socio (Catálogo)"
        verbose_name_plural = "Estados de Socio (Catálogo)"

    def __str__(self) -> str:
        return self.nombre


class SocioEstadoHistorial(ReadOnlyModel):
    """Historial transaccional de cambios de estado societario (`socio_estadoHistorial`)."""

    idEstadoHistorial = models.AutoField(primary_key=True, db_column="idEstadoHistorial")
    idGrupo = models.IntegerField(db_column="idGrupo")
    socio = models.ForeignKey(
        Socio,
        on_delete=models.DO_NOTHING,
        db_column="nroSocio",
        related_name="historial_estados",
    )
    fechaHora = models.DateTimeField(db_column="fechaHora")
    codEstadoSocio = models.IntegerField(db_column="codEstadoSocio")
    socio_motivoCambioEstado = models.IntegerField(db_column="socio_motivoCambioEstado")

    class Meta:
        managed = False
        db_table = "socio_estadoHistorial"
        ordering = ["-fechaHora"]
        verbose_name = "Historial de Estado"
        verbose_name_plural = "Historiales de Estado"

    def __str__(self) -> str:
        return f"Socio {self.socio_id} - Estado {self.codEstadoSocio} ({self.fechaHora})"
