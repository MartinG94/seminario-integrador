"""Filtros para expedientes disciplinarios (S2-05 CA2).

Permite filtrar por estado, legajo/nombre del socio y rango de fechas.
"""

from django.db.models import Q
import django_filters

from expedientes.models import EstadoExpedienteEnum, Expediente


class ExpedienteFilter(django_filters.FilterSet):
    """Filtros del tablero: estado, socio (legajo o nombre) y rango de fechas (CA2)."""

    estado = django_filters.ChoiceFilter(choices=EstadoExpedienteEnum.choices)
    socio = django_filters.CharFilter(method="filter_socio")
    socio_legajo = django_filters.CharFilter(
        field_name="socio__legajo", lookup_expr="icontains"
    )
    fecha_desde = django_filters.DateFilter(
        field_name="created_at", lookup_expr="date__gte"
    )
    fecha_hasta = django_filters.DateFilter(
        field_name="created_at", lookup_expr="date__lte"
    )

    class Meta:
        model = Expediente
        fields = ["estado", "socio", "socio_legajo", "fecha_desde", "fecha_hasta"]

    def filter_socio(self, queryset, name, value):
        if not value:
            return queryset
        val = value.strip()
        return queryset.filter(
            Q(socio__legajo__icontains=val)
            | Q(socio__first_name__icontains=val)
            | Q(socio__last_name__icontains=val)
        )
