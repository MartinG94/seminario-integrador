"""Contenido visible natural y upgrade owned que conserva actos y ediciones UAT."""

from typing import Any

import pytest
from django.core.exceptions import ValidationError
from django.core.management.base import CommandError

from tests.infrastructure.test_scrum77_schema_bootstrap import (
    bootstrap_database as bootstrap_database,
)
from tests.infrastructure.test_scrum77_seed_integration import prepare_seed, snapshot

pytestmark = pytest.mark.django_db(transaction=True, databases="__all__")


def legacy_content(seed: Any, monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    from core import demo_scenes
    from socios.demo_presentation import ScenePresentation, legacy_scene_reason

    real_serializer = demo_scenes.SolicitudT01Serializer

    class OriginalAnnexSerializer(real_serializer):
        def save(self, **kwargs: Any) -> Any:
            kwargs["anexo_relato"] = (
                "Hecho sintético, sin efectos sobre personas ni actos institucionales."
            )
            return super().save(**kwargs)

    def original(key: str) -> ScenePresentation:
        return ScenePresentation(
            title=f"SCRUM-77 [{key}]",
            reason=legacy_scene_reason(key),
            causal="Escena sintética de demostración",
            place="Sede AVEIT — espacio ficticio de demostración",
            witnesses="No se presentan testigos reales en esta demostración.",
        )

    with monkeypatch.context() as previous_source:
        previous_source.setattr(demo_scenes, "_scene_reason", legacy_scene_reason)
        previous_source.setattr(demo_scenes, "scene_presentation", original, raising=False)
        previous_source.setattr(demo_scenes, "SolicitudT01Serializer", OriginalAnnexSerializer)
        return seed.run_demo_seed()


def case_refs() -> dict[str, Any]:
    from core.models import DemoFixtureOwnership
    from expedientes.models import Expediente

    return {
        ref.fixture_key: ref
        for ref in DemoFixtureOwnership.objects.filter(namespace=Expediente._meta.db_table)
    }


def test_fresh_seed_writes_natural_cases_and_requests_without_extra_audits(
    bootstrap_database: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    from expedientes.models import Expediente, SolicitudT01
    from socios.demo_presentation import SCENE_PRESENTATIONS

    seed = prepare_seed(bootstrap_database, monkeypatch)
    seed.run_demo_seed()
    assert Expediente.objects.count() == 15
    for key, ref in case_refs().items():
        presentation = SCENE_PRESENTATIONS[key.removesuffix(".expediente")]
        case = Expediente.objects.get(pk=ref.object_key)
        assert case.motivo in (presentation.case_text, presentation.reason)
        assert not case.cambios_estado.filter(actor="DEMO_PRESENTATION_V1").exists()
    for request in SolicitudT01.objects.all():
        presentation = next(p for p in SCENE_PRESENTATIONS.values() if p.title == request.titulo)
        assert request.motivo == request.razon == request.anexo_relato == presentation.reason
        assert request.anexo_lugar == presentation.place
        assert request.anexo_testigos == presentation.witnesses
    before = snapshot(bootstrap_database)
    seed.run_demo_seed()
    assert snapshot(bootstrap_database) == before


def test_owned_legacy_upgrade_is_three_way_audited_and_preserves_uat_and_acts(
    bootstrap_database: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    from expedientes.models import CambioEstadoExpediente, Expediente
    from expedientes.services.workflow_service import ExpedienteWorkflowService
    from socios.demo_presentation import SCENE_PRESENTATIONS
    from socios.models import Socio

    seed = prepare_seed(bootstrap_database, monkeypatch)
    legacy_content(seed, monkeypatch)
    refs = case_refs()
    edited = Expediente.objects.get(pk=refs["cause.created.low"].object_key)
    edited.motivo = "Aclaración conservada durante la UAT"
    edited.save(update_fields=["motivo"])
    member = Socio.objects.get(legajo="99077001")
    uat = ExpedienteWorkflowService.open_expediente(
        motivo="Expediente adicional de la UAT", socio_ids=[member.pk], actor=member.legajo
    )
    before_cases = {case.pk: case for case in Expediente.objects.all()}
    original_history = list(CambioEstadoExpediente.objects.order_by("pk").values())
    before = snapshot(bootstrap_database)
    report = seed.run_demo_seed()
    after = snapshot(bootstrap_database)
    allowed = {"expedientes_expediente", "expedientes_cambio_estado", "core_demofixtureownership"}
    assert all(before[table] == after[table] for table in before if table not in allowed)
    assert Expediente.objects.count() == 16
    assert Expediente.objects.get(pk=edited.pk).motivo == edited.motivo
    assert Expediente.objects.get(pk=uat.pk).motivo == uat.motivo
    assert (
        list(
            CambioEstadoExpediente.objects.filter(pk__in=[row["id"] for row in original_history])
            .order_by("pk")
            .values()
        )
        == original_history
    )
    for key, ref in refs.items():
        case = Expediente.objects.get(pk=ref.object_key)
        previous = before_cases[case.pk]
        assert (
            case.estado,
            case.created_at,
            case.updated_at,
            case.plazo_limite_at,
            case.numero,
        ) == (
            previous.estado,
            previous.created_at,
            previous.updated_at,
            previous.plazo_limite_at,
            previous.numero,
        )
        if case.pk == edited.pk:
            continue
        assert case.motivo == SCENE_PRESENTATIONS[key.removesuffix(".expediente")].case_text
        audit = case.cambios_estado.get(actor="DEMO_PRESENTATION_V1")
        assert audit.estado_anterior == audit.estado_nuevo == case.estado
        assert any(item["fixture_key"] == f"{key}.presentation.v1" for item in report["fixtures"])
    assert seed.run_demo_seed() == report
    assert snapshot(bootstrap_database) == after


def test_presentation_upgrade_rolls_back_text_and_audit_together(
    bootstrap_database: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    from core.demo_fixtures import DemoFixtureRegistry

    seed = prepare_seed(bootstrap_database, monkeypatch)
    legacy_content(seed, monkeypatch)
    before = snapshot(bootstrap_database)
    real_record = DemoFixtureRegistry.record

    def fail_after_audit(registry: Any, key: str, *args: Any, **kwargs: Any) -> Any:
        value = real_record(registry, key, *args, **kwargs)
        if key.endswith(".presentation.v1"):
            raise RuntimeError("Fallo tras registrar presentación")
        return value

    monkeypatch.setattr(DemoFixtureRegistry, "record", fail_after_audit)
    with pytest.raises(RuntimeError, match="Fallo tras registrar"):
        seed.run_demo_seed()
    assert snapshot(bootstrap_database) == before


def test_foreign_legacy_placeholder_cannot_be_adopted_or_duplicated(
    bootstrap_database: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    from expedientes.services.workflow_service import ExpedienteWorkflowService
    from socios.demo_presentation import legacy_scene_reason
    from socios.models import Socio

    seed = prepare_seed(bootstrap_database, monkeypatch)
    seed.run_demo_seed()
    ExpedienteWorkflowService.open_expediente(
        motivo=legacy_scene_reason("cause.created.low"),
        socio_ids=[Socio.objects.get(legajo="99077001").pk],
        actor="UAT",
    )
    before = snapshot(bootstrap_database)
    with pytest.raises(CommandError, match="ajena|coincid"):
        seed.run_demo_seed()
    assert snapshot(bootstrap_database) == before


@pytest.mark.parametrize("kind", ["case", "request"])
def test_owned_reference_allows_another_uat_row_with_the_same_human_label(
    bootstrap_database: Any, monkeypatch: pytest.MonkeyPatch, kind: str
) -> None:
    from expedientes.models import SolicitudT01
    from expedientes.services.workflow_service import ExpedienteWorkflowService
    from socios.demo_presentation import SCENE_PRESENTATIONS
    from socios.models import Socio

    seed = prepare_seed(bootstrap_database, monkeypatch)
    original = seed.run_demo_seed()
    if kind == "case":
        ExpedienteWorkflowService.open_expediente(
            motivo=SCENE_PRESENTATIONS["cause.created.low"].case_text,
            socio_ids=[Socio.objects.get(legajo="99077001").pk],
            actor="UAT",
        )
    else:
        SolicitudT01.objects.create(
            solicitante=Socio.objects.get(legajo="99077005"),
            tipo_accion=SolicitudT01.TipoAccion.SANCTION,
            titulo=SCENE_PRESENTATIONS["t01.cd.draft"].title,
            motivo="Borrador distinto preparado durante la UAT",
        )
    before = snapshot(bootstrap_database)
    assert seed.run_demo_seed() == original
    assert snapshot(bootstrap_database) == before


@pytest.mark.parametrize("corrupt_field", ["state", "reason"])
def test_registered_presentation_audit_must_still_be_the_exact_nontransition_event(
    bootstrap_database: Any, monkeypatch: pytest.MonkeyPatch, corrupt_field: str
) -> None:
    from core.models import DemoFixtureOwnership
    from expedientes.models import CambioEstadoExpediente

    seed = prepare_seed(bootstrap_database, monkeypatch)
    legacy_content(seed, monkeypatch)
    seed.run_demo_seed()
    marker = DemoFixtureOwnership.objects.get(fixture_key="cause.created.low.presentation.v1")
    audit = CambioEstadoExpediente.objects.get(pk=marker.object_key)
    if corrupt_field == "state":
        audit.estado_nuevo = "justificando"
        audit.save(update_fields=["estado_nuevo"])
    else:
        audit.motivo = "Texto ajeno al evento de actualización aprobado"
        audit.save(update_fields=["motivo"])
    before = snapshot(bootstrap_database)
    with pytest.raises(ValidationError, match="auditoría"):
        seed.run_demo_seed()
    assert snapshot(bootstrap_database) == before


def test_presentation_audit_allows_later_valid_case_transitions_without_rewriting(
    bootstrap_database: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    from expedientes.services.workflow_service import ExpedienteWorkflowService

    seed = prepare_seed(bootstrap_database, monkeypatch)
    legacy_content(seed, monkeypatch)
    report = seed.run_demo_seed()
    case_id = report["mappings"]["causes"]["cause.created.low"]
    ExpedienteWorkflowService.transition(
        expediente_id=case_id,
        estado_nuevo="justificando",
        actor="UAT",
        motivo="Avance válido posterior a la actualización de presentación",
    )
    before = snapshot(bootstrap_database)
    assert seed.run_demo_seed() == report
    assert snapshot(bootstrap_database) == before
