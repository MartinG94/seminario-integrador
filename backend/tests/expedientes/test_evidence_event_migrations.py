"""Compatibilidad de las migraciones paralelas de evidencia y eventos."""

from django.db.migrations.loader import MigrationLoader


def test_evidence_and_events_share_a_conflict_free_migration_graph() -> None:
    loader = MigrationLoader(None)

    assert loader.detect_conflicts() == {}

    apps = loader.project_state().apps
    for model_name in (
        "EventoInstitucional",
        "AsistenciaEvento",
        "RegistroApercibimiento",
        "EvidenciaDescargo",
        "AuditoriaDescargaEvidencia",
    ):
        assert apps.get_model("expedientes", model_name) is not None
