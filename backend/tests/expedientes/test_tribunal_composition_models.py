"""Persistencia inmutable de la composición estampada y la Resolución por Asamblea (S4-04)."""

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from expedientes.models import (
    ComposicionTribunal,
    CondicionIntegranteEnum,
    IntegranteComposicion,
    ResolucionAsamblea,
)
from tests.expedientes.conftest import PDF_BYTES

pytestmark = pytest.mark.django_db


@pytest.fixture
def composicion(causal_expediente, causal_vocal) -> ComposicionTribunal:
    composicion = ComposicionTribunal.objects.create(expediente=causal_expediente, apartados=[])
    IntegranteComposicion.objects.create(
        composicion=composicion,
        anio_social=5,
        socio=causal_vocal,
        condicion=CondicionIntegranteEnum.TITULAR,
        nro_socio=76002,
        nombre_completo="Nombre Apellido76002",
        grupo="G58",
    )
    return composicion


def test_composicion_e_integrantes_son_inmutables(composicion):
    composicion.apartados = [{"socio_id": 1}]
    with pytest.raises(ValidationError):
        composicion.save()
    with pytest.raises(ValidationError):
        composicion.delete()
    integrante = composicion.integrantes.get()
    integrante.condicion = CondicionIntegranteEnum.SUPLENTE
    with pytest.raises(ValidationError):
        integrante.save()
    with pytest.raises(ValidationError):
        integrante.delete()


def test_una_composicion_por_expediente(composicion):
    with pytest.raises(IntegrityError), transaction.atomic():
        ComposicionTribunal.objects.create(expediente=composicion.expediente)


def test_firma_del_integrante_distingue_grupo_y_condicion(composicion):
    assert composicion.integrantes.get().firma == "76002 - Nombre Apellido76002 - G58"
    suplente = IntegranteComposicion(
        nro_socio=11928,
        nombre_completo="Abril Gusella",
        grupo="G58",
        condicion=CondicionIntegranteEnum.SUPLENTE,
    )
    assert suplente.firma == "11928 - Abril Gusella - G58 (Sup.)"


def test_condiciones_sin_ad_hoc_manual():
    assert set(CondicionIntegranteEnum.values) == {"TITULAR", "SUPLENTE"}


def test_resolucion_por_asamblea_es_inmutable(causal_expediente, causal_vocal):
    resolucion = ResolucionAsamblea.objects.create(
        expediente=causal_expediente,
        acta_blob=PDF_BYTES,
        acta_nombre="acta.pdf",
        acta_tamanio_bytes=len(PDF_BYTES),
        acta_sha256="0" * 64,
        registrada_por=causal_vocal.user,
        registrada_por_legajo=causal_vocal.legajo,
    )
    resolucion.acta_nombre = "otra.pdf"
    with pytest.raises(ValidationError):
        resolucion.save()
    with pytest.raises(ValidationError):
        resolucion.delete()
