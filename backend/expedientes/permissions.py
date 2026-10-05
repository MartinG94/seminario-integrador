from accounts.permissions import HasAnyRole
from socios.models import Role


class CanCreateT01(HasAnyRole):
    """Autoridades procesales habilitadas para crear y tramitar T01."""

    allowed_roles = (Role.FISCALIZADORA, Role.CD, Role.TD)
