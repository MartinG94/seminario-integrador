"""Esquema y escrituras legadas exclusivos de la base de tests."""

from datetime import date

from padron.models import Socio, SocioEstado, SocioEstudio, Subcomision
from ranking.models import PuntajeAplicado, PuntajeGeneral

LEGACY_MODELS = (Subcomision, SocioEstado, Socio, SocioEstudio, PuntajeGeneral, PuntajeAplicado)


def create_legacy_record(model, **kwargs):
    """Completa los datos requeridos sin relajar el modelo productivo."""
    obj = model(**kwargs)
    save_legacy_records(model, [obj])
    return obj


def save_legacy_records(model, objects):
    """Bypass explícito de fixtures; nunca se importa desde código productivo."""
    for obj in objects:
        if model is Socio:
            defaults = {
                "fechaIngreso": date(2024, 1, 1),
                "fechaNac": date(2000, 1, 1),
                "codTipoDoc": 1,
                "nroDoc": 0,
                "codSexo": 1,
                "anoSocial": 1,
                "idTipoSocio": 1,
            }
            for name, value in defaults.items():
                if getattr(obj, name) is None:
                    setattr(obj, name, value)
        elif model is SocioEstudio and obj.codEspecialidad is None:
            obj.codEspecialidad = 1
        obj._allow_write = True
        obj.save(force_insert=True)


def get_or_create_legacy_record(model, defaults=None, **kwargs):
    obj = model.objects.filter(**kwargs).first()
    if obj is not None:
        return obj, False
    return create_legacy_record(model, **{**(defaults or {}), **kwargs}), True


def create_legacy_tables(connection):
    """Crea sólo tablas ausentes y registra su propiedad para el teardown."""
    existing = set(connection.introspection.table_names())
    created = []
    with connection.schema_editor() as editor:
        for model in LEGACY_MODELS:
            if model._meta.db_table not in existing:
                editor.create_model(model)
                created.append(model)
        if Socio in created:
            # Sólo el esquema de tests admite subcomisiones NULL del legado.
            # No se modifica el campo de padron.models.
            old_field = Socio._meta.get_field("subcomision")
            field = old_field.clone()
            field.set_attributes_from_name(old_field.name)
            field.model = Socio
            field.remote_field.model = old_field.remote_field.model
            field.remote_field.field_name = old_field.remote_field.field_name
            field.null = True
            editor.alter_field(Socio, old_field, field)
    return created


def drop_legacy_tables(connection, created):
    """No borra tablas ajenas; padron puede haber limpiado las suyas antes."""
    with connection.schema_editor() as editor:
        for model in reversed(created):
            if model._meta.db_table in connection.introspection.table_names():
                editor.delete_model(model)
