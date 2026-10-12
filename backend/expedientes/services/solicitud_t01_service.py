"""Clasificación y materialización de destinatarios institucionales del T01."""

from typing import NoReturn

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import ValidationError

from padron.domain import SocioInstitucionalDTO
from padron.models import Socio as InstitutionalSocio
from padron.models import SocioEstudio
from socios.models import Role, SocialCategory, Socio, Subcomision


def _reject_classification() -> NoReturn:
    raise ValidationError(
        {"destinatarios_socios_ids": "El socio no tiene una clasificación social confirmada."}
    )


def _reject_identity() -> NoReturn:
    raise ValidationError(
        {"destinatarios_socios_ids": "No se pudo acreditar la identidad del socio destinatario."}
    )


def canonical_t01_classification(dto: SocioInstitucionalDTO) -> tuple[str, int | None]:
    """Deriva la escala por año; sólo el par explícito EX_TRAVELER/null queda fuera."""
    category = getattr(dto.category, "value", dto.category)
    if category == SocialCategory.EX_TRAVELER:
        if dto.social_year is not None:
            _reject_classification()
        return SocialCategory.EX_TRAVELER, None
    if category not in {SocialCategory.JUNIOR, SocialCategory.SENIOR, "PASSIVE", "ACTIVE"}:
        _reject_classification()
    year = dto.social_year
    if isinstance(year, bool) or not isinstance(year, int):
        _reject_classification()
    try:
        return Socio.category_for_social_year(year), year
    except DjangoValidationError:
        _reject_classification()


def validate_t01_reference(dto: SocioInstitucionalDTO, expected_id: int) -> None:
    """El ID seleccionado debe identificar el DTO institucional que se recibió."""
    if (
        isinstance(expected_id, bool)
        or not isinstance(expected_id, int)
        or expected_id <= 0
        or isinstance(dto.socio_id, bool)
        or not isinstance(dto.socio_id, int)
        or dto.socio_id != expected_id
    ):
        _reject_identity()
    canonical_t01_classification(dto)


def _synchronize_classification(local: Socio, category: str, social_year: int | None) -> Socio:
    if (local.category, local.social_year) != (category, social_year):
        local.category = category
        local.social_year = social_year
        local.save(update_fields=["category", "social_year"])
    return local


def _validate_institutional_legajo(
    dto: SocioInstitucionalDTO, *, require_association: bool
) -> None:
    if not dto.legajo:
        return
    try:
        institutional_legajo = int(dto.legajo)
    except (TypeError, ValueError):
        if require_association:
            _reject_identity()
        return
    owners = set(
        SocioEstudio.objects.filter(nroLegajo=institutional_legajo)
        .order_by()
        .values_list("socio_id", flat=True)
        .distinct()
    )
    if owners != {dto.socio_id} and (owners or require_association):
        _reject_identity()


def materialize_t01_recipient(dto: SocioInstitucionalDTO) -> Socio:
    """Resuelve identidad inequívoca y conserva los datos de cuentas y socios previos.

    Se llama dentro de la transacción de emisión. La PK local jamás se usa como
    equivalencia de nroSocio; el vínculo user_id institucional o el legajo real
    corroborado permiten resolver la persona, y las referencias contradictorias abortan.
    """
    category, year = canonical_t01_classification(dto)
    institutional = InstitutionalSocio.objects.filter(pk=dto.socio_id).values("user_id").first()
    user_id = institutional["user_id"] if institutional else None
    UserModel = get_user_model()
    linked_user = None
    linked_local = None
    if user_id is not None:
        if InstitutionalSocio.objects.filter(user_id=user_id).exclude(pk=dto.socio_id).exists():
            _reject_identity()
        linked_user = UserModel.objects.select_for_update().filter(pk=user_id).first()
        if linked_user is None:
            _reject_identity()
        linked_local = Socio.objects.select_for_update().filter(user_id=user_id).first()
    else:
        _validate_institutional_legajo(dto, require_association=institutional is not None)

    by_legajo = (
        Socio.objects.select_for_update().filter(legajo=dto.legajo).first() if dto.legajo else None
    )
    by_email = (
        Socio.objects.select_for_update().filter(email__iexact=dto.email).first()
        if dto.email
        else None
    )
    candidates = [local for local in (linked_local, by_legajo, by_email) if local is not None]
    if len({local.pk for local in candidates}) > 1:
        _reject_identity()
    if linked_local is not None:
        return _synchronize_classification(linked_local, category, year)
    if linked_user is not None and candidates:
        _reject_identity()
    if by_legajo is not None:
        if dto.email and by_legajo.email.casefold() != dto.email.casefold():
            _reject_identity()
        return _synchronize_classification(by_legajo, category, year)
    if by_email is not None or not dto.legajo:
        _reject_identity()

    existing_user = UserModel.objects.select_for_update().filter(username=dto.legajo).first()
    if existing_user is not None and (linked_user is None or existing_user.pk != linked_user.pk):
        _reject_identity()
    if (
        linked_user is None
        and dto.email
        and UserModel.objects.filter(email__iexact=dto.email).exists()
    ):
        _reject_identity()

    email = dto.email or f"{dto.legajo}@aveit.utn.edu.ar"
    user = linked_user or UserModel.objects.create_user(username=dto.legajo, email=email)
    subcomision = None
    if dto.subcomision:
        subcomision, _ = Subcomision.objects.get_or_create(name=dto.subcomision.name)
    return Socio.objects.create(
        user=user,
        legajo=dto.legajo,
        first_name=dto.first_name,
        last_name=dto.last_name,
        email=email,
        subcomision=subcomision,
        social_year=year,
        category=category,
        role=Role.SOCIO,
        is_enabled=dto.is_active,
    )
