"""
Autorización RBAC del lado del servidor (CA3).

Ocultar botones o rutas en la SPA es sólo una mejora de experiencia de usuario:
la decisión vinculante se toma acá, en cada request, sin confiar en el cliente.
"""

from rest_framework.permissions import BasePermission

from accounts import audit
from socios.models import Role


def role_of(user) -> str:
    """Rol RBAC efectivo del usuario, leído del padrón (nunca del token)."""
    socio = getattr(user, "socio", None)
    return socio.role if socio else ""


class HasAnyRole(BasePermission):
    """Autoriza si el rol del socio está entre `allowed_roles`.

    El rol se relee de la base en cada petición en lugar de confiar en el claim
    del JWT: así, una baja o un cambio de rol surte efecto de inmediato y no
    recién cuando expira el token emitido.
    """

    allowed_roles: tuple[str, ...] = ()
    message = "No posee autorización para acceder a este recurso."

    def has_permission(self, request, view) -> bool:
        user = request.user
        socio = getattr(user, "socio", None)
        role = socio.role if socio else ""
        identifier = getattr(user, "username", "-")
        resource = request.path

        granted = bool(socio and socio.is_enabled and role in self.allowed_roles)
        if granted:
            audit.log_access_granted(identifier=identifier, role=role, resource=resource)
        else:
            audit.log_access_denied(identifier=identifier, role=role, resource=resource)
        return granted


class IsTribunalOrDirectiva(HasAnyRole):
    """RF-05-WS: nómina completa del padrón y funciones de gestión."""

    allowed_roles = (Role.TD, Role.CD, Role.ADMIN)


class IsAdminComputos(HasAnyRole):
    """ACT-05: administración de cuentas y roles RBAC."""

    allowed_roles = (Role.ADMIN,)
