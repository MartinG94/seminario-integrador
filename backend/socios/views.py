import logging
from typing import Any, Optional

from django.db.models import Sum
from django.http import Http404
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.permissions import BasePermission, IsAuthenticated

from accounts.permissions import IsTribunalOrDirectiva
from accounts.serializers import SocioProfileSerializer
from padron.domain import SocioCategoryEnum, SocioInstitucionalDTO
from padron.factory import get_padron_repository
from socios.filters import AccentInsensitiveSearchFilter
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
    ) -> None:
        self.id = dto.socio_id
        self.pk = dto.socio_id
        self.legajo = dto.legajo or str(dto.socio_id)
        self.first_name = dto.first_name
        self.last_name = dto.last_name
        self.email = dto.email or f"{self.legajo}@aveit.test"
        self.role = role
        self.category = dto.category.value if hasattr(dto.category, "value") else str(dto.category)
        self.social_year = dto.social_year
        self.is_enabled = dto.is_active
        self.points_balance = points_balance
        sub_name = dto.subcomision.name if dto.subcomision else None
        self.subcomision = InstitutionalSubcomision(sub_name) if sub_name else None

    def get_category_display(self) -> str:
        return "Activo" if self.category == SocioCategoryEnum.ACTIVE.value else "Pasivo"


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

        obj_legajo = getattr(obj, "legajo", None)
        return bool(obj_legajo and str(requester_socio.legajo) == str(obj_legajo))


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

        # 1. Intentar resolver primero en el modelo local Socio
        socio: Optional[Socio] = None
        if pk_str.isdigit():
            socio = Socio.objects.select_related("subcomision").filter(pk=int(pk_str)).first()
        if not socio and pk_str:
            socio = Socio.objects.select_related("subcomision").filter(legajo=pk_str).first()

        if socio is not None:
            self.check_object_permissions(self.request, socio)
            return socio

        # 2. Si no se encuentra en el modelo local, consultar la Capa Anticorrupción del padrón
        padron_dto: Optional[SocioInstitucionalDTO] = None
        try:
            repo = get_padron_repository()
            if pk_str.isdigit():
                padron_dto = repo.get_by_id(int(pk_str))
            if not padron_dto and pk_str:
                padron_dto = repo.get_by_legajo(pk_str)
        except Exception as exc:
            logger.error(
                "Error al consultar el padrón institucional para identificador %s: %s",
                pk_str,
                exc,
            )
            padron_dto = None

        if padron_dto is not None:
            local_socio: Optional[Socio] = None
            if padron_dto.legajo:
                local_socio = Socio.objects.filter(legajo=padron_dto.legajo).first()
            if not local_socio and padron_dto.email:
                local_socio = Socio.objects.filter(email__iexact=padron_dto.email).first()

            role = local_socio.role if local_socio else Role.SOCIO
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
                padron_dto, role=role, points_balance=points_balance
            )
            self.check_object_permissions(self.request, adapted_socio)
            return adapted_socio

        raise Http404("Socio no encontrado en el padrón.")
