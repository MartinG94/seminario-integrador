"""Lectura común del saldo aplicado; no modifica puntos ni su caché legado."""

import os
from decimal import Decimal

from django.db.models import Sum

from padron.ports import PadronRepositoryInterface
from ranking.models import PuntajeAplicado
from socios.identity import AmbiguousSocioIdentity, resolve_owned_institutional_candidate
from socios.models import Socio


def has_institutional_points_source() -> bool:
    """El padrón mock no acredita una fuente de puntos institucionales reales."""
    return os.getenv("PADRON_ADAPTER", "database").lower() != "mock"


def read_applied_points_balance(institutional_number: int) -> Decimal:
    """Suma los asientos individuales con el mismo criterio del ranking."""
    total = PuntajeAplicado.objects.filter(socio_id=institutional_number).aggregate(
        total=Sum("puntajeAplicado")
    )["total"]
    return total if total is not None else Decimal("0.00")


def read_local_points_balance(
    local: Socio, repository: PadronRepositoryInterface
) -> Decimal | None:
    """None significa propiedad institucional sin acreditar; las fallas se propagan."""
    try:
        identity = resolve_owned_institutional_candidate(local, repository)
    except AmbiguousSocioIdentity:
        return None
    return read_applied_points_balance(identity.socio_id) if identity is not None else None
