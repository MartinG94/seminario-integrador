"""Filtros para expedientes disciplinarios (S2-05 CA2).

Permite filtrar por estado, legajo/nombre del socio y rango de fechas.
"""

import django_filters
from django.db.models import Q

from expedientes.models import EstadoExpedienteEnum, Expediente, UrgenciaExpedienteEnum


class ExpedienteFilter(django_filters.FilterSet):
    """Filtros del tablero: estado, socio (legajo o nombre), urgencia y rango de fechas (CA2)."""

    estado = django_filters.ChoiceFilter(choices=EstadoExpedienteEnum.choices)
    urgencia = django_filters.ChoiceFilter(choices=UrgenciaExpedienteEnum.choices)
    socio = django_filters.CharFilter(method="filter_socio")
    socio_legajo = django_filters.CharFilter(field_name="socio__legajo", lookup_expr="icontains")
    fecha_desde = django_filters.DateFilter(field_name="created_at", lookup_expr="date__gte")
    fecha_hasta = django_filters.DateFilter(field_name="created_at", lookup_expr="date__lte")

    class Meta:
        model = Expediente
        fields = ["estado", "urgencia", "socio", "socio_legajo", "fecha_desde", "fecha_hasta"]

    def filter_socio(self, queryset, name, value):
        if not value:
            return queryset
        val = value.strip()
        return queryset.filter(
            Q(socio__legajo__icontains=val)
            | Q(socio__first_name__icontains=val)
            | Q(socio__last_name__icontains=val)
            | Q(socios__legajo__icontains=val)
            | Q(socios__first_name__icontains=val)
            | Q(socios__last_name__icontains=val)
        ).distinct()
