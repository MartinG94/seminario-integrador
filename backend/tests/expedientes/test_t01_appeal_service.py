"""Apelación, adecuación e historial del T01 (PB-02, CA1–CA5)."""

from datetime import timedelta
from decimal import Decimal

import pytest
from django.test import override_settings
from django.utils import timezone

from expedientes.models import (
    AdecuacionT01,
    ApelacionT01,
    CambioEstadoExpediente,
    EstadoExpedienteEnum,
    Expediente,
    PeriodoApelacion,
    SolicitudT01,
)
from expedientes.services.t01_appeal_service import (
    T01AppealForbidden,
    T01AppealService,
    T01AppealStateError,
    T01AppealValidationError,
)
from expedientes.services.workflow_service import ExpedienteWorkflowService
from notifications.models import EmailOutbox
from socios.models import Role

pytestmark = pytest.mark.django_db

APELACION = "No estuve presente en el laboratorio ese día; adjunto testigos."
MOTIVOS = "El debate acreditó que la falta fue compartida con un tercer socio."


@pytest.fixture
def en_apelacion(t01_expediente) -> Expediente:
    return ExpedienteWorkflowService.transition(
        expediente_id=t01_expediente.pk,
        estado_nuevo=EstadoExpedienteEnum.JUSTIFICANDO,
        actor="tribunal",
        motivo="Apertura del período de apelación",
    )


@pytest.fixture
def en_debate(en_apelacion) -> Expediente:
    Expediente.objects.filter(pk=en_apelacion.pk).update(
        estado=EstadoExpedienteEnum.REVISION_RESOLUCION
    )
    en_apelacion.refresh_from_db()
    return en_apelacion


def apelar(expediente, socio, texto=APELACION):
    return T01AppealService.present_appeal(
        expediente_id=expediente.pk, user=socio.user, texto=texto
    )


def adecuar(expediente, vocal, **overrides):
    params = {
        "puntos": Decimal("-2"),
        "socio_ids": [s.id for s in expediente.socios.all()],
        "motivos": MOTIVOS,
        "reabrir_plazo": False,
    }
    params.update(overrides)
    return T01AppealService.adjust(expediente_id=expediente.pk, user=vocal.user, **params)


class TestApelacion:
    @override_settings(TRIBUNAL_EMAIL="tribunal@aveit.test")
    def test_apelacion_versionada_con_constancia_por_mail(self, en_apelacion, t01_involucrados):
        socio = t01_involucrados[0]
        primera = apelar(en_apelacion, socio)
        segunda = apelar(en_apelacion, socio, APELACION + " Corrijo la fecha.")

        assert (primera.numero, segunda.numero) == (1, 2)
        assert ApelacionT01.objects.get(pk=primera.pk).texto == APELACION
        destinos = {tuple(m.to) for m in EmailOutbox.objects.all()}
        assert destinos == {(socio.email,), ("tribunal@aveit.test",)}
        assert EmailOutbox.objects.count() == 4

    def test_socio_ajeno_no_apela(self, en_apelacion, make_socio):
        with pytest.raises(T01AppealForbidden):
            apelar(en_apelacion, make_socio(legajo="78999"))

    def test_fuera_de_etapa(self, t01_expediente, t01_involucrados):
        with pytest.raises(T01AppealStateError, match="no admite apelaciones"):
            apelar(t01_expediente, t01_involucrados[0])

    def test_plazo_vencido(self, en_apelacion, t01_involucrados):
        socio = t01_involucrados[0]
        limite = PeriodoApelacion.objects.get(expediente=en_apelacion, socio=socio).limite_at
        with pytest.raises(T01AppealStateError, match="venció"):
            with pytest.MonkeyPatch.context() as mp:
                mp.setattr(timezone, "now", lambda: limite + timedelta(seconds=1))
                apelar(en_apelacion, socio)

    def test_texto_breve(self, en_apelacion, t01_involucrados):
        with pytest.raises(T01AppealValidationError, match="20 caracteres"):
            apelar(en_apelacion, t01_involucrados[0], "No fui yo")

    def test_expediente_sin_t01(self, causal_expediente, causal_imputado):
        causal_expediente.estado = EstadoExpedienteEnum.JUSTIFICANDO
        causal_expediente.save(update_fields=["estado"])
        with pytest.raises(T01AppealValidationError, match="T01"):
            apelar(causal_expediente, causal_imputado)


