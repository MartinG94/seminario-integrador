"""Oráculos SCRUM-77 y saldo propio contra demo real, conservando las altas de UAT.

Ejecutar por stdin dentro del backend demo, sin pytest ni bases de pruebas:
Get-Content -Raw docs/gestion-proyecto/evidencias/scrum77-ampliacion/verificar_http.py |
  docker compose -p sgd-aveit-scrum77-demo -f docker-compose.scrum77-demo.yml exec -T backend python

El helper original conserva sus aserciones estrictas para scratch. Esta variante
ad hoc filtra exclusivamente su vista de fixtures, después de cotejar las
colecciones HTTP completas con la BD efectiva, incluidas las altas de UAT.
Sólo envía GET y POST al login. Nunca imprime JWT, credenciales ni filas privadas.
"""

import hashlib
import inspect
import json
import os
import sys
from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any
from urllib.error import HTTPError
from urllib.parse import parse_qs, urlsplit
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
import django

django.setup()

from django.db import connection
from django.db.models import Q

from core.demo_fixtures import DemoFixtureRegistry
from expedientes.models import Expediente, SolicitudT01
from socios.demo_catalog import CATALOG
from tests.infrastructure import test_scrum77_demo_http as original


def snapshot() -> dict[str, Any]:
    """Lectura de todas las tablas; únicamente conserva huellas y conteos."""
    tables: dict[str, Any] = {}
    with connection.cursor() as cursor:
        cursor.execute("SHOW FULL TABLES WHERE Table_type='BASE TABLE'")
        names = sorted(row[0] for row in cursor.fetchall())
        for name in names:
            cursor.execute(f"SELECT * FROM {connection.ops.quote_name(name)}")
            rows = sorted(cursor.fetchall(), key=repr)
            tables[name] = {
                "count": len(rows),
                "sha256": hashlib.sha256(
                    json.dumps(rows, default=str, ensure_ascii=False).encode()
                ).hexdigest(),
            }
    return tables


class RejectRedirects(HTTPRedirectHandler):
    def redirect_request(
        self, request: Any, fp: Any, code: int, message: str,
        headers: Any, newurl: str,
    ) -> None:
        raise AssertionError("No se permiten redirecciones.")


