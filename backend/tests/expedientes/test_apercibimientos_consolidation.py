"""Tests unitarios TDD para el motor de llamados de atención, felicitaciones y terna 3:1.

Valida las 5 reglas PO:
1. `register_warning` y `register_felicitacion` abren un expediente con 0.00 puntos
   identificable como `es_llamado` / `es_felicitacion`.
2. Transicionan a `JUSTIFICANDO` (con plazo de 5 días hábiles) si el envío del correo es
   exitoso, o permanecen en `CREADO` (sin plazo congelado) si falla el envío.
3. No modifican contadores en `atencionFelicitacion` ni `PuntajeAplicado` antes de emitir.
4. Al emitir resolución (`LedgerService.registrar_resolucion`):
   - El 1.° y 2.° confirmado incrementan el contador a 1 y 2 sin tocar `PuntajeAplicado`.
   - El 3.° confirmado aplica -1.00 (llamados) o +1.00 (felicitaciones) en `PuntajeAplicado`
     vinculado a esa 3.ª resolución, sin crear un 4.° expediente, dejando el contador en 0.
   - Si el 3.° tiene descargo aceptado (`ACCEPTED` / sin efecto), el contador queda en 2
     y `PuntajeAplicado` no recibe movimientos.
"""

import socket
from decimal import Decimal
from unittest.mock import patch

import pytest
from django.core.exceptions import ValidationError

from expedientes.models import (
    AtencionFelicitacion,
    DecisionCausalDescargo,
    DecisionCausalEnum,
    DescargoExpediente,
    EstadoExpedienteEnum,
    Expediente,
    Resolucion,
    SolicitudT01,
    TipoDescargoEnum,
    detectar_medida_expediente,
)
from expedientes.services.ledger_service import LedgerService
from expedientes.services.warning_accumulation_service import WarningAccumulationService
from notifications.models import EmailOutbox, EmailOutboxStatus
from ranking.models import PuntajeAplicado
from socios.models import Role, Socio


@pytest.fixture
def socio_test(make_socio):
    """Socio de prueba con número institucional asignado."""
    return make_socio(legajo="20001", numero_socio=20001, role=Role.SOCIO)


@pytest.fixture
def vocal_test(make_socio):
    """Vocal del Tribunal de Disciplina para emitir resoluciones."""
    return make_socio(legajo="20099", numero_socio=20099, role=Role.TD, social_year=5)


def _emitir_expediente(
    expediente: Expediente,
    vocal: Socio,
    *,
    decision: str | None = None,
) -> Resolucion:
    if decision is not None:
        descargo = DescargoExpediente.objects.create(
            expediente=expediente,
            socio=expediente.socio,
            tipo=TipoDescargoEnum.T02_CERTIFICADO,
        )
        DecisionCausalDescargo.objects.create(
            expediente=expediente,
            descargo=descargo,
            version=1,
            decision=decision,
            regla_sugerida=decision,
            descargo_snapshot={},
            autor=vocal.user,
            autor_legajo=vocal.legajo,
            autor_rol=vocal.role,
        )
    expediente.estado = EstadoExpedienteEnum.EMITIDO
    expediente.save(update_fields=["estado"])
    resolucion = Resolucion.objects.create(
        expediente=expediente,
        numero_expediente_snapshot=expediente.numero,
        vistos="Vistos.",
        considerandos="Considerandos.",
        articulos_resolutivos="Artículo 1.",
        created_by=vocal.user,
    )
    LedgerService.registrar_resolucion(resolucion, vocal.user)
    return resolucion


