"""Servicio de dominio puro para las reglas canónicas del padrón institucional.

Contiene la lógica de negocio estatutaria que traduce el esquema legado al modelo
canónico 2026 de SGD-AVEIT, independiente del framework web y de la base de datos.

Funciones puras y testeables de forma aislada — sin dependencias de Django ORM.

Referencia normativa:
  - ADR-001, Sección 4.1 (reglas CA1–CA5).
  - Aclaración corregida del PO, SCRUM-77, RN77-01–04.
  - Constitución del Proyecto, Principio 8.
"""

from datetime import date
from typing import Optional

from padron.domain import (
    CATEGORY_FILTER_ALIASES,
    JUNIOR_SOCIAL_YEARS,
    SENIOR_SOCIAL_YEARS,
    MembershipStatusEnum,
    SocioCategoryEnum,
    SubcomisionDTO,
)

# Constante del centinela de subcomisión en el esquema legado.
_SENTINEL_SUBCOMISION_CODE = 99


def classify_category(ano_social: object, *, is_ex_traveler: bool = False) -> SocioCategoryEnum:
    """Prioriza condición confirmada; un año desconocido no acredita exviajero."""
    if is_ex_traveler is True:
        return SocioCategoryEnum.EX_TRAVELER
    if isinstance(ano_social, bool) or not isinstance(ano_social, int):
        return SocioCategoryEnum.UNKNOWN
    if ano_social in JUNIOR_SOCIAL_YEARS:
        return SocioCategoryEnum.JUNIOR
    if ano_social in SENIOR_SOCIAL_YEARS:
        return SocioCategoryEnum.SENIOR
    return SocioCategoryEnum.UNKNOWN


def normalize_category_filter(value: str) -> SocioCategoryEnum:
    """Normaliza sólo filtros de entrada; códigos desconocidos elevan ValueError."""
    canonical = value.strip().upper()
    if canonical in CATEGORY_FILTER_ALIASES:
        return CATEGORY_FILTER_ALIASES[canonical]
    return SocioCategoryEnum(canonical)


def normalize_legajo(nro_legajo: Optional[int]) -> Optional[str]:
    """Normaliza el legajo universitario a cadena de texto canónica (CA2).

    - Entero > 0 → str(nro_legajo).
    - None o 0 (centinela) → None. Prohibido inventar prefijos artificiales.
    """
    if nro_legajo is None or nro_legajo <= 0:
        return None
    return str(nro_legajo)


def normalize_dni(nro_doc: Optional[int]) -> Optional[str]:
    """Normaliza el documento de identidad a cadena de texto limpia (CA2/H15).

    - Entero > 0 → str(nro_doc).
    - None, 0 o negativo (centinela/anómalo) → None.
    """
    if nro_doc is None or nro_doc <= 0:
        return None
    return str(nro_doc)


def resolve_membership_status(
    cod_estado_socio: Optional[int],
    fecha_baja: Optional[date],
) -> tuple[MembershipStatusEnum, bool]:
    """Resuelve el estado de membresía y vigencia operativa (CA4/BLK-005).

    Aplica la matriz exhaustiva de 5 estados del catálogo institucional legado,
    con prevalencia de `fecha_baja` no nula como TERMINATED.

    Retorna (membership_status, is_active).
    """
    # Prevalencia de baja formal asentada en socio_lista.fechaBaja.
    if fecha_baja is not None:
        return MembershipStatusEnum.TERMINATED, False

    # Matriz de correspondencia codEstadoSocio → MembershipStatusEnum.
    if cod_estado_socio is None:
        # Fallback defensivo para registros huérfanos sin historial.
        return MembershipStatusEnum.ENABLED, True
    if cod_estado_socio == 1:
        return MembershipStatusEnum.ENABLED, True
    if cod_estado_socio in (2, 3, 4):
        return MembershipStatusEnum.SUSPENDED, False
    if cod_estado_socio == 5:
        return MembershipStatusEnum.TERMINATED, False
    # Cualquier código no documentado: tratamiento conservador como SUSPENDED.
    return MembershipStatusEnum.SUSPENDED, False


def resolve_email(emails: list[dict]) -> Optional[str]:
    """Extrae el email institucional prioritario desde registros satélite (BLK-004).

    Prioridad:
      1. Casilla con habilitado=True y comprobado=True.
      2. Primera casilla con habilitado=True.
      3. None si no existen emails habilitados.
    """
    # Primer paso: buscar habilitado + comprobado.
    for entry in emails:
        if entry.get("habilitado") and entry.get("comprobado"):
            return entry["email"]

    # Segundo paso: fallback a primera habilitada.
    for entry in emails:
        if entry.get("habilitado"):
            return entry["email"]

    return None


def resolve_subcomision(cod_subcomision: int, nombre: str) -> Optional[SubcomisionDTO]:
    """Intercepta el centinela de subcomisión y traduce a DTO canónico (H03).

    - codSubcomision == 99 ('Sin Subcomisión') → None.
    - Cualquier otro código válido → SubcomisionDTO.
    """
    if cod_subcomision == _SENTINEL_SUBCOMISION_CODE:
        return None
    return SubcomisionDTO(id=cod_subcomision, name=nombre)
