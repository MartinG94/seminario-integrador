"""Resolución de referencias de consulta y propiedad entre padrones."""

from django.db.models import Exists, OuterRef, Q

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
            if (
                not isinstance(dto.socio_id, int)
                or isinstance(dto.socio_id, bool)
                or dto.socio_id != number
            ):
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
    if member is not None:
        shared_academic_number = SocioEstudio.objects.filter(
            nroLegajo=OuterRef("nroLegajo")
        ).exclude(socio_id=dto.socio_id)
        academic_numbers = (
            SocioEstudio.objects.filter(socio_id=dto.socio_id)
            .annotate(shared=Exists(shared_academic_number))
            .filter(shared=False)
            .values_list("nroLegajo", flat=True)
            .distinct()
        )
        legajos = [str(number) for number in academic_numbers if number > 0]
        owners = list(Socio.objects.select_related("subcomision").filter(legajo__in=legajos)[:2])
        return owners[0] if len(owners) == 1 else None
    number = _positive_number(str(dto.legajo)) if dto.legajo is not None else None
    if number is None:
        return None
    return Socio.objects.select_related("subcomision").filter(legajo=str(number)).first()


def resolve_owned_institutional_candidate(
    local: Socio, repository: PadronRepositoryInterface
) -> SocioInstitucionalDTO | None:
    """Resuelve la identidad propia usando los mismos vínculos de propiedad del legajo."""
    candidate_ids = list(
        InstitutionalSocio.objects.filter(user_id=local.user_id).values_list("pk", flat=True)[:2]
    )
    if not candidate_ids:
        number = _positive_number(local.legajo)
        if number is None:
            return None
        candidate_ids = list(
            SocioEstudio.objects.filter(nroLegajo=number)
            .values_list("socio_id", flat=True)
            .distinct()[:2]
        )
    if len(candidate_ids) > 1:
        raise AmbiguousSocioIdentity
    if not candidate_ids:
        return None

    dto = resolve_institutional_candidate(repository, str(candidate_ids[0]), allow_legajo=False)
    if dto is None:
        return None
    owner = resolve_institutional_owner(dto)
    return dto if owner is not None and owner.pk == local.pk else None
