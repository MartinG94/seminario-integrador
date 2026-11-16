"""Catálogo y validación de los parámetros del sistema (Spec 010).

Dominio puro: no depende de Django ni de la base. El catálogo define qué se puede
configurar, con qué tipo y entre qué límites; la persistencia sólo guarda los cambios.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from enum import Enum
from typing import Any, Final


class ParameterType(str, Enum):
    INTEGER = "INTEGER"
    DECIMAL = "DECIMAL"
    BOOLEAN = "BOOLEAN"
    EMAIL = "EMAIL"


class ParameterCategory(str, Enum):
    PLAZOS = "PLAZOS"
    UMBRALES = "UMBRALES"
    CORREOS = "CORREOS"
    ADJUNTOS = "ADJUNTOS"


class ParameterValidationError(ValueError):
    """El valor propuesto no respeta el tipo o los límites del parámetro."""


class UnknownParameterError(KeyError):
    """La clave no pertenece al catálogo."""


@dataclass(frozen=True)
class ParameterDefinition:
    clave: str
    categoria: str
    etiqueta: str
    descripcion: str
    tipo: ParameterType
    default: Any
    minimo: Decimal | None = None
    maximo: Decimal | None = None
    unidad: str = ""
    editable: bool = True


PLAZO_DESCARGO: Final = "plazo_descargo_dias_habiles"
PLAZO_APELACION: Final = "plazo_apelacion_dias_habiles"
UMBRAL_CRITICO: Final = "umbral_critico"
UMBRAL_PREVENTIVO: Final = "umbral_preventivo"
UMBRAL_PREVENTIVO_ACTIVO: Final = "umbral_preventivo_activo"
EMAIL_COMISION_DIRECTIVA: Final = "email_comision_directiva"
EMAIL_TRIBUNAL: Final = "email_tribunal_disciplina"
ADJUNTOS_TAMANO_MB: Final = "adjuntos_tamano_maximo_mb"
ADJUNTOS_CANTIDAD: Final = "adjuntos_cantidad_maxima"

MAX_EMAIL_LENGTH: Final = 150
MAX_DECIMAL_PLACES: Final = 2
_EMAIL_PATTERN: Final = re.compile(r"^[^@\s]+@[^@\s.]+(\.[^@\s.]+)+$")

CATALOG: Final[tuple[ParameterDefinition, ...]] = (
    ParameterDefinition(
        clave=PLAZO_DESCARGO,
        categoria=ParameterCategory.PLAZOS.value,
        etiqueta="Plazo de descargo",
        descripcion="Días hábiles para presentar el descargo desde la apertura del plazo.",
        tipo=ParameterType.INTEGER,
        default=5,
        minimo=Decimal(1),
        maximo=Decimal(30),
        unidad="días hábiles",
    ),
    ParameterDefinition(
        clave=PLAZO_APELACION,
        categoria=ParameterCategory.PLAZOS.value,
        etiqueta="Plazo de apelación del T01",
        descripcion="Días hábiles para apelar una solicitud T01.",
        tipo=ParameterType.INTEGER,
        default=5,
        minimo=Decimal(1),
        maximo=Decimal(30),
        unidad="días hábiles",
    ),
    ParameterDefinition(
        clave=UMBRAL_CRITICO,
        categoria=ParameterCategory.UMBRALES.value,
        etiqueta="Umbral crítico",
        descripcion="Saldo que dispara la alerta crítica. Fijado por el Art. 93 del R.I.",
        tipo=ParameterType.DECIMAL,
        default=Decimal("-10.0"),
        unidad="puntos",
        editable=False,
    ),
    ParameterDefinition(
        clave=UMBRAL_PREVENTIVO,
        categoria=ParameterCategory.UMBRALES.value,
        etiqueta="Umbral preventivo",
        descripcion="Saldo que dispara la alerta preventiva cuando está activa.",
        tipo=ParameterType.DECIMAL,
        default=Decimal("-7.0"),
        minimo=Decimal("-9.99"),
        maximo=Decimal("-0.01"),
        unidad="puntos",
    ),
    ParameterDefinition(
        clave=UMBRAL_PREVENTIVO_ACTIVO,
        categoria=ParameterCategory.UMBRALES.value,
        etiqueta="Alerta preventiva activa",
        descripcion="Si está activa, se registra una alerta al cruzar el umbral preventivo.",
        tipo=ParameterType.BOOLEAN,
        default=False,
    ),
    ParameterDefinition(
        clave=EMAIL_COMISION_DIRECTIVA,
        categoria=ParameterCategory.CORREOS.value,
        etiqueta="Comisión Directiva",
        descripcion="Casilla que recibe los avisos dirigidos a la Comisión Directiva.",
        tipo=ParameterType.EMAIL,
        default=None,
    ),
    ParameterDefinition(
        clave=EMAIL_TRIBUNAL,
        categoria=ParameterCategory.CORREOS.value,
        etiqueta="Tribunal de Disciplina",
        descripcion="Casilla que recibe los avisos dirigidos al Tribunal de Disciplina.",
        tipo=ParameterType.EMAIL,
        default=None,
    ),
    ParameterDefinition(
        clave=ADJUNTOS_TAMANO_MB,
        categoria=ParameterCategory.ADJUNTOS.value,
        etiqueta="Tamaño máximo por archivo",
        descripcion="Tamaño máximo de cada comprobante adjunto a un descargo.",
        tipo=ParameterType.INTEGER,
        default=5,
        minimo=Decimal(1),
        maximo=Decimal(20),
        unidad="MB",
    ),
    ParameterDefinition(
        clave=ADJUNTOS_CANTIDAD,
        categoria=ParameterCategory.ADJUNTOS.value,
        etiqueta="Cantidad máxima de comprobantes",
        descripcion="Cantidad máxima de comprobantes vigentes por descargo.",
        tipo=ParameterType.INTEGER,
        default=5,
        minimo=Decimal(1),
        maximo=Decimal(10),
        unidad="comprobantes",
    ),
)

_BY_KEY: Final[dict[str, ParameterDefinition]] = {d.clave: d for d in CATALOG}


def get_definition(clave: str) -> ParameterDefinition:
    try:
        return _BY_KEY[clave]
    except KeyError as exc:
        raise UnknownParameterError(clave) from exc


def _format_number(value: Decimal) -> str:
    """Número en notación local: coma decimal y sin ceros sobrantes."""
    text = format(value.normalize(), "f")
    return text.replace(".", ",")


def _range_message(definition: ParameterDefinition) -> str:
    unidad = f" {definition.unidad}" if definition.unidad else ""
    return (
        f"{definition.etiqueta} debe estar entre {_format_number(definition.minimo)} y "
        f"{_format_number(definition.maximo)}{unidad}."
    )


def _check_range(definition: ParameterDefinition, value: Decimal) -> None:
    if definition.minimo is not None and value < definition.minimo:
        raise ParameterValidationError(_range_message(definition))
    if definition.maximo is not None and value > definition.maximo:
        raise ParameterValidationError(_range_message(definition))


def _to_decimal(definition: ParameterDefinition, raw: Any, message: str) -> Decimal:
    if isinstance(raw, bool) or raw is None or (isinstance(raw, str) and not raw.strip()):
        raise ParameterValidationError(message)
    try:
        value = Decimal(str(raw).strip().replace(",", "."))
    except (InvalidOperation, ValueError) as exc:
        raise ParameterValidationError(message) from exc
    if not value.is_finite():
        raise ParameterValidationError(message)
    return value


def _normalize_integer(definition: ParameterDefinition, raw: Any) -> int:
    message = f"{definition.etiqueta} debe ser un número entero."
    value = _to_decimal(definition, raw, message)
    if value != value.to_integral_value():
        raise ParameterValidationError(message)
    _check_range(definition, value)
    return int(value)


def _normalize_decimal(definition: ParameterDefinition, raw: Any) -> str:
    message = f"{definition.etiqueta} debe ser un número."
    value = _to_decimal(definition, raw, message)
    if -value.as_tuple().exponent > MAX_DECIMAL_PLACES:
        raise ParameterValidationError(
            f"{definition.etiqueta} admite hasta {MAX_DECIMAL_PLACES} decimales."
        )
    _check_range(definition, value)
    return format(value, "f")


def _normalize_boolean(definition: ParameterDefinition, raw: Any) -> bool:
    if not isinstance(raw, bool):
        raise ParameterValidationError(f"{definition.etiqueta} debe indicarse como sí o no.")
    return raw


def _normalize_email(definition: ParameterDefinition, raw: Any) -> str:
    message = f"{definition.etiqueta}: ingresá un correo electrónico válido."
    if not isinstance(raw, str):
        raise ParameterValidationError(message)
    value = raw.strip().lower()
    if not value or len(value) > MAX_EMAIL_LENGTH or not _EMAIL_PATTERN.match(value):
        raise ParameterValidationError(message)
    return value


def normalize_value(definition: ParameterDefinition, raw: Any) -> Any:
    """Valida `raw` y devuelve el valor a persistir (serializable a JSON).

    Los decimales se guardan como texto para no perder precisión.
    """
    if not definition.editable:
        raise ParameterValidationError(
            f"{definition.etiqueta} es un valor reglamentario y no puede modificarse."
        )
    if definition.tipo == ParameterType.INTEGER:
        return _normalize_integer(definition, raw)
    if definition.tipo == ParameterType.DECIMAL:
        return _normalize_decimal(definition, raw)
    if definition.tipo == ParameterType.BOOLEAN:
        return _normalize_boolean(definition, raw)
    return _normalize_email(definition, raw)


def to_python(definition: ParameterDefinition, stored: Any) -> Any:
    """Convierte el valor persistido al tipo de dominio (los decimales, a `Decimal`)."""
    if definition.tipo == ParameterType.DECIMAL and stored is not None:
        return Decimal(str(stored))
    return stored
