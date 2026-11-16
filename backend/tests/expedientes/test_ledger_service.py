"""Asientos del libro mayor al emitir resoluciones (Spec 011, T3 y T4)."""

from datetime import datetime, timezone
from decimal import Decimal

import pytest

from expedientes.domain.closed_decision import ClosedDecision
from expedientes.models import (
    AsientoLibroMayor,
    AtencionFelicitacion,
    DecisionCausalDescargo,
    DescargoExpediente,
    EstadoExpedienteEnum,
    Expediente,
    Resolucion,
    TipoDescargoEnum,
)
from expedientes.services.ledger_service import (
    LedgerService,
    resolver_impacto_socio,
    resolver_nro_socio,
)
from expedientes.services.resolution_service import (
    ExpedienteConsolidatedDecisionProvider,
    emitir_resolucion,
)
from ranking.domain.ledger import GENESIS_HASH, ImpactoSocio, TipoImpacto
from ranking.models import PuntajeAplicado

pytestmark = pytest.mark.django_db


class ProveedorCerrado:
    def get_closed_decision(self, expediente_id):
        return ClosedDecision(
            id="d",
            expediente_id=expediente_id,
            estado="CLOSED",
            resultado="SANCTION",
            puntos_finales=Decimal("-2.00"),
            medidas=[],
            considerandos_base="",
            version=1,
            closed_at=datetime.now(timezone.utc),
        )


def _resolucion(expediente, autor) -> Resolucion:
    return Resolucion.objects.create(
        expediente=expediente,
        numero_expediente_snapshot=expediente.numero,
        vistos="Vistos.",
        considerandos="Considerando.",
        articulos_resolutivos="Artículo 1.",
        created_by=autor.user,
    )


def _expediente(numero, socios, puntos=Decimal("-2.00")) -> Expediente:
    expediente = Expediente.objects.create(
        numero=numero,
        socio=socios[0],
        motivo="Hecho",
        puntos=puntos,
        estado=EstadoExpedienteEnum.REVISION_RESOLUCION,
    )
    expediente.socios.add(*socios)
    return expediente


def _decision(expediente, socio, vocal, decision="REJECTED", puntaje_final=None):
    descargo = DescargoExpediente.objects.create(
        expediente=expediente, socio=socio, tipo=TipoDescargoEnum.T02_CERTIFICADO
    )
    snapshot = {} if puntaje_final is None else {"puntaje_final": puntaje_final}
    DecisionCausalDescargo.objects.create(
        expediente=expediente,
        descargo=descargo,
        version=1,
        decision=decision,
        regla_sugerida=decision,
        descargo_snapshot=snapshot,
        autor=vocal.user,
        autor_legajo=vocal.legajo,
        autor_rol=vocal.role,
    )


def _saldo(nro: int) -> Decimal:
    return sum(
        (p.puntajeAplicado for p in PuntajeAplicado.objects.filter(socio_id=nro)),
        Decimal("0"),
    )


class TestImpactoIndividual:
    def test_sin_descargo_aplica_lo_solicitado(self, causal_expediente, causal_imputado):
        causal_expediente.puntos = Decimal("-3.00")
        causal_expediente.save()
        impacto = resolver_impacto_socio(causal_expediente, causal_imputado)
        assert impacto == ImpactoSocio(TipoImpacto.PUNTOS, Decimal("-3.00"))

    def test_causal_aceptada_absuelve(self, causal_expediente, causal_imputado, causal_vocal):
        _decision(causal_expediente, causal_imputado, causal_vocal, decision="ACCEPTED")
        impacto = resolver_impacto_socio(causal_expediente, causal_imputado)
        assert impacto.tipo == TipoImpacto.SIN_IMPACTO

    def test_puntaje_ratificado_prevalece(self, causal_expediente, causal_imputado, causal_vocal):
        _decision(causal_expediente, causal_imputado, causal_vocal, puntaje_final="-1.5")
        impacto = resolver_impacto_socio(causal_expediente, causal_imputado)
        assert impacto == ImpactoSocio(TipoImpacto.PUNTOS, Decimal("-1.50"))

    def test_rank_menos_cero_veinticinco_es_llamado(self, causal_expediente, causal_imputado):
        causal_expediente.puntos = Decimal("-0.25")
        causal_expediente.save()
        impacto = resolver_impacto_socio(causal_expediente, causal_imputado)
        assert impacto.tipo == TipoImpacto.LLAMADO_ATENCION

    def test_nro_socio_por_identificador_numerico(self, causal_imputado):
        assert resolver_nro_socio(causal_imputado) == 76001


