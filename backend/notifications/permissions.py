"""
Permisos de acceso para el subsistema de notificaciones y encolado de correos.
"""

from django.conf import settings
from rest_framework.permissions import BasePermission

from socios.models import Role


class HasInternalServiceKeyOrAdmin(BasePermission):
    """
    Autoriza peticiones autenticadas mediante una clave de servicio interna
    (X-Internal-Service-Key) para integraciones backend-to-backend o,
    en su defecto, a usuarios autenticados con rol administrativo o de gestión.
    """

    message = (
        "No posee credenciales de servicio válidas ni rol administrativo para despachar correos."
    )

    def has_permission(self, request, view) -> bool:
        # 1. Comprobación de API Key interna inter-servicios
        expected_key = getattr(settings, "INTERNAL_SERVICE_KEY", None)
        provided_key = request.headers.get("X-Internal-Service-Key") or request.META.get(
            "HTTP_X_INTERNAL_SERVICE_KEY"
        )

        if expected_key and provided_key and provided_key == expected_key:
            return True

        # 2. Comprobación alternativa de usuario con rol administrativo
        user = request.user
        if user and user.is_authenticated:
            if user.is_staff or user.is_superuser:
                return True
            socio = getattr(user, "socio", None)
            if socio and socio.is_enabled and socio.role in (Role.ADMIN, Role.TD, Role.CD):
                return True

        return False
