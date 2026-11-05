"""Validación E2E del flujo real de sustitución ad-hoc por Asamblea y asignación de Cómputos."""

import pytest
from django.db import connection
from django.utils import timezone
from rest_framework import status

from expedientes.models import (
    ComposicionTribunal,
    ConceptoExpedienteEnum,
    EstadoExpedienteEnum,
)
from expedientes.services.tribunal_composition_service import TribunalCompositionService
from expedientes.services.tribunal_roster import CARGO_TITULAR_TD
from socios.models import Role
from tests.expedientes.conftest import CARGO_SOCIO_ORDINARIO

pytestmark = pytest.mark.django_db


def test_flujo_e2e_asamblea_computos_resolucion_desasignacion(
    causal_expediente, tribunal_nomina, make_legacy_socio, api_client
):
    """Validación E2E del flujo real:

    1. Causa con Titular y Suplente de 5.° año involucrados (Caso A).
    2. Composición inicial: asiento 5 vacío, requiere ad-hoc = True, aviso a CD encolado.
    3. Asamblea designa a un socio de 5.° año ('adhoc_5').
    4. Cómputos le otorga el rol/permisos según la estructura de la tabla legacy.
    5. 'adhoc_5' ingresa al sistema, participa en la confección y firma de la resolución.
    6. Se emite el expediente: se estampa inmutablemente la composición con 'adhoc_5'.
    7. Cómputos le retira el rol/permisos a 'adhoc_5'.
    8. Verificación: el expediente emitido conserva la firma histórica inmutable de 'adhoc_5',
       mientras que 'adhoc_5' ya no tiene permisos para causas futuras.
    """
    base = timezone.localdate().year - 1962

    # PASO 1: Involucrar a titular y suplente de 5.° año en el expediente
    t5 = tribunal_nomina["t5"]
    s5 = tribunal_nomina["s5"]
    causal_expediente.socios.add(t5, s5)

    # PASO 2: Verificar estado antes de la intervención de Asamblea
    desc_inicial = TribunalCompositionService.describe(causal_expediente.pk)
    asiento_5_inicial = next(a for a in desc_inicial["asientos"] if a["anio_social"] == 5)
    assert desc_inicial["requiere_ad_hoc"] is True
    assert asiento_5_inicial["socio_id"] is None
    assert len(desc_inicial["apartados"]) == 2

    # PASO 3: Se designa un socio de 5.° año por asamblea
    adhoc_5 = make_legacy_socio(
        nro_socio=83005,
        social_year=5,
        cargo=CARGO_SOCIO_ORDINARIO,  # idTipoSocio: 12
        role=Role.SOCIO,
        grupo=base - 5,  # G59
    )

    # PASO 4: Cómputos le otorga el rol/permisos en la tabla legacy y en la app
    with connection.cursor() as cursor:
        cursor.execute(
            "UPDATE socio_lista SET idTipoSocio = %s WHERE nroSocio = %s",
            [CARGO_TITULAR_TD, int(adhoc_5.legajo)],
        )
    adhoc_5.role = Role.TD
    adhoc_5.save(update_fields=["role"])

    desc_con_adhoc = TribunalCompositionService.describe(causal_expediente.pk)
    asiento_5_con_adhoc = next(a for a in desc_con_adhoc["asientos"] if a["anio_social"] == 5)
    assert asiento_5_con_adhoc["socio_id"] == adhoc_5.id
    assert desc_con_adhoc["requiere_ad_hoc"] is False

    # PASO 5: adhoc_5 participa en confección y transición
    api_client.force_authenticate(adhoc_5.user)
    causal_expediente.estado = EstadoExpedienteEnum.ESPERA_RESOLUCION
    causal_expediente.save(update_fields=["estado"])

    resp_trans = api_client.post(
        f"/api/v1/expedientes/{causal_expediente.pk}/transicionar/",
        {"to_status": EstadoExpedienteEnum.PENDIENTE_CORREOS},
        format="json",
    )
    assert resp_trans.status_code == status.HTTP_200_OK

    # PASO 6: Emisión del expediente
    causal_expediente.concepto = ConceptoExpedienteEnum.CD
    causal_expediente.save(update_fields=["concepto"])
    resp_emitir = api_client.post(
        f"/api/v1/expedientes/{causal_expediente.pk}/transicionar/",
        {"to_status": EstadoExpedienteEnum.EMITIDO},
        format="json",
    )
    assert resp_emitir.status_code == status.HTTP_200_OK

    causal_expediente.refresh_from_db()
    assert causal_expediente.estado == EstadoExpedienteEnum.EMITIDO
    comp_estampada = ComposicionTribunal.objects.get(expediente=causal_expediente)
    firmas = [i.firma for i in comp_estampada.integrantes.all()]
    assert any("83005" in f for f in firmas)

    # PASO 7: Cómputos retira el rol/permisos a adhoc_5
    with connection.cursor() as cursor:
        cursor.execute(
            "UPDATE socio_lista SET idTipoSocio = %s WHERE nroSocio = %s",
            [CARGO_SOCIO_ORDINARIO, int(adhoc_5.legajo)],
        )
    adhoc_5.role = Role.SOCIO
    adhoc_5.save(update_fields=["role"])

    # PASO 8: Verificación post-desasignación
    desc_final = TribunalCompositionService.describe(causal_expediente.pk)
    asiento_5_final = next(a for a in desc_final["asientos"] if a["anio_social"] == 5)
    assert asiento_5_final["socio_id"] == adhoc_5.id
    assert "83005" in asiento_5_final["firma"]

    # adhoc_5 ya no tiene permisos para consultar/operar como TD
    api_client.force_authenticate(adhoc_5.user)
    resp_td = api_client.get(f"/api/v1/expedientes/{causal_expediente.pk}/composicion/")
    assert resp_td.status_code == status.HTTP_403_FORBIDDEN
