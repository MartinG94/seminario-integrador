"""Vistas DRF para la Capa Anticorrupción del padrón institucional.

Endpoints:
  - PadronHealthCheckView: /api/v1/padron/health/ (CA5, AllowAny)
  - PadronSocioListView: /api/v1/padron/socios/ (CA1, CA3, CA4, IsAuthenticated)
  - PadronSocioDetailView: /api/v1/padron/socios/<int:socio_id>/ (CA2, IsAuthenticated)
  - PadronSocioLegajoDetailView: /api/v1/padron/socios/legajo/<str:legajo>/ (CA2, IsAuthenticated)
  - PadronSubcomisionListView: /api/v1/padron/subcomisiones/ (CA1, IsAuthenticated)

Referencia: plan.md §5, spec.md §RF-PADRON-01.
"""

from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from padron.domain import MembershipStatusEnum, SocioCategoryEnum
from padron.factory import get_padron_repository
from padron.serializers import (
    HealthStatusSerializer,
    PaginatedSociosSerializer,
    SocioFilterParamsSerializer,
    SocioInstitucionalSerializer,
    SubcomisionSerializer,
)


class PadronHealthCheckView(APIView):
    """Endpoint de observabilidad y health check de la conexión al padrón (CA5, H04, MED-003)."""

    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request, *args, **kwargs):
        """Monitorea el estado operativo y latencia de la fuente de datos."""
        repo = get_padron_repository()
        health_dto = repo.check_health()
        serializer = HealthStatusSerializer(health_dto)

        # HEALTHY y DEGRADED responden 200 OK; UNAVAILABLE responde 503
        http_status = (
            status.HTTP_200_OK
            if health_dto.status in ("HEALTHY", "DEGRADED")
            else status.HTTP_503_SERVICE_UNAVAILABLE
        )
        response = Response(serializer.data, status=http_status)
        response["Cache-Control"] = "no-cache, no-store, must-revalidate"
        return response


class PadronSocioListView(APIView):
    """Endpoint de listado paginado y búsqueda de socios (CA1, CA3, CA4, HIGH-004, MED-001)."""

    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        """Valida query params con SocioFilterParamsSerializer y consulta repositorio."""
        filter_serializer = SocioFilterParamsSerializer(data=request.query_params)
        if not filter_serializer.is_valid():
            return Response(filter_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        params = filter_serializer.validated_data
        search = params.get("search")
        subcomision_id = params.get("subcomision_id")
        category = SocioCategoryEnum(params["category"]) if "category" in params else None
        is_active = params.get("is_active")
        membership_status = (
            MembershipStatusEnum(params["membership_status"])
            if "membership_status" in params
            else None
        )
        page = params.get("page", 1)
        page_size = params.get("page_size", 20)

        repo = get_padron_repository()
        paginated_socios = repo.list_socios(
            search=search,
            subcomision_id=subcomision_id,
            category=category,
            is_active=is_active,
            membership_status=membership_status,
            page=page,
            page_size=page_size,
        )
        serializer = PaginatedSociosSerializer(paginated_socios)
        return Response(serializer.data, status=status.HTTP_200_OK)


class PadronSocioDetailView(APIView):
    """Endpoint de detalle unívoco de socio por nroSocio (CA2, H05)."""

    permission_classes = [IsAuthenticated]

    def get(self, request, socio_id: int, *args, **kwargs):
        """Resuelve el socio por su identificador primario institucional."""
        repo = get_padron_repository()
        socio = repo.get_by_id(socio_id)
        if socio is None:
            return Response(
                {"detail": "Socio no encontrado."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = SocioInstitucionalSerializer(socio)
        return Response(serializer.data, status=status.HTTP_200_OK)


class PadronSocioLegajoDetailView(APIView):
    """Endpoint de detalle unívoco de socio por número de legajo UTN (CA2, H05)."""

    permission_classes = [IsAuthenticated]

    def get(self, request, legajo: str, *args, **kwargs):
        """Resuelve el socio por su legajo universitario."""
        repo = get_padron_repository()
        socio = repo.get_by_legajo(legajo)
        if socio is None:
            return Response(
                {"detail": "Socio con el legajo indicado no encontrado."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = SocioInstitucionalSerializer(socio)
        return Response(serializer.data, status=status.HTTP_200_OK)


class PadronSubcomisionListView(APIView):
    """Endpoint de catálogo de subcomisiones oficiales (CA1, H03, MED-IT2-001)."""

    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        """Retorna la nómina alfabética de subcomisiones activas excluyendo centinela 99."""
        repo = get_padron_repository()
        subcomisiones = repo.list_subcomisiones()
        serializer = SubcomisionSerializer(subcomisiones, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
