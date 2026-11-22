"""Asientos del libro mayor al emitir resoluciones (Spec 011, T3 y T4)."""

from datetime import datetime, timezone
from decimal import Decimal

import pytest

from expedientes.domain.causal_resolution import CausalDecision
from expedientes.domain.closed_decision import ClosedDecision
from expedientes.models import (
    AsientoLibroMayor,
    AtencionFelicitacion,
    DecisionCausalDescargo,
    DescargoExpediente,
    EnmiendaResolucion,
    EstadoExpedienteEnum,
    EstadoResolucionEnum,
    Expediente,
    Resolucion,
    ResultadoValoracionT03Enum,
    TipoDescargoEnum,
    ValoracionT03,
)
from expedientes.services.causal_resolution_service import CausalResolutionService
from expedientes.services.ledger_service import (
    LedgerService,
    SocioSinNumeroError,
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


@pytest.fixture(autouse=True)
def numero_socio_imputado(causal_imputado):
    """El libro mayor usa el N° de socio institucional (SCRUM-114) como clave."""
    causal_imputado.numero_socio = 76001
    causal_imputado.save(update_fields=["numero_socio"])
    return causal_imputado


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

    def test_puntaje_final_de_la_decision(self, causal_expediente, causal_imputado, causal_vocal):
        _decision(causal_expediente, causal_imputado, causal_vocal, puntaje_final="-1.5")
        impacto = resolver_impacto_socio(causal_expediente, causal_imputado)
        assert impacto == ImpactoSocio(TipoImpacto.PUNTOS, Decimal("-1.50"))

    def test_puntaje_final_vacio_aplica_la_regla_base(
        self, causal_expediente, causal_imputado, causal_vocal
    ):
        _decision(causal_expediente, causal_imputado, causal_vocal, "ACCEPTED", puntaje_final="")
        assert resolver_impacto_socio(causal_expediente, causal_imputado).tipo == (
            TipoImpacto.SIN_IMPACTO
        )

    def test_puntaje_ratificado_prevalece_sobre_la_decision(
        self, causal_expediente, causal_imputado, causal_vocal
    ):
        _decision(causal_expediente, causal_imputado, causal_vocal, puntaje_final="-1.5")
        DescargoExpediente.objects.filter(socio=causal_imputado).update(puntaje_ratificado="-0.5")
        impacto = resolver_impacto_socio(causal_expediente, causal_imputado)
        assert impacto == ImpactoSocio(TipoImpacto.PUNTOS, Decimal("-0.50"))

    def test_socio_excluido_no_recibe_lo_solicitado(self, causal_expediente, causal_imputado):
        causal_expediente.puntos = Decimal("-3.00")
        causal_expediente.save()
        DescargoExpediente.objects.create(
            expediente=causal_expediente,
            socio=causal_imputado,
            tipo=TipoDescargoEnum.T02_CERTIFICADO,
            es_vigente=False,
            esta_excluido=True,
            motivo_exclusion="Excluido fundadamente por el Tribunal.",
        )
        assert resolver_impacto_socio(causal_expediente, causal_imputado).tipo == (
            TipoImpacto.SIN_IMPACTO
        )

    def test_valoracion_t03_vigente(self, causal_expediente, causal_imputado, causal_vocal):
        descargo = DescargoExpediente.objects.create(
            expediente=causal_expediente,
            socio=causal_imputado,
            tipo=TipoDescargoEnum.T03_EXTRAORDINARIO,
            texto="Descargo extraordinario.",
        )
        ValoracionT03.objects.create(
            expediente=causal_expediente,
            descargo=descargo,
            version=1,
            resultado=ResultadoValoracionT03Enum.REJECTED,
            puntaje_final="-0.75",
            fundamento="Valoración del Tribunal con fundamento suficiente.",
            autor=causal_vocal.user,
            autor_legajo=causal_vocal.legajo,
            autor_rol=causal_vocal.role,
            autor_condicion="TITULAR",
        )
        impacto = resolver_impacto_socio(causal_expediente, causal_imputado)
        assert impacto == ImpactoSocio(TipoImpacto.PUNTOS, Decimal("-0.75"))

    def test_rank_menos_cero_veinticinco_es_llamado(self, causal_expediente, causal_imputado):
        causal_expediente.puntos = Decimal("-0.25")
        causal_expediente.save()
        impacto = resolver_impacto_socio(causal_expediente, causal_imputado)
        assert impacto.tipo == TipoImpacto.LLAMADO_ATENCION

    def test_nro_socio_es_el_numero_institucional(self, causal_imputado, make_socio):
        assert resolver_nro_socio(causal_imputado) == 76001
        # Nunca se infiere del legajo ni del usuario.
        assert resolver_nro_socio(make_socio(legajo="77999")) is None


class TestAsientosAlEmitir:
    def test_emitir_inserta_movimiento_y_auditoria(self, causal_expediente, causal_vocal):
        resolucion = _resolucion(causal_expediente, causal_vocal)
        emitir_resolucion(resolucion, causal_vocal.user, ProveedorCerrado())

        (asiento,) = AsientoLibroMayor.objects.filter(resolucion=resolucion)
        assert asiento.tipo == "PUNTOS_DIRECTOS"
        assert asiento.puntos == Decimal("-1.00")  # puntos por defecto del expediente
        assert asiento.autor == causal_vocal.user
        assert asiento.nro_socio == 76001
        assert asiento.hash_anterior == GENESIS_HASH
        movimiento = PuntajeAplicado.objects.get(pk=asiento.puntaje_aplicado_id)
        assert movimiento.expediente_id == causal_expediente.id
        assert _saldo(76001) == Decimal("-1.00")

    def test_resoluciones_individualizadas_por_socio(self, make_socio, causal_vocal):
        a = make_socio(legajo="77001", numero_socio=77001)
        b = make_socio(legajo="77002", numero_socio=77002)
        expediente = _expediente("EXP-0701/2026", [a, b])
        _decision(expediente, b, causal_vocal, decision="ACCEPTED")

        LedgerService.registrar_resolucion(_resolucion(expediente, causal_vocal), causal_vocal.user)

        assert _saldo(77001) == Decimal("-2.00")
        assert _saldo(77002) == Decimal("0")
        tipos = dict(AsientoLibroMayor.objects.values_list("socio_id", "tipo"))
        assert tipos == {a.pk: "PUNTOS_DIRECTOS", b.pk: "SIN_IMPACTO"}

    def test_socio_sin_numero_aborta_sin_desincronizar(self, make_socio, causal_vocal):
        sin_numero = make_socio(legajo="77003")
        expediente = _expediente("EXP-0703/2026", [sin_numero])
        with pytest.raises(SocioSinNumeroError):
            LedgerService.registrar_resolucion(
                _resolucion(expediente, causal_vocal), causal_vocal.user
            )
        assert not AsientoLibroMayor.objects.filter(socio=sin_numero).exists()

    def test_es_idempotente(self, causal_expediente, causal_vocal):
        resolucion = _resolucion(causal_expediente, causal_vocal)
        LedgerService.registrar_resolucion(resolucion, causal_vocal.user)
        LedgerService.registrar_resolucion(resolucion, causal_vocal.user)
        assert AsientoLibroMayor.objects.filter(resolucion=resolucion).count() == 1
        assert PuntajeAplicado.objects.filter(socio_id=76001).count() == 1

    def test_hash_encadenado_y_verificable(self, causal_imputado, causal_vocal):
        for numero in ("EXP-0801/2026", "EXP-0802/2026"):
            expediente = _expediente(numero, [causal_imputado])
            LedgerService.registrar_resolucion(
                _resolucion(expediente, causal_vocal), causal_vocal.user
            )
        primero, segundo = AsientoLibroMayor.objects.filter(socio=causal_imputado).order_by("id")
        assert segundo.hash_anterior == primero.hash_transaccion
        verificacion = LedgerService.verificar_cadena(causal_imputado)
        assert verificacion.valida is True
        assert verificacion.asientos_verificados == 2

    def test_verificador_detecta_alteraciones(self, causal_imputado, causal_vocal):
        expediente = _expediente("EXP-0803/2026", [causal_imputado])
        (asiento,) = LedgerService.registrar_resolucion(
            _resolucion(expediente, causal_vocal), causal_vocal.user
        )
        # Alteración fuera de la aplicación (simula un UPDATE manual sobre la tabla).
        from django.db import connection

        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE expedientes_asiento_libro_mayor SET nro_socio = %s WHERE id = %s",
                [99999, asiento.pk],
            )
        verificacion = LedgerService.verificar_cadena(causal_imputado)
        assert verificacion.valida is False
        assert verificacion.primer_asiento_invalido == asiento.pk


