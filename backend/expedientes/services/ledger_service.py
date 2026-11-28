"""Libro mayor transaccional inmutable (Spec 011, S5-02.1 y S5-02.2).

- Resuelve el impacto individual de cada imputado al emitirse una resolución.
- Inserta los movimientos en el libro mayor legado `tribunal_puntajeaplicado` y su auditoría
  encadenada en `AsientoLibroMayor`.
- La regla 3:1 tiene un único motor (`WarningAccumulationService`): una medida especial se
  cuenta una sola vez, sea al evaluar el descargo o, si no pasó por esa evaluación, al emitir.
- Las enmiendas (SCRUM-103, Opción B) registran la reversión íntegra y el nuevo impacto por
  este mismo camino.
- Nunca modifica ni elimina movimientos (Regla Innegociable 3).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from django.core.exceptions import ValidationError
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
    detectar_medida_expediente,
)
from ranking.domain.ledger import (
    GENESIS_HASH,
    ImpactoSocio,
    TipoAsiento,
    TipoImpacto,
    calcular_hash_asiento,
    clasificar_impacto,
    impacta_libro_mayor,
    tipo_asiento_para,
)
from ranking.models import PuntajeAplicado
from socios.models import Socio

if TYPE_CHECKING:
    from expedientes.models import EnmiendaResolucion

logger = logging.getLogger(__name__)

TIPOS_CON_PUNTOS = (
    TipoAsiento.PUNTOS_DIRECTOS,
    TipoAsiento.LLAMADO_ATENCION,
    TipoAsiento.FELICITACION,
    TipoAsiento.CONSOLIDACION_LLAMADOS,
    TipoAsiento.CONSOLIDACION_FELICITACIONES,
    TipoAsiento.REVERSION,
)
_MEDIDAS = {
    TipoAsiento.LLAMADO_ATENCION: "LLAMADO_ATENCION",
    TipoAsiento.FELICITACION: "FELICITACION",
}
_TIPOS_MEDIDA = (TipoImpacto.LLAMADO_ATENCION, TipoImpacto.FELICITACION)


class SocioSinNumeroError(ValidationError):
    """El socio no tiene N° de socio: su movimiento no podría reflejarse en el Ranking."""


@dataclass(frozen=True)
class ImpactoAplicado:
    puntos: Decimal
    medida: str | None


@dataclass(frozen=True)
class VerificacionCadena:
    valida: bool
    asientos_verificados: int
    primer_asiento_invalido: int | None = None


# --- Resolución del impacto individual -----------------------------------------------------


def imputados_de(expediente: Expediente) -> list[Socio]:
    """Titular y coimputados sin repetir, en orden estable."""
    socios = {expediente.socio_id: expediente.socio}
    for socio in expediente.socios.all():
        socios.setdefault(socio.pk, socio)
    return [socios[pk] for pk in sorted(socios)]


def impacto_solicitado(expediente: Expediente) -> ImpactoSocio:
    """Impacto pedido vigente: el puntaje del expediente (incluye adecuaciones del T01).

    La medida especial del T01 o de un expediente con puntos en 0.00 se resuelve vía
    `detectar_medida_expediente`.
    """
    puntos = Decimal(str(expediente.puntos)) if expediente.puntos is not None else Decimal("0")
    if puntos != Decimal("0"):
        return clasificar_impacto(puntos)
    medida = detectar_medida_expediente(expediente)
    return clasificar_impacto(medida or 0)


def _clasificar_o_none(valor: Any) -> ImpactoSocio | None:
    if valor is None or str(valor).strip() == "":
        return None
    try:
        return clasificar_impacto(valor)
    except ValueError:
        logger.warning("Puntaje ilegible %r: se aplica la regla base.", valor)
        return None


def _impacto_por_valoracion(
    puntaje_final: Any, aceptada: bool, solicitado: ImpactoSocio
) -> ImpactoSocio:
    impacto = _clasificar_o_none(puntaje_final)
    if impacto is not None:
        return impacto
    if aceptada:
        return clasificar_impacto(0)
    return solicitado


def _descargos_de(expediente: Expediente, socio: Socio) -> list[DescargoExpediente]:
    return list(
        DescargoExpediente.objects.filter(expediente=expediente, socio=socio).order_by(
            "-es_vigente", "-id"
        )
    )


def resolver_impacto_socio(
    expediente: Expediente, socio: Socio, solicitado: ImpactoSocio | None = None
) -> ImpactoSocio:
    """Impacto individual (RF-02), en este orden de prioridad:

    1. Exclusión fundada del involucrado (SCRUM-102): no recibe impacto.
    2. Puntaje ratificado del socio (SCRUM-101 y enmiendas, SCRUM-103).
    3. Última decisión causal T02 o valoración T03 de su descargo vigente.
    4. Lo solicitado al abrir la causa.
    """
    solicitado = solicitado or impacto_solicitado(expediente)
    descargos = _descargos_de(expediente, socio)
    if any(d.esta_excluido for d in descargos):
        return clasificar_impacto(0)

    for descargo in descargos:
        ratificado = _clasificar_o_none(descargo.puntaje_ratificado)
        if ratificado is not None:
            return ratificado

    vigente = next((d for d in descargos if d.es_vigente), None)
    if vigente is None:
        return solicitado

    decision = vigente.decisiones_causal.order_by("-version").first()
    if decision is not None:
        snapshot = decision.descargo_snapshot or {}
        return _impacto_por_valoracion(
            snapshot.get("puntaje_final"),
            decision.decision == DecisionCausalEnum.ACCEPTED,
            solicitado,
        )

    valoracion = vigente.valoraciones_t03.order_by("-version").first()
    if valoracion is not None:
        return _impacto_por_valoracion(
            valoracion.puntaje_final,
            valoracion.resultado == ResultadoValoracionT03Enum.ACCEPTED,
            solicitado,
        )
    return solicitado


def impactos_dictaminados(expediente: Expediente) -> dict[int, ImpactoSocio]:
    """Impacto de cada imputado según el dictamen vigente (base del proveedor de decisión)."""
    solicitado = impacto_solicitado(expediente)
    return {
        socio.pk: resolver_impacto_socio(expediente, socio, solicitado)
        for socio in imputados_de(expediente)
    }


def resolver_nro_socio(socio: Socio) -> int | None:
    """N° de socio institucional (`Socio.numero_socio`, SCRUM-114): clave del libro mayor."""
    return int(socio.numero_socio) if socio.numero_socio is not None else None


def _nro_socio_obligatorio(socio: Socio) -> int:
    nro_socio = resolver_nro_socio(socio)
    if nro_socio is None:
        raise SocioSinNumeroError(
            f"{socio.last_name}, {socio.first_name} no tiene N° de socio asignado: no se puede "
            "registrar su movimiento de puntos. Asignale el N° de socio y volvé a emitir."
        )
    return nro_socio


# --- Casos de uso ----------------------------------------------------------------------------


class LedgerService:
    """Casos de uso del libro mayor."""

    @classmethod
    @transaction.atomic
    def registrar_resolucion(cls, resolucion: Resolucion, autor: Any) -> list[AsientoLibroMayor]:
        """Genera los asientos de una resolución emitida (RF-01 a RF-07). Idempotente."""
        resolucion = cls._bloquear(resolucion)
        existentes = list(AsientoLibroMayor.objects.filter(resolucion=resolucion))
        if existentes:
            return existentes

        expediente = resolucion.expediente
        solicitado = impacto_solicitado(expediente)
        asientos: list[AsientoLibroMayor] = []
        for imputado in imputados_de(expediente):
            socio = cls._bloquear_socio(imputado)
            impacto = resolver_impacto_socio(expediente, socio, solicitado)
            asientos.append(
                cls._registrar_impacto(resolucion, socio, impacto, autor, ya_contada=False)
            )
        return asientos

    @classmethod
    @transaction.atomic
    def registrar_enmienda(
        cls, enmienda: EnmiendaResolucion, autor: Any
    ) -> list[AsientoLibroMayor]:
        """Opción B (SCRUM-103): reversión íntegra de lo aplicado y nuevo impacto. Idempotente."""
        resolucion = cls._bloquear(enmienda.resolucion_nueva)
        existentes = list(AsientoLibroMayor.objects.filter(resolucion=resolucion))
        if existentes:
            return existentes

        expediente = resolucion.expediente
        solicitado = impacto_solicitado(expediente)
        asientos: list[AsientoLibroMayor] = []
        for imputado in imputados_de(expediente):
            socio = cls._bloquear_socio(imputado)
            impacto = resolver_impacto_socio(expediente, socio, solicitado)
            medida_previa = cls._medida_aplicada(enmienda.resolucion_anterior, socio)
            misma_medida = medida_previa is not None and medida_previa == impacto.tipo

            neto = cls._neto_aplicado(expediente, socio)
            if not misma_medida and (
                neto != Decimal("0.00") or (medida_previa and medida_previa != impacto.tipo)
            ):
                asientos.append(
                    cls._registrar_reversion(resolucion, socio, neto, medida_previa, impacto, autor)
                )
            asientos.append(
                cls._registrar_impacto(resolucion, socio, impacto, autor, ya_contada=misma_medida)
            )
        return asientos

    # --- Pasos internos ---

    @staticmethod
    def _bloquear(resolucion: Resolucion) -> Resolucion:
        """Serializa la escritura por resolución, aun fuera de `emitir_resolucion`."""
        return (
            Resolucion.objects.select_for_update()
            .select_related("expediente")
            .get(pk=resolucion.pk)
        )

    @staticmethod
    def _bloquear_socio(socio: Socio) -> Socio:
        """Bloqueo pesimista por socio: serializa contadores 3:1 y la cadena de hashes."""
        return Socio.objects.select_for_update().select_related("user").get(pk=socio.pk)

    @classmethod
    def _registrar_impacto(
        cls,
        resolucion: Resolucion,
        socio: Socio,
        impacto: ImpactoSocio,
        autor: Any,
        *,
        ya_contada: bool,
    ) -> AsientoLibroMayor:
        contador = None
        puntaje_aplicado_id = None
        nro_socio = resolver_nro_socio(socio)
        puntos_asiento = Decimal("0.00")

        if impacto.tipo in _TIPOS_MEDIDA:
            es_llamado = impacto.tipo == TipoImpacto.LLAMADO_ATENCION
            if not ya_contada:
                from expedientes.services.warning_accumulation_service import (
                    WarningAccumulationService,
                )

                atencion_actual, _ = AtencionFelicitacion.objects.get_or_create(socio=socio)
                contador_actual = (
                    atencion_actual.llamadosAtencion
                    if es_llamado
                    else atencion_actual.felicitaciones
                )
                if contador_actual + 1 >= WarningAccumulationService.CONSOLIDATION_THRESHOLD:
                    nro_socio = _nro_socio_obligatorio(socio)
                contador, puntaje_aplicado_id, puntos_asiento = (
                    WarningAccumulationService.apply_confirmed_measure(
                        socio=socio,
                        es_llamado=es_llamado,
                        expediente_id=resolucion.expediente_id,
                        nro_socio=nro_socio,
                        actor=getattr(autor, "username", None) or "TRIBUNAL",
                    )
                )
            else:
                registro, _ = AtencionFelicitacion.objects.get_or_create(socio=socio)
                contador = registro.llamadosAtencion if es_llamado else registro.felicitaciones
                puntaje_aplicado_id = None
                puntos_asiento = Decimal("0.00")
        elif impacta_libro_mayor(impacto):
            nro_socio = _nro_socio_obligatorio(socio)
            puntaje_aplicado_id = PuntajeAplicado.registrar_movimiento(
                nro_socio=nro_socio, puntos=impacto.puntos, expediente_id=resolucion.expediente_id
            ).pk
            puntos_asiento = impacto.puntos

        return cls._crear_asiento(
            resolucion=resolucion,
            socio=socio,
            nro_socio=nro_socio,
            tipo=tipo_asiento_para(impacto),
            puntos=puntos_asiento,
            contador_resultante=contador,
            puntaje_aplicado_id=puntaje_aplicado_id,
            autor=autor,
        )

    @classmethod
    def _registrar_reversion(
        cls,
        resolucion: Resolucion,
        socio: Socio,
        neto: Decimal,
        medida_previa: TipoImpacto | None,
        impacto: ImpactoSocio,
        autor: Any,
    ) -> AsientoLibroMayor:
        contador = None
        if medida_previa and medida_previa != impacto.tipo:
            contador = cls._revertir_medida(
                socio, medida_previa, autor, restaurar_terna=(neto != Decimal("0.00"))
            )
        puntaje_aplicado_id = None
        nro_socio = resolver_nro_socio(socio)
        if neto != Decimal("0.00"):
            nro_socio = _nro_socio_obligatorio(socio)
            puntaje_aplicado_id = PuntajeAplicado.registrar_movimiento(
                nro_socio=nro_socio, puntos=-neto, expediente_id=resolucion.expediente_id
            ).pk
        return cls._crear_asiento(
            resolucion=resolucion,
            socio=socio,
            nro_socio=nro_socio,
            tipo=TipoAsiento.REVERSION,
            puntos=-neto,
            contador_resultante=contador,
            puntaje_aplicado_id=puntaje_aplicado_id,
            autor=autor,
        )

    @staticmethod
    def _neto_aplicado(expediente: Expediente, socio: Socio) -> Decimal:
        """Puntos ya aplicados al socio por la causa, incluidos los movimientos legados."""
        nro_socio = resolver_nro_socio(socio)
        if nro_socio is not None:
            total = PuntajeAplicado.objects.filter(
                expediente_id=expediente.pk, socio_id=nro_socio
            ).aggregate(total=Sum("puntajeAplicado"))["total"]
        else:
            total = AsientoLibroMayor.objects.filter(
                expediente=expediente, socio=socio, tipo__in=TIPOS_CON_PUNTOS
            ).aggregate(total=Sum("puntos"))["total"]
        return Decimal(str(total or 0)).quantize(Decimal("0.01"))

    @staticmethod
    def _medida_aplicada(resolucion: Resolucion, socio: Socio) -> TipoImpacto | None:
        tipo = (
            AsientoLibroMayor.objects.filter(
                resolucion=resolucion,
                socio=socio,
                tipo__in=(TipoAsiento.LLAMADO_ATENCION, TipoAsiento.FELICITACION),
            )
            .values_list("tipo", flat=True)
            .first()
        )
        return TipoImpacto(tipo) if tipo else None

    @staticmethod
    def _revertir_medida(
        socio: Socio,
        medida: TipoImpacto,
        autor: Any,
        *,
        restaurar_terna: bool = False,
    ) -> int:
        from expedientes.services.warning_accumulation_service import (
            WarningAccumulationService,
        )

        actor = getattr(autor, "username", None) or "TRIBUNAL"
        if medida == TipoImpacto.LLAMADO_ATENCION:
            return WarningAccumulationService.revert_warning(
                socio_id=socio.pk,
                actor=actor,
                restaurar_terna=restaurar_terna,
            ).llamadosAtencion
        return WarningAccumulationService.revert_felicitacion(
            socio_id=socio.pk,
            actor=actor,
            restaurar_terna=restaurar_terna,
        ).felicitaciones

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
        autor: Any,
    ) -> AsientoLibroMayor:
        anterior = (
            AsientoLibroMayor.objects.filter(socio=socio)
            .order_by("-created_at", "-id")
            .values_list("hash_transaccion", flat=True)
            .first()
        )
        hash_anterior = anterior or GENESIS_HASH
        autor_id = getattr(autor, "pk", None)
        created_at = timezone.now()
        puntos = Decimal(puntos).quantize(Decimal("0.01"))
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
                nro_socio=nro_socio,
                puntaje_aplicado_id=puntaje_aplicado_id,
                autor_id=autor_id,
                created_at=created_at,
            ),
            created_at=created_at,
        )

    # --- Integridad --------------------------------------------------------------------------

    @staticmethod
    def verificar_cadena(socio: Socio) -> VerificacionCadena:
        """Recalcula el hash encadenado de cada asiento del socio, en orden de inserción."""
        esperado_anterior = GENESIS_HASH
        verificados = 0
        for asiento in AsientoLibroMayor.objects.filter(socio=socio).order_by("created_at", "id"):
            recalculado = calcular_hash_asiento(
                esperado_anterior,
                resolucion_id=asiento.resolucion_id,
                expediente_id=asiento.expediente_id,
                socio_id=asiento.socio_id,
                tipo=asiento.tipo,
                puntos=asiento.puntos,
                contador_resultante=asiento.contador_resultante,
                nro_socio=asiento.nro_socio,
                puntaje_aplicado_id=asiento.puntaje_aplicado_id,
                autor_id=asiento.autor_id,
                created_at=asiento.created_at,
            )
            if (
                asiento.hash_anterior != esperado_anterior
                or asiento.hash_transaccion != recalculado
            ):
                return VerificacionCadena(False, verificados, asiento.pk)
            esperado_anterior = asiento.hash_transaccion
            verificados += 1
        return VerificacionCadena(True, verificados)

    # --- Consultas del socio (S5-02.2) -------------------------------------------------------

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
    def _agrupar(filas: Any) -> dict[int, ImpactoAplicado]:
        """Suma puntos y conserva la medida vigente (la de la última resolución con medida)."""
        resultado: dict[int, ImpactoAplicado] = {}
        for clave, tipo, puntos in filas:
            previo = resultado.get(clave, ImpactoAplicado(Decimal("0.00"), None))
            medida = previo.medida
            puntos_dec = Decimal(puntos)
            if tipo in _MEDIDAS:
                medida = _MEDIDAS[tipo] if puntos_dec == Decimal("0.00") else None
            elif tipo in (TipoAsiento.PUNTOS_DIRECTOS, TipoAsiento.SIN_IMPACTO):
                medida = None
            resultado[clave] = ImpactoAplicado(previo.puntos + puntos_dec, medida)
        return resultado

    @classmethod
    def impactos_por_expediente(cls, socio: Socio) -> dict[int, ImpactoAplicado]:
        """Puntos aplicados y medida por causa del socio, en una sola consulta (RF-13)."""
        filas = (
            AsientoLibroMayor.objects.filter(socio=socio)
            .order_by("created_at", "id")
            .values_list("expediente_id", "tipo", "puntos")
        )
        return cls._agrupar(filas)

    @classmethod
    def impactos_de_resolucion(cls, resolucion: Resolucion) -> dict[int, ImpactoAplicado]:
        """Impacto neto vigente de cada socio de la causa tras una resolución (RF-16)."""
        filas = (
            AsientoLibroMayor.objects.filter(
                expediente_id=resolucion.expediente_id,
                resolucion__version__lte=resolucion.version,
            )
            .order_by("created_at", "id")
            .values_list("socio_id", "tipo", "puntos")
        )
        return cls._agrupar(filas)
