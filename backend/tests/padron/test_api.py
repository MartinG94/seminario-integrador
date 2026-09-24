"""Tests de integración/API para los endpoints de detalle por ID y Legajo del padrón institucional.

Cobertura:
  - GET /api/v1/padron/socios/<id>/: 200 OK, 404 Not Found, 401 Unauthorized (CA2, H05).
  - GET /api/v1/padron/socios/legajo/<legajo>/: 200 OK, 404 Not Found, 401 Unauthorized (CA2, H05).

Referencia: spec.md §RF-PADRON-02, plan.md §5, tasks.md T5.2.
"""

from unittest.mock import MagicMock, patch

from rest_framework import status
from rest_framework.test import APIClient

from padron.domain import (
    MembershipStatusEnum,
    SocioCategoryEnum,
    SocioInstitucionalDTO,
    SubcomisionDTO,
)


def _make_dummy_user() -> MagicMock:
    """Crea un usuario autenticado mock para pruebas de endpoints protegidos."""
    user = MagicMock()
    user.is_authenticated = True
    return user


def _make_sample_socio_dto(socio_id: int = 1001, legajo: str = "85421") -> SocioInstitucionalDTO:
    """Genera un DTO canónico de prueba."""
    return SocioInstitucionalDTO(
        socio_id=socio_id,
        legajo=legajo,
        dni="41234567",
        first_name="Esteban",
        last_name="Pérez",
        email="esteban.perez@aveit.utn.edu.ar",
        subcomision=SubcomisionDTO(id=10, name="Tribunal de Disciplina"),
        social_year=4,
        category=SocioCategoryEnum.ACTIVE,
        is_active=True,
        membership_status=MembershipStatusEnum.ENABLED,
    )


# ==============================================================================
# Endpoint: GET /api/v1/padron/socios/<int:socio_id>/
# ==============================================================================


class TestPadronSocioDetailView:
    """Pruebas para el endpoint de ficha unívoca de socio por nroSocio."""

    def setup_method(self) -> None:
        self.client = APIClient()
        self.url = "/api/v1/padron/socios/1001/"

    def test_unauthenticated_request_returns_401(self) -> None:
        """Petición anónima es rechazada con HTTP 401 Unauthorized."""
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @patch("padron.views.get_padron_repository")
    def test_existing_socio_returns_200_and_canonical_payload(self, mock_get_repo) -> None:
        """Socio existente retorna HTTP 200 con la estructura canónica."""
        mock_repo = MagicMock()
        mock_repo.get_by_id.return_value = _make_sample_socio_dto(socio_id=1001)
        mock_get_repo.return_value = mock_repo

        self.client.force_authenticate(user=_make_dummy_user())
        response = self.client.get(self.url)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["socio_id"] == 1001
        assert data["legajo"] == "85421"
        assert data["first_name"] == "Esteban"
        assert data["category"] == "ACTIVE"
        assert data["membership_status"] == "ENABLED"
        assert data["is_active"] is True
        mock_repo.get_by_id.assert_called_once_with(1001)

    @patch("padron.views.get_padron_repository")
    def test_nonexistent_socio_returns_404(self, mock_get_repo) -> None:
        """Socio inexistente retorna HTTP 404 Not Found."""
        mock_repo = MagicMock()
        mock_repo.get_by_id.return_value = None
        mock_get_repo.return_value = mock_repo

        self.client.force_authenticate(user=_make_dummy_user())
        response = self.client.get("/api/v1/padron/socios/999999/")

        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert "detail" in data


# ==============================================================================
# Endpoint: GET /api/v1/padron/socios/legajo/<str:legajo>/
# ==============================================================================


class TestPadronSocioLegajoDetailView:
    """Pruebas para el endpoint de ficha unívoca de socio por número de legajo UTN."""

    def setup_method(self) -> None:
        self.client = APIClient()
        self.url = "/api/v1/padron/socios/legajo/85421/"

    def test_unauthenticated_request_returns_401(self) -> None:
        """Petición anónima es rechazada con HTTP 401 Unauthorized."""
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @patch("padron.views.get_padron_repository")
    def test_existing_legajo_returns_200_and_canonical_payload(self, mock_get_repo) -> None:
        """Legajo existente retorna HTTP 200 con la estructura canónica."""
        mock_repo = MagicMock()
        mock_repo.get_by_legajo.return_value = _make_sample_socio_dto(socio_id=1001, legajo="85421")
        mock_get_repo.return_value = mock_repo

        self.client.force_authenticate(user=_make_dummy_user())
        response = self.client.get(self.url)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["socio_id"] == 1001
        assert data["legajo"] == "85421"
        assert data["first_name"] == "Esteban"
        mock_repo.get_by_legajo.assert_called_once_with("85421")

    @patch("padron.views.get_padron_repository")
    def test_nonexistent_legajo_returns_404(self, mock_get_repo) -> None:
        """Legajo inexistente retorna HTTP 404 Not Found."""
        mock_repo = MagicMock()
        mock_repo.get_by_legajo.return_value = None
        mock_get_repo.return_value = mock_repo

        self.client.force_authenticate(user=_make_dummy_user())
        response = self.client.get("/api/v1/padron/socios/legajo/000000/")

        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert "detail" in data


# ==============================================================================
# Endpoint: GET /api/v1/padron/subcomisiones/ (CA1, H03, MED-IT2-001)
# ==============================================================================


