import time

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from socios.models import Role, Socio, Subcomision

UserModel = get_user_model()


@pytest.fixture
def test_setup(db):
    """Fixture de entorno con subcomisiones y usuarios de distintos roles."""
    sub_computos = Subcomision.objects.create(name="Cómputos")
    sub_rrhh = Subcomision.objects.create(name="Recursos Humanos")
    sub_rrpp = Subcomision.objects.create(name="Relaciones Públicas")

    def _create_socio(
        legajo: str,
        first_name: str,
        last_name: str,
        role: str = Role.SOCIO,
        subcomision: Subcomision = sub_computos,
        social_year: int = 2,
        is_enabled: bool = True,
        email: str | None = None,
    ) -> Socio:
        email = email or f"{legajo}@aveit.test"
        user = UserModel.objects.create_user(
            username=legajo, email=email, password="Aveit-Test-2026!"
        )
        return Socio.objects.create(
            user=user,
            legajo=legajo,
            first_name=first_name,
            last_name=last_name,
            email=email,
            subcomision=subcomision,
            social_year=social_year,
            role=role,
            is_enabled=is_enabled,
        )

    return {
        "create_socio": _create_socio,
        "sub_computos": sub_computos,
        "sub_rrhh": sub_rrhh,
        "sub_rrpp": sub_rrpp,
    }


# ==============================================================================
# CA1: Búsqueda Insensible a Mayúsculas y Tildes
# ==============================================================================


@pytest.mark.django_db
def test_search_by_last_name_and_accent_insensitivity(test_setup, authenticate):
    create = test_setup["create_socio"]
    td_user = create("408917", "Nicolás", "Rosales", role=Role.TD)
    create("1001", "Diego", "Sánchez")
    create("1002", "Lucas", "Gómez")

    client = authenticate(td_user)

    # Búsqueda sin acento debe encontrar registro con tilde ("sanchez" -> "Sánchez")
    res_no_accent = client.get("/api/v1/socios/?search=sanchez")
    assert res_no_accent.status_code == 200
    results = res_no_accent.data["results"]
    assert len(results) == 1
    assert results[0]["last_name"] == "Sánchez"

    # Búsqueda con acento debe encontrar registro con tilde ("Sánchez" -> "Sánchez")
    res_with_accent = client.get("/api/v1/socios/?search=Sánchez")
    assert res_with_accent.status_code == 200
    assert len(res_with_accent.data["results"]) == 1
    assert res_with_accent.data["results"][0]["last_name"] == "Sánchez"

    # Búsqueda case-insensitive ("DIEGO" -> "Diego")
    res_upper = client.get("/api/v1/socios/?search=DIEGO")
    assert res_upper.status_code == 200
    assert len(res_upper.data["results"]) == 1
    assert res_upper.data["results"][0]["first_name"] == "Diego"


@pytest.mark.django_db
def test_search_by_legajo(test_setup, authenticate):
    create = test_setup["create_socio"]
    td_user = create("408917", "Nicolás", "Rosales", role=Role.TD)
    create("74907", "Lucas", "Gastiaburu")
    create("85194", "Lucas", "Guillén")

    client = authenticate(td_user)
    res = client.get("/api/v1/socios/?search=74907")
    assert res.status_code == 200
    results = res.data["results"]
    assert len(results) == 1
    assert results[0]["legajo"] == "74907"


@pytest.mark.django_db
def test_search_by_subcomision(test_setup, authenticate):
    create = test_setup["create_socio"]
    td_user = create("408917", "Nicolás", "Rosales", role=Role.TD)
    create("74907", "Lucas", "Gastiaburu", subcomision=test_setup["sub_computos"])
    create("85194", "Camila", "López", subcomision=test_setup["sub_rrhh"])
    socio_rrpp = create("85195", "Esteban", "Domínguez", subcomision=test_setup["sub_rrpp"])

    client = authenticate(td_user)
    # Búsqueda insensible a tildes y mayúsculas en subcomisión: "computos" -> "Cómputos"
    res = client.get("/api/v1/socios/?search=computos")
    assert res.status_code == 200
    results = res.data["results"]
    assert len(results) == 2  # td_user ("Cómputos") + Lucas ("Cómputos")
    assert all(r["subcomision"] == "Cómputos" for r in results)

    # Búsqueda sin tilde ("publicas") debe encontrar subcomisión con tilde ("Relaciones Públicas")
    res_publicas = client.get("/api/v1/socios/?search=publicas")
    assert res_publicas.status_code == 200
    assert len(res_publicas.data["results"]) == 1
    assert res_publicas.data["results"][0]["id"] == socio_rrpp.pk
    assert res_publicas.data["results"][0]["subcomision"] == "Relaciones Públicas"


@pytest.mark.django_db
def test_search_without_matches_returns_empty_paginated_list(test_setup, authenticate):
    create = test_setup["create_socio"]
    td_user = create("408917", "Nicolás", "Rosales", role=Role.TD)
    create("74907", "Lucas", "Gastiaburu")

    client = authenticate(td_user)
    res = client.get("/api/v1/socios/?search=InexistenteTotal2026")
    assert res.status_code == 200
    assert res.data["count"] == 0
    assert res.data["results"] == []


# ==============================================================================
# CA2: Detalle de Legajo
# ==============================================================================