class TestAdecuacion:
    @pytest.fixture
    def vocal(self, make_socio):
        return make_socio(legajo="78100", role=Role.TD, social_year=6)

    def test_adecua_puntos_e_involucrados_sin_borrar_el_original(
        self, en_debate, t01_involucrados, make_socio, vocal, t01_solicitante
    ):
        tercero = make_socio(legajo="78004")
        ids = [t01_involucrados[0].id, tercero.id]

        adecuacion = adecuar(en_debate, vocal, puntos=Decimal("-1.5"), socio_ids=ids)

        en_debate.refresh_from_db()
        assert en_debate.puntos == Decimal("-1.5")
        assert set(en_debate.socios.values_list("pk", flat=True)) == set(ids)
        assert adecuacion.version == 1
        assert adecuacion.puntos_anteriores == Decimal("-2")
        assert {s["id"] for s in adecuacion.socios_anteriores} == {s.id for s in t01_involucrados}
        assert adecuacion.autor_legajo == "78100"
        solicitud = SolicitudT01.objects.get(expediente=en_debate)
        assert solicitud.puntos == Decimal("-2")
        assert solicitud.snapshot_emitido["puntos"] == "-2.00"
        assert en_debate.estado == EstadoExpedienteEnum.REVISION_RESOLUCION

    def test_motivos_al_solicitante_y_a_los_solicitados(
        self, en_debate, t01_involucrados, vocal, t01_solicitante
    ):
        adecuar(en_debate, vocal, socio_ids=[t01_involucrados[0].id], puntos=Decimal("-1"))

        destinos = sorted(m.to[0] for m in EmailOutbox.objects.all())
        assert destinos == sorted(
            [t01_solicitante.email, t01_involucrados[0].email, t01_involucrados[1].email]
        )
        assert all(MOTIVOS in m.body_text for m in EmailOutbox.objects.all())

    def test_versiones_correlativas(self, en_debate, vocal):
        adecuar(en_debate, vocal, puntos=Decimal("-1"))
        adecuar(en_debate, vocal, puntos=Decimal("-3"))
        assert list(
            AdecuacionT01.objects.filter(expediente=en_debate).values_list("version", flat=True)
        ) == [1, 2]

    def test_reabre_periodo_para_los_afectados(
        self, en_debate, t01_involucrados, make_socio, vocal
    ):
        tercero = make_socio(legajo="78004")
        ids = [s.id for s in t01_involucrados] + [tercero.id]

        adecuacion = adecuar(en_debate, vocal, socio_ids=ids, reabrir_plazo=True)

        en_debate.refresh_from_db()
        assert en_debate.estado == EstadoExpedienteEnum.JUSTIFICANDO
        assert adecuacion.socios_con_nuevo_plazo == [tercero.id]
        nuevo = PeriodoApelacion.objects.get(expediente=en_debate, origen="ADECUACION")
        assert nuevo.socio == tercero
        assert nuevo.adecuacion == adecuacion
        assert CambioEstadoExpediente.objects.filter(
            expediente=en_debate,
            estado_anterior=EstadoExpedienteEnum.REVISION_RESOLUCION,
            estado_nuevo=EstadoExpedienteEnum.JUSTIFICANDO,
        ).exists()
        assert apelar(en_debate, tercero).numero == 1
        with pytest.raises(T01AppealStateError, match="venció"):
            with pytest.MonkeyPatch.context() as mp:
                inicial = PeriodoApelacion.objects.get(
                    expediente=en_debate, socio=t01_involucrados[1]
                )
                mp.setattr(timezone, "now", lambda: inicial.limite_at + timedelta(seconds=1))
                apelar(en_debate, t01_involucrados[1])

    def test_agravar_reabre_para_todos(self, en_debate, t01_involucrados, vocal):
        adecuacion = adecuar(en_debate, vocal, puntos=Decimal("-4"), reabrir_plazo=True)
        assert adecuacion.socios_con_nuevo_plazo == sorted(s.id for s in t01_involucrados)

    def test_reabrir_sin_afectados(self, en_debate, vocal):
        with pytest.raises(T01AppealValidationError, match="afectados"):
            adecuar(en_debate, vocal, puntos=Decimal("-1"), reabrir_plazo=True)
        assert not AdecuacionT01.objects.exists()

    def test_fuera_del_debate(self, en_apelacion, vocal):
        with pytest.raises(T01AppealStateError, match="Justificaciones en revisión"):
            adecuar(en_apelacion, vocal, puntos=Decimal("-1"))

    def test_socio_inexistente(self, en_debate, vocal):
        with pytest.raises(T01AppealValidationError, match="no existen"):
            adecuar(en_debate, vocal, socio_ids=[999999])


class TestHistorial:
    def test_autoridad_ve_todo(self, en_debate, t01_involucrados, make_socio):
        Expediente.objects.filter(pk=en_debate.pk).update(estado=EstadoExpedienteEnum.JUSTIFICANDO)
        apelar(en_debate, t01_involucrados[0])
        apelar(en_debate, t01_involucrados[1])
        cd = make_socio(legajo="78200", role=Role.CD)

        historial = T01AppealService.history(expediente_id=en_debate.pk, user=cd.user)

        assert historial["es_t01"] is True
        assert historial["original"]["snapshot"]["puntos"] == "-2.00"
        assert historial["puntos_vigentes"] == "-2.00"
        assert {s["id"] for s in historial["involucrados"]} == {s.id for s in t01_involucrados}
        assert len(historial["apelaciones"]) == 2
        assert len(historial["periodos"]) == 2

    def test_socio_ve_solo_lo_propio(self, en_apelacion, t01_involucrados):
        apelar(en_apelacion, t01_involucrados[0])
        apelar(en_apelacion, t01_involucrados[1])

        historial = T01AppealService.history(
            expediente_id=en_apelacion.pk, user=t01_involucrados[1].user
        )

        assert [a["socio_id"] for a in historial["apelaciones"]] == [t01_involucrados[1].id]
        assert [p["socio_id"] for p in historial["periodos"]] == [t01_involucrados[1].id]
        assert historial["periodos"][0]["abierto"] is True

    def test_tercero_no_consulta(self, en_apelacion, make_socio):
        with pytest.raises(T01AppealForbidden):
            T01AppealService.history(
                expediente_id=en_apelacion.pk, user=make_socio(legajo="78999").user
            )


class TestParametro:
    def test_registra_el_nuevo_plazo(self, make_socio):
        vocal = make_socio(legajo="78100", role=Role.TD)
        parametro = T01AppealService.set_business_days(dias_habiles=7, user=vocal.user)
        assert parametro.dias_habiles == 7

    def test_plazo_invalido(self, make_socio):
        with pytest.raises(T01AppealValidationError, match="entre 1 y 30"):
            T01AppealService.set_business_days(dias_habiles=0, user=make_socio(legajo="78100").user)
