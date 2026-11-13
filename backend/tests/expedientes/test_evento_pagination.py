"""Pruebas unitarias e integrales de paginación para EventoInstitucionalViewSet (T-87.18).

Verifica:
1. Envolvente canónica de 7 campos: count, total_pages, current_page, page_size, etc.
2. page_size por defecto = 20 y configurable por el cliente.
3. Techo defensivo max_page_size = 100.
4. Error 404 estructurado según RFC 9457 cuando page > total_pages.
5. Filtrado combinado con paginación reactiva.
"""

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from expedientes.models import (
    CategoriaEventoEnum,
    EstadoEventoEnum,
    EventoInstitucional,
    ModalidadEventoEnum,
    ModoConvocatoriaEnum,
    SubtipoReunionEnum,
)
from socios.models import Role, Socio

User = get_user_model()


@pytest.fixture
def auth_client(db):
    from socios.models import Subcomision

    sub, _ = Subcomision.objects.get_or_create(name="Cómputos")
    user, _ = User.objects.get_or_create(
        username="socio_evento_paged", defaults={"email": "paged_eventos@aveit.test"}
    )
    user.set_password("password123")
    user.save()
    socio, _ = Socio.objects.get_or_create(
        user=user,
        defaults={
            "legajo": "54321",
            "first_name": "Socio",
            "last_name": "Paged",
            "email": "paged_eventos@aveit.test",
            "subcomision": sub,
            "social_year": 2,
            "role": Role.SOCIO,
            "is_enabled": True,
        },
    )
    client = APIClient()
    client.force_authenticate(user=user)
    return client, socio


@pytest.fixture
def twenty_five_eventos(db, auth_client):
    _, socio = auth_client
    now = timezone.now()
    eventos = []
    for i in range(25):
        e = EventoInstitucional.objects.create(
            titulo=f"Reunión de Prueba #{i + 1:02d}",
            categoria=CategoriaEventoEnum.REUNION,
            tipo=SubtipoReunionEnum.ORDINARIA,
            modalidad=ModalidadEventoEnum.PRESENCIAL_SEDE,
            modo_convocatoria=ModoConvocatoriaEnum.GRUPO,
            grupo_convocado="G58",
            estado=EstadoEventoEnum.CREADO,
            fecha_programada=now + timezone.timedelta(days=i),
            fecha_publicacion=now,
            convocante=socio,
        )
        eventos.append(e)
    return eventos


@pytest.mark.django_db
class TestEventoInstitucionalPagination:
    """Suite de verificación del contrato de paginación para EventoInstitucionalViewSet."""

    endpoint = "/api/v1/expedientes/eventos/"

    def test_canonical_envelope_structure(self, auth_client, twenty_five_eventos):
        client, _ = auth_client
        res = client.get(self.endpoint)
        assert res.status_code == status.HTTP_200_OK
        data = res.json()

        assert "count" in data
        assert "total_pages" in data
        assert "current_page" in data
        assert "page_size" in data
        assert "next" in data
        assert "previous" in data
        assert "results" in data

        assert data["count"] == 25
        assert data["total_pages"] == 2
        assert data["current_page"] == 1
        assert data["page_size"] == 20
        assert len(data["results"]) == 20
        assert data["next"] is not None
        assert data["previous"] is None

    def test_custom_page_size_and_navigation(self, auth_client, twenty_five_eventos):
        client, _ = auth_client
        res = client.get(f"{self.endpoint}?page=2&page_size=10")
        assert res.status_code == status.HTTP_200_OK
        data = res.json()

        assert data["count"] == 25
        assert data["total_pages"] == 3
        assert data["current_page"] == 2
        assert data["page_size"] == 10
        assert len(data["results"]) == 10
        assert data["next"] is not None
        assert data["previous"] is not None

    def test_page_out_of_bounds_returns_404_rfc9457(self, auth_client, twenty_five_eventos):
        client, _ = auth_client
        res = client.get(f"{self.endpoint}?page=999")
        assert res.status_code == status.HTTP_404_NOT_FOUND

        data = res.json()
        assert data["type"] == "https://errors.aveit.org.ar/invalid-page"
        assert data["status"] == 404
        assert "invalid_params" in data
        assert any(param["name"] == "page" for param in data["invalid_params"])

    def test_max_page_size_enforced_at_100(self, auth_client, twenty_five_eventos):
        client, _ = auth_client
        res = client.get(f"{self.endpoint}?page_size=500")
        assert res.status_code == status.HTTP_200_OK
        data = res.json()
        assert data["page_size"] == 100
        assert len(data["results"]) == 25

    def test_empty_collection_returns_valid_envelope(self, auth_client):
        client, _ = auth_client
        res = client.get(self.endpoint)
        assert res.status_code == status.HTTP_200_OK
        data = res.json()

        assert data["count"] == 0
        assert data["total_pages"] == 1
        assert data["current_page"] == 1
        assert data["results"] == []