class TestReglaTresAUno:
    def _emitir_llamado(self, numero, socio, vocal):
        expediente = _expediente(numero, [socio], puntos=Decimal("-0.25"))
        return LedgerService.registrar_resolucion(_resolucion(expediente, vocal), vocal.user)

    def test_dos_llamados_no_mueven_puntos(self, causal_imputado, causal_vocal):
        self._emitir_llamado("EXP-0901/2026", causal_imputado, causal_vocal)
        self._emitir_llamado("EXP-0902/2026", causal_imputado, causal_vocal)
        assert not PuntajeAplicado.objects.filter(socio_id=76001).exists()
        assert AtencionFelicitacion.objects.get(socio=causal_imputado).llamadosAtencion == 2

    def test_tercer_llamado_consolida_por_el_motor_unico(self, causal_imputado, causal_vocal):
        for n in range(3):
            (asiento,) = self._emitir_llamado(f"EXP-091{n}/2026", causal_imputado, causal_vocal)
        assert asiento.tipo == "LLAMADO_ATENCION"
        assert asiento.contador_resultante == 0
        assert AtencionFelicitacion.objects.get(socio=causal_imputado).llamadosAtencion == 0
        # La consolidación abre un único expediente por -1,00 (circuito vigente de main).
        consolidaciones = Expediente.objects.filter(
            socio=causal_imputado, motivo__startswith="Consolidación reglamentaria"
        )
        assert consolidaciones.count() == 1
        assert consolidaciones.get().puntos == Decimal("-1.00")
        # Ningún punto fraccionario ni doble consolidación en el libro mayor.
        assert not PuntajeAplicado.objects.filter(socio_id=76001).exists()

    def test_medida_evaluada_no_se_cuenta_dos_veces(
        self, causal_expediente, causal_descargo, causal_imputado, causal_vocal
    ):
        """B2: la decisión causal ya contó la felicitación; la emisión no la suma de nuevo."""
        AtencionFelicitacion.objects.create(socio=causal_imputado, felicitaciones=1)
        CausalResolutionService.decide(
            expediente_id=causal_expediente.id,
            descargo_id=causal_descargo.id,
            decision=CausalDecision.ACCEPTED,
            fundamento="Felicitación institucional por aporte extraordinario al plenario.",
            evidencia_ids=None,
            user=causal_vocal.user,
            puntaje_final="FELICITACION",
        )
        assert AtencionFelicitacion.objects.get(socio=causal_imputado).felicitaciones == 2

        (asiento,) = LedgerService.registrar_resolucion(
            _resolucion(causal_expediente, causal_vocal), causal_vocal.user
        )

        assert asiento.tipo == "FELICITACION"
        assert asiento.contador_resultante == 2
        assert AtencionFelicitacion.objects.get(socio=causal_imputado).felicitaciones == 2
        assert not PuntajeAplicado.objects.filter(socio_id=76001).exists()

    def test_tercera_felicitacion_evaluada_consolida_una_sola_vez(
        self, causal_expediente, causal_descargo, causal_imputado, causal_vocal
    ):
        AtencionFelicitacion.objects.create(socio=causal_imputado, felicitaciones=2)
        CausalResolutionService.decide(
            expediente_id=causal_expediente.id,
            descargo_id=causal_descargo.id,
            decision=CausalDecision.ACCEPTED,
            fundamento="Felicitación institucional por aporte extraordinario al plenario.",
            evidencia_ids=None,
            user=causal_vocal.user,
            puntaje_final="FELICITACION",
        )
        LedgerService.registrar_resolucion(
            _resolucion(causal_expediente, causal_vocal), causal_vocal.user
        )

        assert AtencionFelicitacion.objects.get(socio=causal_imputado).felicitaciones == 0
        acreditaciones = Expediente.objects.filter(
            socio=causal_imputado, motivo__startswith="Acreditación reglamentaria"
        )
        assert acreditaciones.count() == 1


