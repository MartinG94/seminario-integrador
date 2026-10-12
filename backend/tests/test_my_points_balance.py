"""RF77-15: saldo propio aplicado, identidad acreditada y lectura inmutable."""

from dataclasses import replace
from datetime import date
from decimal import Decimal
from typing import Any

import pytest
from django.contrib.auth import get_user_model
from django.db import DatabaseError, connection
from django.test.utils import CaptureQueriesContext
from rest_framework.test import APIClient

from expedientes.models import EstadoExpedienteEnum, Expediente
from padron.adapters import DatabasePadronAdapter
from padron.models import Socio as InstitutionalSocio
from padron.models import SocioEstudio
from padron.models import Subcomision as InstitutionalSubcomision
from ranking.models import PuntajeAplicado, PuntajeGeneral
from socios.institutional_conditions import register_ex_traveler
from socios.models import Role, SocialCategory, Socio
from tests.legacy_schema import create_legacy_record
from tests.test_scrum77_legajo_identity import (
    identity_satellite_tables as identity_satellite_tables,
)

BALANCE_URL = "/api/v1/socios/me/points-balance/"


@pytest.fixture
def balance_world(make_socio: Any, monkeypatch: Any) -> dict[str, Any]:
    from socios import views

    local = make_socio(legajo="99077001", social_year=4)
    other = make_socio(legajo="99077002", social_year=2)
    sub = create_legacy_record(InstitutionalSubcomision, codSubcomision=7748, nombre="Cómputos")
    repository = DatabasePadronAdapter()
    monkeypatch.setattr(views, "get_padron_repository", lambda: repository)

    def member(
        number: int,
        *,
        user_id: int | None = None,
        academic_number: int | None = None,
        social_year: int | None = 1,
    ) -> InstitutionalSocio:
        record = InstitutionalSocio(
            nroSocio=number,
            nombre=local.first_name,
            apellido=local.last_name,
            subcomision=sub,
            user_id=user_id,
            fechaIngreso=date(2024, 1, 1),
            fechaNac=date(2000, 1, 1),
            codTipoDoc=1,
            nroDoc=77480000 + number % 1000000,
            codSexo=1,
            anoSocial=social_year,
            idTipoSocio=12,
        )
        record._allow_write = True
        record.save(force_insert=True)
        if academic_number is not None:
            create_legacy_record(
                SocioEstudio,
                compositeKey=number * 10,
                socio=record,
                nroLegajo=academic_number,
                codEspecialidad=1,
            )
        return record

    return {
        "local": local,
        "other": other,
        "member": member,
        "repository": repository,
    }


def own_balance(socio: Socio | None, params: dict[str, str] | None = None) -> Any:
    client = APIClient()
    if socio is not None:
        client.force_authenticate(socio.user)
    return client.get(BALANCE_URL, params or {})


def legajo_balance(socio: Socio, identifier: int, source: str) -> Any:
    client = APIClient()
    client.force_authenticate(socio.user)
    return client.get(f"/api/v1/socios/{identifier}/legajo/", {"identity_source": source})


@pytest.mark.django_db
@pytest.mark.parametrize("movements", [(3, -1), (-2, -1), ()])
def test_own_balance_matches_ranking_and_ignores_cache_pending_and_other_recipients(
    balance_world: dict[str, Any], movements: tuple[int, ...]
) -> None:
    local = balance_world["local"]
    member = balance_world["member"](770001, user_id=local.user_id, academic_number=99077001)
    other_member = balance_world["member"](770002, user_id=balance_world["other"].user_id)
    for points in movements:
        create_legacy_record(
            PuntajeAplicado, socio=member, puntajeAplicado=Decimal(points), expediente_id=774801
        )
    create_legacy_record(
        PuntajeAplicado, socio=other_member, puntajeAplicado=Decimal(20), expediente_id=774801
    )
    create_legacy_record(PuntajeGeneral, socio=member, puntos=Decimal(99))
    for index, points in enumerate((-1, -3, -2)):
        case = Expediente.objects.create(
            numero=f"TEST-7748-{index}",
            socio=local,
            motivo="Pedido pendiente que no altera el libro mayor.",
            puntos=points,
            estado=EstadoExpedienteEnum.CREADO,
        )
        case.socios.add(local, balance_world["other"])
    response = own_balance(local)
    assert response.status_code == 200
    assert set(response.json()) == {"points_balance"}
    assert isinstance(response.json()["points_balance"], (int, float))
    expected = sum((Decimal(value) for value in movements), Decimal(0))
    assert Decimal(str(response.json()["points_balance"])) == expected
    assert response["Cache-Control"] == "no-store"
    ranking = APIClient().get("/api/v1/ranking/", {"q": "99077001"})
    assert ranking.status_code == 200
    matching_rows = [row for row in ranking.json() if row["id"] == str(member.pk)]
    assert len(matching_rows) == 1
    assert Decimal(str(matching_rows[0]["saldo"])) == expected
    assert Decimal(str(matching_rows[0]["saldoPuntajeGeneral"])) == Decimal(99)


