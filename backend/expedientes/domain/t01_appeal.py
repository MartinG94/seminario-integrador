"""Reglas de dominio para apelar y adecuar un T01 (PB-02).

Dominio puro sin dependencias de Django (Reglamento Procesal 2026, arts. 12 y 14):
- Plazo de apelación parametrizado en días hábiles (por defecto 5, art. 12).
- Apelación con texto acotado.
- Adecuación de puntos e involucrados con motivos, y socios afectados que pueden
  recibir un nuevo período de apelación (derecho de defensa).
"""

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum

DEFAULT_APPEAL_BUSINESS_DAYS = 5
MIN_BUSINESS_DAYS = 1
MAX_BUSINESS_DAYS = 30
MIN_APPEAL_LENGTH = 20
MAX_APPEAL_LENGTH = 5000
MIN_GROUNDS_LENGTH = 20


class ActionType(StrEnum):
    SANCTION = "SANCTION"
    MERIT = "MERIT"


class AppealError(ValueError):
    """La operación no respeta las reglas de apelación o adecuación del T01."""


@dataclass(frozen=True)
class Adjustment:
    added: frozenset[int]
    removed: frozenset[int]
    points_changed: bool
    worsens: bool
    affected: frozenset[int]


def validate_business_days(days: int) -> None:
    if not MIN_BUSINESS_DAYS <= days <= MAX_BUSINESS_DAYS:
        raise AppealError(
            f"El plazo de apelación debe estar entre {MIN_BUSINESS_DAYS} y "
            f"{MAX_BUSINESS_DAYS} días hábiles."
        )


def validate_appeal_text(text: str) -> str:
    text = text.strip()
    if len(text) < MIN_APPEAL_LENGTH:
        raise AppealError(f"Escribí tu apelación con al menos {MIN_APPEAL_LENGTH} caracteres.")
    if len(text) > MAX_APPEAL_LENGTH:
        raise AppealError(f"La apelación no puede superar los {MAX_APPEAL_LENGTH} caracteres.")
    return text


def evaluate_adjustment(
    *,
    action: ActionType,
    old_points: Decimal,
    new_points: Decimal,
    old_ids: set[int],
    new_ids: set[int],
    grounds: str,
    reopen: bool,
) -> Adjustment:
    """Valida la adecuación del debate (OP 30) y calcula los socios afectados.

    Un socio queda afectado si se lo agrega a la causa o si los puntos empeoran para
    todos (sanción más severa o mérito menor).
    """
    if not new_ids:
        raise AppealError("Debe quedar al menos un involucrado en el expediente.")
    if action == ActionType.SANCTION and new_points >= 0:
        raise AppealError("Una sanción debe tener puntos negativos.")
    if action == ActionType.MERIT and new_points <= 0:
        raise AppealError("Un mérito debe tener puntos positivos.")
    points_changed = new_points != old_points
    if not points_changed and new_ids == old_ids:
        raise AppealError("La adecuación no modifica puntos ni involucrados.")
    if len(grounds.strip()) < MIN_GROUNDS_LENGTH:
        raise AppealError(
            f"Indicá los motivos de la adecuación con al menos {MIN_GROUNDS_LENGTH} caracteres."
        )

    added = frozenset(new_ids - old_ids)
    worsens = new_points < old_points
    affected = frozenset(new_ids) if worsens else added
    if reopen and not affected:
        raise AppealError(
            "No hay socios afectados por la adecuación: no corresponde abrir un nuevo período."
        )
    return Adjustment(
        added=added,
        removed=frozenset(old_ids - new_ids),
        points_changed=points_changed,
        worsens=worsens,
        affected=affected,
    )
