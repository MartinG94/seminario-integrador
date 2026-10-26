"""Contrato interno para consumir el dictamen cerrado de SCRUM-55."""
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Protocol


@dataclass(frozen=True)
class ClosedDecision:
    id: str
    expediente_id: int
    estado: str
    resultado: str
    puntos_finales: Decimal
    medidas: list[str]
    considerandos_base: str
    version: int
    closed_at: datetime


class ClosedDecisionProvider(Protocol):
    def get_closed_decision(self, expediente_id: int) -> ClosedDecision | None: ...
