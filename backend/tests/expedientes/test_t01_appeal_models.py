"""Historial inmutable de apelaciones, períodos, adecuaciones y plazo (PB-02, CA2/CA4)."""

from datetime import timedelta
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone

from expedientes.models import (
    AdecuacionT01,
    ApelacionT01,
    OrigenPeriodoApelacionEnum,
    ParametroPlazoApelacion,
    PeriodoApelacion,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def apelacion(causal_expediente, causal_imputado) -> ApelacionT01:
    return ApelacionT01.objects.create(
        expediente=causal_expediente,
        socio=causal_imputado,
        numero=1,
        texto="No estuve presente en el lugar del hecho.",
    )


def test_plazo_vigente_por_defecto_y_ultimo_registrado(causal_vocal):
    assert ParametroPlazoApelacion.vigente() == 5
    ParametroPlazoApelacion.objects.create(dias_habiles=7, autor=causal_vocal.user)
    ParametroPlazoApelacion.objects.create(dias_habiles=4, autor=causal_vocal.user)
    assert ParametroPlazoApelacion.vigente() == 4


def test_parametro_es_inmutable(causal_vocal):
    parametro = ParametroPlazoApelacion.objects.create(dias_habiles=7, autor=causal_vocal.user)
    parametro.dias_habiles = 9
    with pytest.raises(ValidationError):
        parametro.save()
    with pytest.raises(ValidationError):
        parametro.delete()


def test_apelacion_es_inmutable_y_versionada(apelacion):
    apelacion.texto = "Texto alterado después de presentar."
    with pytest.raises(ValidationError):
        apelacion.save()
    with pytest.raises(ValidationError):
        apelacion.delete()
    with pytest.raises(IntegrityError), transaction.atomic():
        ApelacionT01.objects.create(
            expediente=apelacion.expediente,
            socio=apelacion.socio,
            numero=1,
            texto="Versión duplicada de la apelación del socio.",
        )


def test_periodo_es_inmutable(causal_expediente, causal_imputado):
    ahora = timezone.now()
    periodo = PeriodoApelacion.objects.create(
        expediente=causal_expediente,
        socio=causal_imputado,
        origen=OrigenPeriodoApelacionEnum.APERTURA,
        dias_habiles=5,
        inicio_at=ahora,
        limite_at=ahora + timedelta(days=7),
    )
    periodo.limite_at = ahora + timedelta(days=30)
    with pytest.raises(ValidationError):
        periodo.save()
    with pytest.raises(ValidationError):
        periodo.delete()


def test_adecuacion_es_inmutable(causal_expediente, causal_vocal):
    adecuacion = AdecuacionT01.objects.create(
        expediente=causal_expediente,
        version=1,
        puntos_anteriores=Decimal("-2"),
        puntos_nuevos=Decimal("-1"),
        socios_anteriores=[],
        socios_nuevos=[],
        motivos="El debate atenuó la gravedad de la falta.",
        autor=causal_vocal.user,
        autor_legajo=causal_vocal.legajo,
    )
    adecuacion.motivos = "Otro motivo cualquiera para la adecuación."
    with pytest.raises(ValidationError):
        adecuacion.save()
    with pytest.raises(ValidationError):
        adecuacion.delete()
