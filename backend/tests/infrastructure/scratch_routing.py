"""Aislar los managers default de migraciones históricas en ensayos UUID propios."""

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from django.db import connections
from django.db.backends.base.base import BaseDatabaseWrapper


@contextmanager
def route_default_to_scratch(database: BaseDatabaseWrapper) -> Iterator[None]:
    parent = connections["default"]
    assert parent.settings_dict["NAME"].startswith("test_")
    assert database.settings_dict["NAME"].startswith(
        ("test_scrum77_bootstrap_", "test_scrum77_ddl_")
    )
    assert parent is not database

    def reject_parent_domain_sql(
        execute: Any, sql: str, params: Any, many: bool, context: Any
    ) -> Any:
        assert "expedientes_" not in sql.lower(), "RunPython no debe consultar/escribir en pytest."
        return execute(sql, params, many, context)

    connections["default"] = database
    try:
        with parent.execute_wrapper(reject_parent_domain_sql):
            yield
    finally:
        connections["default"] = parent
