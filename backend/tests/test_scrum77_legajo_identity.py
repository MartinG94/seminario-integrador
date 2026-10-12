"""TS77.43: selección de namespace y propiedad institucional verificables."""

from collections.abc import Iterator
from datetime import date
from typing import Any

import pytest
from django.db import connection
from rest_framework.test import APIClient

from padron.adapters import DatabasePadronAdapter
from padron.models import (
    Socio as InstitutionalSocio,
)
from padron.models import (
    SocioEmail,
    SocioEstadoHistorial,
    SocioEstudio,
)
from padron.models import (
    Subcomision as InstitutionalSubcomision,
)
from socios.models import Role, Socio
from tests.legacy_schema import create_legacy_record


@pytest.fixture(scope="session", autouse=True)
def identity_satellite_tables(django_db_setup: Any, django_db_blocker: Any) -> Iterator[None]:
    created = []
    with django_db_blocker.unblock():
        existing = set(connection.introspection.table_names())
        with connection.schema_editor() as editor:
            for model in (SocioEmail, SocioEstadoHistorial):
                if model._meta.db_table not in existing:
                    editor.create_model(model)
                    created.append(model)
                    existing.add(model._meta.db_table)
    yield
    with django_db_blocker.unblock():
        with connection.schema_editor() as editor:
            for model in reversed(created):
                if model._meta.db_table in connection.introspection.table_names():
                    editor.delete_model(model)


@pytest.fixture
def identity_world(make_socio: Any, monkeypatch: Any) -> dict[str, Any]:
    from socios import views

    local = make_socio(legajo="8843001", social_year=2)
    other = make_socio(legajo="8843002", social_year=4)
    authority = make_socio(legajo="8843003", role=Role.TD, social_year=6)
    sub = create_legacy_record(InstitutionalSubcomision, codSubcomision=8843, nombre="Cómputos")
    repo = DatabasePadronAdapter()
    monkeypatch.setattr(views, "get_padron_repository", lambda: repo)

    def institutional(
        number: int,
        *,
        legajo: int | None = 9843001,
        user_id: int | None = None,
        year: int | None = 4,
        email: str | None = None,
    ) -> InstitutionalSocio:
        member = InstitutionalSocio(
            nroSocio=number,
            nombre="Ficha institucional",
            apellido=f"Referencia {number}",
            fechaIngreso=date(2024, 1, 1),
            fechaNac=date(2000, 1, 1),
            codTipoDoc=1,
            nroDoc=90000000 + number % 1000000,
            codSexo=1,
            subcomision=sub,
            anoSocial=year,
            idTipoSocio=12,
            user_id=user_id,
        )
        member._allow_write = True
        member.save(force_insert=True)
        if legajo is not None:
            create_legacy_record(
                SocioEstudio,
                compositeKey=number * 10,
                socio=member,
                nroLegajo=legajo,
                codEspecialidad=1,
            )
        if email is not None:
            create_legacy_record(
                SocioEmail,
                compositeKey=number * 10 + 1,
                socio=member,
                idEmail=1,
                email=email,
                comprobado=True,
                habilitado=True,
            )
        return member

    return {"local": local, "other": other, "authority": authority, "create": institutional}


def request_legajo(socio: Socio | None, number: int | str, source: str | None = None) -> Any:
    client = APIClient()
    if socio is not None:
        client.force_authenticate(socio.user)
    params = {} if source is None else {"identity_source": source}
    return client.get(f"/api/v1/socios/{number}/legajo/", params)


@pytest.mark.django_db
def test_explicit_institutional_source_never_uses_a_colliding_local_pk(
    identity_world: dict,
) -> None:
    local = identity_world["local"]
    member = identity_world["create"](local.pk)
    response = request_legajo(identity_world["authority"], member.pk, "institutional")
    assert response.status_code == 200
    assert response.data["first_name"] == member.nombre
    assert response.data["legajo"] == "9843001"
    assert response.data["category"] == "SENIOR"


@pytest.mark.django_db
def test_explicit_local_source_does_not_query_the_institutional_repository(
    identity_world: dict, monkeypatch: Any
) -> None:
    from socios import views

    local = identity_world["local"]
    identity_world["create"](local.pk)

    def unexpected_repository() -> None:
        pytest.fail("La fuente local consultó otro namespace.")

    monkeypatch.setattr(views, "get_padron_repository", unexpected_repository)
    response = request_legajo(local, local.pk, "local")
    assert response.status_code == 200
    assert response.data["first_name"] == local.first_name


