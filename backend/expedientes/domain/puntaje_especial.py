from decimal import Decimal
from enum import StrEnum
from typing import Any


class PuntajeEspecial(StrEnum):
    NINGUNO = ""
    LLAMADO_ATENCION = "LLAMADO_ATENCION"
    FELICITACION = "FELICITACION"


RANK: dict[PuntajeEspecial, Decimal] = {
    PuntajeEspecial.LLAMADO_ATENCION: Decimal("-0.25"),
    PuntajeEspecial.FELICITACION: Decimal("0.25"),
}


def parse_puntaje_especial(valor: Any) -> PuntajeEspecial:
    """Normaliza un valor string o enum a PuntajeEspecial."""
    if not valor:
        return PuntajeEspecial.NINGUNO
    normalizado = str(valor).strip().upper()
    if normalizado in (
        "LLAMADO_ATENCION",
        "LLAMADO DE ATENCIÓN",
        "LLAMADO DE ATENCION",
        "APERCIBIMIENTO",
    ):
        return PuntajeEspecial.LLAMADO_ATENCION
    if normalizado in ("FELICITACION", "FELICITACIÓN", "RECONOCIMIENTO"):
        return PuntajeEspecial.FELICITACION
    try:
        dec = Decimal(normalizado)
        if dec == Decimal("-0.25"):
            return PuntajeEspecial.LLAMADO_ATENCION
        if dec == Decimal("0.25"):
            return PuntajeEspecial.FELICITACION
    except Exception:
        pass
    return PuntajeEspecial.NINGUNO


def puntaje_especial_to_rank(especial: PuntajeEspecial | str) -> Decimal | None:
    parsed = parse_puntaje_especial(especial)
    return RANK.get(parsed)
