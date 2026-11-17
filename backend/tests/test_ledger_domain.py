"""Dominio puro del libro mayor: impacto, regla 3:1 y hash encadenado (Spec 011, T1)."""

from decimal import Decimal

import pytest

from ranking.domain.ledger import (
    GENESIS_HASH,
    AsientoPlanificado,
    ImpactoSocio,
    TipoAsiento,
    TipoImpacto,
    acumular_tres_a_uno,
    calcular_hash_asiento,
    clasificar_impacto,
    planificar_asientos,
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


class TestReglaTresAUno:
    def test_primer_y_segundo_acumulado_no_consolidan(self):
        assert acumular_tres_a_uno(0) == (1, False)
        assert acumular_tres_a_uno(1) == (2, False)

    def test_tercer_acumulado_consolida_y_descuenta_tres(self):
        assert acumular_tres_a_uno(2) == (0, True)

    def test_contador_legado_mayor_a_dos_tambien_consolida(self):
        assert acumular_tres_a_uno(4) == (2, True)

    def test_rechaza_contador_negativo(self):
        with pytest.raises(ValueError):
            acumular_tres_a_uno(-1)


class TestPlanificarAsientos:
    def test_puntos_directos_impactan_libro_mayor(self):
        plan = planificar_asientos(ImpactoSocio(TipoImpacto.PUNTOS, Decimal("-2.00")), 0)
        assert plan == [
            AsientoPlanificado(TipoAsiento.PUNTOS_DIRECTOS, Decimal("-2.00"), None, True)
        ]

    def test_sin_impacto_queda_solo_en_auditoria(self):
        plan = planificar_asientos(ImpactoSocio(TipoImpacto.SIN_IMPACTO, Decimal("0.00")), 0)
        assert plan == [AsientoPlanificado(TipoAsiento.SIN_IMPACTO, Decimal("0.00"), None, False)]

    def test_llamado_sin_consolidar_no_mueve_puntos(self):
        plan = planificar_asientos(ImpactoSocio(TipoImpacto.LLAMADO_ATENCION, Decimal("0")), 1)
        assert plan == [AsientoPlanificado(TipoAsiento.LLAMADO_ATENCION, Decimal("0.00"), 2, False)]

    def test_tercer_llamado_consolida_menos_un_punto(self):
        plan = planificar_asientos(ImpactoSocio(TipoImpacto.LLAMADO_ATENCION, Decimal("0")), 2)
        assert plan == [
            AsientoPlanificado(TipoAsiento.LLAMADO_ATENCION, Decimal("0.00"), 0, False),
            AsientoPlanificado(TipoAsiento.CONSOLIDACION_LLAMADOS, Decimal("-1.00"), 0, True),
        ]

    def test_tercera_felicitacion_consolida_mas_un_punto(self):
        plan = planificar_asientos(ImpactoSocio(TipoImpacto.FELICITACION, Decimal("0")), 2)
        assert plan[-1] == AsientoPlanificado(
            TipoAsiento.CONSOLIDACION_FELICITACIONES, Decimal("1.00"), 0, True
        )
        assert sum(a.puntos for a in plan) == Decimal("1.00")


class TestHashEncadenado:
    DATOS = {
        "resolucion_id": 7,
        "expediente_id": 3,
        "socio_id": 11,
        "tipo": TipoAsiento.PUNTOS_DIRECTOS,
        "puntos": Decimal("-2.00"),
        "contador_resultante": None,
        "created_at_iso": "2026-11-15T10:00:00+00:00",
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