class TestAsientosAlEmitir:
    def test_emitir_inserta_movimiento_y_auditoria(self, causal_expediente, causal_vocal):
        resolucion = _resolucion(causal_expediente, causal_vocal)
        emitir_resolucion(resolucion, causal_vocal.user, ProveedorCerrado())

        (asiento,) = AsientoLibroMayor.objects.filter(resolucion=resolucion)
        assert asiento.tipo == "PUNTOS_DIRECTOS"
        assert asiento.puntos == Decimal("-1.00")  # puntos por defecto del expediente
        assert asiento.autor == causal_vocal.user
        assert asiento.hash_anterior == GENESIS_HASH
        movimiento = PuntajeAplicado.objects.get(pk=asiento.puntaje_aplicado_id)
        assert movimiento.expediente_id == causal_expediente.id
        assert _saldo(76001) == Decimal("-1.00")

    def test_resoluciones_individualizadas_por_socio(self, make_socio, causal_vocal):
        a = make_socio(legajo="77001")
        b = make_socio(legajo="77002")
        expediente = _expediente("EXP-0701/2026", [a, b])
        _decision(expediente, b, causal_vocal, decision="ACCEPTED")

        LedgerService.registrar_resolucion(_resolucion(expediente, causal_vocal), causal_vocal.user)

        assert _saldo(77001) == Decimal("-2.00")
        assert _saldo(77002) == Decimal("0")
        tipos = dict(AsientoLibroMayor.objects.values_list("socio_id", "tipo"))
        assert tipos == {a.pk: "PUNTOS_DIRECTOS", b.pk: "SIN_IMPACTO"}

    def test_es_idempotente(self, causal_expediente, causal_vocal):
        resolucion = _resolucion(causal_expediente, causal_vocal)
        LedgerService.registrar_resolucion(resolucion, causal_vocal.user)
        LedgerService.registrar_resolucion(resolucion, causal_vocal.user)
        assert AsientoLibroMayor.objects.filter(resolucion=resolucion).count() == 1
        assert PuntajeAplicado.objects.filter(socio_id=76001).count() == 1

    def test_hash_encadenado_por_socio(self, causal_imputado, causal_vocal):
        for numero in ("EXP-0801/2026", "EXP-0802/2026"):
            expediente = _expediente(numero, [causal_imputado])
            LedgerService.registrar_resolucion(
                _resolucion(expediente, causal_vocal), causal_vocal.user
            )
        primero, segundo = AsientoLibroMayor.objects.filter(socio=causal_imputado).order_by("id")
        assert segundo.hash_anterior == primero.hash_transaccion


class TestReglaTresAUno:
    def _emitir_llamado(self, numero, socio, vocal):
        expediente = _expediente(numero, [socio], puntos=Decimal("-0.25"))
        return LedgerService.registrar_resolucion(_resolucion(expediente, vocal), vocal.user)

    def test_dos_llamados_no_mueven_puntos(self, causal_imputado, causal_vocal):
        self._emitir_llamado("EXP-0901/2026", causal_imputado, causal_vocal)
        self._emitir_llamado("EXP-0902/2026", causal_imputado, causal_vocal)
        assert not PuntajeAplicado.objects.filter(socio_id=76001).exists()
        assert AtencionFelicitacion.objects.get(socio=causal_imputado).llamadosAtencion == 2

    def test_tercer_llamado_consolida_un_punto(self, causal_imputado, causal_vocal):
        for n in range(3):
            asientos = self._emitir_llamado(f"EXP-091{n}/2026", causal_imputado, causal_vocal)
        assert [a.tipo for a in asientos] == ["LLAMADO_ATENCION", "CONSOLIDACION_LLAMADOS"]
        assert _saldo(76001) == Decimal("-1.00")
        assert AtencionFelicitacion.objects.get(socio=causal_imputado).llamadosAtencion == 0

    def test_felicitacion_ratificada_suma_al_contador(
        self, causal_expediente, causal_imputado, causal_vocal
    ):
        AtencionFelicitacion.objects.create(socio=causal_imputado, felicitaciones=2)
        _decision(causal_expediente, causal_imputado, causal_vocal, puntaje_final="FELICITACION")
        LedgerService.registrar_resolucion(
            _resolucion(causal_expediente, causal_vocal), causal_vocal.user
        )
        assert _saldo(76001) == Decimal("1.00")
        assert AtencionFelicitacion.objects.get(socio=causal_imputado).felicitaciones == 0


def test_proveedor_no_usa_puntos_fraccionarios_para_llamados(
    causal_expediente, causal_descargo, causal_vocal
):
    DecisionCausalDescargo.objects.create(
        expediente=causal_expediente,
        descargo=causal_descargo,
        version=1,
        decision="REJECTED",
        regla_sugerida="REJECTED",
        descargo_snapshot={"puntaje_final": "LLAMADO_ATENCION"},
        autor=causal_vocal.user,
        autor_legajo=causal_vocal.legajo,
        autor_rol=causal_vocal.role,
    )
    decision = ExpedienteConsolidatedDecisionProvider().get_closed_decision(causal_expediente.id)
    assert decision.puntos_finales == Decimal("0.00")
    assert decision.medidas == ["Llamado de atención"]
    assert decision.resultado == "SANCTION"
