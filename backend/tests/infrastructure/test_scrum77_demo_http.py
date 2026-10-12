"""Oráculos HTTP/BD del catálogo real, reutilizables por scratch y servidor demo.

Sólo el login usa POST. No crea solicitudes, firma actos ni modifica los fixtures.
La entrada transporta un JWT en memoria; el resumen nunca lo devuelve.
"""

import json
from collections import Counter
from collections.abc import Callable
from decimal import Decimal
from typing import Any
from urllib.error import HTTPError
from urllib.parse import urlencode, urlsplit
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

import pytest
from django.db import connection

from expedientes.models import EstadoExpedienteEnum, Expediente, SolicitudT01
from socios.demo_catalog import CATALOG, expected_balances
from socios.models import Socio
from tests.infrastructure.test_scrum77_schema_bootstrap import (
    bootstrap_database as bootstrap_database,
)

JSONRequest = Callable[[str, str, dict[str, Any] | None, str | None], tuple[int, Any]]


def verify_seeded_demo_http(request_json: JSONRequest) -> dict[str, Any]:
    """Contrastar endpoints públicos con personas, relaciones y saldos persistidos."""
    from core.demo_fixtures import DemoFixtureRegistry

    assert connection.vendor == "mysql", "El smoke requiere MySQL real."
    members = {member.fixture_key: member for member in CATALOG.members}
    groups = {group.fixture_key: group for group in CATALOG.groups}
    expected = expected_balances(CATALOG)
    member_ids = {member.institutional_number for member in CATALOG.members}
    checks = 0
    registry = DemoFixtureRegistry(profile=CATALOG.profile)

    def owned_key(key: str, namespace: str) -> str:
        ownership = registry.get(key)
        assert ownership is not None and ownership.namespace == namespace
        return ownership.object_key

    def call(
        path: str,
        *,
        token: str | None = None,
        payload: dict[str, Any] | None = None,
        expected_status: int = 200,
    ) -> Any:
        nonlocal checks
        status_code, body = request_json(
            "POST" if payload is not None else "GET", path, payload, token
        )
        assert status_code == expected_status, (
            f"{path}: HTTP {status_code}, esperado {expected_status}."
        )
        checks += 1
        return body

    tokens: dict[str, str] = {}
    profiles: dict[str, Socio] = {}
    preserved_roles = {
        "74907": "SOCIO",
        "85194": "FISCALIZADORA",
        "87414": "CD",
        "408917": "TD",
        "403655": "ADMIN",
    }
    for account in CATALOG.accounts:
        profile = Socio.objects.select_related("user").get(legajo=account.username)
        profiles[account.fixture_key] = profile
        assert int(owned_key(account.local_socio_key, "socios_socio")) == profile.pk
        assert int(owned_key(account.user_key, "auth_user")) == profile.user_id
        assert profile.role == account.role
        assert profile.is_enabled == account.is_enabled
        body = call(
            "/api/v1/auth/login/",
            payload={"identifier": account.username},
            expected_status=200 if account.is_enabled else 401,
        )
        if not account.is_enabled:
            continue
        token = body["access"]
        tokens[account.fixture_key] = token
        me = call("/api/v1/auth/me/", token=token)
        group = groups[members[account.member_key].group_key]
        assert me["id"] == profile.pk
        assert me["legajo"] == account.username
        assert me["role"] == account.role
        assert me["category"] == group.category
        assert body["user"] == me
    for account in CATALOG.preserved_accounts:
        profile = Socio.objects.get(legajo=account.legajo)
        body = call("/api/v1/auth/login/", payload={"identifier": account.legajo})
        me = call("/api/v1/auth/me/", token=body["access"])
        assert me["id"] == profile.pk
        assert me["role"] == preserved_roles[account.legajo]
        assert me["category"] == profile.category
        tokens[account.fixture_key] = body["access"]
        call(
            "/api/v1/expedientes/board/",
            token=body["access"],
            expected_status=200 if profile.role in {"TD", "CD", "ADMIN"} else 403,
        )
        call(
            "/api/v1/expedientes/mis-solicitudes/",
            token=body["access"],
            expected_status=200 if profile.role in {"TD", "CD", "FISCALIZADORA"} else 403,
        )
    call("/api/v1/auth/me/", expected_status=401)

    cd_token = tokens["account.g58.01"]
    ordinary_token = tokens["account.g57.01"]
    call("/api/v1/expedientes/board/", token=tokens["account.g59.01"], expected_status=403)
    rows = call("/api/v1/ranking/?ordering=-saldo,apellido,nombre,id")
    assert isinstance(rows, list)
    assert len({int(row["id"]) for row in rows}) == len(rows)
    fixture_rows = {int(row["id"]): row for row in rows if int(row["id"]) in member_ids}
    assert set(fixture_rows) == member_ids
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT socio_id, SUM(puntajeAplicado) FROM tribunal_puntajeaplicado GROUP BY socio_id"
        )
        sql_balances = dict(cursor.fetchall())
    for member in CATALOG.members:
        assert int(owned_key(member.fixture_key, "socio_lista")) == member.institutional_number
        row = fixture_rows[member.institutional_number]
        group = groups[member.group_key]
        sql_balance = sql_balances.get(member.institutional_number, Decimal(0))
        assert sql_balance == expected[member.fixture_key]
        assert Decimal(str(row["saldo"])) == sql_balance
        assert Decimal(str(row["saldoHistorico"])) == sql_balance
        assert row["categoria"] == group.category
        assert row["legajo"] == str(member.academic_number)
        detail = call(
            f"/api/v1/socios/{member.institutional_number}/legajo/?identity_source=institutional",
            token=cd_token,
        )
        assert detail["id"] == member.institutional_number
        assert detail["legajo"] == str(member.academic_number)
        assert detail["category"] == group.category
        assert detail["social_year"] == group.social_year
        assert Decimal(str(detail["points_balance"])) == sql_balance
    assert sum(expected.values()) == Decimal(1)
    for category, expected_count in (
        ("JUNIOR", 4),
        ("SENIOR", 12),
        ("EX_TRAVELER", 4),
        ("UNKNOWN", 0),
    ):
        filtered = call(f"/api/v1/ranking/?categoria={category}")
        assert all(row["categoria"] == category for row in filtered)
        assert sum(int(row["id"]) in member_ids for row in filtered) == expected_count
    for subcommission in CATALOG.subcommissions:
        filtered = call(
            "/api/v1/ranking/?" + urlencode({"subcomision": str(subcommission.institutional_code)})
        )
        assert {int(row["id"]) for row in filtered if int(row["id"]) in member_ids} == {
            member.institutional_number
            for member in CATALOG.members
            if member.subcommission_key == subcommission.fixture_key
        }
    repeated = call("/api/v1/ranking/?ordering=-saldo,apellido,nombre,id")
    assert [row["id"] for row in repeated] == [row["id"] for row in rows]
    call("/api/v1/socios/770001/legajo/?identity_source=institutional", token=ordinary_token)
    call(
        "/api/v1/socios/770005/legajo/?identity_source=institutional",
        token=ordinary_token,
        expected_status=403,
    )
    for member in (CATALOG.members[0], CATALOG.members[4]):
        filtered = call("/api/v1/ranking/?" + urlencode({"q": str(member.academic_number)}))
        assert [int(row["id"]) for row in filtered] == [member.institutional_number]

    junior_ids = []
    for account in CATALOG.accounts:
        member = members[account.member_key]
        group = groups[member.group_key]
        if group.category != "JUNIOR":
            continue
        junior_ids.append(member.institutional_number)
        token = tokens[account.fixture_key]
        own_detail = call(
            f"/api/v1/socios/{member.institutional_number}/legajo/?identity_source=institutional",
            token=token,
        )
        assert own_detail["id"] == member.institutional_number
        assert own_detail["category"] == "JUNIOR"
        assert own_detail["social_year"] == group.social_year
        assert Decimal(str(own_detail["points_balance"])) == Decimal(0)
        call(
            "/api/v1/socios/770005/legajo/?identity_source=institutional",
            token=token,
            expected_status=403,
        )
        call("/api/v1/expedientes/board/", token=token, expected_status=403)
        call("/api/v1/expedientes/mis-solicitudes/", token=token, expected_status=403)
        selector = call(
            "/api/v1/padron/socios/?" + urlencode({"search": str(member.academic_number)}),
            token=cd_token,
        )
        assert selector["count"] == 1
        assert len(selector["results"]) == 1
        selected = selector["results"][0]
        assert selected["socio_id"] == member.institutional_number
        assert selected["legajo"] == str(member.academic_number)
        assert selected["category"] == "JUNIOR"
        assert selected["social_year"] == group.social_year
        assert selected["is_active"] is True
    junior_filter = call("/api/v1/padron/socios/?category=JUNIOR", token=cd_token)
    assert junior_filter["count"] == 4
    assert {row["socio_id"] for row in junior_filter["results"]} == set(junior_ids)

    requests_by_actor: dict[str, set[str]] = {}
    request_scenes = {
        owned_key(scene.fixture_key, "expedientes_solicitudt01"): scene
        for scene in CATALOG.t01_scenes
    }
    subcommissions = {item.fixture_key: item for item in CATALOG.subcommissions}
    for actor_key in ("account.g58.01", "account.g59.01"):
        token = tokens[actor_key]
        local_actor = profiles[actor_key]
        db_requests = {
            str(row.pk): row for row in SolicitudT01.objects.filter(solicitante=local_actor)
        }
        listed = call("/api/v1/expedientes/mis-solicitudes/", token=token)
        assert {row["id"] for row in listed} == set(db_requests)
        assert Counter(row["estado"] for row in listed) == {"DRAFT": 1, "ISSUED": 1}
        requests_by_actor[actor_key] = set(db_requests)
        for row in listed:
            stored = db_requests[row["id"]]
            scene = request_scenes[row["id"]]
            assert row["involucrados"] == [
                {
                    "socio_id": member.institutional_number,
                    "legajo": str(member.academic_number),
                    "first_name": member.first_name,
                    "last_name": member.last_name,
                    "subcomision": (
                        subcommissions[member.subcommission_key].name
                        if subcommissions[member.subcommission_key].institutional_code != 99
                        else "Sin subcomisión"
                    ),
                }
                for member in (members[key] for key in scene.recipient_member_keys)
            ]
            assert row["destinatarios_socios_ids"] == stored.destinatarios_socios_ids
            assert row["urgencia"] == (
                stored.expediente.urgencia if stored.expediente_id else stored.urgencia
            )
            assert row["numero_expediente"] == stored.numero_expediente
            if stored.estado == "ISSUED":
                assert row["numero"] == stored.expediente.numero
                assert row["estado_procesal"] == "justificando"
        drafts = call("/api/v1/expedientes/mis-solicitudes/?estado=DRAFT", token=token)
        assert len(drafts) == 1 and drafts[0]["estado"] == "DRAFT"
        searched = call(
            "/api/v1/expedientes/mis-solicitudes/?" + urlencode({"search": drafts[0]["titulo"]}),
            token=token,
        )
        assert [row["id"] for row in searched] == [drafts[0]["id"]]
    assert not set.intersection(*requests_by_actor.values())
    assert set.union(*requests_by_actor.values()) == {
        owned_key(scene.fixture_key, "expedientes_solicitudt01") for scene in CATALOG.t01_scenes
    }
    foreign_draft = SolicitudT01.objects.get(solicitante=profiles["account.g59.01"], estado="DRAFT")
    call(f"/api/v1/expedientes/{foreign_draft.pk}/", token=cd_token, expected_status=404)
    call("/api/v1/expedientes/mis-solicitudes/", token=ordinary_token, expected_status=403)
    multi = SolicitudT01.objects.get(solicitante=profiles["account.g58.01"], estado="ISSUED")
    assert len(multi.destinatarios_socios_ids) == multi.expediente.socios.count() == 2

    all_cases = {row.pk: row for row in Expediente.objects.all()}
    assert set(all_cases) == {
        int(owned_key(scene.fixture_key, "expedientes_expediente")) for scene in CATALOG.causes
    } | {
        int(owned_key(scene.fixture_key + ".expediente", "expedientes_expediente"))
        for scene in CATALOG.t01_scenes
        if scene.status == "ISSUED"
    }
    board = call("/api/v1/expedientes/board/", token=cd_token)
    assert [column["key"] for column in board["columns"]] == [
        state.value for state in EstadoExpedienteEnum
    ]
    board_rows = {row["id"]: row for column in board["columns"] for row in column["cases"]}
    assert set(board_rows) == set(all_cases)
    assert Counter(row.estado for row in all_cases.values()) == {"creado": 3, "justificando": 2}
    for identifier, row in board_rows.items():
        stored = all_cases[identifier]
        assert row["numero"] == stored.numero
        assert row["urgencia"] == stored.urgencia
        assert row["cantidad_socios"] == stored.socios.count()
        if stored.estado == "justificando":
            assert row["plazo_limite_at"]
    for filters in ({"estado": "creado"}, {"urgencia": "urgente"}, {"socio": "99077001"}):
        filtered = call("/api/v1/expedientes/board/?" + urlencode(filters), token=cd_token)
        ids = {row["id"] for column in filtered["columns"] for row in column["cases"]}
        queryset = Expediente.objects.all()
        if "estado" in filters:
            queryset = queryset.filter(estado=filters["estado"])
        if "urgencia" in filters:
            queryset = queryset.filter(urgencia=filters["urgencia"])
        if "socio" in filters:
            queryset = queryset.filter(socios__legajo=filters["socio"])
        assert ids == set(queryset.values_list("pk", flat=True))
    collection = call("/api/v1/expedientes/gestion/", token=cd_token)
    assert {row["id"] for row in collection} == set(all_cases)
    call("/api/v1/expedientes/board/", token=ordinary_token, expected_status=403)
    call("/api/v1/expedientes/board/", expected_status=401)
    return {
        "http_checks": checks,
        "institutional_ids": sorted(fixture_rows),
        "catalog_balance": str(sum(expected.values())),
        "junior_ids": sorted(junior_ids),
        "request_ids_by_actor": {key: sorted(value) for key, value in requests_by_actor.items()},
        "managed_case_ids": sorted(all_cases),
        "case_numbers": sorted(row.numero for row in all_cases.values()),
    }


