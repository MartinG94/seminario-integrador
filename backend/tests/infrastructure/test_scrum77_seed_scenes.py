"""TS77.12–14: escenas reales, propiedad y temporalidad en schemas MySQL propios."""

import importlib
from collections import Counter
from decimal import Decimal
from typing import Any

import pytest
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from expedientes.domain.calendar import compute_business_deadline
from expedientes.domain.holiday_provider import Argentina2026HolidayProvider
from expedientes.models import (
    CambioEstadoExpediente,
    EstadoExpedienteEnum,
    Expediente,
    ExpedienteNumberSequence,
    SolicitudT01,
)
from expedientes.serializers import EmitirT01Serializer
from notifications.models import EmailOutbox
from socios.demo_catalog import CATALOG
from tests.infrastructure.test_scrum77_schema_bootstrap import (
    bootstrap_database as bootstrap_database,
)

pytestmark = pytest.mark.django_db(transaction=True, databases="__all__")


def prepare_scene_test(database: Any, monkeypatch: pytest.MonkeyPatch) -> tuple[Any, Any, Any]:
    """Importar primero la API pendiente para que el rojo identifique esa carencia."""
    scenes = importlib.import_module("core.demo_scenes")
    fixtures = importlib.import_module("core.demo_fixtures")
    members_module = importlib.import_module("core.demo_members")
    seed = importlib.import_module("core.demo_seed")
    monkeypatch.setattr(seed, "assert_demo_seed_environment", lambda *args, **kwargs: None)
    monkeypatch.setattr(seed, "assert_demo_seed_database", lambda *args, **kwargs: None)
    monkeypatch.setattr(settings, "DEBUG", True)
    importlib.import_module("core.demo_schema").prepare_schema(database)
    registry = fixtures.DemoFixtureRegistry(CATALOG.profile)
    with fixtures.demo_fixture_lock(registry.connection):
        with transaction.atomic():
            members = members_module.load_demo_members(CATALOG, registry)
    return scenes, registry, members


def load_scenes(scenes: Any, registry: Any, members: Any) -> Any:
    fixtures = importlib.import_module("core.demo_fixtures")
    with fixtures.demo_fixture_lock(registry.connection):
        with transaction.atomic():
            return scenes.load_demo_scenes(CATALOG, registry, members)


