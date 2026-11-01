"""Tribunal de la causa: inhibición, suplencia automática y casos críticos (S4-04)."""

import pytest

from expedientes.models import (
    ComposicionTribunal,
    EstadoExpedienteEnum,
    SolicitudT01,
)
from expedientes.services.tribunal_composition_service import (
    AD_HOC_NOTICE_KEY,
    TribunalCompositionNotFound,
    TribunalCompositionService,
    involved_socio_ids,
    is_involved,
)
from expedientes.services.workflow_service import ExpedienteWorkflowService
from notifications.models import EmailOutbox
from tests.expedientes.conftest import CARGO_TITULAR_TD

pytestmark = pytest.mark.django_db


def describe(expediente, user=None):
    return TribunalCompositionService.describe(expediente.pk, user)


def seat_socios(payload) -> dict[int, int | None]:
    return {seat["anio_social"]: seat["socio_id"] for seat in payload["asientos"]}


def solicitar(expediente, solicitante) -> SolicitudT01:
    return SolicitudT01.objects.create(
        solicitante=solicitante,
        tipo_accion=SolicitudT01.TipoAccion.SANCTION,
        expediente=expediente,
    )


def resolver(expediente):
    """Avanza de `Justificaciones en revisión` a `Pendiente de firma y envío`."""
    for estado in (EstadoExpedienteEnum.ESPERA_RESOLUCION, EstadoExpedienteEnum.PENDIENTE_CORREOS):
        ExpedienteWorkflowService.transition(
            expediente_id=expediente.pk, estado_nuevo=estado, actor="vocal", motivo="Avance"
        )


def ad_hoc_notices():
    return EmailOutbox.objects.filter(metadata__tipo="AVISO_TRIBUNAL_AD_HOC")


class TestInvolucrados:
    def test_imputados_y_solicitante_son_partes_interesadas(
        self, causal_expediente, causal_imputado, tribunal_nomina
    ):
        solicitar(causal_expediente, tribunal_nomina["t4"])
        causal_expediente.socios.add(tribunal_nomina["t5"])
        assert involved_socio_ids(causal_expediente) == {
            causal_imputado.id,
            tribunal_nomina["t4"].id,
            tribunal_nomina["t5"].id,
        }
        assert is_involved(causal_expediente, tribunal_nomina["t4"].user)
        assert not is_involved(causal_expediente, tribunal_nomina["t6"].user)

    def test_usuario_sin_ficha_de_socio_no_esta_involucrado(
        self, causal_expediente, django_user_model
    ):
        user = django_user_model.objects.create_user(username="sin-socio", password="x")
        assert is_involved(causal_expediente, user) is False


class TestConsulta:
    def test_sin_involucrados_integran_los_titulares(self, causal_expediente, tribunal_nomina):
        payload = describe(causal_expediente)
        assert payload["estampada"] is False
        assert payload["requiere_ad_hoc"] is False
        assert seat_socios(payload) == {
            4: tribunal_nomina["t4"].id,
            5: tribunal_nomina["t5"].id,
            6: tribunal_nomina["t6"].id,
        }
        assert payload["asientos"][1]["firma"] == "81005 - Nombre Apellido81005 - G59"
        assert payload["apartados"] == []

    def test_titular_imputado_lo_reemplaza_su_suplente(self, causal_expediente, tribunal_nomina):
        causal_expediente.socios.add(tribunal_nomina["t5"])
        payload = describe(causal_expediente)
        seat5 = payload["asientos"][1]
        assert seat5["socio_id"] == tribunal_nomina["s5"].id
        assert seat5["condicion"] == "SUPLENTE"
        assert seat5["firma"] == "82005 - Nombre Apellido82005 - G59 (Sup.)"
        assert seat5["reemplaza_a"] == "Nombre Apellido81005 (N° 81005)"
        (apartado,) = payload["apartados"]
        assert apartado["socio_id"] == tribunal_nomina["t5"].id

    def test_titular_solicitante_lo_reemplaza_su_suplente(self, causal_expediente, tribunal_nomina):
        solicitar(causal_expediente, tribunal_nomina["t6"])
        assert seat_socios(describe(causal_expediente))[6] == tribunal_nomina["s6"].id

    def test_usuario_involucrado(self, causal_expediente, tribunal_nomina):
        causal_expediente.socios.add(tribunal_nomina["t4"])
        assert describe(causal_expediente, tribunal_nomina["t4"].user)["usuario"] == {
            "esta_involucrado": True
        }
        assert describe(causal_expediente, tribunal_nomina["t5"].user)["usuario"] == {
            "esta_involucrado": False
        }

    def test_expediente_inexistente(self):
        with pytest.raises(TribunalCompositionNotFound):
            TribunalCompositionService.describe(999999)


