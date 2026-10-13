"""Autor real, todos los afectados y proyección owned sin alterar documentos."""

from typing import Any

import pytest
from rest_framework.test import APIClient

from tests.infrastructure.test_scrum77_demo_presentation_upgrade import legacy_content
from tests.infrastructure.test_scrum77_schema_bootstrap import (
    bootstrap_database as bootstrap_database,
)
from tests.infrastructure.test_scrum77_seed_integration import prepare_seed, snapshot

pytestmark = pytest.mark.django_db(transaction=True, databases="__all__")


def test_every_case_displays_real_creator_all_members_and_precise_identity_namespaces(
    bootstrap_database: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    from core.models import DemoFixtureOwnership
    from expedientes.models import Expediente
    from socios.demo_catalog import CATALOG
    from socios.demo_presentation import SCENE_PRESENTATIONS
    from socios.models import Socio

    seed = prepare_seed(bootstrap_database, monkeypatch)
    report = seed.run_demo_seed()
    identities = {row["fixture_key"]: row for row in report["identities"]}
    accounts = {row.fixture_key: row.member_key for row in CATALOG.accounts}
    client = APIClient()
    client.force_authenticate(user=Socio.objects.get(legajo="99077005").user)
    before = snapshot(bootstrap_database)
    board = client.get("/api/v1/expedientes/board/")
    assert board.status_code == 200
    cards = {item["id"]: item for column in board.data["columns"] for item in column["cases"]}
    assert len(cards) == 15
    for fixture in (*CATALOG.causes, *CATALOG.t01_scenes, *CATALOG.advanced_causes):
        if getattr(fixture, "status", None) == "DRAFT":
            continue
        key = fixture.fixture_key
        case_key = f"{key}.expediente" if key.startswith("t01.") else key
        ref = DemoFixtureOwnership.objects.get(
            fixture_key=case_key, namespace=Expediente._meta.db_table
        )
        expected_creator = identities[accounts[fixture.creator_account_key]]
        expected_members = {
            identities[key]["local_socio_id"] for key in fixture.recipient_member_keys
        }
        payload = client.get(f"/api/v1/expedientes/{ref.object_key}/")
        assert payload.status_code == 200
        for row in (cards[int(ref.object_key)], payload.data):
            assert row["title"] == SCENE_PRESENTATIONS[key].title
            assert row["motivo"] == SCENE_PRESENTATIONS[key].reason
            assert row["creator"]["local_socio_id"] == expected_creator["local_socio_id"]
            assert (
                row["creator"]["institutional_number"] == expected_creator["institutional_number"]
            )
            assert row["creator"]["academic_number"] == str(expected_creator["academic_number"])
            assert row["creator"]["login_identifier"] == str(expected_creator["academic_number"])
            assert {
                member["local_socio_id"] for member in row["involved_members"]
            } == expected_members
        for key in fixture.recipient_member_keys:
            client.force_authenticate(
                user=Socio.objects.get(pk=identities[key]["local_socio_id"]).user
            )
            own = client.get("/api/v1/expedientes/mis-expedientes/")
            assert own.status_code == 200
            own_row = next(item for item in own.data if item["id"] == int(ref.object_key))
            assert {
                member["local_socio_id"] for member in own_row["involved_members"]
            } == expected_members
        client.force_authenticate(user=Socio.objects.get(legajo="99077005").user)
    assert snapshot(bootstrap_database) == before


def test_legacy_t01_is_projected_and_searchable_without_rewriting_issued_documents(
    bootstrap_database: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    from core.models import DemoFixtureOwnership
    from expedientes.models import SolicitudT01
    from socios.demo_catalog import CATALOG
    from socios.demo_presentation import SCENE_PRESENTATIONS

    seed = prepare_seed(bootstrap_database, monkeypatch)
    legacy_content(seed, monkeypatch)
    before = snapshot(bootstrap_database)
    client = APIClient()
    for fixture in CATALOG.t01_scenes:
        ref = DemoFixtureOwnership.objects.get(fixture_key=fixture.fixture_key)
        request = SolicitudT01.objects.get(pk=ref.object_key)
        client.force_authenticate(user=request.solicitante.user)
        presentation = SCENE_PRESENTATIONS[fixture.fixture_key]
        detail = client.get(f"/api/v1/expedientes/{request.pk}/")
        assert detail.status_code == 200
        assert detail.data["titulo"] == presentation.title
        assert detail.data["motivo"] == detail.data["razon"] == presentation.reason
        rows = client.get("/api/v1/expedientes/mis-solicitudes/", {"search": presentation.title})
        assert rows.status_code == 200
        assert any(str(row["id"]) == str(request.pk) for row in rows.data)
        assert request.titulo == f"SCRUM-77 [{fixture.fixture_key}]"
    assert snapshot(bootstrap_database) == before


def test_creator_local_only_remains_unknown_institutionally_and_primary_member_is_kept(
    bootstrap_database: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    from django.contrib.auth import get_user_model

    from expedientes.models import Expediente
    from expedientes.services.workflow_service import ExpedienteWorkflowService
    from socios.models import Socio

    seed = prepare_seed(bootstrap_database, monkeypatch)
    seed.run_demo_seed()
    user = get_user_model().objects.create_user(
        username="local_creator", first_name="Autor", last_name="Local"
    )
    creator = Socio.objects.create(
        user=user,
        legajo="local_creator",
        first_name="Otro",
        last_name="Perfil",
        role="CD",
        social_year=3,
        email="local-creator@scrum77.test",
    )
    affected = Socio.objects.get(legajo="99077001")
    full_reason = "Motivo particular de la UAT\n\nSegundo párrafo con sus circunstancias completas."
    case = ExpedienteWorkflowService.open_expediente(
        motivo=full_reason, socio_ids=[affected.pk], actor=user.username
    )
    # Comportamiento legado compatible cuando aún no se había materializado el M2M.
    case.socios.clear()
    client = APIClient()
    client.force_authenticate(user=user)
    payload = client.get(f"/api/v1/expedientes/{case.pk}/")
    assert payload.status_code == 200
    assert payload.data["creator"] == {
        "local_socio_id": creator.pk,
        "full_name": "Autor Local",
        "login_identifier": user.username,
        "institutional_number": None,
        "academic_number": None,
    }
    assert [row["local_socio_id"] for row in payload.data["involved_members"]] == [affected.pk]
    assert [row["id"] for row in payload.data["socios"]] == [affected.pk]
    assert payload.data["motivo"] == full_reason
    assert Expediente.objects.get(pk=case.pk).motivo == full_reason


def test_nonpositive_institutional_reference_never_becomes_a_member_identifier(
    bootstrap_database: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    from django.contrib.auth import get_user_model

    from expedientes.services.workflow_service import ExpedienteWorkflowService
    from padron.models import Socio as InstitutionalSocio
    from socios.models import Socio

    seed = prepare_seed(bootstrap_database, monkeypatch)
    seed.run_demo_seed()
    user = get_user_model().objects.create_user(username="invalid_reference_creator")
    creator = Socio.objects.create(
        user=user,
        legajo="invalid_reference",
        first_name="Autor",
        last_name="Local",
        role="CD",
        social_year=3,
        email="invalid-reference@scrum77.test",
    )
    corrupt = InstitutionalSocio.objects.get(pk=770001)
    corrupt.pk = -77
    corrupt.user_id = user.pk
    corrupt.nroDoc = 88077999
    corrupt._allow_write = True
    corrupt.save(force_insert=True)
    affected = Socio.objects.get(legajo="99077001")
    case = ExpedienteWorkflowService.open_expediente(
        motivo="Consulta de identidad inválida",
        socio_ids=[affected.pk],
        actor=user.username,
    )
    client = APIClient()
    client.force_authenticate(user=user)
    payload = client.get(f"/api/v1/expedientes/{case.pk}/")
    assert payload.status_code == 200
    assert payload.data["creator"]["local_socio_id"] == creator.pk
    assert payload.data["creator"]["institutional_number"] is None
    assert payload.data["creator"]["academic_number"] is None


def test_request_projection_preserves_each_edited_field_including_nonoriginal_annex_text(
    bootstrap_database: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    from core.models import DemoFixtureOwnership
    from expedientes.models import SolicitudT01
    from socios.demo_presentation import legacy_scene_reason

    seed = prepare_seed(bootstrap_database, monkeypatch)
    legacy_content(seed, monkeypatch)
    ref = DemoFixtureOwnership.objects.get(fixture_key="t01.cd.draft")
    request = SolicitudT01.objects.get(pk=ref.object_key)
    request.titulo = "Título ajustado durante la UAT"
    request.motivo = "Motivo de la UAT\n\nAclaración adicional que debe conservarse."
    request.anexo_relato = legacy_scene_reason("t01.cd.draft")
    request.save()
    before = snapshot(bootstrap_database)
    client = APIClient()
    client.force_authenticate(user=request.solicitante.user)
    detail = client.get(f"/api/v1/expedientes/{request.pk}/")
    assert detail.status_code == 200
    for field in ("titulo", "motivo", "anexo_relato"):
        assert detail.data[field] == getattr(request, field)
    rows = client.get("/api/v1/expedientes/mis-solicitudes/", {"search": request.titulo})
    assert rows.status_code == 200
    assert any(str(row["id"]) == str(request.pk) for row in rows.data)
    assert snapshot(bootstrap_database) == before