class TestPadronSubcomisionListView:
    """Pruebas para el endpoint de catálogo institucional de subcomisiones."""

    def setup_method(self) -> None:
        self.client = APIClient()
        self.url = "/api/v1/padron/subcomisiones/"

    def test_unauthenticated_request_returns_401(self) -> None:
        """Petición anónima es rechazada con HTTP 401 Unauthorized."""
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @patch("padron.views.get_padron_repository")
    def test_authenticated_returns_200_and_subcomisiones_list(self, mock_get_repo) -> None:
        """Petición autenticada retorna HTTP 200 con la nómina de subcomisiones."""
        subcomisiones = [
            SubcomisionDTO(id=1, name="Cómputos"),
            SubcomisionDTO(id=10, name="Tribunal de Disciplina"),
        ]
        mock_repo = MagicMock()
        mock_repo.list_subcomisiones.return_value = subcomisiones
        mock_get_repo.return_value = mock_repo

        self.client.force_authenticate(user=_make_dummy_user())
        response = self.client.get(self.url)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2
        assert data[0] == {"id": 1, "name": "Cómputos"}
        assert data[1] == {"id": 10, "name": "Tribunal de Disciplina"}
        mock_repo.list_subcomisiones.assert_called_once()

    @patch("padron.views.get_padron_repository")
    def test_subcomisiones_excludes_sentinel_99(self, mock_get_repo) -> None:
        """Verifica que ninguna subcomisión tenga id=99 ni nombre 'Sin Subcomisión'."""
        subcomisiones = [
            SubcomisionDTO(id=1, name="Cómputos"),
            SubcomisionDTO(id=2, name="Recursos Humanos"),
        ]
        mock_repo = MagicMock()
        mock_repo.list_subcomisiones.return_value = subcomisiones
        mock_get_repo.return_value = mock_repo

        self.client.force_authenticate(user=_make_dummy_user())
        response = self.client.get(self.url)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        for item in data:
            assert item["id"] != 99
            assert item["name"] != "Sin Subcomisión"

    @patch("padron.views.get_padron_repository")
    def test_subcomisiones_alphabetical_order(self, mock_get_repo) -> None:
        """Verifica que la nómina de subcomisiones esté ordenada alfabéticamente por nombre."""
        subcomisiones = [
            SubcomisionDTO(id=1, name="Cómputos"),
            SubcomisionDTO(id=7, name="Eventos"),
            SubcomisionDTO(id=2, name="Recursos Humanos"),
            SubcomisionDTO(id=10, name="Tribunal de Disciplina"),
        ]
        mock_repo = MagicMock()
        mock_repo.list_subcomisiones.return_value = subcomisiones
        mock_get_repo.return_value = mock_repo

        self.client.force_authenticate(user=_make_dummy_user())
        response = self.client.get(self.url)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        names = [item["name"] for item in data]
        assert names == sorted(names)


# ==============================================================================
# Endpoint: GET /api/v1/padron/socios/ (CA1, CA3, CA4, HIGH-004, MED-001)
# ==============================================================================


class TestPadronSocioListView:
    """Pruebas para el endpoint de listado paginado y búsqueda de socios."""

    def setup_method(self) -> None:
        self.client = APIClient()
        self.url = "/api/v1/padron/socios/"

    def test_unauthenticated_request_returns_401(self) -> None:
        """Petición anónima es rechazada con HTTP 401 Unauthorized."""
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @patch("padron.views.get_padron_repository")
    def test_valid_request_returns_200_and_paginated_structure(self, mock_get_repo) -> None:
        """Petición válida retorna HTTP 200 con la estructura canónica count y results."""
        from padron.domain import PaginatedSociosDTO

        socio_dto = _make_sample_socio_dto(socio_id=1001)
        paginated_dto = PaginatedSociosDTO(
            count=1,
            results=[socio_dto],
            page=1,
            page_size=20,
        )
        mock_repo = MagicMock()
        mock_repo.list_socios.return_value = paginated_dto
        mock_get_repo.return_value = mock_repo

        self.client.force_authenticate(user=_make_dummy_user())
        response = self.client.get(self.url)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "count" in data
        assert "page" in data
        assert "page_size" in data
        assert "results" in data
        assert data["count"] == 1
        assert len(data["results"]) == 1
        assert data["results"][0]["socio_id"] == 1001

    def test_invalid_query_params_returns_400(self) -> None:
        """Query parameters inválidos (categoría espuria o página negativa) retornan HTTP 400."""
        self.client.force_authenticate(user=_make_dummy_user())

        response = self.client.get(f"{self.url}?category=CATEGORIA_INVALIDA")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "category" in response.json()

        response_page = self.client.get(f"{self.url}?page=0")
        assert response_page.status_code == status.HTTP_400_BAD_REQUEST
        assert "page" in response_page.json()

    @patch("padron.views.get_padron_repository")
    def test_filters_passed_to_repository(self, mock_get_repo) -> None:
        """Parámetros de consulta válidos se tipifican y transmiten al repositorio."""
        from padron.domain import PaginatedSociosDTO

        paginated_dto = PaginatedSociosDTO(count=0, results=[], page=2, page_size=10)
        mock_repo = MagicMock()
        mock_repo.list_socios.return_value = paginated_dto
        mock_get_repo.return_value = mock_repo

        self.client.force_authenticate(user=_make_dummy_user())
        params = {
            "search": "Gómez",
            "subcomision_id": 1,
            "category": "PASSIVE",
            "is_active": "true",
            "membership_status": "ENABLED",
            "page": 2,
            "page_size": 10,
        }
        response = self.client.get(self.url, params)

        assert response.status_code == status.HTTP_200_OK
        mock_repo.list_socios.assert_called_once_with(
            search="Gómez",
            subcomision_id=1,
            category=SocioCategoryEnum.PASSIVE,
            is_active=True,
            membership_status=MembershipStatusEnum.ENABLED,
            page=2,
            page_size=10,
        )