def test_three_created_and_two_issued_causes_use_server_numbers_and_individual_links(
    bootstrap_database: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    scenes, registry, members = prepare_scene_test(bootstrap_database, monkeypatch)
    result = load_scenes(scenes, registry, members)
    assert len(result.causes) == 3
    assert len(result.issued_causes) == 2
    cases = list(Expediente.objects.order_by("pk"))
    assert len(cases) == 5
    assert Counter(case.estado for case in cases) == {"creado": 3, "justificando": 2}
    year = timezone.localdate().year
    assert [case.numero for case in cases] == [f"EXP-{i:04d}/{year}" for i in range(1, 6)]
    assert ExpedienteNumberSequence.objects.get(year=year).last_value == 5
    multi = result.causes["cause.created.urgent.multi"]
    assert set(multi.socios.values_list("legajo", flat=True)) == {"99077001", "99077013"}
    assert multi.socio_id in multi.socios.values_list("pk", flat=True)
    assert multi.puntos == Decimal("-3")
    assert multi.urgencia == "urgente"
    assert len(EstadoExpedienteEnum.values) == 6


def test_two_requesters_have_one_draft_and_one_issued_with_canonical_snapshots(
    bootstrap_database: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    scenes, registry, members = prepare_scene_test(bootstrap_database, monkeypatch)
    result = load_scenes(scenes, registry, members)
    assert len(result.t01s) == 4
    for account in ("account.g58.01", "account.g59.01"):
        rows = SolicitudT01.objects.filter(solicitante=members.accounts[account])
        assert Counter(rows.values_list("estado", flat=True)) == {"DRAFT": 1, "ISSUED": 1}
    draft = result.t01s["t01.cd.draft"]
    assert draft.puntos is None
    assert draft.destinatarios_socios_ids == []
    assert draft.expediente_id is None and draft.issued_at is None
    emission = EmitirT01Serializer(data={}, context={"solicitud": draft})
    with pytest.raises(ValidationError):
        emission.is_valid(raise_exception=True)
    issued = result.t01s["t01.cd.issued.multi"]
    assert issued.destinatarios_socios_ids == [770001, 770006]
    assert [(dto["category"], dto["social_year"]) for dto in issued.snapshots_destinatarios] == [
        ("EX_TRAVELER", None),
        ("SENIOR", 6),
    ]
    assert issued.numero_expediente.startswith(f"T01-{timezone.localdate().year}-")
    assert issued.expediente.urgencia == "urgente"
    assert result.t01s["t01.authority.issued"].expediente.urgencia == "baja"


def test_opening_deadlines_are_current_business_days_and_audited_without_email_dispatch(
    bootstrap_database: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    scenes, registry, members = prepare_scene_test(bootstrap_database, monkeypatch)
    before = timezone.now()
    result = load_scenes(scenes, registry, members)
    after = timezone.now()
    for case in result.causes.values():
        assert case.plazo_inicio_at is None and case.plazo_limite_at is None
        assert before <= case.created_at <= after
        assert case.cambios_estado.count() == 1
    for case in result.issued_causes.values():
        assert before <= case.plazo_inicio_at <= after
        assert case.esta_en_plazo(after)
        assert case.plazo_limite_at == compute_business_deadline(
            start_at=case.plazo_inicio_at,
            business_days=5,
            holiday_provider=Argentina2026HolidayProvider(),
        )
        changes = list(case.cambios_estado.order_by("pk"))
        assert [(row.estado_anterior, row.estado_nuevo) for row in changes] == [
            ("creado", "creado"),
            ("creado", "justificando"),
        ]
        assert all(
            row.actor and row.motivo and before <= row.fecha_hora <= after for row in changes
        )
    assert not EmailOutbox.objects.exists()


def test_repetition_preserves_valid_case_and_draft_edits_audit_and_number_sequence(
    bootstrap_database: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    scenes, registry, members = prepare_scene_test(bootstrap_database, monkeypatch)
    first = load_scenes(scenes, registry, members)
    case = first.causes["cause.created.low"]
    case.motivo = "Edición válida posterior del TD"
    case.urgencia = "urgente"
    case.save(update_fields=["motivo", "urgencia", "updated_at"])
    draft = first.t01s["t01.authority.draft"]
    draft.titulo = "Borrador revisado por su solicitante"
    draft.save()
    before = {
        "causes": list(Expediente.objects.order_by("pk").values()),
        "requests": list(SolicitudT01.objects.order_by("pk").values()),
        "audit": list(CambioEstadoExpediente.objects.order_by("pk").values()),
        "links": list(Expediente.socios.through.objects.order_by("pk").values()),
        "sequence": list(ExpedienteNumberSequence.objects.values()),
    }
    second = load_scenes(scenes, registry, members)
    assert second.causes["cause.created.low"].pk == case.pk
    assert list(Expediente.objects.order_by("pk").values()) == before["causes"]
    assert list(SolicitudT01.objects.order_by("pk").values()) == before["requests"]
    assert list(CambioEstadoExpediente.objects.order_by("pk").values()) == before["audit"]
    assert list(Expediente.socios.through.objects.order_by("pk").values()) == before["links"]
    assert list(ExpedienteNumberSequence.objects.values()) == before["sequence"]


def test_all_compound_scene_objects_have_property_records_and_sequence_is_reference(
    bootstrap_database: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    scenes, registry, members = prepare_scene_test(bootstrap_database, monkeypatch)
    load_scenes(scenes, registry, members)
    ownership = importlib.import_module("core.models").DemoFixtureOwnership
    for model in (Expediente, SolicitudT01, CambioEstadoExpediente, Expediente.socios.through):
        ids = {str(pk) for pk in model.objects.values_list("pk", flat=True)}
        records = ownership.objects.filter(namespace=model._meta.db_table)
        assert {str(record.object_key) for record in records} == ids
    record = registry.get(f"reference.expediente-sequence.{timezone.localdate().year}")
    assert record is not None and record.owned is False


def test_failed_late_scene_rolls_back_causes_t01_audit_links_and_formal_counter(
    bootstrap_database: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    scenes, registry, members = prepare_scene_test(bootstrap_database, monkeypatch)
    original = EmitirT01Serializer.save
    issued_calls = 0

    def fail_second_issued(self: EmitirT01Serializer) -> SolicitudT01:
        nonlocal issued_calls
        result = original(self)
        issued_calls += 1
        if issued_calls == 2:
            raise RuntimeError("Fallo tardío sintético después de la apertura real")
        return result

    sequence = list(ExpedienteNumberSequence.objects.values())
    ownership = importlib.import_module("core.models").DemoFixtureOwnership
    record_ids = list(ownership.objects.order_by("pk").values_list("pk", flat=True))
    monkeypatch.setattr(EmitirT01Serializer, "save", fail_second_issued)
    with pytest.raises(RuntimeError, match="Fallo tardío sintético"):
        load_scenes(scenes, registry, members)
    assert not Expediente.objects.exists() and not SolicitudT01.objects.exists()
    assert not CambioEstadoExpediente.objects.exists()
    assert not Expediente.socios.through.objects.exists()
    assert list(ExpedienteNumberSequence.objects.values()) == sequence
    assert list(ownership.objects.order_by("pk").values_list("pk", flat=True)) == record_ids