@pytest.mark.django_db
class TestDeteccionMedidaExpediente:
    def test_detecta_medidas_por_puntos_t01_y_titulo_motivo(self, socio_test):
        exp_cero_llamado = Expediente.objects.create(
            numero="EXP-DET-1/2026",
            socio=socio_test,
            titulo="Llamado de atención: Impuntualidad leve",
            motivo="Llamado de atención (Art. 100.a): Llegó 20 minutos tarde.",
            puntos=Decimal("0.00"),
        )
        assert detectar_medida_expediente(exp_cero_llamado) == "LLAMADO_ATENCION"
        assert exp_cero_llamado.tipo_medida == "LLAMADO_ATENCION"
        assert exp_cero_llamado.es_llamado is True
        assert exp_cero_llamado.es_felicitacion is False

        exp_cero_felic = Expediente.objects.create(
            numero="EXP-DET-2/2026",
            socio=socio_test,
            titulo="Felicitación institucional",
            motivo="Reconocimiento por organización de jornada.",
            puntos=Decimal("0.00"),
        )
        assert exp_cero_felic.tipo_medida == "FELICITACION"
        assert exp_cero_felic.es_felicitacion is True
        assert exp_cero_felic.es_llamado is False

        exp_hist = Expediente.objects.create(
            numero="EXP-DET-3/2026",
            socio=socio_test,
            motivo="Histórico",
            puntos=Decimal("-0.33"),
        )
        assert exp_hist.es_llamado is True

        exp_t01 = Expediente.objects.create(
            numero="EXP-DET-4/2026",
            socio=socio_test,
            motivo="Mérito T01",
            puntos=Decimal("0.00"),
        )
        SolicitudT01.objects.create(
            solicitante=socio_test,
            destinatarios_socios_ids=[socio_test.id],
            tipo_accion=SolicitudT01.TipoAccion.MERIT,
            puntaje_especial=SolicitudT01.PuntajeEspecial.FELICITACION,
            puntos=Decimal("0.25"),
            causal="Aporte destacado",
            expediente=exp_t01,
        )
        assert exp_t01.es_felicitacion is True


