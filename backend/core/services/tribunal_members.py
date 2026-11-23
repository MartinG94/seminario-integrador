"""Alta y baja del rol TD con auditoría inmutable (Spec 012, RF-10 a RF-13)."""

from __future__ import annotations

from typing import Any

from django.db import transaction
from django.db.models import QuerySet

from accounts import audit
from core.models import TribunalRoleAction, TribunalRoleChange
from socios.filters import AccentInsensitiveSearchFilter
from socios.models import Role, Socio


class TribunalMemberError(Exception):
    """El alta no puede realizarse; el mensaje está redactado para el usuario."""


class TribunalMemberNotFound(Exception):
    """El socio no integra el Tribunal de Disciplina."""


CANDIDATES_LIMIT = 20


class TribunalMemberService:
    @staticmethod
    def candidates(search: str) -> QuerySet[Socio]:
        """Socios Ordinarios habilitados que coinciden con `search`, filtrados en el servidor."""
        queryset = Socio.objects.filter(
            role=Role.SOCIO, is_enabled=True, user__is_active=True
        ).select_related("subcomision")
        terms = (search or "").strip().split()
        if not terms:
            return queryset.none()
        for term in terms:
            regex = AccentInsensitiveSearchFilter.term_query(term)
            queryset = queryset.filter(regex)
        return queryset.order_by("last_name", "first_name", "id")[:CANDIDATES_LIMIT]

    @staticmethod
    def members() -> QuerySet[Socio]:
        return (
            Socio.objects.filter(role=Role.TD)
            .select_related("subcomision")
            .order_by("-social_year", "last_name", "first_name")
        )

    @staticmethod
    def _record(socio: Socio, *, accion: str, previous: str, actor: Any) -> None:
        TribunalRoleChange.objects.create(
            socio=socio, action=accion, previous_role=previous, new_role=socio.role, author=actor
        )
        audit.log_role_change(
            identifier=actor.get_username(),
            target=str(socio.numero_socio or socio.legajo),
            previous_role=previous,
            new_role=socio.role,
        )

    @classmethod
    @transaction.atomic
    def assign(cls, *, socio_id: int, actor: Any) -> Socio:
        socio = Socio.objects.select_for_update().select_related("user").filter(pk=socio_id).first()
        if socio is None:
            raise TribunalMemberError("El socio seleccionado no existe en el padrón.")
        if not socio.is_enabled or not socio.user.is_active:
            raise TribunalMemberError("El socio seleccionado no tiene una cuenta habilitada.")
        if socio.role == Role.TD:
            raise TribunalMemberError("El socio ya integra el Tribunal de Disciplina.")
        if socio.role != Role.SOCIO:
            raise TribunalMemberError(
                f"El socio tiene el rol {socio.get_role_display()}. Sólo un Socio Ordinario "
                "puede ser designado en el Tribunal de Disciplina."
            )
        previous = socio.role
        socio.role = Role.TD
        socio.save(update_fields=["role"])
        cls._record(socio, accion=TribunalRoleAction.GRANT, previous=previous, actor=actor)
        return socio

    @classmethod
    @transaction.atomic
    def revoke(cls, *, socio_id: int, actor: Any) -> Socio:
        socio = Socio.objects.select_for_update().filter(pk=socio_id, role=Role.TD).first()
        if socio is None:
            raise TribunalMemberNotFound
        previous = socio.role
        socio.role = Role.SOCIO
        socio.save(update_fields=["role"])
        cls._record(socio, accion=TribunalRoleAction.REVOKE, previous=previous, actor=actor)
        return socio
