"""Tribunal de la causa: inhibición, suplencia automática y casos ad hoc (S4-04)."""

import pytest
from django.core.exceptions import ValidationError

from expedientes.models import (
    ComposicionTribunal,
    EstadoExpedienteEnum,
    ResolucionAsamblea,
    SolicitudT01,
)
from expedientes.services.assembly_resolution_service import (
    AssemblyResolutionService,
    AssemblyResolutionValidationError,
)
from expedientes.services.tribunal_composition_service import (
    AD_HOC_NOTICE_KEY,
    TribunalCompositionNotFound,
    TribunalCompositionService,
    TribunalCompositionStateError,
    involved_socio_ids,
    is_involved,
)
from expedientes.services.workflow_service import ExpedienteWorkflowService
from notifications.models import EmailOutbox
from tests.expedientes.conftest import CARGO_TITULAR_TD, PDF_BYTES

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
        assert payload["asientos"][1]["firma"] == "81005 - Nombre Apellido81005 - G58"
        assert payload["apartados"] == []
        assert payload["observaciones"] == []

    def test_titular_imputado_lo_reemplaza_su_suplente(self, causal_expediente, tribunal_nomina):
        causal_expediente.socios.add(tribunal_nomina["t5"])
        payload = describe(causal_expediente)
        seat5 = payload["asientos"][1]
        assert seat5["socio_id"] == tribunal_nomina["s5"].id
        assert seat5["condicion"] == "SUPLENTE"
        assert seat5["firma"] == "82005 - Nombre Apellido82005 - G58 (Sup.)"
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

    def test_nomina_incompleta_se_informa(self, causal_expediente, make_legacy_socio):
        make_legacy_socio(81004, 4, CARGO_TITULAR_TD, "TD")
        assert "Falta el suplente del 4.º año." in describe(causal_expediente)["observaciones"]

    def test_expediente_inexistente(self):
        with pytest.raises(TribunalCompositionNotFound):
            TribunalCompositionService.describe(999999)


class TestEstampadoAlResolver:
    def test_resolver_estampa_los_responsables(self, causal_expediente, tribunal_nomina):
        causal_expediente.socios.add(tribunal_nomina["t4"])
        resolver(causal_expediente)

        composicion = ComposicionTribunal.objects.get(expediente=causal_expediente)
        assert [i.firma for i in composicion.integrantes.all()] == [
            "82004 - Nombre Apellido82004 - G59 (Sup.)",
            "81005 - Nombre Apellido81005 - G58",
            "81006 - Nombre Apellido81006 - G57",
        ]
        assert composicion.apartados[0]["socio_id"] == tribunal_nomina["t4"].id
        payload = describe(causal_expediente)
        assert payload["estampada"] is True
        assert payload["asientos"][0]["condicion"] == "SUPLENTE"

    def test_estampada_no_cambia_con_la_nomina(self, causal_expediente, tribunal_nomina):
        resolver(causal_expediente)
        causal_expediente.socios.add(tribunal_nomina["t5"])
        assert seat_socios(describe(causal_expediente))[5] == tribunal_nomina["t5"].id

    def test_nomina_invalida_impide_resolver(self, causal_expediente, make_legacy_socio):
        make_legacy_socio(81004, 4, CARGO_TITULAR_TD, "TD")
        with pytest.raises(ValidationError, match="no está integrado"):
            resolver(causal_expediente)
        assert not ComposicionTribunal.objects.exists()


class TestCasosAdHoc:
    def test_caso_a_inmoviliza_la_resolucion_ordinaria(self, causal_expediente, tribunal_nomina):
        causal_expediente.socios.add(tribunal_nomina["t5"], tribunal_nomina["s5"])
        payload = describe(causal_expediente)
        assert payload["requiere_ad_hoc"] is True
        assert payload["motivos_ad_hoc"] == [
            "El titular y el suplente del 5.º año están involucrados en la causa "
            "(Art. 95 del Estatuto)."
        ]
        with pytest.raises(ValidationError, match="Tribunal Ad-Hoc"):
            resolver(causal_expediente)
        causal_expediente.refresh_from_db()
        assert causal_expediente.estado == EstadoExpedienteEnum.ESPERA_RESOLUCION

    def test_caso_b_tres_integrantes(self, causal_expediente, tribunal_nomina):
        causal_expediente.socios.add(tribunal_nomina["t4"], tribunal_nomina["t5"])
        solicitar(causal_expediente, tribunal_nomina["s6"])
        assert describe(causal_expediente)["requiere_ad_hoc"] is True

    def test_puede_registrar_asamblea_solo_cd_o_admin(
        self, causal_expediente, tribunal_nomina, make_socio
    ):
        causal_expediente.socios.add(tribunal_nomina["t5"], tribunal_nomina["s5"])
        cd = make_socio(legajo="77010", role="CD")
        assert describe(causal_expediente, cd.user)["puede_registrar_asamblea"] is True
        assert (
            describe(causal_expediente, tribunal_nomina["t4"].user)["puede_registrar_asamblea"]
            is False
        )


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


class TestResolucionPorAsamblea:
    @pytest.fixture
    def caso_critico(self, causal_expediente, tribunal_nomina):
        causal_expediente.socios.add(tribunal_nomina["t5"], tribunal_nomina["s5"])
        return causal_expediente

    def registrar(self, expediente, user, content=PDF_BYTES, filename="acta.pdf"):
        return AssemblyResolutionService.register(
            expediente_id=expediente.pk, user=user, content=content, filename=filename
        )

    def test_registrar_acta_emite_el_expediente(self, caso_critico, make_socio):
        cd = make_socio(legajo="77010", role="CD")
        resolucion = self.registrar(caso_critico, cd.user)

        caso_critico.refresh_from_db()
        assert caso_critico.estado == EstadoExpedienteEnum.EMITIDO
        assert resolucion.acta_nombre == "acta.pdf"
        assert resolucion.registrada_por_legajo == "77010"
        assert not ComposicionTribunal.objects.filter(expediente=caso_critico).exists()
        motivos = set(caso_critico.cambios_estado.values_list("motivo", flat=True))
        assert "Resolución por Asamblea Extraordinaria (Art. 95 del Estatuto)." in motivos

    def test_sin_caso_critico_no_corresponde(self, causal_expediente, tribunal_nomina, make_socio):
        cd = make_socio(legajo="77010", role="CD")
        with pytest.raises(TribunalCompositionStateError, match="no requiere"):
            self.registrar(causal_expediente, cd.user)

    def test_no_antes_de_vencer_el_periodo_de_justificaciones(self, caso_critico, make_socio):
        caso_critico.estado = EstadoExpedienteEnum.JUSTIFICANDO
        caso_critico.save(update_fields=["estado"])
        cd = make_socio(legajo="77010", role="CD")
        with pytest.raises(TribunalCompositionStateError, match="período de justificaciones"):
            self.registrar(caso_critico, cd.user)

    def test_el_acta_debe_ser_pdf(self, caso_critico, make_socio):
        cd = make_socio(legajo="77010", role="CD")
        png = b"\x89PNG\r\n\x1a\n" + b"0" * 10
        with pytest.raises(AssemblyResolutionValidationError, match="PDF"):
            self.registrar(caso_critico, cd.user, content=png, filename="acta.png")
        assert not ResolucionAsamblea.objects.exists()

    def test_no_se_registra_dos_veces(self, caso_critico, make_socio):
        cd = make_socio(legajo="77010", role="CD")
        self.registrar(caso_critico, cd.user)
        with pytest.raises(TribunalCompositionStateError, match="ya tiene"):
            self.registrar(caso_critico, cd.user)