@pytest.mark.django_db
def test_real_user_link_does_not_require_an_academic_number(balance_world: dict[str, Any]) -> None:
    local = balance_world["local"]
    member = balance_world["member"](770001, user_id=local.user_id)
    create_legacy_record(PuntajeAplicado, socio=member, puntajeAplicado=Decimal(2))
    response = own_balance(local)
    assert response.status_code == 200
    assert response.json() == {"points_balance": 2}


@pytest.mark.django_db
@pytest.mark.parametrize("year", [1, 2, 3, 4, 6, None])
def test_balance_is_independent_of_junior_senior_or_confirmed_ex_traveler_category(
    balance_world: dict[str, Any], year: int | None
) -> None:
    local = balance_world["local"]
    local.social_year = year
    if year is None:
        local.category = SocialCategory.EX_TRAVELER
    local.save(update_fields=["social_year", "category"])
    member = balance_world["member"](770001, user_id=local.user_id, social_year=year)
    if year is None:
        register_ex_traveler(
            institutional_member=member,
            source_reference="PO: prueba de saldo independiente de clasificación",
            social_cycle="corte de pruebas TS77.48",
        )
    assert balance_world["repository"].get_by_id(member.pk).category.value == local.category
    create_legacy_record(PuntajeAplicado, socio=member, puntajeAplicado=Decimal(2))
    response = own_balance(local)
    assert response.status_code == 200
    assert response.json() == {"points_balance": 2}


@pytest.mark.django_db
def test_unique_academic_owner_with_multiple_courses_can_read_balance(
    balance_world: dict[str, Any],
) -> None:
    local = balance_world["local"]
    member = balance_world["member"](770001, academic_number=int(local.legajo))
    create_legacy_record(
        SocioEstudio,
        compositeKey=7700011,
        socio=member,
        nroLegajo=int(local.legajo),
        codEspecialidad=2,
    )
    create_legacy_record(PuntajeAplicado, socio=member, puntajeAplicado=Decimal(-2))
    response = own_balance(local)
    assert response.status_code == 200
    assert response.json() == {"points_balance": -2}


@pytest.mark.django_db
@pytest.mark.parametrize("second_account", [False, True])
def test_any_real_unique_academic_number_can_accredit_owner_but_two_accounts_are_ambiguous(
    balance_world: dict[str, Any], make_socio: Any, second_account: bool
) -> None:
    local = balance_world["local"]
    member = balance_world["member"](770001, academic_number=int(local.legajo))
    create_legacy_record(
        SocioEstudio,
        compositeKey=7700011,
        socio=member,
        nroLegajo=99177000,
        codEspecialidad=2,
    )
    create_legacy_record(PuntajeAplicado, socio=member, puntajeAplicado=Decimal(2))
    if second_account:
        make_socio(legajo="99177000")
    response = own_balance(local)
    assert response.status_code == (404 if second_account else 200)
    if not second_account:
        assert response.json() == {"points_balance": 2}
        assert legajo_balance(local, member.pk, "institutional").json()["points_balance"] == 2


@pytest.mark.django_db
@pytest.mark.parametrize("role", list(Role.values))
def test_every_enabled_role_reads_only_its_own_balance_even_with_foreign_parameters(
    balance_world: dict[str, Any], role: str
) -> None:
    local = balance_world["local"]
    local.role = role
    local.save(update_fields=["role"])
    own = balance_world["member"](770001, user_id=local.user_id)
    foreign = balance_world["member"](770002, user_id=balance_world["other"].user_id)
    create_legacy_record(PuntajeAplicado, socio=own, puntajeAplicado=Decimal(2))
    create_legacy_record(PuntajeAplicado, socio=foreign, puntajeAplicado=Decimal(40))
    response = own_balance(local, {"socio_id": "770002", "legajo": "99077002", "id": "770002"})
    assert response.status_code == 200
    assert response.json() == {"points_balance": 2}


