"""Factoría de inyección de dependencias para el repositorio de padrón institucional.

Permite alternar de forma desacoplada y determinista entre la implementación
real contra base de datos (DatabasePadronAdapter) y el simulador en memoria
(MockPadronAdapter) para entornos de test y CI/CD (RNF-PADRON-03).

Referencia: ADR-001 §4, plan.md §3.1, spec.md §RF-PADRON-01.
"""

import os

from padron.adapters import DatabasePadronAdapter, MockPadronAdapter
from padron.ports import PadronRepositoryInterface


def get_padron_repository() -> PadronRepositoryInterface:
    """Factoría de resolución de dependencias del repositorio de padrón.

    Evalúa la variable de entorno PADRON_ADAPTER ('database' | 'mock').
    Por defecto retorna DatabasePadronAdapter.
    """
    adapter_type = os.getenv("PADRON_ADAPTER", "database").lower()
    if adapter_type == "mock":
        return MockPadronAdapter()
    return DatabasePadronAdapter()
