"""TS77.43: el namespace local conserva su PK BIGINT, aislada de pytest."""

from typing import Any

import pytest
from django.contrib.auth import get_user_model
from django.db.migrations.executor import MigrationExecutor
from rest_framework.test import APIClient

from socios.models import Role, Socio
from tests.infrastructure.test_scrum77_schema_bootstrap import (
    bootstrap_database as bootstrap_database,
)


@pytest.mark.django_db(transaction=True, databases="__all__")
@pytest.mark.parametrize("source", ["local", None])
def test_local_bigint_identity_is_read_without_advancing_the_parent_sequence(
    bootstrap_database: Any, monkeypatch: pytest.MonkeyPatch, source: str | None
) -> None:
    from socios import views

    # Este escenario sólo prepara el padrón local managed; no acredita saldo institucional.
    monkeypatch.setenv("PADRON_ADAPTER", "mock")
    executor = MigrationExecutor(bootstrap_database)
    executor.migrate(executor.loader.graph.leaf_nodes())

    class EmptyInstitutionalRepository:
        def get_by_id(self, number: int) -> None:
            return None

        def get_by_legajo(self, legajo: str) -> None:
            return None

    monkeypatch.setattr(views, "get_padron_repository", lambda: EmptyInstitutionalRepository())
    user = get_user_model().objects.create_user(username="bigint-local", email="bigint@aveit.test")
    socio = Socio.objects.create(
        pk=2147483648,
        user=user,
        legajo="BIG-43",
        first_name="Socio",
        last_name="BIGINT sintético",
        email="bigint@aveit.test",
        social_year=2,
        role=Role.SOCIO,
    )
    with bootstrap_database.cursor() as cursor:
        cursor.execute(
            "SELECT COLUMN_TYPE FROM information_schema.COLUMNS "
            "WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='socios_socio' AND COLUMN_NAME='id'"
        )
        assert cursor.fetchone() == ("bigint",)
    before = list(Socio.objects.values())
    client = APIClient()
    client.force_authenticate(user)
    params = {} if source is None else {"identity_source": source}
    response = client.get(f"/api/v1/socios/{socio.pk}/legajo/", params)
    assert response.status_code == 200
    assert response.data["id"] == 2147483648
    assert response.data["legajo"] == "BIG-43"
    assert response.data["points_balance"] is None
    assert list(Socio.objects.values()) == before
