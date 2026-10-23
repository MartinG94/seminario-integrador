"""Persistencia inmutable de apartamientos, designaciones y composición (S4-04, CA4)."""

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from expedientes.models import (
    ApartamientoTribunal,
    CausaApartamientoEnum,
    ComposicionTribunal,
    CondicionIntegranteEnum,
    DesignacionAdHoc,
    IntegranteComposicion,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def apartamiento(causal_expediente, causal_vocal) -> ApartamientoTribunal:
    return ApartamientoTribunal.objects.create(
        expediente=causal_expediente,
        socio=causal_vocal,
        causa=CausaApartamientoEnum.CONFLICTO_INTERES,
        fundamento="Comparto vivienda con el socio imputado.",
        autor=causal_vocal.user,
    )


@pytest.fixture
def composicion(causal_expediente, causal_vocal) -> ComposicionTribunal:
    composicion = ComposicionTribunal.objects.create(
        expediente=causal_expediente,
        es_ad_hoc=False,
        apartamientos=[],
        constituida_por=causal_vocal.user,
        constituida_por_legajo=causal_vocal.legajo,
    )
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


def test_causas_de_apartamiento_no_incluyen_recusacion():
    assert set(CausaApartamientoEnum.values) == {"INVOLUCRADO", "CONFLICTO_INTERES"}


def test_apartamiento_es_inmutable(apartamiento):
    apartamiento.fundamento = "Otro fundamento cualquiera"
    with pytest.raises(ValidationError):
        apartamiento.save()
    with pytest.raises(ValidationError):
        apartamiento.delete()


def test_un_apartamiento_por_integrante_y_expediente(apartamiento):
    with pytest.raises(IntegrityError), transaction.atomic():
        ApartamientoTribunal.objects.create(
            expediente=apartamiento.expediente,
            socio=apartamiento.socio,
            causa=CausaApartamientoEnum.CONFLICTO_INTERES,
            fundamento="Segundo apartamiento del mismo integrante.",
            autor=apartamiento.autor,
        )


def test_designacion_es_inmutable(causal_expediente, causal_vocal, make_socio):
    designado = make_socio(legajo="76090", social_year=5)
    designacion = DesignacionAdHoc.objects.create(
        expediente=causal_expediente,
        reemplaza_a=causal_vocal,
        designado=designado,
        anio_social=5,
        acta_asamblea="Acta de Asamblea Extraordinaria N° 3/2026",
        autor=causal_vocal.user,
    )
    designacion.acta_asamblea = "Otra"
    with pytest.raises(ValidationError):
        designacion.save()
    with pytest.raises(ValidationError):
        designacion.delete()


def test_composicion_e_integrantes_son_inmutables(composicion):
    composicion.es_ad_hoc = True
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
        ComposicionTribunal.objects.create(
            expediente=composicion.expediente,
            es_ad_hoc=False,
            apartamientos=[],
            constituida_por=composicion.constituida_por,
            constituida_por_legajo="x",
        )


def test_firma_del_integrante_distingue_grupo_y_condicion(composicion, make_socio):
    titular = composicion.integrantes.get()
    assert titular.firma == "76002 - Nombre Apellido76002 - G58"
    suplente = IntegranteComposicion(
        nro_socio=11928,
        nombre_completo="Abril Gusella",
        grupo="G58",
        condicion=CondicionIntegranteEnum.SUPLENTE,
    )
    assert suplente.firma == "11928 - Abril Gusella - G58 (Sup.)"
    ad_hoc = IntegranteComposicion(
        nro_socio=12000,
        nombre_completo="Socio Designado",
        grupo="",
        condicion=CondicionIntegranteEnum.AD_HOC,
    )
    assert ad_hoc.firma == "12000 - Socio Designado (Ad hoc)"
