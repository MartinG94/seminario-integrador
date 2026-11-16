"""Alta y baja del rol TD con auditoría inmutable (Spec 010, RF-10 a RF-13)."""

from __future__ import annotations

from typing import Any

from django.db import transaction
from django.db.models import QuerySet

from accounts import audit
from core.models import AccionRolTribunal, CambioRolTribunal
from socios.models import Role, Socio


class TribunalMemberError(Exception):
    """El alta no puede realizarse; el mensaje está redactado para el usuario."""


class TribunalMemberNotFound(Exception):
    """El socio no integra el Tribunal de Disciplina."""


class TribunalMemberService:
    @staticmethod
    def members() -> QuerySet[Socio]:
        return (
            Socio.objects.filter(role=Role.TD)
            .select_related("subcomision")
            .order_by("-social_year", "last_name", "first_name")
        )

    @staticmethod
    def _record(socio: Socio, *, accion: str, previous: str, actor: Any) -> None:
        CambioRolTribunal.objects.create(
            socio=socio, accion=accion, rol_anterior=previous, rol_nuevo=socio.role, autor=actor
        )
        audit.log_role_change(
            identifier=actor.get_username(),
            target=socio.legajo,
            previous_role=previous,
            new_role=socio.role,
        )

    @classmethod
    @transaction.atomic
    def assign(cls, *, socio_id: int, actor: Any) -> Socio:
        socio = Socio.objects.select_for_update().filter(pk=socio_id).first()
        if socio is None:
            raise TribunalMemberError("El socio seleccionado no existe en el padrón.")
        if not socio.is_enabled:
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
        cls._record(socio, accion=AccionRolTribunal.ALTA, previous=previous, actor=actor)
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
        cls._record(socio, accion=AccionRolTribunal.BAJA, previous=previous, actor=actor)
        return socio