@pytest.mark.django_db
@pytest.mark.parametrize("collision", ["pk", "number", "name"])
def test_numeric_or_name_coincidences_never_supply_ownership(
    balance_world: dict[str, Any], collision: str
) -> None:
    local = balance_world["local"]
    number = (
        local.pk if collision == "pk" else int(local.legajo) if collision == "number" else 770001
    )
    member = balance_world["member"](number)
    create_legacy_record(PuntajeAplicado, socio=member, puntajeAplicado=Decimal(70))
    response = own_balance(local)
    assert response.status_code == 404
    assert set(response.json()) == {"detail"}
    assert "points_balance" not in response.json()


@pytest.mark.django_db
@pytest.mark.parametrize("ambiguity", ["user", "academic", "different_owner"])
def test_ambiguous_or_foreign_identity_is_rejected_without_a_false_zero(
    balance_world: dict[str, Any], ambiguity: str
) -> None:
    local = balance_world["local"]
    absent = own_balance(local)
    assert absent.status_code == 404
    if ambiguity == "user":
        balance_world["member"](770001, user_id=local.user_id)
        balance_world["member"](770002, user_id=local.user_id)
    elif ambiguity == "academic":
        balance_world["member"](770001, academic_number=int(local.legajo))
        balance_world["member"](770002, academic_number=int(local.legajo))
    else:
        balance_world["member"](
            770001, user_id=balance_world["other"].user_id, academic_number=int(local.legajo)
        )
    response = own_balance(local)
    assert response.status_code == 404
    assert response.json() == absent.json()
    assert "points_balance" not in response.json()


@pytest.mark.django_db
def test_linked_user_has_priority_over_a_separate_academic_match(
    balance_world: dict[str, Any],
) -> None:
    local = balance_world["local"]
    linked = balance_world["member"](770001, user_id=local.user_id)
    foreign = balance_world["member"](770002, academic_number=int(local.legajo))
    create_legacy_record(PuntajeAplicado, socio=linked, puntajeAplicado=Decimal(2))
    create_legacy_record(PuntajeAplicado, socio=foreign, puntajeAplicado=Decimal(70))
    response = own_balance(local)
    assert response.status_code == 200
    assert response.json() == {"points_balance": 2}


@pytest.mark.django_db
def test_disabled_profile_is_rechecked_after_a_real_jwt_login(
    balance_world: dict[str, Any], authenticate: Any
) -> None:
    local = balance_world["local"]
    balance_world["member"](770001, user_id=local.user_id)
    client = authenticate(local)
    local.is_enabled = False
    local.save(update_fields=["is_enabled"])
    response = client.get(BALANCE_URL)
    assert response.status_code == 403
    assert "points_balance" not in response.json()


@pytest.mark.django_db
def test_anonymous_and_profileless_users_cannot_read_balance() -> None:
    assert own_balance(None).status_code == 401
    user = get_user_model().objects.create_user(username="points-without-profile")
    client = APIClient()
    client.force_authenticate(user)
    response = client.get(BALANCE_URL)
    assert response.status_code == 403
    assert "points_balance" not in response.json()


@pytest.mark.django_db
def test_balance_endpoint_does_not_accept_writes(balance_world: dict[str, Any]) -> None:
    client = APIClient()
    client.force_authenticate(balance_world["local"].user)
    response = client.post(BALANCE_URL, {"points_balance": 1000}, format="json")
    assert response.status_code == 405


@pytest.mark.django_db
@pytest.mark.parametrize("failure", [DatabaseError, RuntimeError])
def test_repository_failure_is_sanitized_and_never_returns_zero(
    balance_world: dict[str, Any], monkeypatch: Any, caplog: Any, failure: type[Exception]
) -> None:
    from socios import views

    local = balance_world["local"]
    balance_world["member"](770001, user_id=local.user_id)

    class UnavailableRepository:
        def get_by_id(self, number: int) -> None:
            raise failure("sensitive-balance-diagnostic")

    monkeypatch.setattr(views, "get_padron_repository", lambda: UnavailableRepository())
    response = own_balance(local)
    assert response.status_code == 503
    assert set(response.json()) == {"detail"}
    assert "points_balance" not in response.json()
    assert "sensitive-balance-diagnostic" not in str(response.json())
    assert "sensitive-balance-diagnostic" not in caplog.text


