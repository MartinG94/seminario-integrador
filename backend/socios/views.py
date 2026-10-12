import logging
from typing import Any, Optional

from django.db.models import Sum
from django.http import Http404
from rest_framework.exceptions import ValidationError
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.permissions import BasePermission, IsAuthenticated

from accounts.permissions import IsTribunalOrDirectiva
from accounts.serializers import SocioProfileSerializer
from padron.domain import SocioCategoryEnum, SocioInstitucionalDTO
from padron.factory import get_padron_repository
from socios.filters import AccentInsensitiveSearchFilter
from socios.identity import (
    AmbiguousSocioIdentity,
    resolve_institutional_candidate,
    resolve_institutional_owner,
    resolve_local_candidate,
)
from socios.models import Role, Socio
from socios.pagination import SocioPagination
from socios.serializers import SocioLegajoSerializer

logger = logging.getLogger(__name__)


class InstitutionalSubcomision:
    """Representación mínima de subcomisión para emular la relación ORM en serializers."""

    def __init__(self, name: Optional[str]) -> None:
        self.name = name


class InstitutionalSocioAdapter:
    """Adapta un SocioInstitucionalDTO del Padrón Institucional
    al contrato esperado por SocioLegajoSerializer.
    """

    def __init__(
        self,
        dto: SocioInstitucionalDTO,
        role: str = Role.SOCIO,
        points_balance: float = 0.0,
        owner_local_id: int | None = None,
    ) -> None:
        self.id = dto.socio_id
        self.pk = dto.socio_id
        self.legajo = dto.legajo
        self.owner_local_id = owner_local_id
        self.first_name = dto.first_name
        self.last_name = dto.last_name
        self.email = dto.email or f"{dto.legajo or dto.socio_id}@aveit.test"
        self.role = role
        self.category = dto.category.value if hasattr(dto.category, "value") else str(dto.category)
        self.social_year = dto.social_year
        self.is_enabled = dto.is_active
        self.points_balance = points_balance
        sub_name = dto.subcomision.name if dto.subcomision else None
        self.subcomision = InstitutionalSubcomision(sub_name) if sub_name else None

    def get_category_display(self) -> str:
        return SocioCategoryEnum(self.category).label


class CanViewSocioLegajo(BasePermission):
    """
    Permiso RBAC para visualización de legajo de socio (CA4).
    - TD, CD y ADMIN: pueden consultar cualquier legajo.
    - SOCIO o cualquier rol con legajo activo: solo puede consultar su propio legajo.
    - Usuario anónimo: 401 Unauthorized (controlado por IsAuthenticated).
    - Acceso no autorizado: 403 Forbidden.
    """

    message = "No posee autorización para acceder a este legajo."

    def has_permission(self, request, view) -> bool:
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj: Any) -> bool:
        requester_socio = getattr(request.user, "socio", None)
        if requester_socio is None or not requester_socio.is_enabled:
            return False

        # Autoridades con acceso irrestricto
        if requester_socio.role in (Role.TD, Role.CD, Role.ADMIN):
            return True

        # Socio ordinario o de otro rol consultando exclusivamente su propio legajo
        if hasattr(obj, "pk") and hasattr(obj, "user"):
            return requester_socio.pk == obj.pk

        return getattr(obj, "owner_local_id", None) == requester_socio.pk


class PadronListView(ListAPIView):
    """GET /api/v1/socios/ — nómina del padrón con búsqueda y paginación.

    Restringida a TD, CD y ADMIN.
    Soporta búsqueda insensible a mayúsculas y acentos por:
    - first_name, last_name, legajo, subcomision__name.
    Paginada con count, next, previous, results (CA3).
    """

    permission_classes = [IsTribunalOrDirectiva]
    serializer_class = SocioProfileSerializer
    queryset = Socio.objects.select_related("subcomision").filter(is_enabled=True)
    pagination_class = SocioPagination
    filter_backends = [AccentInsensitiveSearchFilter]


class SocioLegajoDetailView(RetrieveAPIView):
    """GET /api/v1/socios/<pk>/legajo/ — detalle integral del legajo (T7 / CA2 / CA4).

    Valida que solo TD, CD, ADMIN o el socio propietario del legajo puedan acceder.
    Devuelve los datos canónicos del legajo provenientes directamente de Socio.legajo
    o de la Capa Anticorrupción del padrón institucional si el socio reside en el padrón maestro.
    """

    permission_classes = [IsAuthenticated, CanViewSocioLegajo]
    serializer_class = SocioLegajoSerializer
    queryset = Socio.objects.select_related("subcomision").all()

    def get_object(self) -> Any:
        pk = self.kwargs.get("pk")
        pk_str = str(pk).strip() if pk is not None else ""
        sources = self.request.query_params.getlist("identity_source")
        source = sources[0] if len(sources) == 1 else None
        if "identity_source" in self.request.query_params and (
            len(sources) != 1 or source not in ("local", "institutional")
        ):
            raise ValidationError({"identity_source": "Seleccione local o institutional."})
        local: Socio | None = None
        padron_dto: SocioInstitucionalDTO | None = None
        local_owner: Socio | None = None
        try:
            if source != "institutional":
                local = resolve_local_candidate(pk_str, allow_legajo=source is None)
            if source != "local":
                padron_dto = resolve_institutional_candidate(
                    get_padron_repository(), pk_str, allow_legajo=source is None
                )
                if padron_dto is not None:
                    local_owner = resolve_institutional_owner(padron_dto)
            if (
                local is not None
                and padron_dto is not None
                and (local_owner is None or local_owner.pk != local.pk)
            ):
                raise AmbiguousSocioIdentity
        except AmbiguousSocioIdentity:
            raise Http404("Socio no encontrado en el padrón.") from None
        except Exception:
            logger.error("No fue posible verificar la identidad solicitada en el padrón.")
            raise Http404("Socio no encontrado en el padrón.") from None
        if local is not None:
            self.check_object_permissions(self.request, local)
            return local
        if padron_dto is not None:
            role = local_owner.role if local_owner else Role.SOCIO
            points_balance = 0.0
            try:
                from ranking.models import PuntajeAplicado

                pa_sum = PuntajeAplicado.objects.filter(socio_id=padron_dto.socio_id).aggregate(
                    total=Sum("puntajeAplicado")
                )["total"]
                if pa_sum is not None:
                    points_balance = float(pa_sum)
            except Exception:
                points_balance = 0.0

            adapted_socio = InstitutionalSocioAdapter(
                padron_dto,
                role=role,
                points_balance=points_balance,
                owner_local_id=local_owner.pk if local_owner else None,
            )
            self.check_object_permissions(self.request, adapted_socio)
            return adapted_socio

        raise Http404("Socio no encontrado en el padrón.")
