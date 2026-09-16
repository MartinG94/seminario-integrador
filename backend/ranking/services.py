"""Lógica de negocio y consultas optimizadas para el Ranking Reconciliado (SGD-AVEIT)."""

from typing import Optional

from django.db.models import (
    CharField,
    F,
    FloatField,
    OuterRef,
    Q,
    QuerySet,
    Subquery,
    Sum,
    Value,
)
from django.db.models.functions import Coalesce

from ranking.models import PuntajeAplicado, PuntajeGeneral, Socio, SocioEstudio


def calculate_reconciliation(
    saldo_historico: Optional[float], saldo_cache: Optional[float]
) -> tuple[float, float, float, bool]:
    """
    Calcula los valores reconciliados para un socio:
    - saldoHistorico: suma de puntos del libro mayor
    - saldoPuntajeGeneral: puntos del registro en caché
    - diferencia: saldoHistorico - saldoPuntajeGeneral
    - reconciliado: True si diferencia == 0.0, False si hay discrepancia
    """
    sh = round(float(saldo_historico or 0.0), 2)
    sc = round(float(saldo_cache or 0.0), 2)
    diff = round(sh - sc, 2)
    if abs(diff) < 0.0001:
        diff = 0.0
    reconciled = bool(diff == 0.0)
    return sh, sc, diff, reconciled


def get_reconciled_ranking_queryset() -> QuerySet[Socio]:
    """
    Retorna un QuerySet de Socio con todas las anotaciones necesarias para el ranking
    resueltas a nivel de base de datos en una única consulta optimizada (cero N+1).
    """
    saldo_historico_subquery = (
        PuntajeAplicado.objects.filter(socio_id=OuterRef("pk"))
        .values("socio_id")
        .annotate(total=Sum("puntajeAplicado"))
        .values("total")[:1]
    )

    saldo_cache_subquery = PuntajeGeneral.objects.filter(socio_id=OuterRef("pk")).values("puntos")[
        :1
    ]

    legajo_subquery = SocioEstudio.objects.filter(socio_id=OuterRef("pk")).values("nroLegajo")[:1]

    return Socio.objects.select_related("subcomision").annotate(
        saldo_historico_calc=Coalesce(
            Subquery(saldo_historico_subquery, output_field=FloatField()),
            Value(0.0),
            output_field=FloatField(),
        ),
        saldo_cache_calc=Coalesce(
            Subquery(saldo_cache_subquery, output_field=FloatField()),
            Value(0.0),
            output_field=FloatField(),
        ),
        legajo_calc=Subquery(legajo_subquery, output_field=CharField()),
    )


def filter_ranking_queryset(
    queryset: QuerySet[Socio],
    categoria: Optional[str] = None,
    subcomision: Optional[str] = None,
    search: Optional[str] = None,
    reconciliado: Optional[bool] = None,
) -> QuerySet[Socio]:
    """Aplica filtros de búsqueda, categoría, subcomisión y estado de reconciliación."""
    qs = queryset

    # Filtro por categoría estatutaria (ACTIVO / PASIVO)
    if categoria:
        cat_upper = categoria.strip().upper()
        if cat_upper == "ACTIVO":
            qs = qs.filter(anoSocial__gte=4)
        elif cat_upper == "PASIVO":
            qs = qs.filter(anoSocial__lt=4)

    # Filtro por subcomisión (por nombre o ID numérico)
    if subcomision:
        sub_str = subcomision.strip()
        if sub_str.isdigit():
            qs = qs.filter(subcomision_id=int(sub_str))
        else:
            qs = qs.filter(subcomision__nombre__iexact=sub_str)

    # Filtro de búsqueda textual por nombre, apellido o legajo
    if search:
        q_clean = search.strip()
        if q_clean:
            qs = qs.filter(
                Q(nombre__icontains=q_clean)
                | Q(apellido__icontains=q_clean)
                | Q(nroSocio__icontains=q_clean)
                | Q(estudios__nroLegajo__icontains=q_clean)
            ).distinct()

    # Filtro por reconciliado (True / False)
    if reconciliado is not None:
        if reconciliado:
            qs = qs.filter(saldo_historico_calc=F("saldo_cache_calc"))
        else:
            qs = qs.exclude(saldo_historico_calc=F("saldo_cache_calc"))

    return qs


def order_ranking_queryset(
    queryset: QuerySet[Socio], ordering: Optional[str] = None
) -> QuerySet[Socio]:
    """Aplica ordenamiento al ranking con orden por defecto descendente por saldo."""
    if not ordering:
        # Por defecto: mayor saldo primero, desempata alfabéticamente por apellido y nombre
        return queryset.order_by("-saldo_historico_calc", "apellido", "nombre")

    ordering_map = {
        "saldo": ("saldo_historico_calc", "apellido"),
        "+saldo": ("saldo_historico_calc", "apellido"),
        "-saldo": ("-saldo_historico_calc", "apellido"),
        "apellido": ("apellido", "nombre"),
        "+apellido": ("apellido", "nombre"),
        "-apellido": ("-apellido", "nombre"),
        "nombre": ("nombre", "apellido"),
        "+nombre": ("nombre", "apellido"),
        "-nombre": ("-nombre", "apellido"),
        "legajo": ("legajo_calc", "apellido"),
        "+legajo": ("legajo_calc", "apellido"),
        "-legajo": ("-legajo_calc", "apellido"),
    }

    fields = ordering_map.get(ordering.strip())
    if fields:
        return queryset.order_by(*fields)

    return queryset.order_by("-saldo_historico_calc", "apellido", "nombre")
