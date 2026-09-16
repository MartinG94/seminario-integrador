"""Lógica de negocio y consultas optimizadas para el Ranking Reconciliado (SGD-AVEIT)."""

from typing import Optional

from django.db.models import (
    CharField,
    Exists,
    F,
    FloatField,
    OuterRef,
    Q,
    QuerySet,
    Subquery,
    Sum,
    Value,
)
from django.db.models.functions import Abs, Coalesce, Concat, Round

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
            Round(Subquery(saldo_historico_subquery, output_field=FloatField()), 2),
            Value(0.0),
            output_field=FloatField(),
        ),
        saldo_cache_calc=Coalesce(
            Round(Subquery(saldo_cache_subquery, output_field=FloatField()), 2),
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

    # Filtro por subcomisión (por nombre, ID numérico o sin subcomisión)
    if subcomision:
        sub_str = subcomision.strip()
        if sub_str:
            if sub_str.lower() in (
                "sin subcomision",
                "sin subcomisión",
                "ninguna",
                "none",
                "null",
            ):
                qs = qs.filter(subcomision__isnull=True)
            elif sub_str.isdigit():
                qs = qs.filter(subcomision_id=int(sub_str))
            else:
                qs = qs.filter(subcomision__nombre__iexact=sub_str)

    # Filtro de búsqueda textual por nombre, apellido, nroSocio, nombre completo o legajo
    if search:
        q_clean = search.strip()
        if q_clean:
            legajo_match = SocioEstudio.objects.filter(
                socio_id=OuterRef("pk"),
                nroLegajo__icontains=q_clean,
            )
            qs = qs.annotate(
                full_name_direct=Concat("nombre", Value(" "), "apellido"),
                full_name_reverse=Concat("apellido", Value(" "), "nombre"),
            ).filter(
                Q(nombre__icontains=q_clean)
                | Q(apellido__icontains=q_clean)
                | Q(full_name_direct__icontains=q_clean)
                | Q(full_name_reverse__icontains=q_clean)
                | Q(nroSocio__icontains=q_clean)
                | Exists(legajo_match)
            )

    # Filtro por reconciliado (True / False) con tolerancia numérica estricta idéntica a Python
    if reconciliado is not None:
        qs = qs.annotate(_reconciled_diff=Abs(F("saldo_historico_calc") - F("saldo_cache_calc")))
        if reconciliado:
            qs = qs.filter(_reconciled_diff__lt=0.0001)
        else:
            qs = qs.filter(_reconciled_diff__gte=0.0001)

    return qs


def order_ranking_queryset(
    queryset: QuerySet[Socio], ordering: Optional[str] = None
) -> QuerySet[Socio]:
    """Aplica ordenamiento al ranking con orden por defecto descendente por saldo."""
    if not ordering:
        # Por defecto: mayor saldo primero, desempata alfabéticamente por apellido y nombre
        return queryset.order_by("-saldo_historico_calc", "apellido", "nombre")

    ordering_map = {
        "saldo": ("saldo_historico_calc", "apellido", "nombre"),
        "+saldo": ("saldo_historico_calc", "apellido", "nombre"),
        "-saldo": ("-saldo_historico_calc", "apellido", "nombre"),
        "merito": ("-saldo_historico_calc", "apellido", "nombre"),
        "+merito": ("-saldo_historico_calc", "apellido", "nombre"),
        "-merito": ("saldo_historico_calc", "apellido", "nombre"),
        "sancion": ("saldo_historico_calc", "apellido", "nombre"),
        "+sancion": ("saldo_historico_calc", "apellido", "nombre"),
        "-sancion": ("-saldo_historico_calc", "apellido", "nombre"),
        "apellido": ("apellido", "nombre"),
        "+apellido": ("apellido", "nombre"),
        "-apellido": ("-apellido", "nombre"),
        "nombre": ("nombre", "apellido"),
        "+nombre": ("nombre", "apellido"),
        "-nombre": ("-nombre", "apellido"),
        "legajo": ("legajo_calc", "apellido"),
        "+legajo": ("legajo_calc", "apellido"),
        "-legajo": ("-legajo_calc", "apellido"),
        "subcomision": ("subcomision__nombre", "apellido"),
        "+subcomision": ("subcomision__nombre", "apellido"),
        "-subcomision": ("-subcomision__nombre", "apellido"),
    }

    fields = ordering_map.get(ordering.strip())
    if fields:
        return queryset.order_by(*fields)

    return queryset.order_by("-saldo_historico_calc", "apellido", "nombre")
