"""Serializadores de DRF para la validación y transformación del padrón institucional.

Incluye:
  - SocioFilterParamsSerializer: Validación de query params con HTTP 400
    ante opciones inválidas (MED-001).
  - SubcomisionSerializer: Representación canónica de subcomisiones (excluye centinela 99).
  - SocioInstitucionalSerializer: Ficha institucional canónica de socio (CA1–CA4).
  - PaginatedSociosSerializer: Estructura canónica con count y results (LOW-IT2-001).
  - HealthStatusSerializer: Observabilidad con 6 atributos estandarizados (CA5 / MED-003).

Referencia: plan.md §5, spec.md §RF-PADRON-01.
"""

from rest_framework import serializers

from padron.domain import MembershipStatusEnum, SocioCategoryEnum


class SocioFilterParamsSerializer(serializers.Serializer):
    """Validador estricto de parámetros de consulta para el listado de socios (MED-001)."""

    search = serializers.CharField(required=False, allow_blank=True, max_length=100)
    subcomision_id = serializers.IntegerField(required=False, min_value=1)
    category = serializers.ChoiceField(
        choices=[c.value for c in SocioCategoryEnum],
        required=False,
    )
    is_active = serializers.BooleanField(required=False)
    membership_status = serializers.ChoiceField(
        choices=[m.value for m in MembershipStatusEnum],
        required=False,
    )
    page = serializers.IntegerField(required=False, min_value=1, default=1)
    page_size = serializers.IntegerField(required=False, min_value=1, max_value=100, default=20)


class SubcomisionSerializer(serializers.Serializer):
    """Serializador para subcomisiones institucionales."""

    id = serializers.IntegerField()
    name = serializers.CharField()


class SocioInstitucionalSerializer(serializers.Serializer):
    """Serializador para la ficha canónica de un socio del padrón."""

    socio_id = serializers.IntegerField()
    legajo = serializers.CharField(allow_null=True)
    dni = serializers.CharField(allow_null=True)
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    email = serializers.CharField(allow_null=True)
    subcomision = SubcomisionSerializer(allow_null=True)
    social_year = serializers.IntegerField()
    category = serializers.ChoiceField(choices=[c.value for c in SocioCategoryEnum])
    is_active = serializers.BooleanField()
    membership_status = serializers.ChoiceField(choices=[m.value for m in MembershipStatusEnum])


class PaginatedSociosSerializer(serializers.Serializer):
    """Serializador canónico de respuesta paginada con count y results (LOW-IT2-001)."""

    count = serializers.IntegerField(help_text="Total de socios coincidentes con los filtros")
    page = serializers.IntegerField()
    page_size = serializers.IntegerField()
    results = SocioInstitucionalSerializer(many=True)


class HealthStatusSerializer(serializers.Serializer):
    """Serializador para el estado de salud y observabilidad (CA5 / MED-003)."""

    status = serializers.CharField()
    latency_ms = serializers.FloatField()
    source = serializers.CharField()
    record_count = serializers.IntegerField()
    last_checked_at = serializers.CharField()
    message = serializers.CharField()
