from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.permissions import BasePermission, IsAuthenticated

from accounts.permissions import IsTribunalOrDirectiva
from accounts.serializers import SocioProfileSerializer
from socios.filters import AccentInsensitiveSearchFilter
from socios.models import Role, Socio
from socios.pagination import SocioPagination
from socios.serializers import SocioLegajoSerializer


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

    def has_object_permission(self, request, view, obj: Socio) -> bool:
        requester_socio = getattr(request.user, "socio", None)
        if requester_socio is None or not requester_socio.is_enabled:
            return False

        # Autoridades con acceso irrestricto
        if requester_socio.role in (Role.TD, Role.CD, Role.ADMIN):
            return True

        # Socio ordinario o de otro rol consultando exclusivamente su propio legajo
        return requester_socio.pk == obj.pk


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
    Devuelve los datos canónicos del legajo provenientes directamente de Socio.legajo.
    """

    permission_classes = [IsAuthenticated, CanViewSocioLegajo]
    serializer_class = SocioLegajoSerializer
    queryset = Socio.objects.select_related("subcomision").all()
