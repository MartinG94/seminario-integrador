"""Servicio de constitución del Tribunal por causa (S4-04, CA1–CA5)."""

import pytest
from django.core.exceptions import ValidationError

from expedientes.models import (
    ApartamientoTribunal,
    ComposicionTribunal,
    DesignacionAdHoc,
    EstadoExpedienteEnum,
)
from expedientes.services.tribunal_composition_service import (
    TribunalCompositionForbidden,
    TribunalCompositionService,
    TribunalCompositionStateError,
    TribunalCompositionValidationError,
)
from expedientes.services.workflow_service import ExpedienteWorkflowService
from tests.expedientes.conftest import CARGO_TITULAR_TD

pytestmark = pytest.mark.django_db

FUNDAMENTO = "Comparto vivienda con el socio imputado en la causa."
ACTA = "Acta de Asamblea Extraordinaria N° 3/2026"


def describe(expediente):
    return TribunalCompositionService.describe(expediente.pk)


def seat_socios(payload) -> dict[int, int | None]:
    return {seat["anio_social"]: seat["socio_id"] for seat in payload["asientos"]}


class TestConsulta:
    def test_sin_involucrados_integran_los_titulares(self, causal_expediente, tribunal_nomina):
        payload = describe(causal_expediente)
        assert payload["constituida"] is False
        assert payload["es_ad_hoc"] is False
        assert seat_socios(payload) == {
            4: tribunal_nomina["t4"].id,
            5: tribunal_nomina["t5"].id,
            6: tribunal_nomina["t6"].id,
        }
        assert payload["asientos"][1]["firma"] == "81005 - Nombre Apellido81005 - G58"
        assert payload["observaciones"] == []
        assert payload["puede_constituirse"] is True

    def test_titular_involucrado_se_aparta_y_asume_el_suplente(
        self, causal_expediente, tribunal_nomina
    ):
        causal_expediente.socios.add(tribunal_nomina["t5"])
        payload = describe(causal_expediente)
        assert seat_socios(payload)[5] == tribunal_nomina["s5"].id
        seat5 = payload["asientos"][1]
        assert seat5["condicion"] == "SUPLENTE"
        assert seat5["firma"].endswith("(Sup.)")
        assert seat5["reemplaza_a"] == "Nombre Apellido81005 (N° 81005)"
        (apartamiento,) = payload["apartamientos"]
        assert apartamiento["socio_id"] == tribunal_nomina["t5"].id
        assert apartamiento["causa"] == "INVOLUCRADO"
        assert apartamiento["causa_display"] == "Involucrado en la causa (Art. 95)"

    def test_nomina_incompleta_impide_constituir(self, causal_expediente, make_legacy_socio):
        make_legacy_socio(81004, 4, CARGO_TITULAR_TD, "TD")
        payload = describe(causal_expediente)
        assert "Falta el suplente del 4.º año." in payload["observaciones"]
        assert payload["puede_constituirse"] is False

    def test_expediente_inexistente(self):
        from expedientes.services.tribunal_composition_service import (
            TribunalCompositionNotFound,
        )

        with pytest.raises(TribunalCompositionNotFound):
            TribunalCompositionService.describe(999999)


class TestUsuario:
    def test_integrante_y_apartado(self, causal_expediente, tribunal_nomina, causal_vocal):
        causal_expediente.socios.add(tribunal_nomina["t4"])
        describe_for = TribunalCompositionService.describe
        assert describe_for(causal_expediente.pk, tribunal_nomina["t4"].user)["usuario"] == {
            "es_integrante": True,
            "esta_apartado": True,
        }
        assert describe_for(causal_expediente.pk, tribunal_nomina["t5"].user)["usuario"] == {
            "es_integrante": True,
            "esta_apartado": False,
        }
        assert describe_for(causal_expediente.pk, causal_vocal.user)["usuario"] == {
            "es_integrante": False,
            "esta_apartado": False,
        }


