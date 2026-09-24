"""Adaptadores concretos del puerto PadronRepositoryInterface.

Implementaciones:
  - MockPadronAdapter:    Fixtures deterministas en memoria para tests y CI.
  - DatabasePadronAdapter: Consulta real a la BD institucional MySQL (managed=False).

Referencia: ADR-001 §4, plan.md §3.1, spec.md §RNF-PADRON-03.
"""

import logging
import time
from datetime import datetime, timezone
from typing import Optional

from django.db import DatabaseError, OperationalError
from django.db.models import Exists, OuterRef, Prefetch, Q, QuerySet, Subquery

from padron.domain import (
    ACTIVE_SOCIAL_YEARS,
    PASSIVE_SOCIAL_YEARS,
    HealthStatusDTO,
    MembershipStatusEnum,
    PaginatedSociosDTO,
    SocioCategoryEnum,
    SocioInstitucionalDTO,
    SubcomisionDTO,
)
from padron.models import Socio, SocioEstudio, Subcomision
from padron.services import (
    classify_category,
    normalize_dni,
    normalize_legajo,
    resolve_email,
    resolve_membership_status,
    resolve_subcomision,
)

logger = logging.getLogger("padron.adapter")


# ==============================================================================
# Fixtures deterministas para el adaptador Mock
# ==============================================================================

_MOCK_SUBCOMISIONES: list[SubcomisionDTO] = [
    SubcomisionDTO(id=9, name="Comisión Directiva"),
    SubcomisionDTO(id=1, name="Cómputos"),
    SubcomisionDTO(id=7, name="Eventos"),
    SubcomisionDTO(id=11, name="Ex Viajeros"),
    SubcomisionDTO(id=6, name="Gestión Social y Ambiental"),
    SubcomisionDTO(id=5, name="Mantenimiento"),
    SubcomisionDTO(id=4, name="Prensa"),
    SubcomisionDTO(id=2, name="Recursos Humanos"),
    SubcomisionDTO(id=3, name="Relaciones Institucionales"),
    SubcomisionDTO(id=8, name="Rifas"),
    SubcomisionDTO(id=10, name="Tribunal de Disciplina"),
]

_MOCK_SOCIOS: list[SocioInstitucionalDTO] = [
    SocioInstitucionalDTO(
        socio_id=1001,
        legajo="85421",
        dni="41234567",
        first_name="Esteban",
        last_name="Pérez",
        email="esteban.perez@aveit.utn.edu.ar",
        subcomision=SubcomisionDTO(id=10, name="Tribunal de Disciplina"),
        social_year=4,
        category=SocioCategoryEnum.ACTIVE,
        is_active=True,
        membership_status=MembershipStatusEnum.ENABLED,
    ),
    SocioInstitucionalDTO(
        socio_id=1002,
        legajo="89123",
        dni="42345678",
        first_name="Lucía",
        last_name="Gómez",
        email="lucia.gomez@aveit.utn.edu.ar",
        subcomision=SubcomisionDTO(id=1, name="Cómputos"),
        social_year=3,
        category=SocioCategoryEnum.PASSIVE,
        is_active=True,
        membership_status=MembershipStatusEnum.ENABLED,
    ),
    SocioInstitucionalDTO(
        socio_id=1003,
        legajo="90455",
        dni="43456789",
        first_name="Martín",
        last_name="Rossi",
        email="martin.rossi@aveit.utn.edu.ar",
        subcomision=SubcomisionDTO(id=1, name="Cómputos"),
        social_year=2,
        category=SocioCategoryEnum.PASSIVE,
        is_active=True,
        membership_status=MembershipStatusEnum.ENABLED,
    ),
]


# ==============================================================================
# MockPadronAdapter — Adaptador de prueba en memoria
# ==============================================================================


