"""Permisos de seguridad y autorización RBAC para el módulo de expedientes.

Implementa:
- CA4: Enlace seguro con autenticación forzada y autorización por objeto (IsImputadoOrTribunal).
- Reexportación de IsTribunalOrDirectiva para acciones exclusivas de gestión del TD.
- CanCreateT01: Autoridades procesales habilitadas para crear y tramitar T01.
- CanOpenExpedientes y CanTransitionExpedientes: Roles para apertura y
  transiciones manuales (PR #43).
- IsNotInvolvedInExpediente: inhibición de las partes interesadas (S4-04).
"""

from rest_framework.permissions import BasePermission

from accounts import audit
from accounts.permissions import HasAnyRole, IsTribunalOrDirectiva
from expedientes.models import Expediente
from expedientes.services.tribunal_composition_service import INVOLVED_MESSAGE, is_involved
from socios.models import Role

__all__ = [
    "CanAdjustT01",
    "CanCreateT01",
    "CanManageAppealDeadline",
    "CanManageCalendar",
    "CanManageEventos",
    "CanManageReglamentos",
    "CanOpenExpedientes",
    "CanResolveCausal",
    "CanTransitionExpedientes",
    "CanValueT03",
    "CanViewReportes",
    "IsComisionDirectivaOrAdmin",
    "IsImputadoOrTribunal",
    "IsNotInvolvedInExpediente",
    "IsTribunalOrDirectiva",
]


class CanManageReglamentos(HasAnyRole):
    """Autoridades habilitadas para gestionar artículos de reglamentos (exclusivo TD y CD)."""

    allowed_roles = (Role.TD, Role.CD)


class CanViewReportes(HasAnyRole):
    """Autoridades y órganos de control habilitados para consultar reportes
    (TD, CD, Revisores, Admin).
    """

    allowed_roles = (Role.TD, Role.CD, Role.REVISORES, Role.ADMIN, Role.FISCALIZADORA)


class IsComisionDirectivaOrAdmin(HasAnyRole):
    """Acceso restringido a CD y Administradores para programar reuniones y cargar asistencia."""

    allowed_roles = (Role.CD, Role.ADMIN)


class CanManageEventos(HasAnyRole):
    """Autoridades facultadas para gestionar eventos (exclusivo CD, TD, Autoridad SC)."""

    allowed_roles = (Role.CD, Role.TD, Role.AUTORIDAD_SC)


class CanManageCalendar(HasAnyRole):
    """Autoridades y administradores autorizados a configurar calendario y feriados (CA5)."""

    allowed_roles = (Role.ADMIN, Role.CD, Role.TD)


class CanOpenExpedientes(HasAnyRole):
    """Autoridades habilitadas para abrir expedientes: TD, CD, Revisores y Autoridades SC (Notas del PO)."""

    allowed_roles = (Role.TD, Role.CD, Role.AUTORIDAD_SC, Role.REVISORES, Role.FISCALIZADORA)


class CanTransitionExpedientes(HasAnyRole):
    """Sólo el Tribunal puede hacer transiciones manuales."""

    allowed_roles = (Role.TD,)


class CanResolveCausal(HasAnyRole):
    """Sólo los miembros del Tribunal resuelven causales T02 (S4-02)."""

    allowed_roles = (Role.TD,)


class CanValueT03(HasAnyRole):
    """Sólo los Miembros Titulares o Suplentes del Tribunal valoran descargos T03 (S4-03)."""

    allowed_roles = (Role.TD,)


class IsNotInvolvedInExpediente(BasePermission):
    """Inhibe a las partes interesadas del expediente `pk` (Art. 95 Estatuto, Art. 24 RPD).

    - Métodos de lectura (SAFE_METHODS): Se permite acceso de solo lectura al visor para
      garantizar la publicidad procesal.
    - Operaciones mutativas (POST, PUT, PATCH, DELETE): Imputados, solicitantes y
      miembros apartados no evalúan justificativos, no transicionan la causa ni
      redactan, firman o emiten la resolución: responde 403 Forbidden.
    """

    message = INVOLVED_MESSAGE

    def _get_expediente(self, view):
        expediente_id = view.kwargs.get("pk") or view.kwargs.get("expediente_id")
        if expediente_id:
            return Expediente.objects.filter(pk=expediente_id).first()
        return None

    def has_permission(self, request, view) -> bool:
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return True
        expediente = self._get_expediente(view)
        if expediente is not None and is_involved(expediente, request.user):
            return False
        return True

    def has_object_permission(self, request, view, obj) -> bool:
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return True
        expediente = obj if isinstance(obj, Expediente) else getattr(obj, "expediente", None)
        if expediente is not None and is_involved(expediente, request.user):
            return False
        return True


class CanAdjustT01(HasAnyRole):
    """Sólo el Tribunal debate y adecúa el T01 (PB-02)."""

    allowed_roles = (Role.TD,)


class CanManageAppealDeadline(HasAnyRole):
    """TD y Administración parametrizan el plazo de apelación del T01 (PB-02)."""

    allowed_roles = (Role.TD, Role.ADMIN)


class CanCreateT01(HasAnyRole):
    """Autoridades procesales habilitadas para crear y tramitar T01."""

    allowed_roles = (Role.AUTORIDAD_SC, Role.REVISORES, Role.CD, Role.TD, Role.FISCALIZADORA)


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
