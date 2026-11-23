"""Inmutabilidad del libro mayor: asiento de auditoría y tabla legada (Spec 011, T2)."""

from decimal import Decimal

import pytest
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction

from expedientes.models import AsientoLibroMayor, Resolucion
from ranking.domain.ledger import GENESIS_HASH, TipoAsiento
from ranking.models import PuntajeAplicado


@pytest.fixture
def resolucion(causal_expediente, causal_vocal) -> Resolucion:
    return Resolucion.objects.create(
        expediente=causal_expediente,
        numero_expediente_snapshot=causal_expediente.numero,
        vistos="Vistos.",
        considerandos="Considerando.",
        articulos_resolutivos="Artículo 1.",
        created_by=causal_vocal.user,
    )


def _asiento(resolucion, socio, tipo=TipoAsiento.PUNTOS_DIRECTOS, hash_transaccion="a" * 64):
    return AsientoLibroMayor.objects.create(
        resolucion=resolucion,
        expediente=resolucion.expediente,
        socio=socio,
        nro_socio=int(socio.legajo),
        tipo=tipo,
        puntos=Decimal("-2.00"),
        hash_anterior=GENESIS_HASH,
        hash_transaccion=hash_transaccion,
    )


@pytest.mark.django_db
class TestPuntajeAplicadoInsertOnly:
    def test_registrar_movimiento_inserta_en_tabla_legada(self, causal_expediente):
        movimiento = PuntajeAplicado.registrar_movimiento(
            nro_socio=76001, puntos=Decimal("-2.00"), expediente_id=causal_expediente.id
        )
        assert movimiento.pk is not None
        guardado = PuntajeAplicado.objects.get(pk=movimiento.pk)
        assert guardado.puntajeAplicado == Decimal("-2.00")
        assert guardado.socio_id == 76001
        assert guardado.expediente_id == causal_expediente.id

    def test_movimiento_registrado_no_se_modifica_ni_elimina(self, causal_expediente):
        movimiento = PuntajeAplicado.registrar_movimiento(
            nro_socio=76001, puntos=Decimal("1.00"), expediente_id=causal_expediente.id
        )
        movimiento.puntajeAplicado = Decimal("5.00")
        with pytest.raises(PermissionDenied):
            movimiento.save()
        with pytest.raises(PermissionDenied):
            movimiento.delete()
        with pytest.raises(PermissionDenied):
            PuntajeAplicado.objects.filter(pk=movimiento.pk).update(puntajeAplicado=9)
        with pytest.raises(PermissionDenied):
            PuntajeAplicado.objects.filter(pk=movimiento.pk).delete()

    def test_no_registra_movimientos_en_cero(self, causal_expediente):
        with pytest.raises(ValueError):
            PuntajeAplicado.registrar_movimiento(
                nro_socio=76001, puntos=Decimal("0"), expediente_id=causal_expediente.id
            )


@pytest.mark.django_db
class TestAsientoLibroMayorInmutable:
    def test_crea_asiento_con_fecha(self, resolucion, causal_imputado):
        asiento = _asiento(resolucion, causal_imputado)
        assert asiento.created_at is not None
        assert asiento.get_tipo_display() == "Puntos directos"

    def test_asiento_no_se_modifica_ni_elimina(self, resolucion, causal_imputado):
        asiento = _asiento(resolucion, causal_imputado)
        asiento.puntos = Decimal("3.00")
        with pytest.raises(ValidationError):
            asiento.save()
        with pytest.raises(ValidationError):
            asiento.delete()

    def test_operaciones_masivas_estan_bloqueadas(self, resolucion, causal_imputado):
        asiento = _asiento(resolucion, causal_imputado)
        with pytest.raises(ValidationError):
            AsientoLibroMayor.objects.filter(pk=asiento.pk).update(puntos=Decimal("1"))
        with pytest.raises(ValidationError):
            AsientoLibroMayor.objects.filter(pk=asiento.pk).delete()
        with pytest.raises(ValidationError):
            AsientoLibroMayor.objects.bulk_update([asiento], ["puntos"])

    def test_no_duplica_tipo_por_resolucion_y_socio(self, resolucion, causal_imputado):
        _asiento(resolucion, causal_imputado)
        with pytest.raises(IntegrityError), transaction.atomic():
            _asiento(resolucion, causal_imputado, hash_transaccion="b" * 64)