@pytest.mark.django_db
def test_ledger_failure_is_a_sanitized_service_error(
    balance_world: dict[str, Any], caplog: Any
) -> None:
    local = balance_world["local"]
    balance_world["member"](770001, user_id=local.user_id)

    def unavailable_ledger(execute: Any, sql: str, params: Any, many: bool, context: Any) -> Any:
        if "SUM(" in sql.upper() and "tribunal_puntajeaplicado" in sql:
            raise DatabaseError("sensitive-ledger-diagnostic")
        return execute(sql, params, many, context)

    with connection.execute_wrapper(unavailable_ledger):
        response = own_balance(local)
    assert response.status_code == 503
    assert "points_balance" not in response.json()
    assert "sensitive-ledger-diagnostic" not in str(response.json())
    assert "sensitive-ledger-diagnostic" not in caplog.text


@pytest.mark.django_db
@pytest.mark.parametrize("wrong_number", [770002, 770001.0, "770001", True, 0, -1])
def test_repository_cannot_replace_the_confirmed_institutional_number(
    balance_world: dict[str, Any], monkeypatch: Any, wrong_number: Any
) -> None:
    from socios import views

    local = balance_world["local"]
    member = balance_world["member"](770001, user_id=local.user_id)
    dto = balance_world["repository"].get_by_id(member.pk)

    class InconsistentRepository:
        def get_by_id(self, number: int) -> Any:
            return replace(dto, socio_id=wrong_number)

    monkeypatch.setattr(views, "get_padron_repository", lambda: InconsistentRepository())
    response = own_balance(local)
    assert response.status_code == 404
    assert "points_balance" not in response.json()


@pytest.mark.django_db
def test_successful_balance_read_preserves_rows_and_executes_only_selects(
    balance_world: dict[str, Any],
) -> None:
    local = balance_world["local"]
    member = balance_world["member"](
        770001, user_id=local.user_id, academic_number=int(local.legajo)
    )
    create_legacy_record(PuntajeAplicado, socio=member, puntajeAplicado=Decimal(2))
    create_legacy_record(PuntajeGeneral, socio=member, puntos=Decimal(0))
    models = (
        get_user_model(),
        Socio,
        InstitutionalSocio,
        SocioEstudio,
        PuntajeAplicado,
        PuntajeGeneral,
    )

    def snapshot() -> list[list[dict[str, Any]]]:
        return [list(model.objects.order_by("pk").values()) for model in models]

    before = snapshot()
    with CaptureQueriesContext(connection) as queries:
        response = own_balance(local)
        local_response = legajo_balance(local, local.pk, "local")
        institutional_response = legajo_balance(local, member.pk, "institutional")
    assert response.status_code == 200
    assert response.json() == {"points_balance": 2}
    assert local_response.status_code == institutional_response.status_code == 200
    assert (
        local_response.json()["points_balance"]
        == institutional_response.json()["points_balance"]
        == 2
    )
    assert snapshot() == before
    assert queries.captured_queries
    assert all(
        query["sql"].lstrip().upper().startswith("SELECT") for query in queries.captured_queries
    )


@pytest.mark.django_db
@pytest.mark.parametrize("source", ["local", "institutional"])
@pytest.mark.parametrize("movements", [(3, -1), (-2, -1), ()])
def test_local_and_institutional_legajos_match_applied_balance(
    balance_world: dict[str, Any], source: str, movements: tuple[int, ...]
) -> None:
    local = balance_world["local"]
    member = balance_world["member"](
        770001, user_id=local.user_id, academic_number=int(local.legajo)
    )
    create_legacy_record(PuntajeGeneral, socio=member, puntos=Decimal(99))
    for points in movements:
        create_legacy_record(PuntajeAplicado, socio=member, puntajeAplicado=Decimal(points))
    response = legajo_balance(local, local.pk if source == "local" else member.pk, source)
    assert response.status_code == 200
    expected = sum((Decimal(value) for value in movements), Decimal(0))
    assert Decimal(str(response.json()["points_balance"])) == expected
    assert response.json()["id"] == (local.pk if source == "local" else member.pk)
    assert own_balance(local).json()["points_balance"] == response.json()["points_balance"]


