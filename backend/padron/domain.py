"""Entidades de dominio inmutables para la Capa Anticorrupción del padrón institucional.

Define los DTOs (Data Transfer Objects) y enumeraciones canónicas que constituyen
el vocabulario ubicuo del dominio societario de AVEIT 2026.

Referencia normativa:
  - Estatuto AVEIT 2026, Arts. 3 y 6 (categorías Pasivo / Activo).
  - Constitución del Proyecto, Principio 8 (terminología canónica).
  - ADR-001, Sección 4.1 (reglas de transformación CA1–CA5).
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class SocioCategoryEnum(str, Enum):
    """Categoría estatutaria según año social (Arts. 3 y 6 Estatuto 2026).

    - PASSIVE: 1.º a 3.º año social (alias histórico: Junior).
    - ACTIVE:  4.º a 6.º año social (alias histórico: Senior).
    - UNKNOWN: Año social no parametrizado, nulo o fuera del rango 1–6.
    """

    PASSIVE = "PASSIVE"
    ACTIVE = "ACTIVE"
    UNKNOWN = "UNKNOWN"


# Rangos estatutarios canónicos de año social (Arts. 3 y 6 Estatuto AVEIT 2026).
# Fuente Única de Verdad (SSOT) para la capa de dominio puro y consultas de infraestructura.
PASSIVE_SOCIAL_YEARS: tuple[int, ...] = (1, 2, 3)
ACTIVE_SOCIAL_YEARS: tuple[int, ...] = (4, 5, 6)


class MembershipStatusEnum(str, Enum):
    """Estado de vigencia societaria / cuenta (Principio 7: código en inglés).

    Derivado del registro más reciente en `socio_estadoHistorial`.
    - ENABLED:    Habilitado / cuota al día / plenos derechos (codEstadoSocio=1).
    - SUSPENDED:  En receso, licencia o suspensión temporal (codEstadoSocio=2,3,4).
    - TERMINATED: Baja societaria definitiva (codEstadoSocio=5 o fechaBaja no nula).
    """

    ENABLED = "ENABLED"
    SUSPENDED = "SUSPENDED"
    TERMINATED = "TERMINATED"


@dataclass(frozen=True)
class SubcomisionDTO:
    """Subcomisión institucional canónica (excluye centinela cod=99)."""

    id: int
    name: str


@dataclass(frozen=True)
class SocioInstitucionalDTO:
    """Representación canónica de un socio del padrón institucional AVEIT.

    Todos los campos siguen las reglas de transformación definidas en ADR-001 §4.1:
    - legajo: str(nroLegajo) si existe estudio; None si carece.
    - dni: str(nroDoc) si > 0; None si ausente o 0.
    - subcomision: None si codSubcomision == 99 (centinela).
    - category: derivada exclusivamente de anoSocial (CA3).
    - is_active / membership_status: derivados de socio_estadoHistorial (CA4).
    """

    socio_id: int
    legajo: Optional[str]
    dni: Optional[str]
    first_name: str
    last_name: str
    email: Optional[str]
    subcomision: Optional[SubcomisionDTO]
    social_year: int
    category: SocioCategoryEnum
    is_active: bool
    membership_status: MembershipStatusEnum


@dataclass(frozen=True)
class PaginatedSociosDTO:
    """Resultado paginado del listado de socios (HIGH-004 / LOW-IT2-001).

    Alineado a la convención canónica de DRF con count y results.
    """

    count: int
    results: list[SocioInstitucionalDTO]
    page: int
    page_size: int


@dataclass(frozen=True)
class HealthStatusDTO:
    """Estado de salud y observabilidad de la conexión al padrón (CA5 / H04).

    Expuesto por el endpoint /api/v1/padron/health/ con umbrales cuantitativos:
    - HEALTHY:     latencia < 500ms y record_count > 0  -> HTTP 200
    - DEGRADED:    500ms <= latencia <= 3000ms o count=0 -> HTTP 200
    - UNAVAILABLE: latencia > 3000ms o excepción BD     -> HTTP 503
    """

    status: str
    latency_ms: float
    source: str
    record_count: int
    last_checked_at: str
    message: str