def verify_running_demo_http(base_url: str = "http://127.0.0.1:8000") -> dict[str, Any]:
    """Ejecutar los mismos oráculos contra el servidor loopback, sin proxy/redirección."""
    parsed = urlsplit(base_url)
    assert parsed.scheme == "http" and parsed.hostname in {"127.0.0.1", "localhost"}
    assert not parsed.username and not parsed.password and not parsed.query and not parsed.fragment

    class RejectRedirects(HTTPRedirectHandler):
        def redirect_request(
            self, request: Any, fp: Any, code: int, message: str, headers: Any, newurl: str
        ) -> None:
            raise AssertionError("El smoke no acepta redirecciones.")

    opener = build_opener(ProxyHandler({}), RejectRedirects())

    def request_json(
        method: str, path: str, payload: dict[str, Any] | None, token: str | None
    ) -> tuple[int, Any]:
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        data = json.dumps(payload).encode() if payload is not None else None
        request = Request(base_url.rstrip("/") + path, data=data, headers=headers, method=method)
        try:
            with opener.open(request, timeout=15) as response:
                assert response.url == request.full_url, "El smoke no acepta redirecciones."
                return response.status, json.loads(response.read())
        except HTTPError as error:
            return error.code, json.loads(error.read())

    return verify_seeded_demo_http(request_json)


