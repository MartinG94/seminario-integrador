"""Altas demo protegidas y propiedad persistente; nunca actualiza ni elimina filas."""

from collections.abc import Callable, Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any, TypeVar

from django.apps import apps
from django.core.exceptions import ValidationError
from django.core.management.base import CommandError
from django.db import IntegrityError, connections, models
from django.db.backends.base.base import BaseDatabaseWrapper

from core.demo_schema import read_contracts
from core.models import DemoFixtureOwnership
from socios.demo_catalog import CATALOG

T = TypeVar("T", bound=models.Model)
_LOCK_GENERATIONS: ContextVar[dict[int, object] | None] = ContextVar(
    "scrum77_demo_lock_generations", default=None
)


def _assert_environment(profile: str, database: BaseDatabaseWrapper) -> None:
    # La importación diferida evita que el orquestador cargue sus propios loaders al importar.
    from core.demo_seed import assert_demo_seed_database, assert_demo_seed_environment

    assert_demo_seed_environment(profile)
    assert_demo_seed_database(database)


def _assert_schema(database: BaseDatabaseWrapper) -> None:
    from core.demo_seed import assert_demo_seed_schema

    assert_demo_seed_schema(database)


def _assert_lock(database: BaseDatabaseWrapper) -> None:
    name = f"scrum77-schema:{database.settings_dict['NAME']}"
    with database.cursor() as cursor:
        cursor.execute("SELECT IS_USED_LOCK(%s), CONNECTION_ID()", [name])
        owner, current = cursor.fetchone()
    if owner is None or owner != current:
        raise CommandError("La escritura demo requiere el bloqueo compartido de esta conexión.")


@contextmanager
def demo_fixture_lock(
    connection: BaseDatabaseWrapper | None = None, *, profile: str = CATALOG.profile
) -> Iterator[None]:
    """Serializa DML y comparte la exclusión existente de prepare/transition."""
    database = connection or connections["default"]
    _assert_environment(profile, database)
    if database.in_atomic_block:
        raise CommandError("El bloqueo de la carga debe adquirirse antes de la transacción.")
    name = f"scrum77-schema:{database.settings_dict['NAME']}"
    with database.cursor() as cursor:
        cursor.execute("SELECT GET_LOCK(%s, 0)", [name])
        if cursor.fetchone() != (1,):
            raise CommandError(
                "Hay otra preparación o carga demo en curso; no se realizaron cambios."
            )
    generations = dict(_LOCK_GENERATIONS.get() or {})
    generations[id(database)] = object()
    context_token = _LOCK_GENERATIONS.set(generations)
    try:
        yield
    finally:
        _LOCK_GENERATIONS.reset(context_token)
        with database.cursor() as cursor:
            cursor.execute("SELECT RELEASE_LOCK(%s)", [name])


