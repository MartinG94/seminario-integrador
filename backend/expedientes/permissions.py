"""Permisos de seguridad y autorización RBAC para el módulo de expedientes.

Implementa:
- CA4: Enlace seguro con autenticación forzada y autorización por objeto (IsImputadoOrTribunal).
- Reexportación de IsTribunalOrDirectiva para acciones exclusivas de gestión del TD.
- CanCreateT01: Autoridades procesales habilitadas para crear y tramitar T01.
"""

from rest_framework.permissions import BasePermission

from accounts import audit
from accounts.permissions import HasAnyRole, IsTribunalOrDirectiva
from socios.models import Role

__all__ = ["CanCreateT01", "IsImputadoOrTribunal", "IsTribunalOrDirectiva"]


class CanCreateT01(HasAnyRole):
    """Autoridades procesales habilitadas para crear y tramitar T01."""

    allowed_roles = (Role.FISCALIZADORA, Role.CD, Role.TD)


class IsImputadoOrTribunal(BasePermission):
    """Control de acceso por objeto para consulta de causas disciplinarias (CA4).

    Reglas:
    - 401 si el usuario es anónimo o no autenticado (has_permission = False).
    - 200/True si el usuario integra roles de gestión (TD, CD, ADMIN) o es staff activo.
    - 200/True si el usuario es el socio imputado activo en la causa específica.
    - 403/False si el usuario es un socio ordinario ajeno a la causa o deshabilitado,
      registrando auditoría de seguridad ACCESS_DENIED.
    """

    message = "No posee autorización para consultar este expediente disciplinario."

    def has_permission(self, request, view) -> bool:
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj) -> bool:
        user = request.user
        if not user or not user.is_authenticated:
            return False

        socio = getattr(user, "socio", None)
        role = socio.role if socio else ""
        identifier = getattr(user, "username", "-")
        resource = getattr(request, "path", "-")

        # Autoridades de gestión siempre autorizadas (TD, CD, ADMIN) o staff activo
        if socio and socio.is_enabled and role in (Role.TD, Role.CD, Role.ADMIN) or user.is_staff:
            audit.log_access_granted(identifier=identifier, role=role, resource=resource)
            return True

        # Socio imputado: sólo si está habilitado y coincide socio_id del expediente
        if socio and socio.is_enabled and getattr(obj, "socio_id", None) == socio.id:
            audit.log_access_granted(identifier=identifier, role=role, resource=resource)
            return True

        # Acceso denegado a terceros o socios deshabilitados
        audit.log_access_denied(identifier=identifier, role=role, resource=resource)
        return False
