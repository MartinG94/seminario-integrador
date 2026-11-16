"""Dominio puro del libro mayor de puntos (Spec 011, S5-02.1).

Sin dependencias de Django: clasifica el impacto individual de una resolución, aplica la
regla 3:1 de llamados de atención y felicitaciones (Notas del PO, 07/10/2026, sección 6)
y calcula el hash SHA-256 encadenado de cada asiento.
"""

import hashlib
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from enum import StrEnum
from typing import Any, NamedTuple

CONSOLIDATION_THRESHOLD = 3
GENESIS_HASH = "0" * 64
_PRECISION = Decimal("0.01")

_LLAMADO_ALIASES = frozenset(
    {"LLAMADO_ATENCION", "LLAMADO DE ATENCIÓN", "LLAMADO DE ATENCION", "APERCIBIMIENTO"}
)
_FELICITACION_ALIASES = frozenset({"FELICITACION", "FELICITACIÓN", "RECONOCIMIENTO"})
# Valores de orden heredados (±0,25 y ±0,33) que identifican medidas especiales: nunca son puntos.
_LLAMADO_RANKS = frozenset({Decimal("-0.25"), Decimal("-0.33")})
_FELICITACION_RANKS = frozenset({Decimal("0.25"), Decimal("0.33")})


class TipoImpacto(StrEnum):
    PUNTOS = "PUNTOS"
    SIN_IMPACTO = "SIN_IMPACTO"
    LLAMADO_ATENCION = "LLAMADO_ATENCION"
    FELICITACION = "FELICITACION"


class TipoAsiento(StrEnum):
    PUNTOS_DIRECTOS = "PUNTOS_DIRECTOS"
    SIN_IMPACTO = "SIN_IMPACTO"
    LLAMADO_ATENCION = "LLAMADO_ATENCION"
    FELICITACION = "FELICITACION"
    CONSOLIDACION_LLAMADOS = "CONSOLIDACION_LLAMADOS"
    CONSOLIDACION_FELICITACIONES = "CONSOLIDACION_FELICITACIONES"


@dataclass(frozen=True)
class ImpactoSocio:
    tipo: TipoImpacto
    puntos: Decimal


@dataclass(frozen=True)
class AsientoPlanificado:
    tipo: TipoAsiento
    puntos: Decimal
    contador_resultante: int | None
    impacta_libro_mayor: bool


class ResultadoAcumulacion(NamedTuple):
    contador: int
    consolidado: bool


def clasificar_impacto(valor: Any) -> ImpactoSocio:
    """Normaliza un puntaje final (número o medida especial) en un impacto tipado."""
    if valor is None or str(valor).strip() == "":
        raise ValueError("El impacto de la resolución no está definido.")
    texto = str(valor).strip().upper()
    if texto in _LLAMADO_ALIASES:
        return ImpactoSocio(TipoImpacto.LLAMADO_ATENCION, Decimal("0.00"))
    if texto in _FELICITACION_ALIASES:
        return ImpactoSocio(TipoImpacto.FELICITACION, Decimal("0.00"))
    try:
        puntos = Decimal(str(valor).strip()).quantize(_PRECISION)
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"Puntaje inválido: {valor!r}.") from exc
    if puntos in _LLAMADO_RANKS:
        return ImpactoSocio(TipoImpacto.LLAMADO_ATENCION, Decimal("0.00"))
    if puntos in _FELICITACION_RANKS:
        return ImpactoSocio(TipoImpacto.FELICITACION, Decimal("0.00"))
    if puntos == Decimal("0.00"):
        return ImpactoSocio(TipoImpacto.SIN_IMPACTO, Decimal("0.00"))
    return ImpactoSocio(TipoImpacto.PUNTOS, puntos)


def acumular_tres_a_uno(contador_actual: int) -> ResultadoAcumulacion:
    """Suma una medida al contador y consolida al llegar a tres (descuenta tres)."""
    if contador_actual < 0:
        raise ValueError("El contador de medidas no puede ser negativo.")
    nuevo = contador_actual + 1
    if nuevo >= CONSOLIDATION_THRESHOLD:
        return ResultadoAcumulacion(nuevo - CONSOLIDATION_THRESHOLD, True)
    return ResultadoAcumulacion(nuevo, False)


def planificar_asientos(impacto: ImpactoSocio, contador_actual: int) -> list[AsientoPlanificado]:
    """Traduce un impacto en los asientos a registrar.

    `contador_actual` es el contador de la medida que corresponde al impacto
    (llamados para un llamado de atención, felicitaciones para una felicitación).
    """
    if impacto.tipo == TipoImpacto.PUNTOS:
        return [
            AsientoPlanificado(
                TipoAsiento.PUNTOS_DIRECTOS, impacto.puntos.quantize(_PRECISION), None, True
            )
        ]
    if impacto.tipo == TipoImpacto.SIN_IMPACTO:
        return [AsientoPlanificado(TipoAsiento.SIN_IMPACTO, Decimal("0.00"), None, False)]

    es_llamado = impacto.tipo == TipoImpacto.LLAMADO_ATENCION
    contador, consolidado = acumular_tres_a_uno(contador_actual)
    plan = [
        AsientoPlanificado(
            TipoAsiento.LLAMADO_ATENCION if es_llamado else TipoAsiento.FELICITACION,
            Decimal("0.00"),
            contador,
            False,
        )
    ]
    if consolidado:
        plan.append(
            AsientoPlanificado(
                TipoAsiento.CONSOLIDACION_LLAMADOS
                if es_llamado
                else TipoAsiento.CONSOLIDACION_FELICITACIONES,
                Decimal("-1.00") if es_llamado else Decimal("1.00"),
                contador,
                True,
            )
        )
    return plan


def calcular_hash_asiento(
    hash_anterior: str,
    *,
    resolucion_id: int,
    expediente_id: int,
    socio_id: int,
    tipo: str,
    puntos: Decimal,
    contador_resultante: int | None,
    created_at_iso: str,
) -> str:
    """SHA-256 del asiento encadenado al hash del asiento anterior del mismo socio."""
    payload = "|".join(
        (
            hash_anterior,
            str(resolucion_id),
            str(expediente_id),
            str(socio_id),
            str(tipo),
            str(Decimal(puntos).quantize(_PRECISION)),
            "" if contador_resultante is None else str(contador_resultante),
            created_at_iso,
        )
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
