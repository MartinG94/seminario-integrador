"""Permisos de servidor para los flujos de expedientes."""

from accounts.permissions import HasAnyRole
from socios.models import Role


class CanOpenExpedientes(HasAnyRole):
    """Autoridades habilitadas para abrir expedientes: TD, CD y autoridades (Notas del PO)."""

    allowed_roles = (Role.TD, Role.CD, Role.FISCALIZADORA)


class CanTransitionExpedientes(HasAnyRole):
    """Sólo el Tribunal puede hacer transiciones manuales."""

    allowed_roles = (Role.TD,)


class CanCreateT01(HasAnyRole):
    """Autoridades procesales habilitadas para crear y tramitar T01."""

    allowed_roles = (Role.FISCALIZADORA, Role.CD, Role.TD)
