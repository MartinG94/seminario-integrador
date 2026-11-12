"""Pruebas de consistencia de puntaje especial e idempotencia en evaluación de descargos."""

from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError

from expedientes.domain.causal_resolution import CausalDecision
from expedientes.domain.puntaje_especial import (
    PuntajeEspecial,
    parse_puntaje_especial,
)
from expedientes.models import (
    AtencionFelicitacion,
    Expediente,
    SolicitudT01,
)
from expedientes.serializers import (
    BoardExpedienteSerializer,
    ExpedienteListSerializer,
    SolicitudT01Serializer,
)
from expedientes.services.causal_resolution_service import CausalResolutionService


@pytest.mark.django_db
class TestPuntajeEspecialDomainYModel:
    def test_parse_puntaje_especial(self):
        assert parse_puntaje_especial("LLAMADO_ATENCION") == PuntajeEspecial.LLAMADO_ATENCION
        assert parse_puntaje_especial("llamado de atención") == PuntajeEspecial.LLAMADO_ATENCION
        assert parse_puntaje_especial("-0.25") == PuntajeEspecial.LLAMADO_ATENCION
        assert parse_puntaje_especial(Decimal("-0.25")) == PuntajeEspecial.LLAMADO_ATENCION

        assert parse_puntaje_especial("FELICITACION") == PuntajeEspecial.FELICITACION
        assert parse_puntaje_especial("felicitación") == PuntajeEspecial.FELICITACION
        assert parse_puntaje_especial("0.25") == PuntajeEspecial.FELICITACION
        assert parse_puntaje_especial(Decimal("0.25")) == PuntajeEspecial.FELICITACION

        assert parse_puntaje_especial("-1.0") == PuntajeEspecial.NINGUNO
        assert parse_puntaje_especial(None) == PuntajeEspecial.NINGUNO

    def test_solicitud_t01_validation_incoherente(self, make_socio):
        socio = make_socio(legajo="79001")
        solicitud = SolicitudT01(
            solicitante=socio,
            destinatarios_socios_ids=[socio.id],
            tipo_accion=SolicitudT01.TipoAccion.SANCTION,
            puntos=Decimal("-1.0"),
            puntaje_especial=SolicitudT01.PuntajeEspecial.LLAMADO_ATENCION,
            titulo="Test",
            motivo="Motivo",
        )
        with pytest.raises(ValidationError) as exc_info:
            solicitud.clean()
        assert "puntaje_especial" in exc_info.value.message_dict

    def test_solicitud_t01_serializer_autocompleta_especial(self, make_socio):
        socio = make_socio(legajo="79002")
        serializer = SolicitudT01Serializer(
            data={
                "solicitante": socio.id,
                "destinatarios_socios_ids": [socio.id],
                "puntaje_especial": "LLAMADO_ATENCION",
                "titulo": "Falta a reunión",
                "motivo": "Motivo fundado",
                "razon": "Razon",
            }
        )
        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["puntos"] == Decimal("-0.25")
        assert serializer.validated_data["tipo_accion"] == SolicitudT01.TipoAccion.SANCTION

    def test_expediente_serializer_expone_puntaje_solicitado(self, make_socio):
        socio = make_socio(legajo="79003")
        exp = Expediente.objects.create(
            numero="EXP-TEST/2026",
            socio=socio,
            motivo="Test",
            puntos=Decimal("-0.25"),
        )
        list_data = ExpedienteListSerializer(exp).data
        assert list_data.get("puntaje_solicitado") == "LLAMADO_ATENCION"

        board_data = BoardExpedienteSerializer(exp).data
        assert board_data.get("puntaje_solicitado") == "LLAMADO_ATENCION"

    def test_solicitud_t01_serializer_valida_expedientes_referenciados(self, make_socio):
        from expedientes.models import EstadoExpedienteEnum

        socio = make_socio(legajo="79004")
        emitido = Expediente.objects.create(
            numero="EXP-0991/2026",
            titulo="Precedente relevante",
            socio=socio,
            motivo="Motivo precedente",
            estado=EstadoExpedienteEnum.EMITIDO,
        )
        no_emitido = Expediente.objects.create(
            numero="EXP-0992/2026",
            socio=socio,
            motivo="No emitido",
            estado=EstadoExpedienteEnum.JUSTIFICANDO,
        )

        # 1. Rechaza no emitido
        s_invalido = SolicitudT01Serializer(
            data={
                "solicitante": socio.id,
                "destinatarios_socios_ids": [socio.id],
                "tipo_accion": "SANCTION",
                "puntos": "-1.00",
                "titulo": "Falta",
                "motivo": "Motivo",
                "expedientes_referenciados": [no_emitido.id],
            }
        )
        assert not s_invalido.is_valid()
        assert "expedientes_referenciados" in s_invalido.errors

        # 2. Acepta emitido y expone detalle
        s_valido = SolicitudT01Serializer(
            data={
                "solicitante": socio.id,
                "destinatarios_socios_ids": [socio.id],
                "tipo_accion": "SANCTION",
                "puntos": "-1.00",
                "titulo": "Falta",
                "motivo": "Motivo",
                "expedientes_referenciados": [emitido.id],
            }
        )
        assert s_valido.is_valid(), s_invalido.errors
        instancia = s_valido.save(solicitante=socio)
        data = SolicitudT01Serializer(instancia).data
        assert data["expedientes_referenciados"] == [emitido.id]
        assert len(data["expedientes_referenciados_detalle"]) == 1
        assert data["expedientes_referenciados_detalle"][0]["numero"] == "EXP-0991/2026"


