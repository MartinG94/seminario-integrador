"""RF77-17: historial propio respaldado y saldo de la misma lectura MySQL."""

from decimal import Decimal
from typing import Any

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from rest_framework.test import APIClient

from core.models import DemoFixtureOwnership
from expedientes.models import Expediente
from padron.adapters import DatabasePadronAdapter
from ranking.models import PuntajeAplicado
from socios.demo_catalog import CATALOG, expected_balances
from socios.models import Socio
from tests.infrastructure.test_scrum77_schema_bootstrap import (
    bootstrap_database as bootstrap_database,
)
from tests.infrastructure.test_scrum77_seed_integration import prepare_seed, snapshot
from tests.legacy_schema import create_legacy_record

HISTORY_URL = "/api/v1/socios/me/points-history/"
pytestmark = pytest.mark.django_db(transaction=True, databases="__all__")


@pytest.fixture
def history_world(bootstrap_database: Any, monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    from socios import views

    seed = prepare_seed(bootstrap_database, monkeypatch)
    report = seed.run_demo_seed()
    monkeypatch.setattr(views, "get_padron_repository", lambda: DatabasePadronAdapter())
    local = Socio.objects.get(legajo="99077001")
    client = APIClient()
    client.force_authenticate(local.user)
    return {"database": bootstrap_database, "report": report, "local": local, "client": client}


def test_original_merit_is_visible_with_literal_resolution_and_unchanged_rows(
    history_world: dict[str, Any],
) -> None:
    before = snapshot(history_world["database"])
    response = history_world["client"].get(HISTORY_URL)
    assert response.status_code == 200
    assert set(response.json()) == {"points_balance", "entries"}
    assert response.json()["points_balance"] == 2
    entries = response.json()["entries"]
    assert len(entries) == 1
    entry = entries[0]
    assert entry["applied_points"] == 2
    assert entry["managed_case"] is None
    assert entry["historical_case"]["state"] == "emitido"
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT p.idPuntajeAplicado, e.idExpediente, e.nroExpediente, e.fechaHora, "
            "r.idDatosResolucion, r.consideracion, r.reglamento1 "
            "FROM tribunal_puntajeaplicado p "
            "JOIN tribunal_expediente e ON e.idExpediente=p.expediente_id "
            "JOIN tribunal_datosresolucion r ON r.idDatosResolucion=e.dataRes_id "
            "WHERE p.socio_id=%s",
            [770001],
        )
        row = cursor.fetchone()
    assert entry["movement_id"] == row[0]
    assert entry["historical_case"]["id"] == row[1]
    assert entry["historical_case"]["number"] == row[2]
    assert entry["historical_case"]["recorded_at"] == row[3].isoformat()
    assert entry["resolution"] == {"id": row[4], "text": row[5], "regulations": [row[6]]}
    assert "VISTO:" in entry["resolution"]["text"]
    assert "CONSIDERANDO:" in entry["resolution"]["text"]
    assert "SE RESUELVE:" in entry["resolution"]["text"]
    assert response["Cache-Control"] == "no-store"
    assert snapshot(history_world["database"]) == before


def test_all_enabled_demo_accounts_have_only_their_individual_applied_history(
    history_world: dict[str, Any],
) -> None:
    expected = expected_balances(CATALOG)
    members = {member.fixture_key: member for member in CATALOG.members}
    for account in CATALOG.accounts:
        if not account.is_enabled:
            continue
        local = Socio.objects.get(legajo=account.username)
        client = APIClient()
        client.force_authenticate(local.user)
        response = client.get(HISTORY_URL, {"socio_id": "770002", "legajo": "99077002"})
        assert response.status_code == 200
        body = response.json()
        number = members[account.member_key].institutional_number
        ledger = list(PuntajeAplicado.objects.filter(socio_id=number).order_by("pk"))
        assert [entry["movement_id"] for entry in body["entries"]] == [row.pk for row in ledger]
        assert Decimal(str(body["points_balance"])) == expected[account.member_key]
        assert (
            sum((Decimal(str(entry["applied_points"])) for entry in body["entries"]), Decimal(0))
            == expected[account.member_key]
        )
        assert all(entry["historical_case"]["state"] == "emitido" for entry in body["entries"])


