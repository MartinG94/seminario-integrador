"""Plazo parametrizado y períodos de apelación por socio del T01 (PB-02, CA1/CA5)."""

from datetime import timedelta

import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone

from expedientes.models import (
    EstadoExpedienteEnum,
    Expediente,
    ParametroPlazoApelacion,
    PeriodoApelacion,
)
from expedientes.services.deadline_service import DeadlineEnforcementService
from expedientes.services.t01_appeal_service import T01AppealService
from expedientes.services.workflow_service import ExpedienteWorkflowService

pytestmark = pytest.mark.django_db


def abrir_periodo(expediente: Expediente) -> Expediente:
    return ExpedienteWorkflowService.transition(
        expediente_id=expediente.pk,
        estado_nuevo=EstadoExpedienteEnum.JUSTIFICANDO,
        actor="tribunal",
        motivo="Apertura del período de apelación",
    )


def test_identifica_expedientes_originados_en_t01(t01_expediente, causal_expediente):
    assert T01AppealService.is_t01(t01_expediente) is True
    assert T01AppealService.is_t01(causal_expediente) is False


def test_abre_un_periodo_por_socio_con_el_plazo_vigente(
    t01_expediente, t01_involucrados, causal_vocal
):
    ParametroPlazoApelacion.objects.create(dias_habiles=3, autor=causal_vocal.user)

    expediente = abrir_periodo(t01_expediente)

    periodos = list(PeriodoApelacion.objects.filter(expediente=expediente))
    assert {p.socio_id for p in periodos} == {s.id for s in t01_involucrados}
    assert {p.dias_habiles for p in periodos} == {3}
    assert {p.origen for p in periodos} == {"APERTURA"}
    assert expediente.plazo_limite_at == periodos[0].limite_at


def test_iniciar_plazo_descargo_usa_el_parametro_en_t01(t01_expediente, causal_vocal):
    ParametroPlazoApelacion.objects.create(dias_habiles=2, autor=causal_vocal.user)
    t01_expediente.iniciar_plazo_descargo(timezone.now())
    assert set(
        PeriodoApelacion.objects.filter(expediente=t01_expediente).values_list(
            "dias_habiles", flat=True
        )
    ) == {2}


def test_cambiar_el_parametro_no_altera_periodos_abiertos(t01_expediente, causal_vocal):
    expediente = abrir_periodo(t01_expediente)
    limite = expediente.plazo_limite_at
    ParametroPlazoApelacion.objects.create(dias_habiles=10, autor=causal_vocal.user)
    assert {p.limite_at for p in expediente.periodos_apelacion.all()} == {limite}


def test_expediente_sin_t01_no_abre_periodos(causal_expediente):
    causal_expediente.estado = EstadoExpedienteEnum.CREADO
    causal_expediente.save(update_fields=["estado"])
    abrir_periodo(causal_expediente)
    assert not PeriodoApelacion.objects.exists()


def test_el_plazo_efectivo_es_el_ultimo_periodo_abierto(t01_expediente, t01_involucrados):
    expediente = abrir_periodo(t01_expediente)
    ahora = timezone.now()
    PeriodoApelacion.objects.create(
        expediente=expediente,
        socio=t01_involucrados[0],
        origen="ADECUACION",
        dias_habiles=5,
        inicio_at=ahora,
        limite_at=ahora + timedelta(days=20),
    )
    assert T01AppealService.effective_deadline(expediente) == ahora + timedelta(days=20)


def test_no_pasa_a_revision_hasta_vencer_el_ultimo_periodo(t01_expediente, t01_involucrados):
    expediente = abrir_periodo(t01_expediente)
    ahora = timezone.now()
    Expediente.objects.filter(pk=expediente.pk).update(plazo_limite_at=ahora - timedelta(days=1))
    PeriodoApelacion.objects.create(
        expediente=expediente,
        socio=t01_involucrados[0],
        origen="ADECUACION",
        dias_habiles=5,
        inicio_at=ahora,
        limite_at=ahora + timedelta(days=3),
    )

    with pytest.raises(ValidationError, match="período de justificaciones"):
        ExpedienteWorkflowService.transition(
            expediente_id=expediente.pk,
            estado_nuevo=EstadoExpedienteEnum.REVISION_RESOLUCION,
            actor="tribunal",
            motivo="Cierre",
        )
    assert DeadlineEnforcementService().close_expired_deadlines() == 0
    assert (
        DeadlineEnforcementService().close_expired_deadlines(ahora=ahora + timedelta(days=30)) == 1
    )
