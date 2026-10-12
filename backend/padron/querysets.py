"""Lectura SQL de clasificación institucional antes de contar o paginar."""

from django.db.models import Exists, OuterRef, QuerySet

from padron.domain import JUNIOR_SOCIAL_YEARS, SENIOR_SOCIAL_YEARS, SocioCategoryEnum
from padron.models import Socio
from socios.models import InstitutionalMembershipCondition


def with_institutional_condition(queryset: QuerySet[Socio]) -> QuerySet[Socio]:
    """Anota una condición confirmada en la consulta, sin búsquedas por fila."""
    confirmed = InstitutionalMembershipCondition.objects.filter(
        institutional_number=OuterRef("nroSocio"), condition="EX_TRAVELER"
    )
    return queryset.annotate(is_ex_traveler_confirmed=Exists(confirmed))


def filter_institutional_category(
    queryset: QuerySet[Socio], category: SocioCategoryEnum
) -> QuerySet[Socio]:
    """La condición excluye a exviajeros de la escala y de UNKNOWN."""
    if category == SocioCategoryEnum.JUNIOR:
        return queryset.filter(anoSocial__in=JUNIOR_SOCIAL_YEARS, is_ex_traveler_confirmed=False)
    if category == SocioCategoryEnum.SENIOR:
        return queryset.filter(anoSocial__in=SENIOR_SOCIAL_YEARS, is_ex_traveler_confirmed=False)
    if category == SocioCategoryEnum.EX_TRAVELER:
        return queryset.filter(is_ex_traveler_confirmed=True)
    if category == SocioCategoryEnum.UNKNOWN:
        return queryset.filter(is_ex_traveler_confirmed=False).exclude(
            anoSocial__in=JUNIOR_SOCIAL_YEARS + SENIOR_SOCIAL_YEARS
        )
    raise ValueError("La clasificación de consulta no es válida.")
