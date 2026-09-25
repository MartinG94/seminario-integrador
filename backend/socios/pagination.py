from rest_framework.pagination import PageNumberPagination


class SocioPagination(PageNumberPagination):
    """Paginador canónico para el padrón de socios (CA3)."""

    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100
