"""Reglas de dominio puras del descargo reglamentario (SCRUM-49 / S3-05).

Sin acoplamiento a frameworks: concentra el límite de texto del Formulario T03 para que
serializer, vistas y pruebas compartan una única fuente de verdad.
"""

# Decisión del PO (16/10/2026): igual al límite del motivo del T01. Para extenderse, el
# socio dispone del adjunto de hasta 5 PDF de 5 MB.
MAX_DESCARGO_TEXT_LENGTH = 5000


def descargo_text_too_long_message() -> str:
    """Mensaje de error cuando el texto del descargo supera el límite vigente."""
    return f"El motivo o justificación no puede superar los {MAX_DESCARGO_TEXT_LENGTH} caracteres."
