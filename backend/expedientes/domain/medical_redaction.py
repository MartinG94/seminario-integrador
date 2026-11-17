"""Detección y censura de datos de salud en textos publicables (Spec 011, RF-17).

Dominio puro: sin Django. La censura trabaja por oración para no dejar fragmentos
que permitan inferir el dato reservado.
"""

import re
import unicodedata

TEXTO_RESERVADO = "[Dato de salud reservado]"

# Raíces sin tildes; el texto se normaliza antes de comparar.
PALABRAS_SALUD: tuple[str, ...] = (
    "medic",
    "salud",
    "enfermedad",
    "enfermo",
    "diagnostic",
    "reposo",
    "tratamiento",
    "clinic",
    "hospital",
    "internacion",
    "cirugia",
    "patologia",
    "sintoma",
    "psicolog",
    "psiquiatr",
    "discapacidad",
)

_FIN_DE_ORACION = re.compile(r"(?<=[.!?;])\s+")


def _normalizar(texto: str) -> str:
    sin_tildes = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in sin_tildes if not unicodedata.combining(c)).lower()


def contiene_datos_salud(texto: str | None) -> bool:
    """True si el texto menciona información de salud protegida."""
    normalizado = _normalizar(texto or "")
    return any(palabra in normalizado for palabra in PALABRAS_SALUD)


def _censurar_linea(linea: str) -> str:
    oraciones = _FIN_DE_ORACION.split(linea)
    resultado: list[str] = []
    for oracion in oraciones:
        reemplazo = TEXTO_RESERVADO if contiene_datos_salud(oracion) else oracion
        if reemplazo == TEXTO_RESERVADO and resultado and resultado[-1] == TEXTO_RESERVADO:
            continue
        resultado.append(reemplazo)
    return " ".join(resultado)


def censurar_datos_salud(texto: str | None) -> str:
    """Reemplaza cada oración con datos de salud por `TEXTO_RESERVADO`, línea por línea."""
    if not texto:
        return ""
    return "\n".join(_censurar_linea(linea) for linea in texto.split("\n"))
