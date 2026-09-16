"""Lógica de negocio y consultas optimizadas para el Ranking Reconciliado (SGD-AVEIT)."""

import re
import unicodedata
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
from django.db.models.functions import Abs, Cast, Coalesce, Concat, Round

from ranking.models import PuntajeAplicado, PuntajeGeneral, Socio, SocioEstudio


def make_accent_insensitive_regex(text: str) -> str:
    """
    Construye un patrón regex compatible con SQLite y MySQL que empareja
    caracteres con y sin tilde en español (ej: 'perez' -> 'p[eéèëêEÉÈËÊ]r[eéèëêEÉÈËÊ]z').
    """
    replacements = {
        "a": "[aáàäâAÁÀÄÂ]",
        "e": "[eéèëêEÉÈËÊ]",
        "i": "[iíìïîIÍÌÏÎ]",
        "o": "[oóòöôOÓÒÖÔ]",
        "u": "[uúùüûUÚÙÜÛ]",
        "n": "[nñNÑ]",
    }
    pattern_parts = []
    for char in text:
        nfkd = unicodedata.normalize("NFKD", char)
        base_char = nfkd[0].lower()
        if base_char in replacements:
            pattern_parts.append(replacements[base_char])
        elif char.isspace():
            pattern_parts.append(r"\s+")
        else:
            pattern_parts.append(re.escape(char))
    return "".join(pattern_parts)


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

    legajo_subquery = (
        SocioEstudio.objects.filter(socio_id=OuterRef("pk"))
        .order_by("compositeKey")
        .values("nroLegajo")[:1]
    )

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
        legajo_calc=Coalesce(
            Subquery(legajo_subquery, output_field=CharField()),
            Cast("nroSocio", output_field=CharField()),
            output_field=CharField(),
        ),
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
            qs = qs.filter(Q(anoSocial__lt=4) | Q(anoSocial__isnull=True))

    # Filtro por subcomisión (por nombre insensible a acentos, ID numérico o sin subcomisión)
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
                sub_pattern = f"^{make_accent_insensitive_regex(sub_str)}$"
                qs = qs.filter(
                    Q(subcomision__nombre__iexact=sub_str)
                    | Q(subcomision__nombre__iregex=sub_pattern)
                )

    # Filtro de búsqueda textual por nombre, apellido, nroSocio,
    # nombre completo, legajo o subcomisión (insensible a acentos y multi-término)
    if search:
        q_clean = search.strip()
        if q_clean:
            tokens = q_clean.split()
            qs = qs.annotate(
                full_name_direct=Concat("nombre", Value(" "), "apellido"),
                full_name_reverse=Concat("apellido", Value(" "), "nombre"),
            )
            for tok in tokens:
                tok_pat = make_accent_insensitive_regex(tok)
                legajo_match = SocioEstudio.objects.filter(
                    socio_id=OuterRef("pk"),
                    nroLegajo__icontains=tok,
                )
                qs = qs.filter(
                    Q(nombre__icontains=tok)
                    | Q(nombre__iregex=tok_pat)
                    | Q(apellido__icontains=tok)
                    | Q(apellido__iregex=tok_pat)
                    | Q(full_name_direct__icontains=tok)
                    | Q(full_name_direct__iregex=tok_pat)
                    | Q(full_name_reverse__icontains=tok)
                    | Q(full_name_reverse__iregex=tok_pat)
                    | Q(subcomision__nombre__icontains=tok)
                    | Q(subcomision__nombre__iregex=tok_pat)
                    | Q(nroSocio__icontains=tok)
                    | Q(legajo_calc__icontains=tok)
                    | Q(legajo_calc__iregex=tok_pat)
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

    ordering_map: dict[str, tuple[str, ...]] = {
        "id": ("nroSocio",),
        "+id": ("nroSocio",),
        "-id": ("-nroSocio",),
        "saldo": ("saldo_historico_calc", "apellido", "nombre"),
        "+saldo": ("saldo_historico_calc", "apellido", "nombre"),
        "-saldo": ("-saldo_historico_calc", "apellido", "nombre"),
        "puntos": ("saldo_historico_calc", "apellido", "nombre"),
        "+puntos": ("saldo_historico_calc", "apellido", "nombre"),
        "-puntos": ("-saldo_historico_calc", "apellido", "nombre"),
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
        "legajo": ("legajo_calc", "apellido", "nombre"),
        "+legajo": ("legajo_calc", "apellido", "nombre"),
        "-legajo": ("-legajo_calc", "apellido", "nombre"),
        "subcomision": ("subcomision__nombre", "apellido", "nombre"),
        "+subcomision": ("subcomision__nombre", "apellido", "nombre"),
        "-subcomision": ("-subcomision__nombre", "apellido", "nombre"),
        "diferencia": ("_reconciled_diff", "apellido", "nombre"),
        "+diferencia": ("_reconciled_diff", "apellido", "nombre"),
        "-diferencia": ("-_reconciled_diff", "apellido", "nombre"),
        "reconciliado": ("_reconciled_diff", "apellido", "nombre"),
        "+reconciliado": ("_reconciled_diff", "apellido", "nombre"),
        "-reconciliado": ("-_reconciled_diff", "apellido", "nombre"),
    }

    raw_tokens = [tok.strip().lower() for tok in ordering.split(",") if tok.strip()]
    if not raw_tokens:
        return queryset.order_by("-saldo_historico_calc", "apellido", "nombre")

    qs = queryset
    needs_reconciled_diff = any("diferencia" in tok or "reconciliado" in tok for tok in raw_tokens)
    if needs_reconciled_diff:
        qs = qs.annotate(_reconciled_diff=Abs(F("saldo_historico_calc") - F("saldo_cache_calc")))

    combined_fields: list[str] = []
    seen: set[str] = set()

    for tok in raw_tokens:
        fields = ordering_map.get(tok)
        if fields:
            for f in fields:
                norm_f = f.lstrip("+-")
                if norm_f not in seen:
                    seen.add(norm_f)
                    combined_fields.append(f)

    if combined_fields:
        return qs.order_by(*combined_fields)

    return qs.order_by("-saldo_historico_calc", "apellido", "nombre")
