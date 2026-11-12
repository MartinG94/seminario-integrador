from importlib import import_module
from types import SimpleNamespace

import pytest
from django.apps import apps
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.db import transaction

from expedientes.models import Expediente, ExpedienteNumberSequence, SolicitudT01


def migration_module():
    return import_module("expedientes.migrations.0026_normalize_canonical_numbers")


def run_migration():
    migration_module().normalize_numbers(apps, SimpleNamespace())


@pytest.mark.django_db(transaction=True)
def test_normaliza_expediente_solicitud_y_contador(make_socio):
    socio = make_socio(legajo="91001")
    expediente = Expediente.objects.create(
        numero="EXP-0007/2026", socio=socio, motivo="Histórico", puntos="1.00"
    )
    solicitud = SolicitudT01.objects.create(
        solicitante=socio,
        tipo_accion="MERIT",
        estado="ISSUED",
        expediente=expediente,
        puntos="1.00",
        destinatarios_socios_ids=[socio.id],
        snapshot_emitido={"numero": "privado"},
    )
    run_migration()
    expediente.refresh_from_db()
    solicitud.refresh_from_db()
    assert expediente.numero == "7/2026"
    assert solicitud.numero_expediente == "7/2026"
    assert ExpedienteNumberSequence.objects.get(year=2026).last_value == 7


@pytest.mark.django_db(transaction=True)
def test_preserva_borrador_y_identificador_historico_desconocido(make_socio):
    socio = make_socio(legajo="91002")
    unknown = Expediente.objects.create(
        numero="MERGE-001/2026", socio=socio, motivo="Desconocido", puntos="1.00"
    )
    draft = SolicitudT01.objects.create(
        solicitante=socio, tipo_accion="MERIT", estado="DRAFT", puntos="1.00"
    )
    run_migration()
    unknown.refresh_from_db()
    draft.refresh_from_db()
    assert unknown.numero == "MERGE-001/2026"
    assert draft.numero_expediente is None


@pytest.mark.django_db(transaction=True)
def test_sincroniza_solicitud_legacy_con_expediente_ya_canonico(make_socio):
    socio = make_socio(legajo="91006")
    expediente = Expediente.objects.create(
        numero="7/2026", socio=socio, motivo="Canónico", puntos="1.00"
    )
    solicitud = SolicitudT01.objects.create(
        solicitante=socio,
        tipo_accion="MERIT",
        estado="ISSUED",
        expediente=expediente,
        puntos="1.00",
        destinatarios_socios_ids=[socio.id],
        numero_expediente="T01-2026-LEGACY",
    )
    run_migration()
    solicitud.refresh_from_db()
    assert solicitud.numero_expediente == "7/2026"


@pytest.mark.django_db(transaction=True)
def test_colision_historica_hace_rollback_completo(make_socio):
    socio = make_socio(legajo="91003")
    first = Expediente.objects.create(
        numero="EXP-0007/2026", socio=socio, motivo="Uno", puntos="1.00"
    )
    second = Expediente.objects.create(numero="7/2026", socio=socio, motivo="Dos", puntos="1.00")
    with pytest.raises(RuntimeError, match="Colisión"):
        with transaction.atomic():
            run_migration()
    first.refresh_from_db()
    second.refresh_from_db()
    assert first.numero == "EXP-0007/2026"
    assert second.numero == "7/2026"


@pytest.mark.django_db(transaction=True)
def test_issued_sin_expediente_es_conflicto(make_socio):
    socio = make_socio(legajo="91004")
    SolicitudT01.objects.create(
        solicitante=socio,
        tipo_accion="MERIT",
        estado="ISSUED",
        puntos="1.00",
        destinatarios_socios_ids=[socio.id],
    )
    with pytest.raises(RuntimeError, match="sin expediente"):
        run_migration()


@pytest.mark.django_db
def test_orm_normal_no_permite_modificar_solicitud_emitida(make_socio):
    socio = make_socio(legajo="91007")
    solicitud = SolicitudT01.objects.create(
        solicitante=socio,
        tipo_accion="MERIT",
        estado="ISSUED",
        puntos="1.00",
        destinatarios_socios_ids=[socio.id],
    )
    solicitud.numero_expediente = "7/2026"
    with pytest.raises(ValidationError, match="inmutable"):
        solicitud.save(update_fields=["numero_expediente"])


@pytest.mark.django_db
def test_comando_simulacion_no_modifica_e_idempotencia(make_socio):
    socio = make_socio(legajo="91005")
    expediente = Expediente.objects.create(
        numero="EXP-0008/2026", socio=socio, motivo="Simulación", puntos="1.00"
    )
    call_command("reconcile_expediente_numbers")
    expediente.refresh_from_db()
    assert expediente.numero == "EXP-0008/2026"

    call_command("reconcile_expediente_numbers", apply=True)
    expediente.refresh_from_db()
    assert expediente.numero == "8/2026"
    call_command("reconcile_expediente_numbers", apply=True)
    expediente.refresh_from_db()
    assert expediente.numero == "8/2026"
