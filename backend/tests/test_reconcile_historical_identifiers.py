"""Pruebas del comando seguro de reconciliación histórica de SCRUM-114."""

import pytest
from django.core.management import call_command
from django.utils import timezone

from expedientes.models import EstadoExpedienteEnum, EstadoResolucionEnum, Expediente, Resolucion
from notifications.models import EmailOutbox


@pytest.mark.django_db
def test_simulation_does_not_modify_outbox(make_socio):
    socio = make_socio(legajo="89123")
    socio.numero_socio = 1002
    socio.save(update_fields=["numero_socio"])
    item = EmailOutbox.objects.create(
        to=[socio.email],
        subject="Histórico",
        body_text="contenido original",
        metadata={"socio_id": str(socio.pk), "origen": "test"},
    )
    call_command("reconcile_historical_identifiers")
    item.refresh_from_db()
    assert item.metadata == {"socio_id": str(socio.pk), "origen": "test"}


@pytest.mark.django_db
def test_apply_is_idempotent_and_preserves_metadata(make_socio):
    socio = make_socio(legajo="89123")
    socio.numero_socio = 1002
    socio.save(update_fields=["numero_socio"])
    item = EmailOutbox.objects.create(
        to=[socio.email],
        subject="Histórico",
        body_text="contenido original",
        metadata={"socio_id": socio.pk, "origen": "test"},
    )
    call_command("reconcile_historical_identifiers", "--apply")
    item.refresh_from_db()
    assert item.metadata["numero_socio"] == 1002
    assert item.metadata["origen"] == "test"
    call_command("reconcile_historical_identifiers", "--apply")
    item.refresh_from_db()
    assert item.metadata["numero_socio"] == 1002


@pytest.mark.django_db
def test_conflict_sent_and_missing_identity_are_not_modified(make_socio):
    socio = make_socio(legajo="89123")
    socio.numero_socio = 1002
    socio.save(update_fields=["numero_socio"])
    conflict = EmailOutbox.objects.create(
        to=[socio.email],
        subject="Conflicto",
        body_text="original",
        metadata={"socio_id": socio.pk, "numero_socio": 9999},
    )
    sent = EmailOutbox.objects.create(
        to=[socio.email],
        subject="Enviado",
        body_text="original",
        metadata={"socio_id": socio.pk},
        sent_at=timezone.now(),
    )
    unresolved = EmailOutbox.objects.create(
        to=["unknown@example.test"],
        subject="Sin correspondencia",
        body_text="original",
        metadata={"socio_id": 999999},
    )
    call_command("reconcile_historical_identifiers", "--apply")
    assert EmailOutbox.objects.get(pk=conflict.pk).metadata["numero_socio"] == 9999
    assert EmailOutbox.objects.get(pk=sent.pk).metadata == {"socio_id": socio.pk}
    assert EmailOutbox.objects.get(pk=unresolved.pk).metadata == {"socio_id": 999999}


@pytest.mark.django_db
def test_draft_signers_are_completed_but_issued_resolution_is_unchanged(
    make_socio,
):
    imputado = make_socio(legajo="76001")
    causal_expediente = Expediente.objects.create(
        numero="EXP-RECONCILIACION-2026",
        socio=imputado,
        motivo="Caso de prueba de reconciliación",
        estado=EstadoExpedienteEnum.REVISION_RESOLUCION,
    )
    socio = make_socio(legajo="89123", role="TD", social_year=5)
    socio.numero_socio = 1002
    socio.save(update_fields=["numero_socio"])
    draft = Resolucion.objects.create(
        expediente=causal_expediente,
        version=1,
        numero_expediente_snapshot=causal_expediente.numero,
        vistos="Vistos",
        considerandos="Considerandos",
        articulos_resolutivos="Artículos",
        firmantes=[{"user_id": socio.user_id, "legajo": socio.legajo}],
        created_by=socio.user,
    )
    issued = Resolucion.objects.create(
        expediente=causal_expediente,
        version=2,
        estado=EstadoResolucionEnum.ISSUED,
        numero_expediente_snapshot=causal_expediente.numero,
        contenido_hash="a" * 64,
        firmantes=[{"user_id": socio.user_id, "legajo": socio.legajo}],
        created_by=socio.user,
    )
    call_command("reconcile_historical_identifiers", "--apply")
    draft.refresh_from_db()
    issued.refresh_from_db()
    assert draft.firmantes[0]["legajo"] == "89123"
    assert draft.firmantes[0]["numero_socio"] == 1002
    assert issued.firmantes == [{"user_id": socio.user_id, "legajo": "89123"}]
    assert issued.contenido_hash == "a" * 64