class TestEstampadoAlResolver:
    def test_resolver_estampa_los_responsables(self, causal_expediente, tribunal_nomina):
        causal_expediente.socios.add(tribunal_nomina["t4"])
        resolver(causal_expediente)

        composicion = ComposicionTribunal.objects.get(expediente=causal_expediente)
        assert [i.firma for i in composicion.integrantes.all()] == [
            "82004 - Nombre Apellido82004 - G60 (Sup.)",
            "81005 - Nombre Apellido81005 - G59",
            "81006 - Nombre Apellido81006 - G58",
        ]
        assert composicion.apartados[0]["socio_id"] == tribunal_nomina["t4"].id
        payload = describe(causal_expediente)
        assert payload["estampada"] is True
        assert payload["asientos"][0]["condicion"] == "SUPLENTE"

    def test_estampada_no_cambia_con_la_nomina(self, causal_expediente, tribunal_nomina):
        resolver(causal_expediente)
        causal_expediente.socios.add(tribunal_nomina["t5"])
        assert seat_socios(describe(causal_expediente))[5] == tribunal_nomina["t5"].id

    def test_nomina_incompleta_no_impide_resolver(self, causal_expediente, make_legacy_socio):
        # Decisión del PO (31/10/2026): la nómina incompleta deja pasar la resolución.
        make_legacy_socio(81004, 4, CARGO_TITULAR_TD, "TD")
        resolver(causal_expediente)

        causal_expediente.refresh_from_db()
        assert causal_expediente.estado == EstadoExpedienteEnum.PENDIENTE_CORREOS
        composicion = ComposicionTribunal.objects.get(expediente=causal_expediente)
        assert [i.anio_social for i in composicion.integrantes.all()] == [4]


class TestCasosCriticos:
    def test_caso_a_se_informa_sin_inmovilizar_la_causa(self, causal_expediente, tribunal_nomina):
        # Decisión del PO (31/10/2026): la Asamblea designa integrantes con rol TD por
        # fuera del sistema; la causa sigue su curso con quienes no están involucrados.
        causal_expediente.socios.add(tribunal_nomina["t5"], tribunal_nomina["s5"])
        payload = describe(causal_expediente)
        assert payload["requiere_ad_hoc"] is True
        assert payload["motivos_ad_hoc"] == [
            "El titular y el suplente del 5.º año están involucrados en la causa "
            "(Art. 95 del Estatuto)."
        ]
        resolver(causal_expediente)
        causal_expediente.refresh_from_db()
        assert causal_expediente.estado == EstadoExpedienteEnum.PENDIENTE_CORREOS
        composicion = ComposicionTribunal.objects.get(expediente=causal_expediente)
        assert [i.anio_social for i in composicion.integrantes.all()] == [4, 6]

    def test_caso_b_tres_integrantes(self, causal_expediente, tribunal_nomina):
        causal_expediente.socios.add(tribunal_nomina["t4"], tribunal_nomina["t5"])
        solicitar(causal_expediente, tribunal_nomina["s6"])
        assert describe(causal_expediente)["requiere_ad_hoc"] is True


class TestAvisoAComisionDirectiva:
    def test_apertura_con_caso_critico_encola_un_aviso(self, tribunal_nomina, settings):
        settings.COMISION_DIRECTIVA_EMAIL = "cd@aveit.org"
        expediente = ExpedienteWorkflowService.open_expediente(
            motivo="Incidente en plenario",
            socio_ids=[tribunal_nomina["t4"].id, tribunal_nomina["s4"].id],
            actor="cd",
        )
        (aviso,) = ad_hoc_notices()
        assert aviso.to == ["cd@aveit.org"]
        assert expediente.numero in aviso.subject
        assert "Asamblea General" in aviso.body_text
        assert aviso.idempotency_key == AD_HOC_NOTICE_KEY.format(expediente_id=expediente.pk)

    def test_aviso_es_idempotente(self, causal_expediente, tribunal_nomina):
        causal_expediente.socios.add(tribunal_nomina["t6"], tribunal_nomina["s6"])
        TribunalCompositionService.notify_if_ad_hoc(causal_expediente)
        TribunalCompositionService.notify_if_ad_hoc(causal_expediente)
        assert ad_hoc_notices().count() == 1

    def test_sin_caso_critico_no_hay_aviso(self, tribunal_nomina):
        ExpedienteWorkflowService.open_expediente(
            motivo="Inasistencia", socio_ids=[tribunal_nomina["t4"].id], actor="cd"
        )
        assert not ad_hoc_notices().exists()