@pytest.mark.django_db(transaction=True, databases="__all__")
def test_catalog_http_profiles_ranking_requests_and_board_match_real_mysql(
    bootstrap_database: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """HTTP DRF en scratch MySQL UUID, con login/JWT real y sin force_authenticate."""
    from django.conf import settings
    from rest_framework.test import APIClient

    from core import demo_seed
    from core.demo_schema import prepare_schema

    prepare_schema(bootstrap_database)
    monkeypatch.setattr(settings, "DEBUG", True)
    for name in (
        "assert_demo_seed_environment",
        "assert_demo_seed_database",
        "assert_demo_seed_schema",
    ):
        monkeypatch.setattr(demo_seed, name, lambda *args, **kwargs: None)
    demo_seed.run_demo_seed(profile=CATALOG.profile)
    client = APIClient()

    def request_json(
        method: str, path: str, payload: dict[str, Any] | None, token: str | None
    ) -> tuple[int, Any]:
        headers = {"HTTP_AUTHORIZATION": f"Bearer {token}"} if token else {}
        if method == "POST":
            response = client.post(path, payload, format="json", **headers)
        else:
            response = client.get(path, **headers)
        return response.status_code, response.data

    result = verify_seeded_demo_http(request_json)
    assert len(result["institutional_ids"]) == 20
    assert len(result["managed_case_ids"]) == 5
    assert Decimal(result["catalog_balance"]) == Decimal(1)
    assert result["junior_ids"] == [770017, 770018, 770019, 770020]
    assert result["http_checks"] == 111
