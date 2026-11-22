"""Dominio puro del libro mayor de puntos (Spec 011, S5-02.1).

Sin dependencias de Django: clasifica el impacto individual de una resolución (las medidas
especiales nunca son puntos fraccionarios, Notas del PO 07/10/2026, sección 6) y calcula el
hash SHA-256 encadenado de cada asiento.
"""

import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from enum import StrEnum
from typing import Any

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
    REVERSION = "REVERSION"


@dataclass(frozen=True)
class ImpactoSocio:
    tipo: TipoImpacto
    puntos: Decimal


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


_TIPO_POR_IMPACTO = {
    TipoImpacto.PUNTOS: TipoAsiento.PUNTOS_DIRECTOS,
    TipoImpacto.SIN_IMPACTO: TipoAsiento.SIN_IMPACTO,
    TipoImpacto.LLAMADO_ATENCION: TipoAsiento.LLAMADO_ATENCION,
    TipoImpacto.FELICITACION: TipoAsiento.FELICITACION,
}


def tipo_asiento_para(impacto: ImpactoSocio) -> TipoAsiento:
    """Tipo de asiento que registra un impacto individual.

    La consolidación 3:1 no se decide aquí: la aplica el motor único de acumulación
    (`WarningAccumulationService`), que es quien mueve los contadores y acredita el punto.
    """
    return _TIPO_POR_IMPACTO[impacto.tipo]


def impacta_libro_mayor(impacto: ImpactoSocio) -> bool:
    """Sólo los puntos directos mueven el saldo; las medidas especiales nunca son puntos."""
    return impacto.tipo == TipoImpacto.PUNTOS and impacto.puntos != Decimal("0.00")


def normalizar_fecha(momento: datetime) -> str:
    """Fecha en UTC con microsegundos: igual al escribir y al releer de MySQL DATETIME(6)."""
    if momento.tzinfo is None:
        momento = momento.replace(tzinfo=timezone.utc)
    return momento.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def calcular_hash_asiento(
    hash_anterior: str,
    *,
    resolucion_id: int,
    expediente_id: int,
    socio_id: int,
    tipo: str,
    puntos: Decimal,
    contador_resultante: int | None,
    nro_socio: int | None,
    puntaje_aplicado_id: int | None,
    autor_id: int | None,
    created_at: datetime,
) -> str:
    """SHA-256 del asiento encadenado al hash del asiento anterior del mismo socio.

    Incluye todos los campos que identifican el movimiento: si cualquiera se altera, la
    cadena deja de verificar.
    """

    def opcional(valor: int | None) -> str:
        return "" if valor is None else str(valor)

    payload = "|".join(
        (
            hash_anterior,
            str(resolucion_id),
            str(expediente_id),
            str(socio_id),
            opcional(nro_socio),
            str(tipo),
            str(Decimal(puntos).quantize(_PRECISION)),
            opcional(contador_resultante),
            opcional(puntaje_aplicado_id),
            opcional(autor_id),
            normalizar_fecha(created_at),
        )
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