@pytest.mark.django_db
def test_legajo_detail_returns_expected_fields_and_exact_legajo(test_setup, authenticate):
    create = test_setup["create_socio"]
    td_user = create("408917", "Nicolás", "Rosales", role=Role.TD)
    socio = create("74907", "Lucas", "Gastiaburu", social_year=5)

    client = authenticate(td_user)
    res = client.get(f"/api/v1/socios/{socio.pk}/legajo/")

    assert res.status_code == 200
    data = res.data
    assert data["id"] == socio.pk
    assert data["legajo"] == "74907"
    assert data["legajo"] == socio.legajo
    assert data["first_name"] == "Lucas"
    assert data["last_name"] == "Gastiaburu"
    assert data["email"] == "74907@aveit.test"
    assert data["role"] == Role.SOCIO
    assert data["category"] == "ACTIVE"
    assert data["category_display"] == "Activo"
    assert data["subcomision_name"] == "Cómputos"
    assert data["social_year"] == 5
    assert data["is_enabled"] is True
    assert data["points_balance"] == 0.0


# ==============================================================================
# CA3: Paginación y Prevención de N+1
# ==============================================================================


@pytest.mark.django_db
def test_padron_pagination_format_and_page_size(test_setup, authenticate):
    create = test_setup["create_socio"]
    td_user = create("408917", "Nicolás", "Rosales", role=Role.TD)

    # Creamos 25 socios (más que el page_size por defecto = 20)
    for i in range(25):
        create(f"800{i:02d}", f"Socio{i}", f"Prueba{i}")

    client = authenticate(td_user)
    res = client.get("/api/v1/socios/")

    assert res.status_code == 200
    assert "count" in res.data
    assert "next" in res.data
    assert "previous" in res.data
    assert "results" in res.data
    assert res.data["count"] == 26  # 25 creados + td_user
    assert len(res.data["results"]) == 20
    assert res.data["next"] is not None
    assert res.data["previous"] is None


@pytest.mark.django_db
def test_padron_query_count_prevents_n_plus_one(
    test_setup, authenticate, django_assert_num_queries
):
    create = test_setup["create_socio"]
    td_user = create("408917", "Nicolás", "Rosales", role=Role.TD)
    for i in range(15):
        create(f"900{i:02d}", f"Nombre{i}", f"Apellido{i}")

    client = authenticate(td_user)

    # select_related("subcomision") mantiene queries O(1) independiente del número de socios:
    # 1. User auth (SimpleJWT)
    # 2. Socio auth & role lookup (HasAnyRole)
    # 3. Count query para paginación
    # 4. Fetch query con join/select_related a subcomisión
    with django_assert_num_queries(4):
        res = client.get("/api/v1/socios/")
        assert res.status_code == 200
        assert len(res.data["results"]) == 16


# ==============================================================================
# CA4: RBAC en Detalle de Legajo
# ==============================================================================


@pytest.mark.parametrize("role", [Role.TD, Role.CD, Role.ADMIN])
@pytest.mark.django_db
def test_authorized_authorities_can_view_any_legajo(test_setup, authenticate, role):
    create = test_setup["create_socio"]
    authority = create(f"100{role}", "Autoridad", "Prueba", role=role)
    otro_socio = create("74907", "Lucas", "Gastiaburu", role=Role.SOCIO)

    client = authenticate(authority)
    res = client.get(f"/api/v1/socios/{otro_socio.pk}/legajo/")
    assert res.status_code == 200
    assert res.data["legajo"] == "74907"


@pytest.mark.django_db
def test_socio_can_view_own_legajo(test_setup, authenticate):
    create = test_setup["create_socio"]
    socio = create("74907", "Lucas", "Gastiaburu", role=Role.SOCIO)

    client = authenticate(socio)
    res = client.get(f"/api/v1/socios/{socio.pk}/legajo/")
    assert res.status_code == 200
    assert res.data["legajo"] == "74907"


@pytest.mark.django_db
def test_socio_cannot_view_other_socio_legajo_returns_403(test_setup, authenticate):
    create = test_setup["create_socio"]
    socio_a = create("74907", "Lucas", "Gastiaburu", role=Role.SOCIO)
    socio_b = create("85194", "Axel", "Villegas", role=Role.SOCIO)

    client = authenticate(socio_a)
    res = client.get(f"/api/v1/socios/{socio_b.pk}/legajo/")
    assert res.status_code == 403
    assert res.data["detail"] == "No posee autorización para acceder a este legajo."


@pytest.mark.django_db
def test_unauthenticated_user_cannot_access_legajo_detail_returns_401(test_setup):
    create = test_setup["create_socio"]
    socio = create("74907", "Lucas", "Gastiaburu", role=Role.SOCIO)

    anonymous_client = APIClient()
    res = anonymous_client.get(f"/api/v1/socios/{socio.pk}/legajo/")
    assert res.status_code == 401


# ==============================================================================
# Performance: Respuesta bajo 500 ms (RNF-01)
# ==============================================================================


@pytest.mark.django_db
def test_search_response_time_under_500ms(test_setup, authenticate):
    create = test_setup["create_socio"]
    td_user = create("408917", "Nicolás", "Rosales", role=Role.TD)
    for i in range(30):
        create(f"700{i:02d}", f"Socio{i}", f"Apellido{i}")

    client = authenticate(td_user)

    start = time.perf_counter()
    res = client.get("/api/v1/socios/?search=socio")
    elapsed_ms = (time.perf_counter() - start) * 1000

    assert res.status_code == 200
    assert elapsed_ms < 500.0, f"Búsqueda demoró {elapsed_ms:.2f}ms, esperado < 500ms"
