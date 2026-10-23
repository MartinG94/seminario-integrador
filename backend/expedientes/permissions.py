"""Permisos de seguridad y autorización RBAC para el módulo de expedientes.

Implementa:
- CA4: Enlace seguro con autenticación forzada y autorización por objeto (IsImputadoOrTribunal).
- Reexportación de IsTribunalOrDirectiva para acciones exclusivas de gestión del TD.
- CanCreateT01: Autoridades procesales habilitadas para crear y tramitar T01.
- CanOpenExpedientes y CanTransitionExpedientes: Roles para apertura y
  transiciones manuales (PR #43).
"""

from rest_framework.permissions import BasePermission

from accounts import audit
from accounts.permissions import HasAnyRole, IsTribunalOrDirectiva
from socios.models import Role

__all__ = [
    "CanConstituteTribunal",
    "CanCreateT01",
    "CanDesignateAdHoc",
    "CanManageCalendar",
    "CanManageEventos",
    "CanOpenExpedientes",
    "CanResolveCausal",
    "CanTransitionExpedientes",
    "IsComisionDirectivaOrAdmin",
    "IsImputadoOrTribunal",
    "IsTribunalOrDirectiva",
]


class IsComisionDirectivaOrAdmin(HasAnyRole):
    """Acceso restringido a CD y Administradores para programar reuniones y cargar asistencia."""

    allowed_roles = (Role.CD, Role.ADMIN)


class CanManageEventos(HasAnyRole):
    """Autoridades facultadas para gestionar eventos (CD, Tribunal, Fiscalizadora, Admin)."""

    allowed_roles = (Role.CD, Role.ADMIN, Role.TD, Role.FISCALIZADORA)


class CanManageCalendar(HasAnyRole):
    """Autoridades y administradores autorizados a configurar calendario y feriados (CA5)."""

    allowed_roles = (Role.ADMIN, Role.CD, Role.TD)


class CanOpenExpedientes(HasAnyRole):
    """Autoridades habilitadas para abrir expedientes: TD, CD y autoridades (Notas del PO)."""

    allowed_roles = (Role.TD, Role.CD, Role.FISCALIZADORA)


class CanTransitionExpedientes(HasAnyRole):
    """Sólo el Tribunal puede hacer transiciones manuales."""

    allowed_roles = (Role.TD,)


class CanResolveCausal(HasAnyRole):
    """Sólo los vocales del Tribunal resuelven causales T02 (S4-02)."""

    allowed_roles = (Role.TD,)


class CanConstituteTribunal(HasAnyRole):
    """Sólo el Tribunal constituye su cuerpo y declara apartamientos propios (S4-04)."""

    allowed_roles = (Role.TD,)


class CanDesignateAdHoc(HasAnyRole):
    """TD o CD registran la designación ad hoc resuelta por Asamblea (Art. 95, S4-04)."""

    allowed_roles = (Role.TD, Role.CD)


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

        # Socio imputado (titular o co-imputado): sólo si está habilitado
        if socio and socio.is_enabled:
            is_titular = getattr(obj, "socio_id", None) == socio.id
            is_coimputado = hasattr(obj, "socios") and obj.socios.filter(pk=socio.pk).exists()
            if is_titular or is_coimputado:
                audit.log_access_granted(identifier=identifier, role=role, resource=resource)
                return True

        # Acceso denegado a terceros o socios deshabilitados
        audit.log_access_denied(identifier=identifier, role=role, resource=resource)
        return False
