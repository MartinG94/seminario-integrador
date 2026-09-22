import unicodedata

from django.db.models import Q, QuerySet
from rest_framework.filters import BaseFilterBackend
from rest_framework.request import Request
from rest_framework.views import APIView


def make_accent_insensitive_regex(term: str) -> str:
    """
    Construye una expresión regular tolerante a variantes diacríticas en español.
    Ejemplo: 'sanchez' matchea 's[aá]nch[eé]z'.
    """
    accent_map = {
        "a": "[aáÁA]",
        "á": "[aáÁA]",
        "e": "[eéÉE]",
        "é": "[eéÉE]",
        "i": "[iíÍI]",
        "í": "[iíÍI]",
        "o": "[oóÓO]",
        "ó": "[oóÓO]",
        "u": "[uúüÚÜU]",
        "ú": "[uúüÚÜU]",
        "ü": "[uúüÚÜU]",
        "n": "[nñÑN]",
        "ñ": "[nñÑN]",
    }

    normalized = unicodedata.normalize("NFC", term)
    pattern_parts = []
    for char in normalized:
        low = char.lower()
        if low in accent_map:
            pattern_parts.append(accent_map[low])
        else:
            pattern_parts.append(unicodedata.normalize("NFD", char))
    return "".join(pattern_parts)


class AccentInsensitiveSearchFilter(BaseFilterBackend):
    """
    Filtro de búsqueda multi-término para el Padrón de Socios (CA1).
    Permite filtrar por first_name, last_name, legajo y subcomision__name
    de forma insensible a mayúsculas y acentos tanto en SQLite como en MySQL.
    """

    search_param = "search"

    def filter_queryset(self, request: Request, queryset: QuerySet, view: APIView) -> QuerySet:
        search_terms = request.query_params.get(self.search_param) or request.query_params.get("q")
        if not search_terms:
            return queryset

        terms = search_terms.strip().split()
        if not terms:
            return queryset

        for term in terms:
            regex_pattern = make_accent_insensitive_regex(term)

            term_query = (
                Q(first_name__icontains=term)
                | Q(first_name__iregex=regex_pattern)
                | Q(last_name__icontains=term)
                | Q(last_name__iregex=regex_pattern)
                | Q(legajo__icontains=term)
                | Q(subcomision__name__icontains=term)
                | Q(subcomision__name__iregex=regex_pattern)
            )
            queryset = queryset.filter(term_query)

        return queryset
