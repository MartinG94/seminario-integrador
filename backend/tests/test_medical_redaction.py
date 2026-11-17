"""Censura de datos de salud en publicaciones (Spec 011, T7). Dominio puro."""

import pytest

from expedientes.domain.medical_redaction import (
    TEXTO_RESERVADO,
    censurar_datos_salud,
    contiene_datos_salud,
)

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    "texto",
    [
        "Presentó certificado médico.",
        "Estuvo en REPOSO por indicación profesional",
        "Diagnóstico reservado",
        "Consulta psicológica",
    ],
)
def test_detecta_datos_de_salud_sin_importar_tildes_ni_mayusculas(texto):
    assert contiene_datos_salud(texto)


@pytest.mark.parametrize("texto", ["", None, "Inasistencia a la reunión plenaria.", "Medida"])
def test_no_detecta_textos_sin_datos_de_salud(texto):
    assert not contiene_datos_salud(texto)


def test_censura_solo_la_oracion_con_datos_de_salud():
    texto = "El socio faltó a la reunión. Presentó certificado médico por gripe. Se lo absuelve."
    assert censurar_datos_salud(texto) == (
        f"El socio faltó a la reunión. {TEXTO_RESERVADO} Se lo absuelve."
    )


def test_conserva_saltos_de_linea_y_agrupa_oraciones_consecutivas():
    texto = "VISTO:\nEl tratamiento indicado. El reposo de 48 horas.\nArt. 1: Absolver."
    assert censurar_datos_salud(texto) == f"VISTO:\n{TEXTO_RESERVADO}\nArt. 1: Absolver."


def test_texto_vacio():
    assert censurar_datos_salud(None) == ""
