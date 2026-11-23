"""Detección y censura de datos de salud en textos publicables (Spec 011, RF-17).

Dominio puro: sin Django. La censura trabaja por oración para no dejar fragmentos
que permitan inferir el dato reservado.
"""

import re
import unicodedata

TEXTO_RESERVADO = "[Dato de salud reservado]"

# Patrones sobre texto normalizado (minúsculas y sin tildes). Cada uno exige comienzo de
# palabra y define su terminación, para no censurar "saludo", "saludable" o "medición".
PATRONES_SALUD: tuple[str, ...] = (
    r"medic(?:o|a|os|as|amento|amentos|acion|aciones|ado|ada|ados|adas|ina|inal|inales)\b",
    r"salud\b",
    r"enferm(?:o|a|os|as|edad|edades|eria|ero|era)\b",
    r"diagnostic(?:o|a|os|as|ado|ada)\b",
    r"reposo\b",
    r"tratamiento(?:s)?\b",
    r"clinic(?:o|a|os|as)\b",
    r"hospital(?:es|izacion|izado|izada)?\b",
    r"internacion(?:es)?\b",
    r"internad(?:o|a|os|as)\b",
    r"cirugia(?:s)?\b",
    r"quirurgic(?:o|a|os|as)\b",
    r"operacion(?:es)?\s+(?:quirurgica|de\s+urgencia)",
    r"operad(?:o|a)\s+de\b",
    r"patologi(?:a|as|co|ca)\b",
    r"sintoma(?:s|tico|tica)?\b",
    r"psicolog(?:o|a|os|as|ico|ica|icos|icas|ia)\b",
    r"psiquiatr(?:a|as|ico|ica|ia)\b",
    r"discapacidad(?:es)?\b",
    r"lesion(?:es|ado|ada)?\b",
    r"fractura(?:s|do|da)?\b",
    r"fiebre(?:s)?\b",
    r"embaraz(?:o|os|ada|adas)\b",
    r"parto(?:s)?\b",
    r"accidente(?:s)?\b",
    r"terapi(?:a|as|euta|eutico|eutica)\b",
    r"licencia\s+(?:medica|por\s+enfermedad)",
    r"certificado\s+medico",
    r"covid(?:-?19)?\b",
    r"gripe\b",
    r"infeccion(?:es)?\b",
    r"guardia\s+medica",
)
_PATRON = re.compile(r"\b(?:" + "|".join(PATRONES_SALUD) + ")")

# Abreviaturas frecuentes que terminan en punto pero no cierran la oración.
_ABREVIATURAS = (
    "dr",
    "dra",
    "sr",
    "sra",
    "srta",
    "art",
    "arts",
    "inc",
    "nro",
    "n",
    "lic",
    "ing",
    "prof",
)
_MARCA = "\u0000"
_PATRON_ABREVIATURA = re.compile(
    r"\b(" + "|".join(_ABREVIATURAS) + r")\.(?=\s)", flags=re.IGNORECASE
)
_FIN_DE_ORACION = re.compile(r"(?<=[.!?;])\s+")


def _normalizar(texto: str) -> str:
    sin_tildes = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in sin_tildes if not unicodedata.combining(c)).lower()


def contiene_datos_salud(texto: str | None) -> bool:
    """True si el texto menciona información de salud protegida."""
    return bool(_PATRON.search(_normalizar(texto or "")))


def _dividir_oraciones(linea: str) -> list[str]:
    protegida = _PATRON_ABREVIATURA.sub(lambda m: m.group(1) + _MARCA, linea)
    return [parte.replace(_MARCA, ".") for parte in _FIN_DE_ORACION.split(protegida)]


def _censurar_linea(linea: str) -> str:
    resultado: list[str] = []
    for oracion in _dividir_oraciones(linea):
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
