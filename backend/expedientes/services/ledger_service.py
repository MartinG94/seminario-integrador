"""Libro mayor transaccional inmutable (Spec 011, S5-02.1 y S5-02.2).

- Resuelve el impacto individual de cada imputado al emitirse una resolución.
- Inserta los movimientos en el libro mayor legado `tribunal_puntajeaplicado` y su auditoría
  encadenada en `AsientoLibroMayor`, aplicando la regla 3:1 de llamados y felicitaciones.
- Nunca modifica ni elimina movimientos (Regla Innegociable 3).
"""

import logging
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from expedientes.models import (
    AsientoLibroMayor,
    AtencionFelicitacion,
    DecisionCausalEnum,
    DescargoExpediente,
    Expediente,
    Resolucion,
    ResultadoValoracionT03Enum,
    SolicitudT01,
)
from padron.models import Socio as LegacySocio
from ranking.domain.ledger import (
    GENESIS_HASH,
    ImpactoSocio,
    TipoAsiento,
    TipoImpacto,
    calcular_hash_asiento,
    clasificar_impacto,
    planificar_asientos,
)
from ranking.models import PuntajeAplicado
from socios.models import Socio

logger = logging.getLogger(__name__)

TIPOS_CON_PUNTOS = (
    TipoAsiento.PUNTOS_DIRECTOS,
    TipoAsiento.CONSOLIDACION_LLAMADOS,
    TipoAsiento.CONSOLIDACION_FELICITACIONES,
)
_MEDIDAS = {
    TipoAsiento.LLAMADO_ATENCION: "LLAMADO_ATENCION",
    TipoAsiento.FELICITACION: "FELICITACION",
}


@dataclass(frozen=True)
class ImpactoAplicado:
    puntos: Decimal
    medida: str | None


def imputados_de(expediente: Expediente) -> list[Socio]:
    """Titular y coimputados sin repetir, en orden estable."""
    socios = {expediente.socio_id: expediente.socio}
    for socio in expediente.socios.all():
        socios.setdefault(socio.pk, socio)
    return [socios[pk] for pk in sorted(socios)]


def impacto_solicitado(expediente: Expediente) -> ImpactoSocio:
    """Puntaje o medida especial pedidos al abrir la causa."""
    solicitud = SolicitudT01.objects.filter(expediente=expediente).first()
    especial = getattr(solicitud, "puntaje_especial", "") if solicitud else ""
    if especial:
        return clasificar_impacto(especial)
    return clasificar_impacto(expediente.puntos if expediente.puntos is not None else 0)


def _impacto_por_valoracion(
    puntaje_final: Any, aceptada: bool, solicitado: ImpactoSocio
) -> ImpactoSocio:
    if puntaje_final is not None and str(puntaje_final).strip() != "":
        try:
            return clasificar_impacto(puntaje_final)
        except ValueError:
            logger.warning("Puntaje final ilegible %r: se aplica la regla base.", puntaje_final)
    if aceptada:
        return clasificar_impacto(0)
    return solicitado


def resolver_impacto_socio(
    expediente: Expediente, socio: Socio, solicitado: ImpactoSocio | None = None
) -> ImpactoSocio:
    """Impacto individual (RF-02): valoración del descargo propio o, si no la hay, lo pedido."""
    solicitado = solicitado or impacto_solicitado(expediente)
    descargo = DescargoExpediente.objects.filter(
        expediente=expediente, socio=socio, es_vigente=True
    ).first()
    if descargo is None:
        return solicitado

    decision = descargo.decisiones_causal.order_by("-version").first()
    if decision is not None:
        snapshot = decision.descargo_snapshot or {}
        return _impacto_por_valoracion(
            snapshot.get("puntaje_final"),
            decision.decision == DecisionCausalEnum.ACCEPTED,
            solicitado,
        )

    valoracion = descargo.valoraciones_t03.order_by("-version").first()
    if valoracion is not None:
        return _impacto_por_valoracion(
            valoracion.puntaje_final,
            valoracion.resultado == ResultadoValoracionT03Enum.ACCEPTED,
            solicitado,
        )
    return solicitado