class DemoFixtureRegistry:
    """Resuelve por propiedad, preserva ediciones y rechaza filas ajenas coincidentes."""

    def __init__(self, profile: str, *, connection: BaseDatabaseWrapper | None = None) -> None:
        self.profile = profile
        self.connection = connection or connections["default"]
        _assert_environment(profile, self.connection)
        _assert_schema(self.connection)
        self._schema_lock_generation: object | None = None
        self._legacy = {contract.name: contract for contract in read_contracts()}
        self._managed = {
            model._meta.db_table: model
            for model in apps.get_models(include_auto_created=True)
            if model._meta.managed
        }

    def _check_write(self) -> None:
        _assert_environment(self.profile, self.connection)
        if not self.connection.in_atomic_block:
            raise CommandError(
                "La carga y su registro de propiedad requieren una transacción exterior."
            )
        _assert_lock(self.connection)
        generation = (_LOCK_GENERATIONS.get() or {}).get(id(self.connection))
        # Sin contexto propio (GET_LOCK manual), nunca se reutiliza una acreditación.
        if generation is None or generation is not self._schema_lock_generation:
            _assert_schema(self.connection)
            self._schema_lock_generation = generation

    def get(self, key: str) -> DemoFixtureOwnership | None:
        return (
            DemoFixtureOwnership.objects.using(self.connection.alias)
            .filter(profile=self.profile, fixture_key=key)
            .first()
        )

    def _validate_reference(self, namespace: str, object_key: str) -> str:
        if namespace in self._managed:
            model = self._managed[namespace]
            try:
                identifier = (
                    model._default_manager.using(self.connection.alias)
                    .filter(pk=object_key)
                    .values_list("pk", flat=True)
                    .first()
                )
            except (ValueError, TypeError, ValidationError):
                identifier = None
        elif namespace in self._legacy:
            pk = self._legacy[namespace].indexes["PRIMARY"][1]
            if len(pk) != 1:
                raise CommandError("La referencia legacy no tiene una identidad única soportada.")
            rows = self._legacy_rows(namespace, {pk[0]: object_key})
            identifier = rows[0][pk[0]] if rows else None
        else:
            raise CommandError("El namespace de la referencia no pertenece al contrato demo.")
        if identifier is None:
            raise CommandError("La referencia registrada no existe; no se recrea ni se reasigna.")
        return str(identifier)

    def record(
        self, key: str, namespace: str, object_key: Any, *, owned: bool = True
    ) -> DemoFixtureOwnership:
        self._check_write()
        identifier = str(object_key)
        for value, maximum in ((key, 160), (namespace, 100), (identifier, 80)):
            if not isinstance(value, str) or not value.strip() or len(value) > maximum:
                raise CommandError("La referencia de fixture no es válida.")
        identifier = self._validate_reference(namespace, identifier)
        existing = self.get(key)
        if existing:
            if (existing.namespace, existing.object_key) != (namespace, identifier):
                raise CommandError("La clave de fixture ya tiene otra referencia; no se reasigna.")
            self._validate_reference(namespace, identifier)
            return existing
        self._validate_reference(namespace, identifier)
        if (
            DemoFixtureOwnership.objects.using(self.connection.alias)
            .filter(namespace=namespace, object_key=identifier)
            .exists()
        ):
            raise CommandError("La identidad ya tiene otro registro de propiedad.")
        try:
            return DemoFixtureOwnership.objects.using(self.connection.alias).create(
                profile=self.profile,
                fixture_key=key,
                namespace=namespace,
                object_key=identifier,
                owned=owned,
            )
        except IntegrityError:
            raise CommandError(
                "Hay una colisión en el registro de propiedad de fixtures."
            ) from None

    def ensure_model(
        self,
        key: str,
        model: type[T],
        lookup: dict[str, Any],
        defaults: dict[str, Any],
        *,
        create: Callable[[], T] | None = None,
        reference: bool = False,
    ) -> T:
        self._check_write()
        namespace = model._meta.db_table
        if namespace not in self._managed:
            raise CommandError("Las altas ORM requieren un modelo managed del contrato.")
        manager = model._default_manager.using(self.connection.alias)
        record = self.get(key)
        matches = list(manager.filter(**lookup)[:2]) if lookup else []
        if record:
            if record.namespace != namespace:
                raise CommandError("La clave de fixture tiene otra referencia de modelo.")
            obj = manager.filter(pk=record.object_key).first()
            if obj is None:
                raise CommandError("La referencia registrada no existe; no se recrea.")
            if any(match.pk != obj.pk for match in matches):
                raise CommandError("La identidad de catálogo coincide con una fila ajena.")
            return obj
        if len(matches) > 1:
            raise CommandError("La identidad de catálogo es ambigua y ajena.")
        if matches:
            if not reference:
                raise CommandError("La identidad de catálogo coincide con una fila ajena.")
            obj = matches[0]
            # Las referencias son explícitas; defaults nunca se usan para repararlas.
            for field, value in defaults.items():
                if getattr(obj, field) != value:
                    raise CommandError("La referencia compartida no corresponde al catálogo.")
            self.record(key, namespace, obj.pk, owned=False)
            return obj
        if not lookup and create is None:
            raise CommandError(
                "El alta requiere una identidad de catálogo o un servicio de creación."
            )
        try:
            obj = create() if create is not None else manager.create(**(defaults | lookup))
        except IntegrityError:
            raise CommandError("La identidad de catálogo colisiona con una fila ajena.") from None
        if not isinstance(obj, model) or obj.pk is None:
            raise CommandError("El servicio no proporcionó una referencia persistida válida.")
        self.record(key, namespace, obj.pk, owned=True)
        return obj

    def _legacy_rows(self, table: str, lookup: dict[str, Any]) -> list[dict[str, Any]]:
        contract = self._legacy.get(table)
        if contract is None or not lookup or set(lookup) - contract.columns.keys():
            raise CommandError("La consulta legacy no pertenece al contrato demo.")
        quote = self.connection.ops.quote_name
        where = " AND ".join(f"{quote(column)} <=> %s" for column in lookup)
        with self.connection.cursor() as cursor:
            cursor.execute(
                f"SELECT * FROM {quote(table)} WHERE {where} LIMIT 2", list(lookup.values())
            )
            columns = [column[0] for column in cursor.description]
            return [dict(zip(columns, row, strict=True)) for row in cursor.fetchall()]

    def ensure_legacy(
        self,
        key: str,
        table: str,
        pk_column: str,
        lookup: dict[str, Any],
        values: dict[str, Any],
        *,
        reference: bool = False,
    ) -> dict[str, Any]:
        self._check_write()
        contract = self._legacy.get(table)
        if (
            contract is None
            or contract.indexes["PRIMARY"][1] != (pk_column,)
            or not values
            or set(values) - contract.columns.keys()
        ):
            raise CommandError("El INSERT legacy no pertenece al contrato demo.")
        record = self.get(key)
        matches = self._legacy_rows(table, lookup)
        if record:
            if record.namespace != table:
                raise CommandError("La clave de fixture tiene otra referencia legacy.")
            rows = self._legacy_rows(table, {pk_column: record.object_key})
            if not rows:
                raise CommandError("La referencia registrada no existe; no se recrea.")
            row = rows[0]
            if any(match[pk_column] != row[pk_column] for match in matches):
                raise CommandError("La identidad de catálogo coincide con una fila ajena.")
            return row
        if len(matches) > 1:
            raise CommandError("La identidad legacy es ambigua y ajena.")
        if matches:
            if not reference:
                raise CommandError("La identidad de catálogo coincide con una fila ajena.")
            row = matches[0]
            if any(row[column] != value for column, value in values.items()):
                raise CommandError("La referencia legacy no corresponde al catálogo.")
            self.record(key, table, row[pk_column], owned=False)
            return row
        quote = self.connection.ops.quote_name
        columns = ", ".join(quote(column) for column in values)
        parameters = ", ".join("%s" for _ in values)
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(
                    f"INSERT INTO {quote(table)} ({columns}) VALUES ({parameters})",
                    list(values.values()),
                )
                identifier = values.get(pk_column, cursor.lastrowid)
        except IntegrityError:
            raise CommandError("La identidad legacy colisiona con una fila ajena.") from None
        self.record(key, table, identifier)
        return self._legacy_rows(table, {pk_column: identifier})[0]

    def export(self) -> list[dict[str, Any]]:
        result = []
        for row in (
            DemoFixtureOwnership.objects.using(self.connection.alias)
            .filter(profile=self.profile)
            .order_by("fixture_key")
        ):
            if self._validate_reference(row.namespace, row.object_key) != row.object_key:
                raise CommandError("La referencia registrada no conserva su identidad canónica.")
            result.append(
                {
                    "fixture_key": row.fixture_key,
                    "namespace": row.namespace,
                    "object_key": row.object_key,
                    "owned": row.owned,
                }
            )
        return result
