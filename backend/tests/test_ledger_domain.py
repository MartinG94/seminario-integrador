"""Dominio puro del libro mayor: impacto, tipo de asiento y hash encadenado (Spec 011, T1)."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from ranking.domain.ledger import (
    GENESIS_HASH,
    ImpactoSocio,
    TipoAsiento,
    TipoImpacto,
    calcular_hash_asiento,
    clasificar_impacto,
    impacta_libro_mayor,
    normalizar_fecha,
    tipo_asiento_para,
)

pytestmark = pytest.mark.unit


class TestClasificarImpacto:
    @pytest.mark.parametrize(
        ("valor", "esperado"),
        [
            ("-2", ImpactoSocio(TipoImpacto.PUNTOS, Decimal("-2.00"))),
            (Decimal("1.5"), ImpactoSocio(TipoImpacto.PUNTOS, Decimal("1.50"))),
            (-0.5, ImpactoSocio(TipoImpacto.PUNTOS, Decimal("-0.50"))),
            ("0", ImpactoSocio(TipoImpacto.SIN_IMPACTO, Decimal("0.00"))),
            (0, ImpactoSocio(TipoImpacto.SIN_IMPACTO, Decimal("0.00"))),
            ("LLAMADO_ATENCION", ImpactoSocio(TipoImpacto.LLAMADO_ATENCION, Decimal("0.00"))),
            ("Felicitación", ImpactoSocio(TipoImpacto.FELICITACION, Decimal("0.00"))),
        ],
    )
    def test_clasifica_valores_validos(self, valor, esperado):
        assert clasificar_impacto(valor) == esperado

    @pytest.mark.parametrize("valor", [Decimal("-0.25"), "0.25", "-0.33", 0.33])
    def test_rank_fraccionario_de_medidas_especiales_no_es_puntaje(self, valor):
        """±0,25 y ±0,33 no son puntos: son llamado o felicitación (Notas del PO, sección 6)."""
        impacto = clasificar_impacto(valor)
        assert impacto.tipo in (TipoImpacto.LLAMADO_ATENCION, TipoImpacto.FELICITACION)
        assert impacto.puntos == Decimal("0.00")

    @pytest.mark.parametrize("valor", [None, "", "abc"])
    def test_rechaza_valores_invalidos(self, valor):
        with pytest.raises(ValueError):
            clasificar_impacto(valor)


class TestTipoDeAsiento:
    def test_cada_impacto_tiene_un_unico_asiento(self):
        assert tipo_asiento_para(ImpactoSocio(TipoImpacto.PUNTOS, Decimal("-2"))) == (
            TipoAsiento.PUNTOS_DIRECTOS
        )
        assert tipo_asiento_para(ImpactoSocio(TipoImpacto.SIN_IMPACTO, Decimal("0"))) == (
            TipoAsiento.SIN_IMPACTO
        )
        assert tipo_asiento_para(ImpactoSocio(TipoImpacto.LLAMADO_ATENCION, Decimal("0"))) == (
            TipoAsiento.LLAMADO_ATENCION
        )
        assert tipo_asiento_para(ImpactoSocio(TipoImpacto.FELICITACION, Decimal("0"))) == (
            TipoAsiento.FELICITACION
        )

    def test_solo_los_puntos_directos_mueven_el_saldo(self):
        assert impacta_libro_mayor(ImpactoSocio(TipoImpacto.PUNTOS, Decimal("-1.00")))
        assert not impacta_libro_mayor(ImpactoSocio(TipoImpacto.LLAMADO_ATENCION, Decimal("0")))
        assert not impacta_libro_mayor(ImpactoSocio(TipoImpacto.FELICITACION, Decimal("0")))
        assert not impacta_libro_mayor(ImpactoSocio(TipoImpacto.SIN_IMPACTO, Decimal("0")))


class TestHashEncadenado:
    DATOS = {
        "resolucion_id": 7,
        "expediente_id": 3,
        "socio_id": 11,
        "tipo": TipoAsiento.PUNTOS_DIRECTOS,
        "puntos": Decimal("-2.00"),
        "contador_resultante": None,
        "nro_socio": 74907,
        "puntaje_aplicado_id": 501,
        "autor_id": 9,
        "created_at": datetime(2026, 11, 15, 10, 0, 0, 123456, tzinfo=timezone.utc),
    }

    def test_hash_es_determinista_y_sha256(self):
        primero = calcular_hash_asiento(GENESIS_HASH, **self.DATOS)
        assert primero == calcular_hash_asiento(GENESIS_HASH, **self.DATOS)
        assert len(primero) == 64
        assert GENESIS_HASH == "0" * 64

    def test_hash_depende_del_anterior_y_del_contenido(self):
        base = calcular_hash_asiento(GENESIS_HASH, **self.DATOS)
        assert calcular_hash_asiento(base, **self.DATOS) != base
        alterado = {**self.DATOS, "puntos": Decimal("-3.00")}
        assert calcular_hash_asiento(GENESIS_HASH, **alterado) != base

    @pytest.mark.parametrize(
        ("campo", "valor"), [("nro_socio", 1), ("puntaje_aplicado_id", 2), ("autor_id", 3)]
    )
    def test_hash_cubre_numero_de_socio_movimiento_y_autor(self, campo, valor):
        base = calcular_hash_asiento(GENESIS_HASH, **self.DATOS)
        assert calcular_hash_asiento(GENESIS_HASH, **{**self.DATOS, campo: valor}) != base

    def test_fecha_normalizada_a_utc_es_independiente_del_huso(self):
        utc = self.DATOS["created_at"]
        cordoba = utc.astimezone(timezone(timedelta(hours=-3)))
        assert normalizar_fecha(utc) == normalizar_fecha(cordoba) == "2026-11-15T10:00:00.123456Z"
        base = calcular_hash_asiento(GENESIS_HASH, **self.DATOS)
        assert calcular_hash_asiento(GENESIS_HASH, **{**self.DATOS, "created_at": cordoba}) == base