def test_advanced_history_links_only_the_registered_emitted_cause_and_recipient(
    history_world: dict[str, Any],
) -> None:
    report = history_world["report"]
    member_by_key = {member.fixture_key: member for member in CATALOG.members}
    for fixture in CATALOG.advanced_causes:
        if fixture.stage != "emitido":
            continue
        member = member_by_key[fixture.recipient_member_keys[0]]
        local = Socio.objects.get(legajo=str(member.academic_number))
        client = APIClient()
        client.force_authenticate(local.user)
        response = client.get(HISTORY_URL)
        assert response.status_code == 200
        case = Expediente.objects.get(pk=report["mappings"]["advanced_causes"][fixture.fixture_key])
        movement = int(report["mappings"]["advanced_movements"][fixture.fixture_key])
        entry = next(item for item in response.json()["entries"] if item["movement_id"] == movement)
        assert entry["managed_case"] == {"id": case.pk, "number": case.numero, "state": "emitido"}
        assert case.numero in entry["resolution"]["text"]
        assert f"nroSocio {member.institutional_number}" in entry["resolution"]["text"]
        assert entry["applied_points"] == float(fixture.requested_points)


def test_a_ledger_entry_without_historical_case_fails_closed(history_world: dict[str, Any]) -> None:
    create_legacy_record(PuntajeAplicado, socio_id=770001, puntajeAplicado=Decimal(3))
    response = history_world["client"].get(HISTORY_URL)
    assert response.status_code == 503
    assert set(response.json()) == {"detail"}


@pytest.mark.parametrize("component", ["history", "resolution", "case", "link", "movement"])
def test_a_broken_registered_advanced_link_is_not_silently_omitted(
    history_world: dict[str, Any], component: str
) -> None:
    local = Socio.objects.get(legajo="99077017")
    key = "advanced.emitted.01"
    if component == "link":
        key += f".link.{local.pk}"
    elif component != "case":
        key += f".{component}"
    ownership = DemoFixtureOwnership.objects.get(profile=CATALOG.profile, fixture_key=key)
    if component == "movement":
        ownership.delete()
    else:
        ownership.object_key = "999999999"
        ownership.save(update_fields=["object_key"])
    client = APIClient()
    client.force_authenticate(local.user)
    response = client.get(HISTORY_URL)
    assert response.status_code == 503
    assert set(response.json()) == {"detail"}


@pytest.mark.parametrize(
    "invalid_backing", ["not_emitted", "no_resolution", "empty_text", "blank_regulation"]
)
def test_incomplete_or_not_emitted_backing_is_a_service_error(
    history_world: dict[str, Any], invalid_backing: str
) -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT puntos_id, dataRes_id FROM tribunal_expediente ORDER BY idExpediente LIMIT 1"
        )
        points_id, resolution_id = cursor.fetchone()
        state_id = 6
        if invalid_backing == "not_emitted":
            cursor.execute(
                "INSERT INTO tribunal_estadoexpediente (idEstadoExpediente,nombre,descripcion) "
                "VALUES (%s,%s,%s)",
                [5, "Pendiente de envío", "Caso propio de pruebas"],
            )
            state_id = 5
        elif invalid_backing == "no_resolution":
            resolution_id = None
        else:
            cursor.execute(
                "INSERT INTO tribunal_datosresolucion (reglamento1,consideracion) VALUES (%s,%s)",
                [
                    " " if invalid_backing == "blank_regulation" else "Referencia de pruebas",
                    "Texto de pruebas" if invalid_backing == "blank_regulation" else "",
                ],
            )
            resolution_id = cursor.lastrowid
        cursor.execute(
            "INSERT INTO tribunal_expediente "
            "(nroExpediente,estadoExpediente_id,puntos_id,dataRes_id) VALUES (%s,%s,%s,%s)",
            ["BAD7757", state_id, points_id, resolution_id],
        )
        case_id = cursor.lastrowid
    create_legacy_record(
        PuntajeAplicado, socio_id=770001, puntajeAplicado=Decimal(3), expediente_id=case_id
    )
    response = history_world["client"].get(HISTORY_URL)
    assert response.status_code == 503
    assert set(response.json()) == {"detail"}


def test_preserved_local_accounts_without_institutional_identity_have_no_invented_history(
    history_world: dict[str, Any],
) -> None:
    for account in CATALOG.preserved_accounts:
        local = Socio.objects.get(legajo=account.legajo)
        client = APIClient()
        client.force_authenticate(local.user)
        response = client.get(HISTORY_URL)
        assert response.status_code == 404
        assert set(response.json()) == {"detail"}