class TestEnmiendaOpcionB:
    def _emitida(self, expediente, vocal, puntos):
        expediente.estado = EstadoExpedienteEnum.EMITIDO
        expediente.puntos = puntos
        expediente.save()
        resolucion = _resolucion(expediente, vocal)
        LedgerService.registrar_resolucion(resolucion, vocal.user)
        Resolucion.objects.filter(pk=resolucion.pk).update(estado=EstadoResolucionEnum.ISSUED)
        return resolucion

    def test_enmienda_revierte_y_aplica_sin_duplicar(self, causal_expediente, causal_vocal):
        anterior = self._emitida(causal_expediente, causal_vocal, Decimal("-3.00"))
        nueva = Resolucion.objects.create(
            expediente=causal_expediente,
            version=2,
            numero_expediente_snapshot=causal_expediente.numero,
            vistos="Vistos.",
            considerandos="Considerando.",
            articulos_resolutivos="Artículo 1.",
            created_by=causal_vocal.user,
        )
        enmienda = EnmiendaResolucion.objects.create(
            resolucion_anterior=anterior,
            resolucion_nueva=nueva,
            motivo_enmienda="Atenuación fundada por hecho nuevo.",
            solicitado_por=causal_vocal.user,
        )
        causal_expediente.puntos = Decimal("-1.00")
        causal_expediente.save()

        LedgerService.registrar_enmienda(enmienda, causal_vocal.user)
        LedgerService.registrar_enmienda(enmienda, causal_vocal.user)  # idempotente

        movimientos = sorted(
            Decimal(str(p.puntajeAplicado)) for p in PuntajeAplicado.objects.filter(socio_id=76001)
        )
        assert movimientos == [Decimal("-3.00"), Decimal("-1.00"), Decimal("3.00")]
        assert _saldo(76001) == Decimal("-1.00")
        tipos = list(
            AsientoLibroMayor.objects.filter(resolucion=nueva)
            .order_by("id")
            .values_list("tipo", flat=True)
        )
        assert tipos == ["REVERSION", "PUNTOS_DIRECTOS"]
        assert LedgerService.verificar_cadena(causal_expediente.socio).valida


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


def test_proveedor_suma_el_impacto_individual_de_cada_socio(make_socio, causal_vocal):
    a = make_socio(legajo="78001", numero_socio=78001)
    b = make_socio(legajo="78002", numero_socio=78002)
    expediente = _expediente("EXP-0705/2026", [a, b], puntos=Decimal("-2.00"))
    _decision(expediente, b, causal_vocal, decision="ACCEPTED")
    decision = ExpedienteConsolidatedDecisionProvider().get_closed_decision(expediente.id)
    assert decision.puntos_finales == Decimal("-2.00")
    assert decision.resultado == "SANCTION"
