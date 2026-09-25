"""Mapeos de sólo lectura de los puntajes legados consumidos por ranking."""

from django.db import models

from padron.models import ReadOnlyModel, Socio


class PuntajeGeneral(ReadOnlyModel):
    """
    Caché histórico acumulado de puntaje general (tabla tribunal_puntajegeneral).
    """

    idPuntajeGeneral = models.AutoField(primary_key=True, db_column="idPuntajeGeneral")
    socio = models.OneToOneField(
        Socio,
        on_delete=models.DO_NOTHING,
        db_constraint=False,
        db_column="socio_id",
        related_name="puntaje_general",
    )
    puntos = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    felicitaciones = models.IntegerField(default=0)
    llamadosAtencion = models.IntegerField(default=0)

    class Meta:
        managed = False
        db_table = "tribunal_puntajegeneral"
        verbose_name = "Puntaje General (Caché)"
        verbose_name_plural = "Puntajes Generales (Caché)"

    def __str__(self) -> str:
        return f"Socio {self.socio_id}: {self.puntos} pts"


class PuntajeAplicado(ReadOnlyModel):
    """
    Libro mayor transaccional de puntos aplicados (tabla tribunal_puntajeaplicado).
    Cada registro representa un movimiento disciplinario o mérito adjudicado.
    """

    idPuntajeAplicado = models.AutoField(primary_key=True, db_column="idPuntajeAplicado")
    puntajeAplicado = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        db_column="puntajeAplicado",
    )
    socio = models.ForeignKey(
        Socio,
        on_delete=models.DO_NOTHING,
        db_constraint=False,
        db_column="socio_id",
        related_name="puntajes_aplicados",
    )
    expediente_id = models.IntegerField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = "tribunal_puntajeaplicado"
        verbose_name = "Puntaje Aplicado (Libro Mayor)"
        verbose_name_plural = "Puntajes Aplicados (Libro Mayor)"

    def __str__(self) -> str:
        return f"Socio {self.socio_id}: {self.puntajeAplicado} pts"
