"""Módulo canónico de paginación server-side para la API REST del SGD-AVEIT.

Define StandardResultsSetPagination y la excepción estructurada RFC 9457
conforme a los requerimientos EARS-U01, EARS-W01 y EARS-W02 de la especificación 010
(SCRUM-87 / SCRUM-118).
"""

from typing import Any, List, Optional

from django.core.paginator import InvalidPage
from rest_framework import exceptions, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler


class InvalidPageError(exceptions.NotFound):
    """Excepción RFC 9457 emitida cuando se solicita una página fuera de rango o inexistente."""

    status_code = status.HTTP_404_NOT_FOUND
    default_code = "invalid_page"

    def __init__(
        self,
        detail: Optional[str] = None,
        code: Optional[str] = None,
        instance: Optional[str] = None,
        page_number: Optional[Any] = None,
        total_pages: Optional[int] = None,
    ):
        msg = detail or "Página inválida. La página solicitada no contiene resultados."
        payload: dict[str, Any] = {
            "type": "https://errors.aveit.org.ar/invalid-page",
            "title": "Página no encontrada",
            "status": status.HTTP_404_NOT_FOUND,
            "detail": msg,
            "instance": instance or "",
        }

        if page_number is not None and total_pages is not None:
            try:
                parsed_page = int(page_number)
                if parsed_page > total_pages:
                    reason = (
                        f"El número de página {parsed_page} excede el total "
                        f"de {total_pages} página(s) disponible(s)."
                    )
                elif parsed_page < 1:
                    reason = f"El número de página {parsed_page} debe ser mayor o igual a 1."
                else:
                    reason = f"El número de página {parsed_page} es inválido."
            except (TypeError, ValueError):
                reason = f"El valor de página '{page_number}' no es un número entero válido."

            payload["invalid_params"] = [
                {
                    "name": "page",
                    "reason": reason,
                }
            ]
        elif page_number is not None:
            payload["invalid_params"] = [
                {
                    "name": "page",
                    "reason": f"El valor proporcionado para 'page' ({page_number}) no es válido.",
                }
            ]

        super().__init__(detail=payload, code=code)
        self.detail = payload


InvalidPageRFC9457Exception = InvalidPageError


def problem_details_exception_handler(
    exc: Exception, context: dict[str, Any]
) -> Optional[Response]:
    """Envuelve respuestas RFC 9457 de paginación con Content-Type application/problem+json."""
    response = drf_exception_handler(exc, context)
    if response is not None and isinstance(exc, InvalidPageError):
        response.content_type = "application/problem+json"
        response["Content-Type"] = "application/problem+json"
    return response


class StandardResultsSetPagination(PageNumberPagination):
    """Paginación canónica estándar para colecciones de la API REST.

    - page_size: 20 registros por defecto.
    - page_size_query_param: 'page_size' (configurable por el cliente).
    - max_page_size: 100 registros (techo rígido anti-DoS).
    - page_query_param: 'page'.
    - Envolvente canónica de 7 campos:
        { count, total_pages, current_page, page_size, next, previous, results }
    - Error estructurado RFC 9457 ante páginas fuera de rango.
    """

    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100
    page_query_param = "page"
    invalid_page_message = "Página inválida. La página solicitada no contiene resultados."

    def paginate_queryset(
        self, queryset: Any, request: Request, view: Optional[Any] = None
    ) -> Optional[List[Any]]:
        """Pagina el queryset resolviendo el tamaño de página y capturando InvalidPage."""
        page_size = self.get_page_size(request)
        if not page_size:
            page_size = self.page_size

        paginator = self.django_paginator_class(queryset, page_size)
        page_number = self.get_page_number(request, paginator)

        try:
            self.page = paginator.page(page_number)
        except InvalidPage:
            req_path = request.get_full_path() if hasattr(request, "get_full_path") else ""
            raise InvalidPageError(
                detail=self.invalid_page_message,
                instance=req_path,
                page_number=page_number,
                total_pages=paginator.num_pages,
            )

        if paginator.num_pages > 1 and self.template is not None:
            self.display_page_controls = True

        self.request = request
        return list(self.page)

    def get_paginated_response(self, data: Any) -> Response:
        """Retorna la respuesta HTTP con la envolvente canónica de 7 campos."""
        current_page_size = self.get_page_size(self.request) or self.page_size
        return Response(
            {
                "count": self.page.paginator.count,
                "total_pages": self.page.paginator.num_pages,
                "current_page": self.page.number,
                "page_size": current_page_size,
                "next": self.get_next_link(),
                "previous": self.get_previous_link(),
                "results": data,
            }
        )

    def get_paginated_response_schema(self, schema: Any) -> dict:
        """Define el esquema OpenAPI para la envolvente canónica de 7 campos."""
        return {
            "type": "object",
            "properties": {
                "count": {
                    "type": "integer",
                    "example": 515,
                },
                "total_pages": {
                    "type": "integer",
                    "example": 26,
                },
                "current_page": {
                    "type": "integer",
                    "example": 1,
                },
                "page_size": {
                    "type": "integer",
                    "example": 20,
                },
                "next": {
                    "type": "string",
                    "nullable": True,
                    "format": "uri",
                    "example": "http://api.aveit.org.ar/v1/ranking/?page=2",
                },
                "previous": {
                    "type": "string",
                    "nullable": True,
                    "format": "uri",
                    "example": None,
                },
                "results": schema,
            },
        }


class PaginatedAPIViewMixin:
    """Mixin para dotar a vistas basadas en APIView pura de las capacidades

    de paginación estándar de GenericAPIView sin romper su arquitectura existente.
    """

    pagination_class: Optional[type[PageNumberPagination]] = StandardResultsSetPagination

    @property
    def paginator(self) -> Optional[PageNumberPagination]:
        """Instancia en caché del paginador asociado a la vista."""
        if not hasattr(self, "_paginator"):
            if self.pagination_class is None:
                self._paginator = None
            else:
                self._paginator = self.pagination_class()
        return self._paginator

    def paginate_queryset(self, queryset: Any) -> Optional[List[Any]]:
        """Invoca el paginador configurado sobre el queryset."""
        if self.paginator is None:
            return None
        return self.paginator.paginate_queryset(queryset, self.request, view=self)

    def get_paginated_response(self, data: Any) -> Response:
        """Retorna la respuesta paginada formateada por el paginador."""
        assert self.paginator is not None, "paginator no debe ser None."
        return self.paginator.get_paginated_response(data)