class MockPadronAdapter:
    """Adaptador mock en memoria para tests y CI/CD (RNF-PADRON-03).

    Utiliza fixtures deterministas basados en los datos semilla del esquema legado.
    Soporta simulación de fallas de conectividad para tests de observabilidad (CA5).
    """

    def __init__(self, simulate_failure: bool = False) -> None:
        self._simulate_failure = simulate_failure
        self._socios = list(_MOCK_SOCIOS)
        self._subcomisiones = list(_MOCK_SUBCOMISIONES)

    def _raise_if_failure(self) -> None:
        """Simula OperationalError si está configurado para fallar."""
        if self._simulate_failure:
            raise OperationalError("Simulated database connection failure")

    def get_by_id(self, socio_id: int) -> Optional[SocioInstitucionalDTO]:
        """Busca un socio por ID institucional en los fixtures."""
        self._raise_if_failure()
        for socio in self._socios:
            if socio.socio_id == socio_id:
                return socio
        return None

    def get_by_legajo(self, legajo: str) -> Optional[SocioInstitucionalDTO]:
        """Busca un socio por legajo en los fixtures."""
        self._raise_if_failure()
        for socio in self._socios:
            if socio.legajo == legajo:
                return socio
        return None

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
        """Retorna lista paginada con filtros aplicados sobre los fixtures."""
        self._raise_if_failure()

        filtered = list(self._socios)

        if search:
            term = search.lower()
            filtered = [
                s
                for s in filtered
                if term in s.last_name.lower()
                or term in s.first_name.lower()
                or (s.legajo and term in s.legajo.lower())
                or (s.dni and term in s.dni.lower())
            ]

        if subcomision_id is not None:
            filtered = [s for s in filtered if s.subcomision and s.subcomision.id == subcomision_id]

        if category is not None:
            filtered = [s for s in filtered if s.category == category]

        if is_active is not None:
            filtered = [s for s in filtered if s.is_active == is_active]

        if membership_status is not None:
            filtered = [s for s in filtered if s.membership_status == membership_status]

        total_count = len(filtered)
        offset = (page - 1) * page_size
        paged = filtered[offset : offset + page_size]

        return PaginatedSociosDTO(
            count=total_count,
            results=paged,
            page=page,
            page_size=page_size,
        )

    def list_subcomisiones(self) -> list[SubcomisionDTO]:
        """Retorna subcomisiones ordenadas alfabéticamente, sin centinela 99."""
        self._raise_if_failure()
        return sorted(self._subcomisiones, key=lambda s: s.name)

    def check_health(self) -> HealthStatusDTO:
        """Verifica el estado del adaptador mock (CA5)."""
        checked_at = datetime.now(timezone.utc).isoformat()

        if self._simulate_failure:
            return HealthStatusDTO(
                status="UNAVAILABLE",
                latency_ms=0.0,
                source="mock_isolated",
                record_count=0,
                last_checked_at=checked_at,
                message="Simulación de falla de conexión activada.",
            )

        start = time.monotonic()
        record_count = len(self._socios)
        latency_ms = (time.monotonic() - start) * 1000

        return HealthStatusDTO(
            status="HEALTHY",
            latency_ms=round(latency_ms, 2),
            source="mock_isolated",
            record_count=record_count,
            last_checked_at=checked_at,
            message="Adaptador mock operando con fixtures en memoria.",
        )


# ==============================================================================
# DatabasePadronAdapter — Adaptador real de sólo lectura (T4)
# ==============================================================================


