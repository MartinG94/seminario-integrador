"""Modelos ORM para el módulo de Ranking y Padrón Legado (SGD-AVEIT)."""

import datetime

from django.db import models


class Subcomision(models.Model):
    """Subcomisión oficial institucional (tabla socio_tiposubcomision)."""

    codSubcomision = models.AutoField(primary_key=True, db_column="codSubcomision")
    nombre = models.CharField(max_length=45)

    class Meta:
        db_table = "socio_tiposubcomision"
        verbose_name = "Subcomisión"
        verbose_name_plural = "Subcomisiones"

    def __str__(self) -> str:
        return self.nombre


class TipoSocio(models.Model):
    """Cargo o tipo estatutario de socio (tabla socio_tipoSocio)."""

    idTipoSocio = models.AutoField(primary_key=True, db_column="idTipoSocio")
    nombre = models.CharField(max_length=45)

    class Meta:
        db_table = "socio_tipoSocio"
        verbose_name = "Tipo de Socio"
        verbose_name_plural = "Tipos de Socio"

    def __str__(self) -> str:
        return self.nombre


class EstadoSocio(models.Model):
    """Estado social de membresía (tabla socio_estado)."""

    codEstadoSocio = models.AutoField(primary_key=True, db_column="codEstadoSocio")
    nombre = models.CharField(max_length=45)
    descripcion = models.CharField(max_length=45, null=True, blank=True)

    class Meta:
        db_table = "socio_estado"
        verbose_name = "Estado de Socio"
        verbose_name_plural = "Estados de Socio"

    def __str__(self) -> str:
        return self.nombre


class Socio(models.Model):
    """
    Padrón central de socios (tabla socio_lista).
    Representa a los miembros de AVEIT con su año social y subcomisión.
    """

    nroSocio = models.AutoField(primary_key=True, db_column="nroSocio")
    apellido = models.CharField(max_length=45)
    nombre = models.CharField(max_length=45)
    fechaIngreso = models.DateField(default=datetime.date.today)
    codTipoDoc = models.IntegerField(default=1)
    nroDoc = models.IntegerField(default=0)
    fechaNac = models.DateField(default=datetime.date.today, null=True, blank=True)
    codSexo = models.IntegerField(default=1)
    subcomision = models.ForeignKey(
        Subcomision,
        on_delete=models.DO_NOTHING,
        db_column="codSubcomision",
        related_name="socios",
        null=True,
        blank=True,
    )
    codEstadoCivil = models.IntegerField(null=True, blank=True)
    fechaBaja = models.DateField(null=True, blank=True)
    anoSocial = models.IntegerField(default=1)
    ingresante = models.BooleanField(default=False)
    tipoSocio = models.ForeignKey(
        TipoSocio,
        on_delete=models.DO_NOTHING,
        db_column="idTipoSocio",
        related_name="socios",
        null=True,
        blank=True,
    )
    user_id = models.IntegerField(null=True, blank=True)
    forzarCambioClave = models.BooleanField(default=False)

    class Meta:
        db_table = "socio_lista"
        verbose_name = "Socio"
        verbose_name_plural = "Socios"

    def __str__(self) -> str:
        return f"{self.apellido}, {self.nombre} ({self.nroSocio})"

    @property
    def categoria(self) -> str:
        """
        Regla Canónica AVEIT (Estatuto 2026 / Decisión PO):
        - Junior / Pasivo: 1.º a 3.º año social -> 'PASIVO'
        - Senior / Activo: 4.º a 6.º año social -> 'ACTIVO'
        """
        return "ACTIVO" if (self.anoSocial or 0) >= 4 else "PASIVO"


class SocioEstudio(models.Model):
    """Registro académico y legajo universitario del socio (tabla socio_estudio)."""

    compositeKey = models.IntegerField(primary_key=True, db_column="compositeKey")
    socio = models.ForeignKey(
        Socio,
        on_delete=models.CASCADE,
        db_column="nroSocio",
        related_name="estudios",
    )
    nroLegajo = models.IntegerField(db_column="nroLegajo")
    codEspecialidad = models.IntegerField(default=1)
    curso = models.CharField(max_length=10, null=True, blank=True)
    aula = models.CharField(max_length=10, null=True, blank=True)
    codTurno = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = "socio_estudio"
        verbose_name = "Estudio de Socio"
        verbose_name_plural = "Estudios de Socio"

    def __str__(self) -> str:
        return f"Legajo {self.nroLegajo} (Socio {self.socio_id})"


class PuntajeGeneral(models.Model):
    """
    Caché histórico acumulado de puntaje general (tabla tribunal_puntajegeneral).
    """

    idPuntajeGeneral = models.AutoField(primary_key=True, db_column="idPuntajeGeneral")
    socio = models.OneToOneField(
        Socio,
        on_delete=models.CASCADE,
        db_column="socio_id",
        related_name="puntaje_general",
    )
    puntos = models.FloatField(default=0.0)
    felicitaciones = models.IntegerField(default=0)
    llamadosAtencion = models.IntegerField(default=0)

    class Meta:
        db_table = "tribunal_puntajegeneral"
        verbose_name = "Puntaje General (Caché)"
        verbose_name_plural = "Puntajes Generales (Caché)"

    def __str__(self) -> str:
        return f"Socio {self.socio_id}: {self.puntos} pts"


class PuntajeAplicado(models.Model):
    """
    Libro mayor transaccional de puntos aplicados (tabla tribunal_puntajeaplicado).
    Cada registro representa un movimiento disciplinario o mérito adjudicado.
    """

    idPuntajeAplicado = models.AutoField(primary_key=True, db_column="idPuntajeAplicado")
    puntajeAplicado = models.FloatField(db_column="puntajeAplicado")
    socio = models.ForeignKey(
        Socio,
        on_delete=models.CASCADE,
        db_column="socio_id",
        related_name="puntajes_aplicados",
    )
    expediente_id = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = "tribunal_puntajeaplicado"
        verbose_name = "Puntaje Aplicado (Libro Mayor)"
        verbose_name_plural = "Puntajes Aplicados (Libro Mayor)"

    def __str__(self) -> str:
        return f"Socio {self.socio_id}: {self.puntajeAplicado} pts"
