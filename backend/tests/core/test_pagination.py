"""Pruebas unitarias e integrales para el módulo de paginación canónica.

Valida la envolvente canónica de 7 campos, límites anti-DoS y el manejo de
errores RFC 9457 para páginas fuera de rango según EARS-U01, EARS-W01 y EARS-W02.
"""

import pytest
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory
from rest_framework.views import APIView

from core.pagination import (
    InvalidPageError,
    InvalidPageRFC9457Exception,
    PaginatedAPIViewMixin,
    StandardResultsSetPagination,
)


class DummyItemListView(APIView):
    """Vista de prueba para verificar integración con StandardResultsSetPagination."""

    permission_classes = [AllowAny]
    authentication_classes = []
    pagination_class = StandardResultsSetPagination

    def get(self, request, *args, **kwargs):
        # Datos simulados: lista de 45 enteros
        items = list(range(1, 46))
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(items, request, view=self)
        if page is not None:
            return paginator.get_paginated_response(page)
        return Response(items)


@pytest.fixture
def factory():
    return APIRequestFactory()


@pytest.fixture
def paginator():
    return StandardResultsSetPagination()


class TestStandardResultsSetPagination:
    """Suite de validación de contratos para StandardResultsSetPagination."""

    def test_canonical_envelope_structure(self, factory, paginator):
        """Verifica que la envolvente contenga exactamente los 7 campos canónicos."""
        data = list(range(1, 51))
        request = Request(factory.get("/api/v1/test/?page=1"))
        page = paginator.paginate_queryset(data, request)
        response = paginator.get_paginated_response(page)

        expected_fields = {
            "count",
            "total_pages",
            "current_page",
            "page_size",
            "next",
            "previous",
            "results",
        }
        assert set(response.data.keys()) == expected_fields
        assert response.data["count"] == 50
        assert response.data["total_pages"] == 3  # ceil(50 / 20)
        assert response.data["current_page"] == 1
        assert response.data["page_size"] == 20
        assert len(response.data["results"]) == 20
        assert "page=2" in response.data["next"]
        assert response.data["previous"] is None

    def test_default_page_size_is_twenty(self, factory, paginator):
        """Comprueba que el tamaño de página por defecto sea 20."""
        data = list(range(1, 35))
        request = Request(factory.get("/api/v1/test/"))
        page = paginator.paginate_queryset(data, request)
        response = paginator.get_paginated_response(page)

        assert response.data["page_size"] == 20
        assert len(response.data["results"]) == 20
        assert response.data["total_pages"] == 2

    def test_custom_page_size_parameter(self, factory, paginator):
        """Permite al cliente especificar page_size dentro de los límites válidos."""
        data = list(range(1, 100))
        request = Request(factory.get("/api/v1/test/?page_size=10"))
        page = paginator.paginate_queryset(data, request)
        response = paginator.get_paginated_response(page)

        assert response.data["page_size"] == 10
        assert len(response.data["results"]) == 10
        assert response.data["total_pages"] == 10

    def test_hard_cap_max_page_size_one_hundred(self, factory, paginator):
        """Asegura que valores de page_size superiores a 100 se acoten a 100 (EARS-W02 anti-DoS)."""
        data = list(range(1, 250))
        request = Request(factory.get("/api/v1/test/?page_size=500"))
        page = paginator.paginate_queryset(data, request)
        response = paginator.get_paginated_response(page)

        assert response.data["page_size"] == 100
        assert len(response.data["results"]) == 100
        assert response.data["total_pages"] == 3

    def test_malformed_page_size_falls_back_to_default(self, factory, paginator):
        """Valores no enteros o negativos en page_size revierten a page_size=20 (EARS-W03)."""
        data = list(range(1, 40))
        request = Request(factory.get("/api/v1/test/?page_size=invalido"))
        page = paginator.paginate_queryset(data, request)
        response = paginator.get_paginated_response(page)

        assert response.data["page_size"] == 20
        assert len(response.data["results"]) == 20

    def test_pagination_next_and_previous_links(self, factory, paginator):
        """Valida que los enlaces next y previous se computen adecuadamente."""
        data = list(range(1, 65))
        # Página intermedia (página 2 de 4)
        request = Request(factory.get("/api/v1/test/?page=2"))
        page = paginator.paginate_queryset(data, request)
        response = paginator.get_paginated_response(page)

        assert response.data["current_page"] == 2
        assert response.data["previous"] is not None
        assert response.data["next"] is not None

        # Última página (página 4 de 4)
        request_last = Request(factory.get("/api/v1/test/?page=4"))
        page_last = paginator.paginate_queryset(data, request_last)
        response_last = paginator.get_paginated_response(page_last)

        assert response_last.data["current_page"] == 4
        assert response_last.data["next"] is None
        assert response_last.data["previous"] is not None

    def test_page_out_of_range_raises_rfc9457_error(self, factory, paginator):
        """Verifica que página fuera de rango lance InvalidPageError (RFC 9457 / EARS-W01)."""
        data = list(range(1, 30))
        request = Request(factory.get("/api/v1/test/?page=9999"))
        expected_msg = "Página inválida. La página solicitada no contiene resultados."

        with pytest.raises(InvalidPageError) as exc_info:
            paginator.paginate_queryset(data, request)

        exc = exc_info.value
        assert exc.status_code == status.HTTP_404_NOT_FOUND
        assert exc.detail["type"] == "https://errors.aveit.org.ar/invalid-page"
        assert exc.detail["title"] == "Página no encontrada"
        assert exc.detail["status"] == 404
        assert exc.detail["detail"] == expected_msg
        assert exc.detail["instance"] == "/api/v1/test/?page=9999"
        assert "invalid_params" in exc.detail
        assert exc.detail["invalid_params"][0]["name"] == "page"
        assert "excede el total" in exc.detail["invalid_params"][0]["reason"]

    def test_page_zero_or_negative_raises_rfc9457_error(self, factory, paginator):
        """Verifica que página 0 o negativa lance InvalidPageError (RFC 9457 / EARS-W01)."""
        data = list(range(1, 30))
        expected_msg = "Página inválida. La página solicitada no contiene resultados."
        for bad_page in ["0", "-1"]:
            request = Request(factory.get(f"/api/v1/test/?page={bad_page}"))
            with pytest.raises(InvalidPageError) as exc_info:
                paginator.paginate_queryset(data, request)

            exc = exc_info.value
            assert exc.status_code == status.HTTP_404_NOT_FOUND
            assert exc.detail["type"] == "https://errors.aveit.org.ar/invalid-page"
            assert exc.detail["title"] == "Página no encontrada"
            assert exc.detail["status"] == 404
            assert exc.detail["detail"] == expected_msg
            assert exc.detail["instance"] == f"/api/v1/test/?page={bad_page}"

    def test_invalid_page_error_direct_instantiation_without_total_pages(self):
        """Verifica construcción de invalid_params cuando solo se conoce el número de página."""
        err = InvalidPageError(page_number="bad-page")
        assert "invalid_params" in err.detail
        assert err.detail["invalid_params"][0]["name"] == "page"
        assert "bad-page" in err.detail["invalid_params"][0]["reason"]

    def test_invalid_page_rfc9457_exception_alias(self):
        """Verifica que InvalidPageRFC9457Exception sea idéntico a InvalidPageError."""
        assert InvalidPageRFC9457Exception is InvalidPageError

    def test_page_non_integer_raises_rfc9457_error(self, factory, paginator):
        """Verifica que solicitar una página no entera lance InvalidPageError con RFC 9457."""
        data = list(range(1, 30))
        request = Request(factory.get("/api/v1/test/?page=abc"))

        with pytest.raises(InvalidPageError) as exc_info:
            paginator.paginate_queryset(data, request)

        exc = exc_info.value
        assert exc.status_code == status.HTTP_404_NOT_FOUND
        assert exc.detail["type"] == "https://errors.aveit.org.ar/invalid-page"
        assert exc.detail["status"] == 404

    def test_empty_collection_pagination(self, factory, paginator):
        """Valida que un conjunto vacío devuelva count=0, total_pages=1 y results=[]."""
        data = []
        request = Request(factory.get("/api/v1/test/"))
        page = paginator.paginate_queryset(data, request)
        response = paginator.get_paginated_response(page)

        assert response.data["count"] == 0
        assert response.data["total_pages"] == 1
        assert response.data["current_page"] == 1
        assert response.data["results"] == []
        assert response.data["next"] is None
        assert response.data["previous"] is None

    def test_openapi_schema_structure(self, paginator):
        """Verifica que el esquema OpenAPI contenga la definición de los 7 campos."""
        schema = paginator.get_paginated_response_schema({"type": "integer"})
        props = schema["properties"]
        assert set(props.keys()) == {
            "count",
            "total_pages",
            "current_page",
            "page_size",
            "next",
            "previous",
            "results",
        }