@pytest.mark.django_db
def test_unspecified_source_rejects_different_people_with_a_generic_404(
    identity_world: dict,
) -> None:
    local = identity_world["local"]
    identity_world["create"](local.pk)
    ambiguous = request_legajo(identity_world["authority"], local.pk)
    absent = request_legajo(identity_world["authority"], 1999999999)
    assert ambiguous.status_code == absent.status_code == 404
    assert ambiguous.data == absent.data
    assert set(ambiguous.data) == {"detail"}


@pytest.mark.django_db
@pytest.mark.parametrize("source", ["", "legacy", "INSTITUTIONAL", "institutional ", "managed"])
def test_invalid_source_returns_400_even_for_an_existing_member(
    identity_world: dict, source: str
) -> None:
    response = request_legajo(identity_world["authority"], identity_world["local"].pk, source)
    assert response.status_code == 400
    assert "identity_source" in response.data


@pytest.mark.django_db
def test_repeated_identity_source_is_rejected(identity_world: dict) -> None:
    client = APIClient()
    client.force_authenticate(identity_world["authority"].user)
    response = client.get(
        f"/api/v1/socios/{identity_world['local'].pk}/legajo/?identity_source=local&identity_source=institutional"
    )
    assert response.status_code == 400


@pytest.mark.django_db
@pytest.mark.parametrize("source", ["local", "institutional"])
def test_explicit_source_has_no_fallback_when_its_record_is_missing(
    identity_world: dict, source: str
) -> None:
    if source == "institutional":
        number = identity_world["local"].pk
    else:
        number = identity_world["create"](9430001).pk
    response = request_legajo(identity_world["authority"], number, source)
    assert response.status_code == 404


@pytest.mark.django_db
@pytest.mark.parametrize("by_legajo", [False, True])
def test_old_unambiguous_local_calls_still_work(identity_world: dict, by_legajo: bool) -> None:
    local = identity_world["local"]
    response = request_legajo(local, local.legajo if by_legajo else local.pk)
    assert response.status_code == 200
    assert response.data["id"] == local.pk


@pytest.mark.django_db
@pytest.mark.parametrize("by_legajo", [False, True])
def test_old_unambiguous_institutional_calls_still_work(
    identity_world: dict, by_legajo: bool
) -> None:
    member = identity_world["create"](9430001)
    response = request_legajo(identity_world["authority"], 9843001 if by_legajo else member.pk)
    assert response.status_code == 200
    assert response.data["id"] == member.pk


@pytest.mark.django_db
def test_a_confirmed_link_does_not_make_the_same_person_ambiguous(identity_world: dict) -> None:
    local = identity_world["local"]
    identity_world["create"](local.pk, user_id=local.user_id)
    response = request_legajo(local, local.pk)
    assert response.status_code == 200
    assert response.data["id"] == local.pk
    assert response.data["legajo"] == local.legajo


@pytest.mark.django_db
def test_real_institutional_user_link_proves_ownership_with_different_ids_and_no_legajo(
    identity_world: dict,
) -> None:
    local = identity_world["local"]
    member = identity_world["create"](9430001, legajo=None, user_id=local.user_id)
    response = request_legajo(local, member.pk, "institutional")
    assert response.status_code == 200
    assert response.data["id"] != local.pk
    assert response.data["legajo"] is None


@pytest.mark.django_db
def test_a_real_unique_academic_legajo_proves_ownership_without_a_user_link(
    identity_world: dict,
) -> None:
    local = identity_world["local"]
    member = identity_world["create"](9430001, legajo=int(local.legajo))
    response = request_legajo(local, member.pk, "institutional")
    assert response.status_code == 200
    assert response.data["id"] == member.pk


@pytest.mark.django_db
def test_multiple_courses_of_the_same_person_do_not_create_false_ambiguity(
    identity_world: dict,
) -> None:
    local = identity_world["local"]
    member = identity_world["create"](9430001, legajo=int(local.legajo))
    create_legacy_record(
        SocioEstudio,
        compositeKey=94300011,
        socio=member,
        nroLegajo=int(local.legajo),
        codEspecialidad=1,
    )
    response = request_legajo(local, member.pk, "institutional")
    assert response.status_code == 200


@pytest.mark.django_db
def test_academic_legajo_shared_by_two_institutional_people_does_not_prove_ownership(
    identity_world: dict,
) -> None:
    local = identity_world["local"]
    member = identity_world["create"](9430001, legajo=int(local.legajo))
    identity_world["create"](9430002, legajo=int(local.legajo))
    response = request_legajo(local, member.pk, "institutional")
    assert response.status_code == 403


@pytest.mark.django_db
def test_a_user_link_to_someone_else_overrides_a_matching_academic_legajo(
    identity_world: dict,
) -> None:
    local = identity_world["local"]
    other = identity_world["other"]
    member = identity_world["create"](9430001, legajo=int(local.legajo), user_id=other.user_id)
    assert request_legajo(local, member.pk, "institutional").status_code == 403
    assert request_legajo(other, member.pk, "institutional").status_code == 200


