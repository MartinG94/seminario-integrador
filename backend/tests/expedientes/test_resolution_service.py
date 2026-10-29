from datetime import datetime, timezone
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError

from expedientes.domain.closed_decision import ClosedDecision
from expedientes.models import EstadoResolucionEnum, Resolucion
from expedientes.services.resolution_service import DictamenNoCerradoError, emitir_resolucion


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