@pytest.mark.django_db
@pytest.mark.parametrize("ambiguity", [False, True])
def test_local_legajo_preserves_profile_but_marks_unconfirmed_balance_unknown(
    balance_world: dict[str, Any], ambiguity: bool
) -> None:
    local = balance_world["local"]
    if ambiguity:
        balance_world["member"](770001, user_id=local.user_id)
        balance_world["member"](770002, user_id=local.user_id)
    response = legajo_balance(local, local.pk, "local")
    assert response.status_code == 200
    assert response.json()["id"] == local.pk
    assert response.json()["legajo"] == local.legajo
    assert response.json()["points_balance"] is None
    assert own_balance(local).status_code == 404


@pytest.mark.django_db
def test_mock_local_legajo_does_not_consult_an_institutional_balance_source(
    balance_world: dict[str, Any], monkeypatch: Any
) -> None:
    from socios import views

    local = balance_world["local"]
    monkeypatch.setenv("PADRON_ADAPTER", "mock")

    def unavailable_repository() -> None:
        pytest.fail("El perfil local en modo mock consultó una fuente de puntos real.")

    def unexpected_institutional_query(
        execute: Any, sql: str, params: Any, many: bool, context: Any
    ) -> Any:
        if any(
            name in sql for name in ("socio_lista", "socio_estudio", "tribunal_puntajeaplicado")
        ):
            pytest.fail("El perfil local en modo mock consultó SQL institucional.")
        return execute(sql, params, many, context)

    monkeypatch.setattr(views, "get_padron_repository", unavailable_repository)
    with connection.execute_wrapper(unexpected_institutional_query):
        response = legajo_balance(local, local.pk, "local")
    assert response.status_code == 200
    assert response.json()["points_balance"] is None


@pytest.mark.django_db
@pytest.mark.parametrize("source", ["local", "institutional"])
def test_legajo_ledger_failure_never_silently_becomes_zero(
    balance_world: dict[str, Any], source: str, caplog: Any
) -> None:
    local = balance_world["local"]
    member = balance_world["member"](770001, user_id=local.user_id)

    def unavailable_ledger(execute: Any, sql: str, params: Any, many: bool, context: Any) -> Any:
        if "SUM(" in sql.upper() and "tribunal_puntajeaplicado" in sql:
            raise DatabaseError("sensitive-legajo-balance-diagnostic")
        return execute(sql, params, many, context)

    with connection.execute_wrapper(unavailable_ledger):
        response = legajo_balance(local, local.pk if source == "local" else member.pk, source)
    assert response.status_code == 503
    assert "points_balance" not in response.json()
    assert "sensitive-legajo-balance-diagnostic" not in str(response.json())
    assert "sensitive-legajo-balance-diagnostic" not in caplog.text


@pytest.mark.django_db
def test_local_legajo_repository_failure_is_a_service_error(
    balance_world: dict[str, Any], monkeypatch: Any, caplog: Any
) -> None:
    from socios import views

    local = balance_world["local"]
    balance_world["member"](770001, user_id=local.user_id)

    class UnavailableRepository:
        def get_by_id(self, number: int) -> None:
            raise DatabaseError("sensitive-local-balance-diagnostic")

    monkeypatch.setattr(views, "get_padron_repository", lambda: UnavailableRepository())
    response = legajo_balance(local, local.pk, "local")
    assert response.status_code == 503
    assert "points_balance" not in response.json()
    assert "sensitive-local-balance-diagnostic" not in str(response.json())
    assert "sensitive-local-balance-diagnostic" not in caplog.text


@pytest.mark.django_db
@pytest.mark.parametrize("source", ["local", "institutional"])
def test_legajo_authorization_precedes_balance_lookup(
    balance_world: dict[str, Any], source: str
) -> None:
    local = balance_world["local"]
    other = balance_world["other"]
    member = balance_world["member"](770002, user_id=other.user_id)

    def unreadable_foreign_ledger(
        execute: Any, sql: str, params: Any, many: bool, context: Any
    ) -> Any:
        if "SUM(" in sql.upper() and "tribunal_puntajeaplicado" in sql:
            pytest.fail("El legajo ajeno consultó puntos antes de verificar el permiso.")
        return execute(sql, params, many, context)

    with connection.execute_wrapper(unreadable_foreign_ledger):
        response = legajo_balance(local, other.pk if source == "local" else member.pk, source)
    assert response.status_code == 403
