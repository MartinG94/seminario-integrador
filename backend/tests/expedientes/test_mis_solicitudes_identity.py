"""TS77.22: los involucrados T01 se leen en el namespace de su proveedor."""

from dataclasses import replace
from types import SimpleNamespace
from typing import Any

import pytest
from django.db import OperationalError, connection
from rest_framework.test import APIClient

from expedientes.models import SolicitudT01
from padron.adapters import DatabasePadronAdapter
from padron.models import Socio as InstitutionalSocio
from padron.models import SocioEstudio
from padron.models import Subcomision as InstitutionalSubcommission
from socios.models import Role, Socio
from tests.legacy_schema import create_legacy_record
from tests.test_scrum77_legajo_identity import (
    identity_satellite_tables as identity_satellite_tables,
)


@pytest.fixture
def identity_request(make_socio: Any, monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    authority = make_socio(legajo="8822001", role=Role.CD)
    shadow = make_socio(legajo="8822002")
    subcommission = create_legacy_record(
        InstitutionalSubcommission, codSubcomision=8822, nombre="Subcomisión institucional"
    )
    members = []
    for index, number in enumerate((shadow.pk, authority.pk)):
        member = create_legacy_record(
            InstitutionalSocio,
            nroSocio=number,
            nombre=f"Nombre institucional {index}",
            apellido=f"Apellido institucional {index}",
            subcomision=subcommission,
            anoSocial=4,
        )
        create_legacy_record(
            SocioEstudio,
            compositeKey=number * 100 + 22,
            socio=member,
            nroLegajo=9922001 + index,
            codEspecialidad=1,
        )
        members.append(member)
    repository = DatabasePadronAdapter()
    monkeypatch.setattr("expedientes.serializers.get_padron_repository", lambda: repository)
    request = SolicitudT01.objects.create(
        solicitante=authority,
        tipo_accion="SANCTION",
        titulo="Borrador institucional",
        destinatarios_socios_ids=[member.pk for member in members],
    )
    client = APIClient(raise_request_exception=False)
    client.force_authenticate(authority.user)
    return {
        "authority": authority,
        "shadow": shadow,
        "members": members,
        "repository": repository,
        "request": request,
        "client": client,
    }


@pytest.mark.django_db
def test_draft_uses_institutional_people_in_input_order_despite_local_pk_collisions(
    identity_request: dict[str, Any],
) -> None:
    world = identity_request
    before = list(SolicitudT01.objects.order_by("pk").values())
    local_before = list(Socio.objects.order_by("pk").values())
    writes = []

    def observe(execute: Any, sql: str, params: Any, many: bool, context: Any) -> Any:
        if sql.lstrip().upper().startswith(("INSERT", "UPDATE", "DELETE")):
            writes.append(sql)
        return execute(sql, params, many, context)

    with connection.execute_wrapper(observe):
        response = world["client"].get("/api/v1/expedientes/mis-solicitudes/")
    assert response.status_code == 200
    assert response.data[0]["involucrados"] == [
        {
            "socio_id": member.pk,
            "legajo": str(9922001 + index),
            "first_name": member.nombre,
            "last_name": member.apellido,
            "subcomision": "Subcomisión institucional",
        }
        for index, member in enumerate(world["members"])
    ]
    assert writes == []
    assert list(SolicitudT01.objects.order_by("pk").values()) == before
    assert list(Socio.objects.order_by("pk").values()) == local_before


@pytest.mark.django_db
def test_draft_without_academic_legajo_preserves_null(
    identity_request: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    world = identity_request
    first = world["members"][0]
    dto = replace(world["repository"].get_by_id(first.pk), legajo=None, subcomision=None)
    monkeypatch.setattr(
        "expedientes.serializers.get_padron_repository",
        lambda: SimpleNamespace(
            get_by_id=lambda identifier: dto if identifier == first.pk else None
        ),
    )
    response = world["client"].get("/api/v1/expedientes/mis-solicitudes/")
    assert response.status_code == 200
    assert response.data[0]["involucrados"] == [
        {
            "socio_id": first.pk,
            "legajo": None,
            "first_name": first.nombre,
            "last_name": first.apellido,
            "subcomision": "Sin subcomisión",
        }
    ]


@pytest.mark.django_db
@pytest.mark.parametrize("snapshot_field", ["snapshots_destinatarios", "snapshot_destinatario"])
def test_historical_snapshot_has_priority_without_query_or_rewrite(
    identity_request: dict[str, Any], monkeypatch: pytest.MonkeyPatch, snapshot_field: str
) -> None:
    world = identity_request
    snapshot = {
        "socio_id": 701,
        "legajo": None,
        "first_name": "Nombre histórico",
        "last_name": "Apellido histórico",
        "category": "PASSIVE",
        "social_year": 3,
        "subcomision": {"name": "Subcomisión histórica"},
    }
    request = world["request"]
    setattr(
        request,
        snapshot_field,
        [snapshot] if snapshot_field == "snapshots_destinatarios" else snapshot,
    )
    request.save(update_fields=[snapshot_field])

    def reject_query() -> None:
        pytest.fail("Un snapshot existente no debe consultar el padrón actual.")

    monkeypatch.setattr("expedientes.serializers.get_padron_repository", reject_query)
    before = list(SolicitudT01.objects.values())
    response = world["client"].get("/api/v1/expedientes/mis-solicitudes/")
    assert response.status_code == 200
    assert response.data[0]["involucrados"] == [
        {
            "socio_id": 701,
            "legajo": None,
            "first_name": "Nombre histórico",
            "last_name": "Apellido histórico",
            "subcomision": "Subcomisión histórica",
        }
    ]
    assert list(SolicitudT01.objects.values()) == before


@pytest.mark.django_db
def test_missing_institutional_reference_never_returns_a_colliding_local_person(
    identity_request: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        "expedientes.serializers.get_padron_repository",
        lambda: SimpleNamespace(get_by_id=lambda identifier: None),
    )
    response = identity_request["client"].get("/api/v1/expedientes/mis-solicitudes/")
    assert response.status_code == 200
    assert response.data[0]["involucrados"] == []


@pytest.mark.django_db
@pytest.mark.parametrize("invalid_identity", [True, "string", "different"])
def test_provider_identity_mismatch_never_returns_an_unrelated_person(
    identity_request: dict[str, Any], monkeypatch: pytest.MonkeyPatch, invalid_identity: Any
) -> None:
    world = identity_request
    first = world["members"][0]
    identifier = (
        str(first.pk)
        if invalid_identity == "string"
        else first.pk + 1
        if invalid_identity == "different"
        else invalid_identity
    )
    dto = replace(world["repository"].get_by_id(first.pk), socio_id=identifier)
    monkeypatch.setattr(
        "expedientes.serializers.get_padron_repository",
        lambda: SimpleNamespace(get_by_id=lambda identifier: dto),
    )
    response = world["client"].get("/api/v1/expedientes/mis-solicitudes/")
    assert response.status_code == 200
    assert response.data[0]["involucrados"] == []


@pytest.mark.django_db
@pytest.mark.parametrize("malformed_ids", [[True], ["1"], {"1": 1}])
def test_malformed_stored_ids_do_not_resolve_as_local_or_institutional_people(
    identity_request: dict[str, Any], monkeypatch: pytest.MonkeyPatch, malformed_ids: Any
) -> None:
    request = identity_request["request"]
    request.destinatarios_socios_ids = malformed_ids
    request.save(update_fields=["destinatarios_socios_ids"])

    def reject_lookup(identifier: Any) -> None:
        pytest.fail("Una referencia JSON inválida no debe consultar el proveedor.")

    monkeypatch.setattr(
        "expedientes.serializers.get_padron_repository",
        lambda: SimpleNamespace(get_by_id=reject_lookup),
    )
    response = identity_request["client"].get("/api/v1/expedientes/mis-solicitudes/")
    assert response.status_code == 200
    assert response.data[0]["involucrados"] == []


@pytest.mark.django_db
def test_provider_failure_is_sanitized_and_never_falls_back_to_local_pk(
    identity_request: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    def fail(identifier: int) -> None:
        raise OperationalError("private-provider-diagnostic")

    monkeypatch.setattr(
        "expedientes.serializers.get_padron_repository", lambda: SimpleNamespace(get_by_id=fail)
    )
    response = identity_request["client"].get("/api/v1/expedientes/mis-solicitudes/")
    assert response.status_code == 503
    assert "private-provider-diagnostic" not in str(response.data)
