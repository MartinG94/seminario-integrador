"""
Pista de auditoría de autenticación y autorización (CA4).

Emite eventos al logger `security` configurado en core.settings. Las funciones
de este módulo son el único punto por el que se registran estos eventos, de
modo que la regla "nunca registrar contraseñas, tokens completos, claves ni
secretos" se cumple en un solo lugar: sólo aceptan campos escalares ya
conocidos (identificador, rol, recurso, resultado) y nunca el cuerpo crudo de
la petición ni las credenciales.
"""

import logging
from typing import Final

logger = logging.getLogger("security")

AUTH_SUCCESS: Final = "AUTH_SUCCESS"
AUTH_FAILURE: Final = "AUTH_FAILURE"
ACCESS_GRANTED: Final = "ACCESS_GRANTED"
ACCESS_DENIED: Final = "ACCESS_DENIED"

# Un identificador de login demasiado largo suele ser un error de tipeo del
# usuario (por ejemplo, pegar la contraseña en el campo de usuario). Se recorta
# para no volcar contenido inesperado en la pista de auditoría.
MAX_IDENTIFIER_LENGTH: Final = 60


def _safe_identifier(identifier: object) -> str:
    if not identifier:
        return "-"
    text = str(identifier).strip()
    if len(text) > MAX_IDENTIFIER_LENGTH:
        return f"{text[:MAX_IDENTIFIER_LENGTH]}...(truncado)"
    return text


def log_authentication_success(*, identifier: str, role: str) -> None:
    logger.info(
        "event=%s user=%s role=%s result=GRANTED",
        AUTH_SUCCESS,
        _safe_identifier(identifier),
        role or "-",
    )


def log_authentication_failure(*, identifier: str, reason_code: str) -> None:
    """`reason_code` es un código interno para el auditor.

    Nunca se devuelve al cliente: la respuesta HTTP 401 es genérica (CA1).
    """
    logger.warning(
        "event=%s user=%s result=DENIED reason=%s",
        AUTH_FAILURE,
        _safe_identifier(identifier),
        reason_code,
    )


def log_access_granted(*, identifier: str, role: str, resource: str) -> None:
    logger.info(
        "event=%s user=%s role=%s resource=%s result=GRANTED",
        ACCESS_GRANTED,
        _safe_identifier(identifier),
        role or "-",
        resource,
    )


def log_access_denied(*, identifier: str, role: str, resource: str) -> None:
    logger.warning(
        "event=%s user=%s role=%s resource=%s result=DENIED",
        ACCESS_DENIED,
        _safe_identifier(identifier),
        role or "-",
        resource,
    )
