"""Catálogo autorizado de escenas históricas adicionales, sin carga ni reloj."""

from collections import Counter
from dataclasses import replace
from datetime import datetime, timezone
from decimal import Decimal

import pytest

from socios import demo_catalog as catalog_module


def test_advanced_catalog_has_requested_states_and_individual_junior_emissions() -> None:
    catalog = catalog_module.CATALOG
    scenes = catalog.advanced_causes
    assert Counter(scene.stage for scene in scenes) == {
        "revision_resolucion": 3,
        "espera_resolucion": 1,
        "pendiente_correos": 2,
        "emitido": 4,
    }
    assert len({scene.fixture_key for scene in scenes}) == 10
    assert all(
        scene.opened_at < scene.justification_started_at < scene.reviewed_at for scene in scenes
    )
    assert all(scene.updated_at <= datetime(2026, 10, 12, tzinfo=timezone.utc) for scene in scenes)
    emitted = [scene for scene in scenes if scene.stage == "emitido"]
    assert [(scene.recipient_member_keys, scene.requested_points) for scene in emitted] == [
        (("member.g62.01",), Decimal("2")),
        (("member.g62.02",), Decimal("-1")),
        (("member.g63.01",), Decimal("-2")),
        (("member.g63.02",), Decimal("1")),
    ]
    balances = catalog_module.expected_balances(catalog)
    assert [balances[f"member.{key}"] for key in ("g62.01", "g62.02", "g63.01", "g63.02")] == [
        Decimal("2"),
        Decimal("-1"),
        Decimal("-2"),
        Decimal("1"),
    ]
    assert balances["member.g57.01"] == Decimal("2")
    assert sum(balances.values()) == Decimal("1")
    assert len(catalog.causes) == 3 and len(catalog.t01_scenes) == 4
    assert len(catalog.historical_movements) == 8
    catalog_module.validate_catalog(catalog)


@pytest.mark.parametrize(
    "field,value",
    [
        ("stage", "creado"),
        ("creator_account_key", "account.g62.01"),
        ("recipient_member_keys", ("member.missing",)),
        ("recipient_member_keys", ()),
        ("requested_points", Decimal("0.33")),
        ("opened_at", datetime(2026, 9, 1)),
        ("justification_started_at", datetime(2026, 1, 1, tzinfo=timezone.utc)),
        ("reviewed_at", datetime(2027, 1, 1, tzinfo=timezone.utc)),
    ],
)
def test_advanced_catalog_rejects_invalid_history(field: str, value: object) -> None:
    catalog = catalog_module.CATALOG
    scene = replace(catalog.advanced_causes[0], **{field: value})
    with pytest.raises(ValueError):
        catalog_module.validate_catalog(
            replace(catalog, advanced_causes=(scene, *catalog.advanced_causes[1:]))
        )


def test_advanced_catalog_rejects_missing_scene_or_duplicate_key() -> None:
    catalog = catalog_module.CATALOG
    for scenes in (
        catalog.advanced_causes[:-1],
        (catalog.advanced_causes[0], *catalog.advanced_causes[:-1]),
    ):
        with pytest.raises(ValueError):
            catalog_module.validate_catalog(replace(catalog, advanced_causes=scenes))