class TestApartamientoPorConflicto:
    def test_integrante_declara_su_conflicto(self, causal_expediente, tribunal_nomina):
        t6 = tribunal_nomina["t6"]
        apartamiento = TribunalCompositionService.declare_conflict(
            expediente_id=causal_expediente.pk, user=t6.user, fundamento=FUNDAMENTO
        )
        assert apartamiento.socio == t6
        assert apartamiento.causa == "CONFLICTO_INTERES"
        assert seat_socios(describe(causal_expediente))[6] == tribunal_nomina["s6"].id

    def test_quien_no_integra_la_nomina_no_puede_apartar(
        self, causal_expediente, tribunal_nomina, causal_vocal
    ):
        with pytest.raises(TribunalCompositionValidationError, match="recusación"):
            TribunalCompositionService.declare_conflict(
                expediente_id=causal_expediente.pk, user=causal_vocal.user, fundamento=FUNDAMENTO
            )

    def test_fundamento_breve(self, causal_expediente, tribunal_nomina):
        with pytest.raises(TribunalCompositionValidationError, match="20 caracteres"):
            TribunalCompositionService.declare_conflict(
                expediente_id=causal_expediente.pk,
                user=tribunal_nomina["t4"].user,
                fundamento="Breve",
            )

    def test_no_se_duplica(self, causal_expediente, tribunal_nomina):
        user = tribunal_nomina["t4"].user
        TribunalCompositionService.declare_conflict(
            expediente_id=causal_expediente.pk, user=user, fundamento=FUNDAMENTO
        )
        with pytest.raises(TribunalCompositionValidationError, match="Ya registraste"):
            TribunalCompositionService.declare_conflict(
                expediente_id=causal_expediente.pk, user=user, fundamento=FUNDAMENTO
            )

    def test_involucrado_ya_esta_apartado(self, causal_expediente, tribunal_nomina):
        causal_expediente.socios.add(tribunal_nomina["t4"])
        with pytest.raises(TribunalCompositionValidationError, match="involucrado"):
            TribunalCompositionService.declare_conflict(
                expediente_id=causal_expediente.pk,
                user=tribunal_nomina["t4"].user,
                fundamento=FUNDAMENTO,
            )

    def test_fuera_de_etapa(self, causal_expediente, tribunal_nomina):
        causal_expediente.estado = EstadoExpedienteEnum.PENDIENTE_CORREOS
        causal_expediente.save(update_fields=["estado"])
        with pytest.raises(TribunalCompositionStateError):
            TribunalCompositionService.declare_conflict(
                expediente_id=causal_expediente.pk,
                user=tribunal_nomina["t4"].user,
                fundamento=FUNDAMENTO,
            )


class TestTribunalAdHoc:
    @pytest.fixture
    def caso_ad_hoc(self, causal_expediente, tribunal_nomina):
        causal_expediente.socios.add(tribunal_nomina["t4"], tribunal_nomina["s4"])
        return causal_expediente

    def test_dos_involucrados_del_mismo_anio(self, caso_ad_hoc, tribunal_nomina):
        payload = describe(caso_ad_hoc)
        assert payload["es_ad_hoc"] is True
        assert {p["socio_id"] for p in payload["pendientes_ad_hoc"]} == {
            tribunal_nomina["t4"].id,
            tribunal_nomina["s4"].id,
        }
        assert payload["puede_constituirse"] is False

    def designar(self, expediente, user, reemplaza_a, designado):
        return TribunalCompositionService.designate_ad_hoc(
            expediente_id=expediente.pk,
            user=user,
            reemplaza_a_id=reemplaza_a.id,
            designado_nro_socio=int(designado.legajo),
            acta_asamblea=ACTA,
        )

    def test_designacion_completa_habilita_constituir(
        self, caso_ad_hoc, tribunal_nomina, make_legacy_socio
    ):
        d1 = make_legacy_socio(90041, 4, grupo=59)
        d2 = make_legacy_socio(90042, 4, grupo=59)
        user = tribunal_nomina["t5"].user
        designacion = self.designar(caso_ad_hoc, user, tribunal_nomina["t4"], d1)
        self.designar(caso_ad_hoc, user, tribunal_nomina["s4"], d2)

        assert designacion.anio_social == 4
        payload = describe(caso_ad_hoc)
        assert seat_socios(payload)[4] == d1.id
        assert payload["asientos"][0]["condicion"] == "AD_HOC"
        assert payload["asientos"][0]["firma"] == "90041 - Nombre Apellido90041 - G59 (Ad hoc)"
        assert len(payload["designaciones_ad_hoc"]) == 2
        assert payload["puede_constituirse"] is True

    def test_designado_de_otro_anio(self, caso_ad_hoc, tribunal_nomina, make_legacy_socio):
        otro = make_legacy_socio(90051, 5)
        with pytest.raises(TribunalCompositionValidationError, match="mismo año social"):
            self.designar(caso_ad_hoc, tribunal_nomina["t5"].user, tribunal_nomina["t4"], otro)

    def test_designado_con_cargo_incompatible(
        self, caso_ad_hoc, tribunal_nomina, make_legacy_socio
    ):
        tesorero = make_legacy_socio(90043, 4, cargo=5)
        with pytest.raises(TribunalCompositionValidationError, match="Tesorero"):
            self.designar(caso_ad_hoc, tribunal_nomina["t5"].user, tribunal_nomina["t4"], tesorero)

    def test_designado_ausente_del_padron(self, caso_ad_hoc, tribunal_nomina, make_socio):
        socio = make_socio(legajo="90044", social_year=4)
        with pytest.raises(TribunalCompositionValidationError, match="padrón"):
            self.designar(caso_ad_hoc, tribunal_nomina["t5"].user, tribunal_nomina["t4"], socio)

    def test_un_apartado_no_designa_en_su_causa(
        self, caso_ad_hoc, tribunal_nomina, make_legacy_socio
    ):
        d1 = make_legacy_socio(90041, 4)
        with pytest.raises(TribunalCompositionForbidden):
            self.designar(caso_ad_hoc, tribunal_nomina["t4"].user, tribunal_nomina["s4"], d1)

    def test_fuera_del_caso_ad_hoc(self, causal_expediente, tribunal_nomina, make_legacy_socio):
        causal_expediente.socios.add(tribunal_nomina["t4"])
        d1 = make_legacy_socio(90041, 4)
        with pytest.raises(TribunalCompositionValidationError, match="Art. 95"):
            self.designar(causal_expediente, tribunal_nomina["t5"].user, tribunal_nomina["t4"], d1)
        assert not DesignacionAdHoc.objects.exists()


