"""Pruebas de los modelos inmutables de la valoración T03 (S4-03, RF-5 a RF-7 y RF-11)."""

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import ProtectedError

from expedientes.models import (
    EstadoExpedienteEnum,
    Expediente,
    ValoracionT03,
    ValoracionT03Antecedente,
)

pytestmark = pytest.mark.django_db

GROUNDS = "El Tribunal considera acreditada la causa extraordinaria invocada."


@pytest.fixture
def valoracion(t03_descargo, tribunal_member) -> ValoracionT03:
    return ValoracionT03.objects.create(
        expediente=t03_descargo.expediente,
        descargo=t03_descargo,
        version=1,
        resultado="ACCEPTED",
        fundamento=GROUNDS,
        descargo_snapshot={"texto": t03_descargo.texto},
        autor=tribunal_member.user,
        autor_legajo=tribunal_member.legajo,
        autor_rol=tribunal_member.role,
        autor_condicion="SUPLENTE",
    )


@pytest.fixture
def emitido(t03_descargo) -> Expediente:
    return Expediente.objects.create(
        numero="EXP-0702/2026",
        socio=t03_descargo.socio,
        motivo="Causa emitida anterior",
        estado=EstadoExpedienteEnum.EMITIDO,
    )


def test_persists_author_condition_version_and_snapshot(valoracion, tribunal_member) -> None:
    stored = ValoracionT03.objects.get(pk=valoracion.pk)

    assert stored.version == 1
    assert stored.resultado == "ACCEPTED"
    assert stored.get_resultado_display() == "Aprobada"
    assert stored.fundamento == GROUNDS
    assert stored.descargo_snapshot == {"texto": valoracion.descargo.texto}
    assert stored.autor_id == tribunal_member.user_id
    assert stored.autor_legajo == "77002"
    assert stored.autor_rol == "TD"
    assert stored.autor_condicion == "SUPLENTE"
    assert stored.created_at is not None
    assert ValoracionT03._meta.db_table == "expedientes_valoracion_t03"


def test_valuation_cannot_be_modified(valoracion) -> None:
    valoracion.fundamento = "Otro fundamento distinto del registrado originalmente."
    with pytest.raises(ValidationError):
        valoracion.save()

    assert ValoracionT03.objects.get(pk=valoracion.pk).fundamento == GROUNDS


def test_valuation_cannot_be_deleted(valoracion) -> None:
    with pytest.raises(ValidationError):
        valoracion.delete()

    assert ValoracionT03.objects.filter(pk=valoracion.pk).exists()


def test_version_is_unique_per_descargo(valoracion) -> None:
    with pytest.raises(IntegrityError), transaction.atomic():
        ValoracionT03.objects.create(
            expediente=valoracion.expediente,
            descargo=valoracion.descargo,
            version=1,
            resultado="REJECTED",
            fundamento=GROUNDS,
            descargo_snapshot={},
            autor=valoracion.autor,
            autor_legajo="77002",
            autor_rol="TD",
            autor_condicion="TITULAR",
        )


def test_descargo_with_valuation_is_protected(valoracion) -> None:
    with pytest.raises(ProtectedError):
        valoracion.descargo.delete()


def test_links_antecedent_with_number_copy(valoracion, emitido) -> None:
    link = ValoracionT03Antecedente.objects.create(
        valoracion=valoracion,
        expediente_antecedente=emitido,
        numero_antecedente=emitido.numero,
    )

    stored = ValoracionT03Antecedente.objects.get(pk=link.pk)
    assert stored.numero_antecedente == "EXP-0702/2026"
    assert list(valoracion.antecedentes.all()) == [stored]
    assert ValoracionT03Antecedente._meta.db_table == "expedientes_valoracion_t03_antecedente"


def test_antecedent_link_is_immutable(valoracion, emitido) -> None:
    link = ValoracionT03Antecedente.objects.create(
        valoracion=valoracion, expediente_antecedente=emitido, numero_antecedente=emitido.numero
    )
    link.numero_antecedente = "EXP-9999/2026"
    with pytest.raises(ValidationError):
        link.save()
    with pytest.raises(ValidationError):
        link.delete()

    assert ValoracionT03Antecedente.objects.get(pk=link.pk).numero_antecedente == "EXP-0702/2026"


def test_antecedent_is_unique_per_valuation(valoracion, emitido) -> None:
    ValoracionT03Antecedente.objects.create(
        valoracion=valoracion, expediente_antecedente=emitido, numero_antecedente=emitido.numero
    )
    with pytest.raises(IntegrityError), transaction.atomic():
        ValoracionT03Antecedente.objects.create(
            valoracion=valoracion,
            expediente_antecedente=emitido,
            numero_antecedente=emitido.numero,
        )


def test_cited_expediente_is_protected(valoracion, emitido) -> None:
    ValoracionT03Antecedente.objects.create(
        valoracion=valoracion, expediente_antecedente=emitido, numero_antecedente=emitido.numero
    )
    with pytest.raises(ProtectedError):
        emitido.delete()
