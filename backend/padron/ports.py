"""Puerto de dominio (interfaz) para acceso de sólo lectura al padrón institucional.

Define el contrato `PadronRepositoryInterface` como Protocol (Python 3.12),
siguiendo el patrón Hexagonal de Puertos y Adaptadores.

Referencia: ADR-001 §4, plan.md §3.
"""

from typing import Optional, Protocol

from padron.domain import (
    HealthStatusDTO,
    MembershipStatusEnum,
    PaginatedSociosDTO,
    SocioCategoryEnum,
    SocioInstitucionalDTO,
    SubcomisionDTO,
)


class PadronRepositoryInterface(Protocol):
    """Puerto de acceso de sólo lectura al padrón institucional.

    Contrato que debe ser implementado por cada adaptador concreto:
    - DatabasePadronAdapter (producción / local Docker).
    - MockPadronAdapter (tests Pytest / CI Pipeline).
    """

    def get_by_id(self, socio_id: int) -> Optional[SocioInstitucionalDTO]:
        """Obtiene un socio por su identificador primario institucional (nroSocio).

        Utilizado para resolver claves foráneas internas (Expedientes, Ranking)
        y como único método para socios que no poseen legajo universitario.
        """
        ...

    def get_by_legajo(self, legajo: str) -> Optional[SocioInstitucionalDTO]:
        """Obtiene un socio por su número de legajo universitario UTN.

        Utilizado para consultas funcionales directas.
        """
        ...

    def list_socios(
        self,
        search: Optional[str] = None,
        subcomision_id: Optional[int] = None,
        category: Optional[SocioCategoryEnum] = None,
        is_active: Optional[bool] = None,
        membership_status: Optional[MembershipStatusEnum] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedSociosDTO:
        """Retorna la lista de socios paginada con filtros aplicados (HIGH-004).

        Ejecuta COUNT(*) y paginación nativa SQL (LIMIT/OFFSET) en BD.
        """
        ...

    def list_subcomisiones(self) -> list[SubcomisionDTO]:
        """Retorna todas las subcomisiones oficiales activas, excluyendo centinela 99."""
        ...

    def check_health(self) -> HealthStatusDTO:
        """Verifica el estado de conexión y latencia con la fuente de datos."""
        ...