class TestConstitucion:
    def test_constitucion_congela_composicion_y_causas(self, causal_expediente, tribunal_nomina):
        causal_expediente.socios.add(tribunal_nomina["t5"])
        TribunalCompositionService.declare_conflict(
            expediente_id=causal_expediente.pk,
            user=tribunal_nomina["t6"].user,
            fundamento=FUNDAMENTO,
        )
        composicion = TribunalCompositionService.constitute(
            expediente_id=causal_expediente.pk, user=tribunal_nomina["t4"].user
        )

        assert composicion.es_ad_hoc is False
        assert composicion.constituida_por_legajo == "81004"
        integrantes = list(composicion.integrantes.all())
        assert [(i.anio_social, i.socio_id, i.condicion) for i in integrantes] == [
            (4, tribunal_nomina["t4"].id, "TITULAR"),
            (5, tribunal_nomina["s5"].id, "SUPLENTE"),
            (6, tribunal_nomina["s6"].id, "SUPLENTE"),
        ]
        assert integrantes[1].reemplaza_a == "Nombre Apellido81005 (N° 81005)"
        causas = {a["socio_id"]: a["causa"] for a in composicion.apartamientos}
        assert causas == {
            tribunal_nomina["t5"].id: "INVOLUCRADO",
            tribunal_nomina["t6"].id: "CONFLICTO_INTERES",
        }

        payload = describe(causal_expediente)
        assert payload["constituida"] is True
        assert seat_socios(payload)[6] == tribunal_nomina["s6"].id
        assert payload["puede_constituirse"] is False

    def test_composicion_constituida_no_cambia_con_la_nomina(
        self, causal_expediente, tribunal_nomina
    ):
        TribunalCompositionService.constitute(
            expediente_id=causal_expediente.pk, user=tribunal_nomina["t4"].user
        )
        causal_expediente.socios.add(tribunal_nomina["t5"])
        assert seat_socios(describe(causal_expediente))[5] == tribunal_nomina["t5"].id

    def test_constituida_no_admite_cambios(self, causal_expediente, tribunal_nomina):
        TribunalCompositionService.constitute(
            expediente_id=causal_expediente.pk, user=tribunal_nomina["t4"].user
        )
        with pytest.raises(TribunalCompositionStateError, match="inmutable"):
            TribunalCompositionService.constitute(
                expediente_id=causal_expediente.pk, user=tribunal_nomina["t4"].user
            )
        with pytest.raises(TribunalCompositionStateError, match="inmutable"):
            TribunalCompositionService.declare_conflict(
                expediente_id=causal_expediente.pk,
                user=tribunal_nomina["t6"].user,
                fundamento=FUNDAMENTO,
            )
        assert not ApartamientoTribunal.objects.exists()

    def test_con_observaciones_no_se_constituye(self, causal_expediente, tribunal_nomina):
        causal_expediente.socios.add(tribunal_nomina["t4"], tribunal_nomina["s4"])
        with pytest.raises(TribunalCompositionStateError, match="reemplazo ad hoc"):
            TribunalCompositionService.constitute(
                expediente_id=causal_expediente.pk, user=tribunal_nomina["t5"].user
            )
        assert not ComposicionTribunal.objects.exists()

    def test_un_apartado_no_constituye_el_cuerpo(self, causal_expediente, tribunal_nomina):
        causal_expediente.socios.add(tribunal_nomina["t4"])
        with pytest.raises(TribunalCompositionForbidden):
            TribunalCompositionService.constitute(
                expediente_id=causal_expediente.pk, user=tribunal_nomina["t4"].user
            )


class TestGuardaDeResolucion:
    def avanzar(self, expediente):
        return ExpedienteWorkflowService.transition(
            expediente_id=expediente.pk,
            estado_nuevo=EstadoExpedienteEnum.PENDIENTE_CORREOS,
            actor="tribunal",
            motivo="Resolución adoptada",
        )

    def test_sin_cuerpo_constituido_no_se_resuelve(self, causal_expediente):
        causal_expediente.estado = EstadoExpedienteEnum.ESPERA_RESOLUCION
        causal_expediente.save(update_fields=["estado"])
        with pytest.raises(ValidationError, match="Constituí el cuerpo"):
            self.avanzar(causal_expediente)

    def test_con_cuerpo_constituido_se_resuelve(self, causal_expediente, tribunal_nomina):
        TribunalCompositionService.constitute(
            expediente_id=causal_expediente.pk, user=tribunal_nomina["t4"].user
        )
        causal_expediente.estado = EstadoExpedienteEnum.ESPERA_RESOLUCION
        causal_expediente.save(update_fields=["estado"])
        assert self.avanzar(causal_expediente).estado == EstadoExpedienteEnum.PENDIENTE_CORREOS