@pytest.mark.django_db
class TestCausalResolutionIdempotencia:
    def test_llamado_atencion_suma_una_sola_vez_aunque_se_guarde_repetido(
        self, causal_descargo, causal_vocal
    ):
        socio = causal_descargo.socio
        atencion, _ = AtencionFelicitacion.objects.get_or_create(socio=socio)
        assert atencion.llamadosAtencion == 0

        # Primera decisión con Llamado de Atención
        CausalResolutionService.decide(
            expediente_id=causal_descargo.expediente_id,
            descargo_id=causal_descargo.id,
            decision=CausalDecision.ACCEPTED,
            fundamento="Primer guardado con llamado de atencion conforme reglamento.",
            evidencia_ids=None,
            user=causal_vocal.user,
            puntaje_final="LLAMADO_ATENCION",
        )
        atencion.refresh_from_db()
        assert atencion.llamadosAtencion == 1

        # Segundo guardado (misma opción LLAMADO_ATENCION)
        CausalResolutionService.decide(
            expediente_id=causal_descargo.expediente_id,
            descargo_id=causal_descargo.id,
            decision=CausalDecision.ACCEPTED,
            fundamento="Segundo guardado con mismo llamado conforme reglamento.",
            evidencia_ids=None,
            user=causal_vocal.user,
            puntaje_final="LLAMADO_ATENCION",
        )
        atencion.refresh_from_db()
        # Debe mantenerse en 1, NO duplicar a 2
        assert atencion.llamadosAtencion == 1

    def test_cambio_de_llamado_a_puntaje_numerico_revierte_contador(
        self, causal_descargo, causal_vocal
    ):
        socio = causal_descargo.socio
        atencion, _ = AtencionFelicitacion.objects.get_or_create(socio=socio)

        # 1. Guardar Llamado de Atención
        CausalResolutionService.decide(
            expediente_id=causal_descargo.expediente_id,
            descargo_id=causal_descargo.id,
            decision=CausalDecision.ACCEPTED,
            fundamento="Llamado inicial dictaminado por falta menor.",
            evidencia_ids=None,
            user=causal_vocal.user,
            puntaje_final="LLAMADO_ATENCION",
        )
        atencion.refresh_from_db()
        assert atencion.llamadosAtencion == 1

        # 2. Tribunal cambia de opinión a -1.0 (sanción numérica)
        CausalResolutionService.decide(
            expediente_id=causal_descargo.expediente_id,
            descargo_id=causal_descargo.id,
            decision=CausalDecision.ACCEPTED,
            fundamento="Cambio a sancion de un punto por reevaluacion de antecedentes.",
            evidencia_ids=None,
            user=causal_vocal.user,
            puntaje_final="-1.0",
        )
        atencion.refresh_from_db()
        # Debe haber compensado el llamado
        assert atencion.llamadosAtencion == 0

    def test_cambio_de_llamado_a_felicitacion_compensa_e_incrementa(
        self, causal_descargo, causal_vocal
    ):
        socio = causal_descargo.socio
        atencion, _ = AtencionFelicitacion.objects.get_or_create(socio=socio)

        # 1. Llamado
        CausalResolutionService.decide(
            expediente_id=causal_descargo.expediente_id,
            descargo_id=causal_descargo.id,
            decision=CausalDecision.ACCEPTED,
            fundamento="Llamado inicial dictaminado por falta menor.",
            evidencia_ids=None,
            user=causal_vocal.user,
            puntaje_final="LLAMADO_ATENCION",
        )
        atencion.refresh_from_db()
        assert atencion.llamadosAtencion == 1
        assert atencion.felicitaciones == 0

        # 2. Felicitación
        CausalResolutionService.decide(
            expediente_id=causal_descargo.expediente_id,
            descargo_id=causal_descargo.id,
            decision=CausalDecision.ACCEPTED,
            fundamento="Cambio a felicitacion institucional por aporte extraordinario.",
            evidencia_ids=None,
            user=causal_vocal.user,
            puntaje_final="FELICITACION",
        )
        atencion.refresh_from_db()
        assert atencion.llamadosAtencion == 0
        assert atencion.felicitaciones == 1
