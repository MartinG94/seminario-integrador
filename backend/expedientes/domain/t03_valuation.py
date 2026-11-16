"""Reglas de dominio para la valoración extraordinaria del descargo T03 (S4-03).

Dominio puro sin dependencias de Django:
- Resultado binario: Aprobada o Desaprobada (RP 2026 Art. 12).
- Fundamento siempre obligatorio, cualquiera sea el resultado (CA1).
"""

import re
from enum import StrEnum

MIN_GROUNDS_LENGTH = 20
MAX_GROUNDS_LENGTH = 5000

_CASE_NUMBER_PATTERN = re.compile(r"^(?:EXP-)?(\d+)/(\d{4})$", re.IGNORECASE | re.ASCII)


class T03ValuationResult(StrEnum):
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


class TribunalCondition(StrEnum):
    """Condición del integrante del Tribunal al momento de valorar (S-7)."""

    TITULAR = "TITULAR"
    SUPLENTE = "SUPLENTE"
    NO_INFORMADA = "NO_INFORMADA"


# idTipoSocio del padrón legacy (socio_lista).
_POSITION_CONDITIONS = {10: TribunalCondition.TITULAR, 11: TribunalCondition.SUPLENTE}


class T03ValuationError(ValueError):
    """La valoración no cumple las reglas del dominio."""


def validate_valuation(result: str, grounds: str) -> T03ValuationResult:
    """Valida el resultado y el fundamento de una valoración T03."""
    if result not in tuple(T03ValuationResult):
        raise T03ValuationError("Indicá un resultado válido: Aprobada o Desaprobada.")
    length = len(grounds.strip()) if isinstance(grounds, str) else 0
    if not MIN_GROUNDS_LENGTH <= length <= MAX_GROUNDS_LENGTH:
        raise T03ValuationError(
            f"Indicá un fundamento de entre {MIN_GROUNDS_LENGTH} y {MAX_GROUNDS_LENGTH} caracteres."
        )
    return T03ValuationResult(result)


def normalize_case_number(text: str) -> str:
    """Lleva `7/2026`, `007/2026` o `EXP-0007/2026` al formato guardado `EXP-0007/2026`."""
    match = _CASE_NUMBER_PATTERN.match(text.strip()) if isinstance(text, str) else None
    if match is None:
        raise T03ValuationError("Ingresá un número de expediente con el formato N/AAAA.")
    return f"EXP-{int(match.group(1)):04d}/{match.group(2)}"


def validate_antecedent_ids(antecedent_ids: list[int], expediente_id: int) -> list[int]:
    """Admite cero o más antecedentes, sin repetidos ni el expediente que se valora."""
    if expediente_id in antecedent_ids:
        raise T03ValuationError("No podés citar como antecedente el mismo expediente que valorás.")
    if len(set(antecedent_ids)) != len(antecedent_ids):
        raise T03ValuationError("Hay un antecedente repetido.")
    return list(antecedent_ids)


def condition_for_position(position: int | None) -> TribunalCondition:
    """Mapea `idTipoSocio` a la condición: 10 Titular, 11 Suplente, otro No informada."""
    return _POSITION_CONDITIONS.get(position, TribunalCondition.NO_INFORMADA)
