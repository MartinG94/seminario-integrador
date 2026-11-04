from datetime import datetime, timezone
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError

from expedientes.domain.closed_decision import ClosedDecision
from expedientes.models import (
    DecisionCausalDescargo,
    EstadoExpedienteEnum,
    EstadoResolucionEnum,
    Resolucion,
)
from expedientes.services.resolution_service import (
    DictamenNoCerradoError,
    ExpedienteConsolidatedDecisionProvider,
    emitir_resolucion,
    obtener_firmantes_td_por_anio_social,
)
from socios.models import Role


class FakeClosedDecisionProvider:
    def __init__(self, decision=None):
        self.decision = decision

    def get_closed_decision(self, expediente_id):
        return (
            self.decision
            if self.decision and self.decision.expediente_id == expediente_id
            else None
        )


def decision_for(expediente, estado="CLOSED"):
    return ClosedDecision(
        id="dictamen-1",
        expediente_id=expediente.pk,
        estado=estado,
        resultado="SANCTION",
        puntos_finales=Decimal("-3.25"),
        medidas=["apercibimiento"],
        considerandos_base="Fundamento cerrado",
        version=2,
        closed_at=datetime.now(timezone.utc),
    )


@pytest.mark.django_db
def test_crear_y_emitir_resolucion_toma_datos_del_dictamen(causal_expediente, causal_vocal):
    resolucion = Resolucion.objects.create(
        expediente=causal_expediente,
        plantilla_version="resolucion-2026.1",
        numero_expediente_snapshot="incorrecto",
        vistos="Vistos el expediente.",
        considerandos="Considerando la prueba.",
        articulos_resolutivos="Artículo 1: aplicar la medida.",
        puntos_finales=Decimal("99.99"),
        created_by=causal_vocal.user,
    )
    emitida = emitir_resolucion(
        resolucion,
        causal_vocal.user,
        FakeClosedDecisionProvider(decision_for(causal_expediente)),
    )

    assert emitida.estado == EstadoResolucionEnum.ISSUED
    assert emitida.numero_expediente_snapshot == causal_expediente.numero
    assert emitida.puntos_finales == Decimal("-3.25")
    assert emitida.medidas == ["apercibimiento"]
    assert emitida.contenido_hash
    assert not hasattr(emitida, "adjuntos")


@pytest.mark.django_db
@pytest.mark.parametrize("field", ["vistos", "considerandos", "articulos_resolutivos"])
def test_emitir_requiere_campos_obligatorios(causal_expediente, causal_vocal, field):
    values = {
        "vistos": "Vistos.",
        "considerandos": "Considerandos.",
        "articulos_resolutivos": "Artículo 1.",
    }
    values[field] = ""
    resolucion = Resolucion.objects.create(
        expediente=causal_expediente,
        plantilla_version="resolucion-2026.1",
        numero_expediente_snapshot=causal_expediente.numero,
        created_by=causal_vocal.user,
        **values,
    )
    with pytest.raises(ValidationError) as exc:
        emitir_resolucion(
            resolucion,
            causal_vocal.user,
            FakeClosedDecisionProvider(decision_for(causal_expediente)),
        )
    assert field in exc.value.message_dict


@pytest.mark.django_db
def test_no_se_emite_sin_dictamen_cerrado(causal_expediente, causal_vocal):
    resolucion = Resolucion.objects.create(
        expediente=causal_expediente,
        plantilla_version="resolucion-2026.1",
        numero_expediente_snapshot=causal_expediente.numero,
        vistos="Vistos.",
        considerandos="Considerandos.",
        articulos_resolutivos="Artículo 1.",
        created_by=causal_vocal.user,
    )
    with pytest.raises(DictamenNoCerradoError):
        emitir_resolucion(resolucion, causal_vocal.user, FakeClosedDecisionProvider())


@pytest.mark.django_db
def test_resolucion_emitida_es_inmutable(causal_expediente, causal_vocal):
    resolucion = Resolucion.objects.create(
        expediente=causal_expediente,
        plantilla_version="resolucion-2026.1",
        numero_expediente_snapshot=causal_expediente.numero,
        vistos="Vistos.",
        considerandos="Considerandos.",
        articulos_resolutivos="Artículo 1.",
        created_by=causal_vocal.user,
    )
    emitir_resolucion(
        resolucion,
        causal_vocal.user,
        FakeClosedDecisionProvider(decision_for(causal_expediente)),
    )
    resolucion.vistos = "modificado"
    with pytest.raises(ValidationError):
        resolucion.save()
    with pytest.raises(ValidationError):
        resolucion.delete()