def main() -> dict[str, Any]:
    assert connection.vendor == "mysql"
    with connection.cursor() as cursor:
        cursor.execute("SELECT DATABASE(), @@session.foreign_key_checks")
        database, foreign_keys = cursor.fetchone()
    assert database == "aveit_tribunal_scrum77_demo" and foreign_keys == 1
    before = snapshot()
    registry = DemoFixtureRegistry(CATALOG.profile)

    def reference(key: str, namespace: str) -> str:
        row = registry.get(key)
        assert row is not None and row.namespace == namespace
        return row.object_key

    fixture_case_ids = {
        int(reference(scene.fixture_key, "expedientes_expediente"))
        for scene in CATALOG.causes
    } | {
        int(reference(scene.fixture_key + ".expediente", "expedientes_expediente"))
        for scene in CATALOG.t01_scenes if scene.status == "ISSUED"
    } | {
        int(reference(scene.fixture_key, "expedientes_expediente"))
        for scene in CATALOG.advanced_causes
    }
    fixture_request_ids = {
        reference(scene.fixture_key, "expedientes_solicitudt01")
        for scene in CATALOG.t01_scenes
    }
    all_cases = {row.pk: row for row in Expediente.objects.all()}
    all_requests = {str(row.pk): row for row in SolicitudT01.objects.all()}
    assert fixture_case_ids <= set(all_cases)
    assert fixture_request_ids <= set(all_requests)
    assert len(fixture_case_ids) == 15 and len(fixture_request_ids) == 4
    owner_by_token: dict[str, int] = {}
    observations: list[dict[str, Any]] = []
    opener = build_opener(ProxyHandler({}), RejectRedirects())

    def request_json(
        method: str, path: str, payload: dict[str, Any] | None, token: str | None
    ) -> tuple[int, Any]:
        assert method == "GET" or (method == "POST" and path == "/api/v1/auth/login/")
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        request = Request(
            "http://127.0.0.1:8000" + path,
            data=json.dumps(payload).encode() if payload is not None else None,
            headers=headers, method=method,
        )
        try:
            with opener.open(request, timeout=15) as response:
                assert response.url == request.full_url
                status_code, body = response.status, json.loads(response.read())
        except HTTPError as error:
            status_code, body = error.code, json.loads(error.read())
        parsed = urlsplit(path)
        params = parse_qs(parsed.query)
        observed: dict[str, Any] = {
            "method": method, "path": parsed.path,
            "query_keys": sorted(params), "status": status_code,
        }
        observations.append(observed)
        if method == "POST" and status_code == 200:
            owner_by_token[body["access"]] = body["user"]["id"]
        if status_code != 200:
            return status_code, body

        if parsed.path == "/api/v1/expedientes/board/":
            rows = [row for column in body["columns"] for row in column["cases"]]
            ids = {row["id"] for row in rows}
            assert len(ids) == len(rows)
            queryset = Expediente.objects.all()
            if "estado" in params:
                queryset = queryset.filter(estado=params["estado"][0])
            if "urgencia" in params:
                queryset = queryset.filter(urgencia=params["urgencia"][0])
            if "socio" in params:
                value = params["socio"][0]
                queryset = queryset.filter(
                    Q(socio__legajo__icontains=value)
                    | Q(socio__first_name__icontains=value)
                    | Q(socio__last_name__icontains=value)
                    | Q(socios__legajo__icontains=value)
                    | Q(socios__first_name__icontains=value)
                    | Q(socios__last_name__icontains=value)
                ).distinct()
            assert ids == set(queryset.values_list("pk", flat=True))
            for row in rows:
                stored = all_cases[row["id"]]
                assert row["numero"] == stored.numero
                assert row["urgencia"] == stored.urgencia
                assert row["cantidad_socios"] == stored.socios.count()
            observed.update({"all_count": len(rows), "all_ids": sorted(ids)})
            body = deepcopy(body)
            for column in body["columns"]:
                column["cases"] = [row for row in column["cases"] if row["id"] in fixture_case_ids]
            observed["fixture_count"] = sum(len(column["cases"]) for column in body["columns"])

        elif parsed.path == "/api/v1/expedientes/gestion/":
            ids = {row["id"] for row in body}
            assert len(ids) == len(body) and ids == set(all_cases)
            observed.update({"all_count": len(body), "all_ids": sorted(ids)})
            body = [row for row in body if row["id"] in fixture_case_ids]
            observed["fixture_count"] = len(body)

        elif parsed.path == "/api/v1/expedientes/mis-solicitudes/":
            assert token in owner_by_token
            local_owner = owner_by_token[token]
            ids = {row["id"] for row in body}
            assert len(ids) == len(body)
            expected_query = SolicitudT01.objects.filter(solicitante_id=local_owner)
            state = params.get("estado", [""])[0].strip()
            if state:
                if state.upper() in {"DRAFT", "ISSUED"}:
                    expected_query = expected_query.filter(estado=state.upper())
                else:
                    expected_query = expected_query.filter(expediente__estado=state)
            search = params.get("search", [""])[0].strip()
            if search:
                expected_query = expected_query.filter(
                    Q(titulo__icontains=search)
                    | Q(motivo__icontains=search)
                    | Q(causal__icontains=search)
                    | Q(numero_expediente__icontains=search)
                    | Q(expediente__numero__icontains=search)
                    | Q(snapshots_destinatarios__icontains=search)
                )
            expected = {str(pk) for pk in expected_query.values_list("pk", flat=True)}
            assert ids == expected
            for row in body:
                stored = all_requests[row["id"]]
                assert stored.solicitante_id == local_owner
                assert row["estado"] == stored.estado
                assert row["destinatarios_socios_ids"] == stored.destinatarios_socios_ids
                assert row["numero_expediente"] == stored.numero_expediente
                if stored.estado == "ISSUED":
                    assert row["numero"] == stored.expediente.numero
                    assert row["estado_procesal"] == stored.expediente.estado
            observed.update({"all_count": len(body), "all_ids": sorted(ids)})
            body = [row for row in body if row["id"] in fixture_request_ids]
            observed["fixture_count"] = len(body)
        return status_code, body

    source = inspect.getsource(original.verify_seeded_demo_http)
    source_hash = hashlib.sha256(source.encode()).hexdigest()
    replacements = (
        ("Expediente.objects.all()", "Expediente.objects.filter(pk__in=fixture_case_ids)", 2),
        (
            "SolicitudT01.objects.filter(solicitante=local_actor)",
            "SolicitudT01.objects.filter(solicitante=local_actor, pk__in=fixture_request_ids)", 1,
        ),
        (
            "SolicitudT01.objects.get(",
            "SolicitudT01.objects.filter(pk__in=fixture_request_ids).get(", 2,
        ),
    )
    for old, new, expected_count in replacements:
        assert source.count(old) == expected_count, "El helper estable cambió; revisar el harness."
        source = source.replace(old, new)
    scope = dict(vars(original))
    scope.update({"fixture_case_ids": fixture_case_ids, "fixture_request_ids": fixture_request_ids})
    exec(compile(source, "<scrum77-live-fixture-view>", "exec"), scope)
    report = scope["verify_seeded_demo_http"](request_json)
    assert report["http_checks"] == len(observations) == (
        141
        + 4 * sum(account.is_enabled for account in CATALOG.accounts)
        + 4 * len(CATALOG.preserved_accounts)
    )
    after = snapshot()
    assert before == after, "Los GET/login no deben alterar filas persistidas."
    return {
        "status": "ok", "verified_at_utc": datetime.now(timezone.utc).isoformat(),
        "database": database, "source_helper_sha256": source_hash,
        "mode": "live_fixture_subset_plus_complete_collection_checks",
        "http_checks": report["http_checks"],
        "http_status_counts": dict(Counter(str(item["status"]) for item in observations)),
        "fixture_report": report,
        "observed_counts": {
            "managed_cases_total": len(all_cases), "managed_cases_fixture": len(fixture_case_ids),
            "requests_total": len(all_requests), "requests_fixture": len(fixture_request_ids),
            "tables": len(before), "ownership_references": len(registry.export()),
        },
        "preserved_uat_case_ids": sorted(set(all_cases) - fixture_case_ids),
        "preserved_uat_request_ids": sorted(set(all_requests) - fixture_request_ids),
        "all_table_rows_unchanged": before == after,
        "table_counts": {key: value["count"] for key, value in before.items()},
        "table_hashes_before": {key: value["sha256"] for key, value in before.items()},
        "table_hashes_after": {key: value["sha256"] for key, value in after.items()},
        "collection_observations": [item for item in observations if "all_count" in item],
    }


if __name__ == "__main__":
    try:
        print(json.dumps(main(), ensure_ascii=False, indent=2))
    except Exception as error:
        print(json.dumps({"status": "error", "error_type": type(error).__name__,
                          "detail": "Falló un oráculo; revisar el harness sin exponer datos."}))
        sys.exit(1)