class DatabasePadronAdapter:
    """Adaptador de sólo lectura contra la BD institucional MySQL (RNF-PADRON-03).

    Consulta modelos unmanaged sin duplicación de datos, aplicando optimizaciones O(1):
    - Prefetch ordenado por `-compositeKey` para desambiguación determinista de estudios.
    - Subquery indexada de último estado sobre `SocioEstadoHistorial`.
    - Búsqueda textual mediante `Exists` para legajo (sin JOINs cartesianos).
    - Paginación nativa SQL (LIMIT/OFFSET).
    """

    def _get_base_queryset(self) -> QuerySet[Socio]:
        """Construye el QuerySet base anotado y con relaciones prefetcheadas."""
        from padron.models import SocioEstadoHistorial

        latest_estado = SocioEstadoHistorial.objects.filter(socio=OuterRef("pk")).order_by(
            "-fechaHora"
        )

        return (
            Socio.objects.annotate(
                latest_cod_estado=Subquery(latest_estado.values("codEstadoSocio")[:1])
            )
            .select_related("subcomision")
            .prefetch_related(
                Prefetch(
                    "estudios",
                    queryset=SocioEstudio.objects.order_by("-compositeKey"),
                ),
                "emails",
            )
        )

    def _map_to_dto(self, socio: Socio) -> SocioInstitucionalDTO:
        """Mapea una entidad ORM prefetcheada a SocioInstitucionalDTO."""
        # 1. Desambiguación determinista de estudio / legajo (H02 / HIGH-001)
        estudios = list(socio.estudios.all())
        nro_legajo = estudios[0].nroLegajo if estudios else None
        legajo = normalize_legajo(nro_legajo)

        # 2. Documento
        dni = normalize_dni(socio.nroDoc)

        # 3. Subcomisión institucional (excluye centinela 99)
        subcomision = None
        if socio.subcomision is not None:
            subcomision = resolve_subcomision(
                socio.subcomision.codSubcomision, socio.subcomision.nombre
            )

        # 4. Email institucional prioritario
        emails_payload = [
            {
                "email": e.email,
                "habilitado": bool(e.habilitado),
                "comprobado": bool(e.comprobado),
            }
            for e in socio.emails.all()
        ]
        email = resolve_email(emails_payload)

        # 5. Categoría estatutaria derivada de año social (CA3)
        category = classify_category(socio.anoSocial)

        # 6. Membresía y vigencia operativa desde historial y fecha de baja (CA4 / BLK-005)
        latest_cod = getattr(socio, "latest_cod_estado", None)
        membership_status, is_active = resolve_membership_status(
            cod_estado_socio=latest_cod,
            fecha_baja=socio.fechaBaja,
        )

        return SocioInstitucionalDTO(
            socio_id=socio.nroSocio,
            legajo=legajo,
            dni=dni,
            first_name=socio.nombre,
            last_name=socio.apellido,
            email=email,
            subcomision=subcomision,
            social_year=socio.anoSocial,
            category=category,
            is_active=is_active,
            membership_status=membership_status,
        )

    def get_by_id(self, socio_id: int) -> Optional[SocioInstitucionalDTO]:
        """Obtiene un socio por su identificador primario institucional (nroSocio)."""
        try:
            socio = self._get_base_queryset().get(pk=socio_id)
            return self._map_to_dto(socio)
        except Socio.DoesNotExist:
            return None

    def get_by_legajo(self, legajo: str) -> Optional[SocioInstitucionalDTO]:
        """Obtiene un socio por su número de legajo universitario UTN."""
        if not legajo or not legajo.strip():
            return None

        try:
            legajo_int = int(legajo.strip())
            if legajo_int <= 0:
                return None
        except (ValueError, TypeError):
            return None

        legajo_match = SocioEstudio.objects.filter(
            socio=OuterRef("pk"),
            nroLegajo=legajo_int,
        )
        socio = self._get_base_queryset().filter(Exists(legajo_match)).first()
        if socio is None:
            return None
        return self._map_to_dto(socio)

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
        """Retorna la lista de socios paginada con filtros nativos SQL."""
        queryset = self._get_base_queryset()

        if search:
            search_term = search.strip()
            legajo_matches = SocioEstudio.objects.filter(
                socio=OuterRef("pk"),
                nroLegajo__icontains=search_term,
            )
            search_filter = (
                Q(apellido__icontains=search_term)
                | Q(nombre__icontains=search_term)
                | Q(nroDoc__icontains=search_term)
                | Exists(legajo_matches)
            )
            queryset = queryset.filter(search_filter)

        if subcomision_id is not None:
            queryset = queryset.filter(subcomision_id=subcomision_id)

        if category is not None:
            if category == SocioCategoryEnum.PASSIVE:
                queryset = queryset.filter(anoSocial__in=PASSIVE_SOCIAL_YEARS)
            elif category == SocioCategoryEnum.ACTIVE:
                queryset = queryset.filter(anoSocial__in=ACTIVE_SOCIAL_YEARS)
            elif category == SocioCategoryEnum.UNKNOWN:
                queryset = queryset.exclude(
                    anoSocial__in=PASSIVE_SOCIAL_YEARS + ACTIVE_SOCIAL_YEARS
                )

        if is_active is not None:
            if is_active:
                queryset = queryset.filter(fechaBaja__isnull=True).filter(
                    Q(latest_cod_estado=1) | Q(latest_cod_estado__isnull=True)
                )
            else:
                queryset = queryset.filter(
                    Q(fechaBaja__isnull=False) | Q(latest_cod_estado__in=[2, 3, 4, 5])
                )

        if membership_status is not None:
            if membership_status == MembershipStatusEnum.ENABLED:
                queryset = queryset.filter(fechaBaja__isnull=True).filter(
                    Q(latest_cod_estado=1) | Q(latest_cod_estado__isnull=True)
                )
            elif membership_status == MembershipStatusEnum.SUSPENDED:
                queryset = queryset.filter(fechaBaja__isnull=True, latest_cod_estado__in=[2, 3, 4])
            elif membership_status == MembershipStatusEnum.TERMINATED:
                queryset = queryset.filter(Q(fechaBaja__isnull=False) | Q(latest_cod_estado=5))

        # Ordenamiento determinista predeterminado
        queryset = queryset.order_by("apellido", "nombre", "nroSocio")

        total_count = queryset.count()
        offset = max(0, (page - 1) * page_size)
        paged_items = [self._map_to_dto(s) for s in queryset[offset : offset + page_size]]

        return PaginatedSociosDTO(
            count=total_count,
            results=paged_items,
            page=page,
            page_size=page_size,
        )

    def list_subcomisiones(self) -> list[SubcomisionDTO]:
        """Retorna subcomisiones oficiales activas en orden alfabético."""
        subcomisiones = (
            Subcomision.objects.exclude(codSubcomision=99)
            .exclude(nombre__iexact="Sin Subcomisión")
            .order_by("nombre")
        )
        return [SubcomisionDTO(id=s.codSubcomision, name=s.nombre) for s in subcomisiones]

    def check_health(self) -> HealthStatusDTO:
        """Verifica el estado de salud y latencia contra la BD institucional (CA5)."""
        checked_at = datetime.now(timezone.utc).isoformat()
        start = time.monotonic()
        try:
            record_count = Socio.objects.count()
            latency_ms = (time.monotonic() - start) * 1000
            latency_ms_rounded = round(latency_ms, 2)

            if latency_ms > 3000:
                status = "UNAVAILABLE"
                msg = "Latencia de conexión a BD supera el umbral crítico (3000ms)."
            elif latency_ms >= 500 or record_count == 0:
                status = "DEGRADED"
                msg = "Conexión a BD institucional degradada (latencia elevada o conteo 0)."
            else:
                status = "HEALTHY"
                msg = "Conexión a base de datos institucional operativa."

            return HealthStatusDTO(
                status=status,
                latency_ms=latency_ms_rounded,
                source="mysql_institutional",
                record_count=record_count,
                last_checked_at=checked_at,
                message=msg,
            )
        except (DatabaseError, TimeoutError, OSError) as exc:
            latency_ms = (time.monotonic() - start) * 1000
            logger.error("Health check error against institutional DB: %s", exc)
            return HealthStatusDTO(
                status="UNAVAILABLE",
                latency_ms=round(latency_ms, 2),
                source="mysql_institutional",
                record_count=0,
                last_checked_at=checked_at,
                message=f"Error de conexión a la base institucional: {str(exc)}",
            )
        except Exception as exc:
            latency_ms = (time.monotonic() - start) * 1000
            logger.critical(
                "Unexpected failure during institutional DB health check: %s",
                exc,
                exc_info=True,
            )
            return HealthStatusDTO(
                status="UNAVAILABLE",
                latency_ms=round(latency_ms, 2),
                source="mysql_institutional",
                record_count=0,
                last_checked_at=checked_at,
                message=f"Error inesperado en verificación de salud: {str(exc)}",
            )
