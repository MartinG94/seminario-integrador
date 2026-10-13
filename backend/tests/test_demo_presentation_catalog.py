"""RF77-20: catálogo de títulos y relatos legibles, sin claves técnicas visibles."""

from socios.demo_catalog import CATALOG


def test_each_scene_and_request_has_a_concrete_human_presentation() -> None:
    from socios.demo_presentation import SCENE_PRESENTATIONS

    keys = {
        scene.fixture_key
        for scene in (*CATALOG.causes, *CATALOG.t01_scenes, *CATALOG.advanced_causes)
    }
    assert len(keys) == 17
    assert set(SCENE_PRESENTATIONS) == keys
    for key, presentation in SCENE_PRESENTATIONS.items():
        assert presentation.title.strip()
        assert len(presentation.title) <= 255
        assert presentation.reason.strip()
        assert presentation.title != presentation.reason
        assert "SCRUM" not in presentation.title.upper()
        assert "SCRUM" not in presentation.reason.upper()
        assert key not in presentation.title
        assert key not in presentation.reason
        assert presentation.case_text == f"{presentation.title}\n\n{presentation.reason}"


def test_emitted_scene_titles_distinguish_merit_from_sanction() -> None:
    from socios.demo_presentation import SCENE_PRESENTATIONS

    for scene in CATALOG.advanced_causes:
        if scene.stage != "emitido":
            continue
        title = SCENE_PRESENTATIONS[scene.fixture_key].title
        assert title.startswith("Reconocimiento" if scene.requested_points > 0 else "Sanción")