def resolver_nro_socio(socio: Socio) -> int | None:
    """`nroSocio` del padrón legado: ficha vinculada al usuario o identificador numérico."""
    nro = (
        LegacySocio.objects.filter(user_id=socio.user_id).values_list("nroSocio", flat=True).first()
    )
    if nro is not None:
        return int(nro)
    for candidato in (getattr(socio.user, "username", ""), socio.legajo):
        texto = str(candidato or "").strip()
        if texto.isdigit():
            return int(texto)
    return None


class LedgerService:
    """Casos de uso del libro mayor."""

    @classmethod
    @transaction.atomic
    def registrar_resolucion(cls, resolucion: Resolucion, autor: Any) -> list[AsientoLibroMayor]:
        """Genera los asientos de una resolución emitida (RF-01 a RF-07). Idempotente."""
        existentes = list(AsientoLibroMayor.objects.filter(resolucion=resolucion))
        if existentes:
            return existentes

        expediente = resolucion.expediente
        solicitado = impacto_solicitado(expediente)
        autor_id = getattr(autor, "pk", None)
        asientos: list[AsientoLibroMayor] = []

        for imputado in imputados_de(expediente):
            # Bloqueo pesimista por socio: serializa contadores 3:1 y la cadena de hashes.
            socio = Socio.objects.select_for_update().select_related("user").get(pk=imputado.pk)
            impacto = resolver_impacto_socio(expediente, socio, solicitado)
            plan = planificar_asientos(impacto, cls._contador_actual(socio, impacto))
            cls._guardar_contador(socio, impacto, plan[0].contador_resultante)
            nro_socio = resolver_nro_socio(socio)

            for item in plan:
                puntaje_aplicado_id = None
                if item.impacta_libro_mayor:
                    if nro_socio is None:
                        logger.error(
                            "Socio %s sin número de socio: el asiento %s queda solo en auditoría.",
                            socio.pk,
                            item.tipo,
                        )
                    else:
                        movimiento = PuntajeAplicado.registrar_movimiento(
                            nro_socio=nro_socio, puntos=item.puntos, expediente_id=expediente.pk
                        )
                        puntaje_aplicado_id = movimiento.pk
                asientos.append(
                    cls._crear_asiento(
                        resolucion=resolucion,
                        socio=socio,
                        nro_socio=nro_socio,
                        tipo=item.tipo,
                        puntos=item.puntos,
                        contador_resultante=item.contador_resultante,
                        puntaje_aplicado_id=puntaje_aplicado_id,
                        autor_id=autor_id,
                    )
                )
        return asientos

    @staticmethod
    def _contador_actual(socio: Socio, impacto: ImpactoSocio) -> int:
        if impacto.tipo not in (TipoImpacto.LLAMADO_ATENCION, TipoImpacto.FELICITACION):
            return 0
        registro, _ = AtencionFelicitacion.objects.select_for_update().get_or_create(socio=socio)
        if impacto.tipo == TipoImpacto.LLAMADO_ATENCION:
            return registro.llamadosAtencion
        return registro.felicitaciones

    @staticmethod
    def _guardar_contador(socio: Socio, impacto: ImpactoSocio, contador: int | None) -> None:
        if contador is None:
            return
        campo = (
            "llamadosAtencion" if impacto.tipo == TipoImpacto.LLAMADO_ATENCION else "felicitaciones"
        )
        registro = AtencionFelicitacion.objects.select_for_update().get(socio=socio)
        setattr(registro, campo, contador)
        registro.save(update_fields=[campo])

    @staticmethod
    def _crear_asiento(
        *,
        resolucion: Resolucion,
        socio: Socio,
        nro_socio: int | None,
        tipo: TipoAsiento,
        puntos: Decimal,
        contador_resultante: int | None,
        puntaje_aplicado_id: int | None,
        autor_id: int | None,
    ) -> AsientoLibroMayor:
        anterior = (
            AsientoLibroMayor.objects.filter(socio=socio)
            .order_by("-created_at", "-id")
            .values_list("hash_transaccion", flat=True)
            .first()
        )
        hash_anterior = anterior or GENESIS_HASH
        created_at = timezone.now()
        return AsientoLibroMayor.objects.create(
            resolucion=resolucion,
            expediente_id=resolucion.expediente_id,
            socio=socio,
            nro_socio=nro_socio,
            tipo=tipo,
            puntos=puntos,
            contador_resultante=contador_resultante,
            puntaje_aplicado_id=puntaje_aplicado_id,
            autor_id=autor_id,
            hash_anterior=hash_anterior,
            hash_transaccion=calcular_hash_asiento(
                hash_anterior,
                resolucion_id=resolucion.pk,
                expediente_id=resolucion.expediente_id,
                socio_id=socio.pk,
                tipo=tipo,
                puntos=puntos,
                contador_resultante=contador_resultante,
                created_at_iso=created_at.isoformat(),
            ),
            created_at=created_at,
        )

    # --- Consultas del socio (S5-02.2) ---------------------------------------------------

    @staticmethod
    def calcular_saldo(socio: Socio) -> Decimal:
        """Saldo del socio = suma de su libro mayor, mismo criterio que el Ranking (RF-08)."""
        nro_socio = resolver_nro_socio(socio)
        if nro_socio is not None:
            total = PuntajeAplicado.objects.filter(socio_id=nro_socio).aggregate(
                total=Sum("puntajeAplicado")
            )["total"]
        else:
            total = AsientoLibroMayor.objects.filter(
                socio=socio, tipo__in=TIPOS_CON_PUNTOS
            ).aggregate(total=Sum("puntos"))["total"]
        return Decimal(str(total or 0)).quantize(Decimal("0.01"))

    @classmethod
    def resumen_socio(cls, socio: Socio) -> dict[str, Any]:
        """Saldo, pendientes 3:1 y movimientos originados por resoluciones (RF-12)."""
        contadores = AtencionFelicitacion.objects.filter(socio=socio).first()
        asientos = (
            AsientoLibroMayor.objects.filter(socio=socio)
            .select_related("expediente")
            .order_by("-created_at", "-id")
        )
        return {
            "saldo": cls.calcular_saldo(socio),
            "llamados_pendientes": contadores.llamadosAtencion if contadores else 0,
            "felicitaciones_pendientes": contadores.felicitaciones if contadores else 0,
            "movimientos": [
                {
                    "id": asiento.id,
                    "fecha": asiento.created_at,
                    "expediente_id": asiento.expediente_id,
                    "expediente_numero": asiento.expediente.numero,
                    "tipo": asiento.tipo,
                    "tipo_display": asiento.get_tipo_display(),
                    "puntos": asiento.puntos,
                    "contador_resultante": asiento.contador_resultante,
                }
                for asiento in asientos
            ],
        }

    @staticmethod
    def impactos_por_expediente(socio: Socio) -> dict[int, ImpactoAplicado]:
        """Puntos aplicados y medida por causa del socio, en una sola consulta (RF-13)."""
        resultado: dict[int, ImpactoAplicado] = {}
        for expediente_id, tipo, puntos in AsientoLibroMayor.objects.filter(
            socio=socio
        ).values_list("expediente_id", "tipo", "puntos"):
            previo = resultado.get(expediente_id, ImpactoAplicado(Decimal("0.00"), None))
            resultado[expediente_id] = ImpactoAplicado(
                puntos=previo.puntos + Decimal(puntos),
                medida=previo.medida or _MEDIDAS.get(tipo),
            )
        return resultado

    @staticmethod
    def impactos_de_resolucion(resolucion: Resolucion) -> dict[int, ImpactoAplicado]:
        """Impacto aplicado a cada socio por una resolución (publicación, RF-16)."""
        resultado: dict[int, ImpactoAplicado] = {}
        for socio_id, tipo, puntos in AsientoLibroMayor.objects.filter(
            resolucion=resolucion
        ).values_list("socio_id", "tipo", "puntos"):
            previo = resultado.get(socio_id, ImpactoAplicado(Decimal("0.00"), None))
            resultado[socio_id] = ImpactoAplicado(
                puntos=previo.puntos + Decimal(puntos),
                medida=previo.medida or _MEDIDAS.get(tipo),
            )
        return resultado
