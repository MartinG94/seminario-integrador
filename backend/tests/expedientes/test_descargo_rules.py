"""Reglas de dominio del descargo (SCRUM-49 / S3-05): límite de texto del T03."""

from expedientes.domain.descargo_rules import (
    MAX_DESCARGO_TEXT_LENGTH,
    descargo_text_too_long_message,
)


def test_limite_de_texto_del_descargo_es_5000_como_el_t01() -> None:
    assert MAX_DESCARGO_TEXT_LENGTH == 5000


def test_mensaje_de_texto_excedido_informa_el_limite_vigente() -> None:
    assert descargo_text_too_long_message() == (
        "El motivo o justificación no puede superar los 5000 caracteres."
    )