@pytest.mark.django_db
def test_a_user_link_shared_by_two_institutional_people_is_not_confirmed(
    identity_world: dict,
) -> None:
    local = identity_world["local"]
    member = identity_world["create"](9430001, legajo=None, user_id=local.user_id)
    identity_world["create"](9430002, legajo=None, user_id=local.user_id)
    assert request_legajo(local, member.pk, "institutional").status_code == 403


@pytest.mark.django_db
def test_a_missing_real_legajo_never_uses_the_institutional_number_as_owner(
    identity_world: dict,
) -> None:
    local = identity_world["local"]
    member = identity_world["create"](int(local.legajo), legajo=None)
    assert request_legajo(local, member.pk, "institutional").status_code == 403
    response = request_legajo(identity_world["authority"], member.pk, "institutional")
    assert response.status_code == 200
    assert response.data["legajo"] is None


@pytest.mark.django_db
def test_matching_email_alone_never_supplies_role_or_ownership(identity_world: dict) -> None:
    authority = identity_world["authority"]
    member = identity_world["create"](9430001, legajo=None, email=authority.email)
    response = request_legajo(authority, member.pk, "institutional")
    assert response.status_code == 200
    assert response.data["role"] == Role.SOCIO
    authority.role = Role.SOCIO
    authority.save(update_fields=["role"])
    assert request_legajo(authority, member.pk, "institutional").status_code == 403


@pytest.mark.django_db
@pytest.mark.parametrize("role", [Role.TD, Role.CD, Role.ADMIN])
def test_enabled_authorities_keep_their_existing_access(identity_world: dict, role: str) -> None:
    authority = identity_world["authority"]
    authority.role = role
    authority.save(update_fields=["role"])
    member = identity_world["create"](9430001, legajo=None)
    assert request_legajo(authority, member.pk, "institutional").status_code == 200


@pytest.mark.django_db
def test_disabled_authority_and_anonymous_clients_cannot_read(identity_world: dict) -> None:
    authority = identity_world["authority"]
    authority.is_enabled = False
    authority.save(update_fields=["is_enabled"])
    member = identity_world["create"](9430001)
    assert request_legajo(authority, member.pk, "institutional").status_code == 403
    assert request_legajo(None, member.pk, "institutional").status_code == 401


@pytest.mark.django_db
def test_reading_the_institutional_legajo_preserves_all_existing_rows(identity_world: dict) -> None:
    local = identity_world["local"]
    member = identity_world["create"](9430001, user_id=local.user_id, legajo=None)
    before_local = list(Socio.objects.values())
    before_member = list(InstitutionalSocio.objects.values())
    before_users = list(type(local.user).objects.values())
    response = request_legajo(local, member.pk, "institutional")
    assert response.status_code == 200
    assert list(Socio.objects.values()) == before_local
    assert list(InstitutionalSocio.objects.values()) == before_member
    assert list(type(local.user).objects.values()) == before_users


@pytest.mark.django_db
def test_repository_failure_cannot_choose_an_unverified_local_candidate(
    identity_world: dict, monkeypatch: Any, caplog: Any
) -> None:
    from socios import views

    class BrokenRepository:
        def get_by_id(self, number: int) -> None:
            raise RuntimeError("sensitive-test-diagnostic")

    monkeypatch.setattr(views, "get_padron_repository", lambda: BrokenRepository())
    local = identity_world["local"]
    response = request_legajo(identity_world["authority"], local.pk)
    assert response.status_code == 404
    assert "sensitive-test-diagnostic" not in str(response.data)
    assert "sensitive-test-diagnostic" not in caplog.text


@pytest.mark.django_db
def test_explicit_institutional_id_never_falls_back_to_an_academic_number(
    identity_world: dict,
) -> None:
    identity_world["create"](9430001, legajo=9430002)
    response = request_legajo(identity_world["authority"], 9430002, "institutional")
    assert response.status_code == 404


@pytest.mark.django_db
def test_explicit_local_id_never_falls_back_to_a_local_academic_number(
    identity_world: dict,
) -> None:
    local = identity_world["local"]
    response = request_legajo(identity_world["authority"], local.legajo, "local")
    assert response.status_code == 404


@pytest.mark.django_db
def test_old_call_with_different_local_pk_and_legajo_candidates_is_ambiguous(
    identity_world: dict, make_socio: Any
) -> None:
    local = identity_world["local"]
    make_socio(legajo=str(local.pk), social_year=4)
    response = request_legajo(identity_world["authority"], local.pk)
    assert response.status_code == 404