@pytest.mark.django_db
def test_consolidated_provider_expediente_inexistente_o_no_cerrado(causal_expediente):
    provider = ExpedienteConsolidatedDecisionProvider()
    assert provider.get_closed_decision(999999) is None

    causal_expediente.estado = EstadoExpedienteEnum.CREADO
    causal_expediente.save()
    assert provider.get_closed_decision(causal_expediente.id) is None

    causal_expediente.estado = EstadoExpedienteEnum.JUSTIFICANDO
    causal_expediente.save()
    assert provider.get_closed_decision(causal_expediente.id) is None


@pytest.mark.django_db
def test_consolidated_provider_expediente_revision_sin_descargos(causal_expediente):
    causal_expediente.estado = EstadoExpedienteEnum.REVISION_RESOLUCION
    causal_expediente.puntos = Decimal("-2.50")
    causal_expediente.save()

    provider = ExpedienteConsolidatedDecisionProvider()
    decision = provider.get_closed_decision(causal_expediente.id)

    assert decision is not None
    assert decision.estado == "CLOSED"
    assert decision.puntos_finales == Decimal("-2.50")
    assert decision.resultado == "SANCTION"
    assert decision.medidas == []


@pytest.mark.django_db
def test_consolidated_provider_con_descargo_y_decision(
    causal_expediente, causal_descargo, causal_vocal
):
    causal_expediente.estado = EstadoExpedienteEnum.ESPERA_RESOLUCION
    causal_expediente.puntos = Decimal("-2.00")
    causal_expediente.save()

    DecisionCausalDescargo.objects.create(
        expediente=causal_expediente,
        descargo=causal_descargo,
        version=1,
        decision="ACCEPTED",
        regla_sugerida="ACCEPTED",
        descargo_snapshot={"puntaje_final": 0.0},
        autor=causal_vocal.user,
        autor_legajo=causal_vocal.legajo,
        autor_rol=causal_vocal.role,
    )

    provider = ExpedienteConsolidatedDecisionProvider()
    decision = provider.get_closed_decision(causal_expediente.id)

    assert decision is not None
    assert decision.puntos_finales == Decimal("0.00")
    assert decision.resultado == "NEUTRAL"


@pytest.mark.django_db
def test_consolidated_provider_con_llamado_de_atencion(
    causal_expediente, causal_descargo, causal_vocal
):
    causal_expediente.estado = EstadoExpedienteEnum.REVISION_RESOLUCION
    causal_expediente.save()

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

    provider = ExpedienteConsolidatedDecisionProvider()
    decision = provider.get_closed_decision(causal_expediente.id)

    assert decision is not None
    assert "Llamado de atención" in decision.medidas
    assert decision.puntos_finales == Decimal("-0.25")
    assert decision.resultado == "SANCTION"


@pytest.mark.django_db
def test_firmantes_td_fallbacks_institucionales():
    firmantes = obtener_firmantes_td_por_anio_social()
    assert len(firmantes) == 3
    assert firmantes[0] == "11735 - Candela Moreno Migliore - G59"
    assert firmantes[1] == "11737 - Catalina Cerda Gallego - G58"
    assert firmantes[2] == "11239 - Giuliano Toselli - G57"


@pytest.mark.django_db
def test_firmantes_td_con_multiples_socios_por_anio(make_socio):
    # Crear dos socios de 4.° año, uno de 5.° y ninguno de 6.°
    s4_1 = make_socio(legajo="40001", role=Role.TD, social_year=4)
    s4_1.first_name = "Ana"
    s4_1.last_name = "Perez"
    s4_1.save()

    s4_2 = make_socio(legajo="40002", role=Role.TD, social_year=4)
    s4_2.first_name = "Belen"
    s4_2.last_name = "Gomez"
    s4_2.save()

    s5 = make_socio(legajo="50001", role=Role.TD, social_year=5)
    s5.first_name = "Carlos"
    s5.last_name = "Ruiz"
    s5.save()

    firmantes = obtener_firmantes_td_por_anio_social()
    assert len(firmantes) == 3
    # El año 4 debe seleccionar exactamente un socio TD de 4.° año determinísticamente (por id)
    assert firmantes[0].startswith(f"{s4_1.legajo} - Ana Perez -")
    # El año 5 selecciona el socio TD de 5.° año
    assert firmantes[1].startswith(f"{s5.legajo} - Carlos Ruiz -")
    # El año 6 debe usar el fallback porque no hay socio TD de 6.° año
    assert firmantes[2] == "11239 - Giuliano Toselli - G57"
