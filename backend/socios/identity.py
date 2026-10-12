"""Resolución de referencias de consulta y propiedad entre padrones."""

from django.db.models import Q

from padron.domain import SocioInstitucionalDTO
from padron.models import Socio as InstitutionalSocio
from padron.models import SocioEstudio
from padron.ports import PadronRepositoryInterface
from socios.models import Socio


class AmbiguousSocioIdentity(LookupError):
    """El identificador no acredita una persona inequívoca."""


def _positive_number(identifier: str, *, maximum: int = 2147483647) -> int | None:
    try:
        number = int(identifier)
    except (ValueError, TypeError):
        return None
    return number if identifier.isdecimal() and 0 < number <= maximum else None


def resolve_local_candidate(identifier: str, *, allow_legajo: bool) -> Socio | None:
    """La fuente explícita usa PK; las llamadas antiguas admiten legajo inequívoco."""
    number = _positive_number(identifier, maximum=9223372036854775807)
    query = Q(pk=number) if number is not None else Q(pk__in=[])
    if allow_legajo:
        query |= Q(legajo=identifier)
    candidates = list(Socio.objects.select_related("subcomision").filter(query)[:2])
    if len(candidates) > 1:
        raise AmbiguousSocioIdentity
    return candidates[0] if candidates else None


def resolve_institutional_candidate(
    repository: PadronRepositoryInterface, identifier: str, *, allow_legajo: bool
) -> SocioInstitucionalDTO | None:
    """La consulta por nroSocio no cae hacia un legajo alternativo."""
    number = _positive_number(identifier)
    candidates: dict[int, SocioInstitucionalDTO] = {}
    if number is not None:
        dto = repository.get_by_id(number)
        if dto is not None:
            if isinstance(dto.socio_id, bool) or dto.socio_id != number:
                raise AmbiguousSocioIdentity
            candidates[dto.socio_id] = dto
    if allow_legajo and identifier:
        if number is not None:
            owners = (
                SocioEstudio.objects.filter(nroLegajo=number)
                .values_list("socio_id", flat=True)
                .distinct()
            )
            if len(list(owners[:2])) > 1:
                raise AmbiguousSocioIdentity
        dto = repository.get_by_legajo(identifier)
        if dto is not None:
            if (
                not isinstance(dto.socio_id, int)
                or isinstance(dto.socio_id, bool)
                or dto.socio_id <= 0
                or number is None
                or _positive_number(str(dto.legajo)) != number
            ):
                raise AmbiguousSocioIdentity
            candidates[dto.socio_id] = dto
    if len(candidates) > 1:
        raise AmbiguousSocioIdentity
    return next(iter(candidates.values()), None)


def resolve_institutional_owner(dto: SocioInstitucionalDTO) -> Socio | None:
    """Sólo un vínculo institucional único o un legajo real acreditan propiedad."""
    member = InstitutionalSocio.objects.filter(pk=dto.socio_id).only("user_id").first()
    if member is not None and member.user_id is not None:
        if InstitutionalSocio.objects.filter(user_id=member.user_id).exclude(pk=member.pk).exists():
            return None
        return Socio.objects.select_related("subcomision").filter(user_id=member.user_id).first()
    number = _positive_number(str(dto.legajo)) if dto.legajo is not None else None
    if number is None:
        return None
    if member is not None:
        owners = set(
            SocioEstudio.objects.filter(nroLegajo=number)
            .values_list("socio_id", flat=True)
            .distinct()
        )
        if owners != {dto.socio_id}:
            return None
    return Socio.objects.select_related("subcomision").filter(legajo=str(number)).first()