@pytest.mark.django_db
class TestWarningAccumulationService:
    """Pruebas del flujo completo de llamados y felicitaciones con emisión y 3:1."""

    def test_register_warning_abre_expediente_0_pts_y_transiciona_a_justificando(
        self, socio_test, settings
    ):
        settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

        ap1, exp1 = WarningAccumulationService.register_warning(
            socio_id=socio_test.id,
            origen_tipo="REUNION_TARDANZA_LEVE",
            motivo="Llegó 18 minutos tarde a reunión ordinaria.",
            articulo_reglamento="Art. 100.a",
        )

        assert exp1 is not None
        exp1.refresh_from_db()
        assert exp1.puntos == Decimal("0.00")
        assert exp1.es_llamado is True
        assert exp1.es_felicitacion is False
        assert exp1.estado == EstadoExpedienteEnum.JUSTIFICANDO
        assert exp1.plazo_inicio_at is not None
        assert exp1.plazo_limite_at is not None

        # No mueve contadores ni PuntajeAplicado antes de emitir
        ap1.refresh_from_db()
        assert ap1.llamadosAtencion == 0
        assert WarningAccumulationService.get_pending_count(socio_test.id) == 0
        assert not PuntajeAplicado.objects.filter(socio_id=20001).exists()

        outbox = EmailOutbox.objects.get(metadata__expediente_id=exp1.id)
        assert outbox.status == EmailOutboxStatus.SENT

    @patch("django.core.mail.message.EmailMultiAlternatives.send")
    def test_register_warning_fallo_smtp_deja_expediente_en_creado_sin_plazo(
        self, mock_send, socio_test, settings
    ):
        settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
        mock_send.side_effect = socket.error("SMTP unreachable")

        ap, exp = WarningAccumulationService.register_warning(
            socio_id=socio_test.id,
            origen_tipo="REUNION_TARDANZA_LEVE",
            motivo="Llegó 22 minutos tarde a reunión.",
            articulo_reglamento="Art. 100.a",
        )

        exp.refresh_from_db()
        assert exp.estado == EstadoExpedienteEnum.CREADO
        assert exp.plazo_inicio_at is None
        assert exp.plazo_limite_at is None
        assert ap.llamadosAtencion == 0
        assert not EmailOutbox.objects.filter(metadata__expediente_id=exp.id).exists()

    def test_emision_llamados_1_2_y_3_consolida_terna_en_puntaje_aplicado(
        self, socio_test, vocal_test, settings
    ):
        settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

        _, exp1 = WarningAccumulationService.register_warning(
            socio_id=socio_test.id,
            origen_tipo="REUNION_TARDANZA_LEVE",
            motivo="Demora 20 min reunión 1.",
        )
        _, exp2 = WarningAccumulationService.register_warning(
            socio_id=socio_test.id,
            origen_tipo="REUNION_TARDANZA_LEVE",
            motivo="Demora 16 min reunión 2.",
        )
        _, exp3 = WarningAccumulationService.register_warning(
            socio_id=socio_test.id,
            origen_tipo="LLAMADO_ATENCION",
            motivo="Falta de aseo en cocina comunitaria.",
            actor="CD_PRESIDENCIA",
        )

        # Antes de emitir, siguen en 0 llamados y 0 movimientos
        assert WarningAccumulationService.get_pending_count(socio_test.id) == 0
        assert not PuntajeAplicado.objects.filter(socio_id=20001).exists()

        # Emitir 1° y 2° confirmado -> contador en 1 y 2, sin PuntajeAplicado
        _emitir_expediente(exp1, vocal_test)
        assert WarningAccumulationService.get_pending_count(socio_test.id) == 1
        assert not PuntajeAplicado.objects.filter(socio_id=20001).exists()

        _emitir_expediente(exp2, vocal_test)
        assert WarningAccumulationService.get_pending_count(socio_test.id) == 2
        assert not PuntajeAplicado.objects.filter(socio_id=20001).exists()

        # Emitir 3° confirmado -> aplica -1.00 vinculado a exp3, sin crear 4° expediente
        _emitir_expediente(exp3, vocal_test)
        assert Expediente.objects.filter(socio=socio_test).count() == 3
        assert WarningAccumulationService.get_pending_count(socio_test.id) == 0

        mov = PuntajeAplicado.objects.get(socio_id=20001)
        assert mov.puntajeAplicado == Decimal("-1.00")
        assert mov.expediente_id == exp3.id

    def test_emision_tercer_llamado_con_descargo_aceptado_no_consolida(
        self, socio_test, vocal_test, settings
    ):
        settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

        for i in range(2):
            _, exp = WarningAccumulationService.register_warning(
                socio_id=socio_test.id,
                motivo=f"Llamado confirmado #{i + 1}",
            )
            _emitir_expediente(exp, vocal_test)

        _, exp3 = WarningAccumulationService.register_warning(
            socio_id=socio_test.id,
            motivo="Tercer llamado con descargo aceptado.",
        )
        _emitir_expediente(exp3, vocal_test, decision=DecisionCausalEnum.ACCEPTED)

        assert WarningAccumulationService.get_pending_count(socio_test.id) == 2
        assert not PuntajeAplicado.objects.filter(socio_id=20001).exists()
        assert LedgerService.calcular_saldo(socio_test) == Decimal("0.00")

    def test_consolidacion_felicitaciones_3_a_1_al_emitir(self, socio_test, vocal_test, settings):
        settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

        exps = []
        for idx, motivo in enumerate(
            (
                "Mérito por voluntariado en jornada de pintura.",
                "Mérito por organización de torneo deportivo.",
                "Mérito por coordinación en plenario estudiantil.",
            ),
            start=1,
        ):
            at, exp = WarningAccumulationService.register_felicitacion(
                socio_id=socio_test.id,
                motivo=motivo,
            )
            assert exp.puntos == Decimal("0.00")
            assert exp.es_felicitacion is True
            assert exp.estado == EstadoExpedienteEnum.JUSTIFICANDO
            assert at.felicitaciones == 0
            exps.append(exp)

        _emitir_expediente(exps[0], vocal_test)
        assert AtencionFelicitacion.objects.get(socio=socio_test).felicitaciones == 1
        assert not PuntajeAplicado.objects.filter(socio_id=20001).exists()

        _emitir_expediente(exps[1], vocal_test)
        assert AtencionFelicitacion.objects.get(socio=socio_test).felicitaciones == 2
        assert not PuntajeAplicado.objects.filter(socio_id=20001).exists()

        _emitir_expediente(exps[2], vocal_test)
        assert AtencionFelicitacion.objects.get(socio=socio_test).felicitaciones == 0
        assert Expediente.objects.filter(socio=socio_test).count() == 3

        mov = PuntajeAplicado.objects.get(socio_id=20001)
        assert mov.puntajeAplicado == Decimal("1.00")
        assert mov.expediente_id == exps[2].id

    def test_rechazo_motivo_vacio(self, socio_test):
        """No permite registrar llamados sin motivo circunstanciado."""
        with pytest.raises(ValidationError):
            WarningAccumulationService.register_warning(
                socio_id=socio_test.id,
                origen_tipo="LLAMADO_ATENCION",
                motivo="   ",
            )

    def test_rechazo_socio_inexistente(self):
        """Lanza ValidationError si el socio_id no corresponde a ningún registro."""
        with pytest.raises(ValidationError):
            WarningAccumulationService.register_warning(
                socio_id=999999,
                origen_tipo="LLAMADO_ATENCION",
                motivo="Apercibimiento socio inválido",
            )