def test_blank_optional_regulations_are_omitted_without_changing_literal_nonblank_text(
    history_world: dict[str, Any],
) -> None:
    text = (
        "Documento sintético: VISTO: prueba de contrato. CONSIDERANDO: fixture aislada. "
        "SE RESUELVE: nroSocio 770001, +3 puntos individuales de prueba."
    )
    with connection.cursor() as cursor:
        cursor.execute("SELECT puntos_id FROM tribunal_expediente ORDER BY idExpediente LIMIT 1")
        points_id = cursor.fetchone()[0]
        cursor.execute(
            "INSERT INTO tribunal_datosresolucion "
            "(reglamento1,reglamento2,reglamento3,consideracion) VALUES (%s,%s,%s,%s)",
            [" Referencia literal ", "   ", "\t", text],
        )
        resolution_id = cursor.lastrowid
        cursor.execute(
            "INSERT INTO tribunal_expediente "
            "(nroExpediente,estadoExpediente_id,puntos_id,dataRes_id) VALUES (%s,%s,%s,%s)",
            ["OPT7757", 6, points_id, resolution_id],
        )
        case_id = cursor.lastrowid
    movement = create_legacy_record(
        PuntajeAplicado, socio_id=770001, puntajeAplicado=Decimal(3), expediente_id=case_id
    )
    response = history_world["client"].get(HISTORY_URL)
    assert response.status_code == 200
    entry = next(item for item in response.json()["entries"] if item["movement_id"] == movement.pk)
    assert entry["resolution"]["text"] == text
    assert entry["resolution"]["regulations"] == [" Referencia literal "]


def test_history_requires_current_enabled_profile_and_does_not_accept_writes(
    history_world: dict[str, Any],
) -> None:
    assert APIClient().get(HISTORY_URL).status_code == 401
    client = history_world["client"]
    assert client.post(HISTORY_URL, {"points_balance": 1000}, format="json").status_code == 405
    local = history_world["local"]
    local.is_enabled = False
    local.save(update_fields=["is_enabled"])
    assert client.get(HISTORY_URL).status_code == 403


def test_history_performs_no_dml(history_world: dict[str, Any]) -> None:
    with CaptureQueriesContext(connection) as queries:
        response = history_world["client"].get(HISTORY_URL)
    assert response.status_code == 200
    forbidden = ("INSERT", "UPDATE", "DELETE", "ALTER", "CREATE", "DROP", "REPLACE")
    assert all(
        not query["sql"].lstrip().upper().startswith(forbidden)
        for query in queries.captured_queries
    )


def test_authority_can_read_all_twenty_institutional_histories_without_duplicating_points(
    history_world: dict[str, Any],
) -> None:
    authority = Socio.objects.get(legajo="87414")
    client = APIClient()
    client.force_authenticate(authority.user)
    expected = expected_balances(CATALOG)
    seen_movements: set[int] = set()
    for member in CATALOG.members:
        response = client.get(
            f"/api/v1/socios/{member.institutional_number}/points-history/",
            {"identity_source": "institutional"},
        )
        assert response.status_code == 200
        body = response.json()
        assert Decimal(str(body["points_balance"])) == expected[member.fixture_key]
        ledger = list(
            PuntajeAplicado.objects.filter(socio_id=member.institutional_number).order_by("pk")
        )
        ids = [entry["movement_id"] for entry in body["entries"]]
        assert ids == [row.pk for row in ledger]
        assert not seen_movements.intersection(ids)
        seen_movements.update(ids)
    assert len(seen_movements) == 12


@pytest.mark.parametrize("source", ["local", "institutional"])
def test_history_from_legajo_keeps_ordinary_ownership_permissions(
    history_world: dict[str, Any], source: str
) -> None:
    local = history_world["local"]
    own_id = local.pk if source == "local" else 770001
    own = history_world["client"].get(
        f"/api/v1/socios/{own_id}/points-history/", {"identity_source": source}
    )
    assert own.status_code == 200
    assert own.json() == history_world["client"].get(HISTORY_URL).json()
    other = Socio.objects.get(legajo="99077005")
    foreign_id = other.pk if source == "local" else 770005
    response = history_world["client"].get(
        f"/api/v1/socios/{foreign_id}/points-history/", {"identity_source": source}
    )
    assert response.status_code == 403