class DummyMixinListView(PaginatedAPIViewMixin, APIView):
    """Vista de prueba basada en PaginatedAPIViewMixin para verificar encapsulamiento."""

    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request, *args, **kwargs):
        items = list(range(1, 31))
        page = self.paginate_queryset(items)
        if page is not None:
            return self.get_paginated_response(page)
        return Response(items)


class TestPaginationIntegrationView:
    """Pruebas de integración de la paginación con vistas DRF y respuesta HTTP."""

    def test_view_returns_200_with_paginated_envelope(self, factory):
        """Una petición válida devuelve HTTP 200 con la estructura de 7 campos."""
        view = DummyItemListView.as_view()
        request = factory.get("/api/v1/dummy/?page=1&page_size=20")
        response = view(request)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 45
        assert response.data["total_pages"] == 3
        assert response.data["current_page"] == 1
        assert response.data["page_size"] == 20
        assert len(response.data["results"]) == 20

    def test_view_returns_404_rfc9457_when_page_exceeds_bounds(self, factory):
        """Una petición fuera de rango devuelve HTTP 404 estructurado RFC 9457."""
        view = DummyItemListView.as_view()
        request = factory.get("/api/v1/dummy/?page=9999")
        response = view(request)
        expected_msg = "Página inválida. La página solicitada no contiene resultados."

        assert response.status_code == status.HTTP_404_NOT_FOUND
        response.render()
        assert response["Content-Type"].split(";")[0].strip() == "application/problem+json"
        assert response.data["type"] == "https://errors.aveit.org.ar/invalid-page"
        assert response.data["title"] == "Página no encontrada"
        assert response.data["status"] == 404
        assert response.data["detail"] == expected_msg
        assert response.data["instance"] == "/api/v1/dummy/?page=9999"
        assert "invalid_params" in response.data
        assert response.data["invalid_params"][0]["name"] == "page"

    def test_paginated_apiview_mixin_integration(self, factory):
        """Verifica que PaginatedAPIViewMixin ejecute la paginación sin GenericAPIView."""
        view = DummyMixinListView.as_view()
        request = factory.get("/api/v1/dummy-mixin/?page=2&page_size=10")
        response = view(request)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 30
        assert response.data["total_pages"] == 3
        assert response.data["current_page"] == 2
        assert response.data["page_size"] == 10
        assert len(response.data["results"]) == 10
        assert response.data["results"][0] == 11
        assert response.data["results"][-1] == 20

    def test_paginated_apiview_mixin_none_pagination_class(self, factory):
        """Verifica que si pagination_class es None, no se produce paginación."""

        class UnpaginatedView(PaginatedAPIViewMixin, APIView):
            permission_classes = [AllowAny]
            pagination_class = None

        view = UnpaginatedView()
        assert view.paginator is None
        assert view.paginate_queryset([1, 2, 3]) is None
