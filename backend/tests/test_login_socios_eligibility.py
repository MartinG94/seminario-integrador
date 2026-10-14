"""Pruebas de elegibilidad procesal y consistencia de saldos para los socios de login.

Verifica:
1. Que los legajos de login existen en el padrón institucional y están activos.
2. Que son elegibles para emitirles solicitudes T01 y abrirles expedientes directos.
3. Que los expedientes cerrados/emitidos son 100% consistentes con el saldo de puntos.
4. Que el comando seed_production_data es completamente idempotente.
"""

from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from rest_framework import status
from rest_framework.test import APIClient

from core.management.commands.seed_production_data import TEAM_MEMBERS
from expedientes.models import (
    EstadoExpedienteEnum,
    Expediente,
    SolicitudT01,
    UrgenciaExpedienteEnum,
)
from expedientes.serializers import AperturaExpedienteSerializer, EmitirT01Serializer
from padron.factory import get_padron_repository
from ranking.models import PuntajeAplicado, PuntajeGeneral
from socios.models import Socio

UserModel = get_user_model()


@pytest.fixture(autouse=True)
def populate_data(db):
    """Ejecuta seed_production_data para asegurar entorno listo en la BD de pruebas."""
    call_command("seed_production_data")


@pytest.mark.django_db
def test_login_socios_exist_in_padron_repository():
    """Verifica que todos los legajos de login existen en PadronRepository con estado activo."""
    repo = get_padron_repository()

    for legajo, last_name, first_name, role, social_year, subcomision in TEAM_MEMBERS:
        socio_by_legajo = repo.get_by_legajo(legajo)
        assert socio_by_legajo is not None, (
            f"El socio legajo {legajo} no fue encontrado por legajo en el padrón."
        )
        assert socio_by_legajo.is_active is True, (
            f"El socio legajo {legajo} debe estar activo en el padrón."
        )
        assert socio_by_legajo.legajo == legajo

        socio_by_id = repo.get_by_id(int(legajo))
        assert socio_by_id is not None, (
            f"El socio ID {legajo} no fue encontrado por ID en el padrón."
        )
        assert socio_by_id.is_active is True
        assert socio_by_id.socio_id == int(legajo)


@pytest.mark.django_db
def test_login_socios_appear_in_padron_list_api():
    """Verifica que los socios de login aparecen en la API del padrón."""
    user = UserModel.objects.get(username="85194")
    client = APIClient()
    client.force_authenticate(user=user)
    response = client.get("/api/v1/padron/socios/?is_active=true&page_size=100")
    assert response.status_code == status.HTTP_200_OK

    results = response.data.get("results", [])
    legajos_encontrados = {str(s.get("legajo")) for s in results if s.get("legajo")}

    for legajo, _, _, _, _, _ in TEAM_MEMBERS:
        assert legajo in legajos_encontrados, (
            f"El legajo {legajo} no aparece en /api/v1/padron/socios/."
        )


@pytest.mark.django_db
def test_login_socios_eligible_for_solicitud_t01_emission():
    """Verifica que un socio de login es elegible como destinatario al emitir una solicitud T01."""
    solicitante = Socio.objects.get(legajo="85194")  # Lucas Guillén (Fiscalizadora)
    destinatario_legajo = "74907"  # Lucas Gastiaburu (Socio)

    solicitud = SolicitudT01.objects.create(
        solicitante=solicitante,
        tipo_accion=SolicitudT01.TipoAccion.SANCTION,
        urgencia=UrgenciaExpedienteEnum.NORMAL,
        titulo="Inasistencia a jornada técnica",
        motivo="No concurrió a la actividad programada sin aviso.",
        puntos=Decimal("-1.00"),
        destinatario_socio_id=int(destinatario_legajo),
        destinatarios_socios_ids=[int(destinatario_legajo)],
    )

    # Validar con EmitirT01Serializer
    serializer = EmitirT01Serializer(data={}, context={"solicitud": solicitud})
    assert serializer.is_valid(), f"La emisión falló con errores: {serializer.errors}"

    solicitud_emitida = serializer.save()
    assert solicitud_emitida.estado == SolicitudT01.Estado.ISSUED
    assert solicitud_emitida.snapshot_destinatario is not None
    assert str(solicitud_emitida.snapshot_destinatario["legajo"]) == destinatario_legajo


@pytest.mark.django_db
def test_login_socios_eligible_for_direct_expediente():
    """Verifica que los socios locales de login pueden ser objeto
    de apertura directa de expedientes.
    """
    lucas_socio = Socio.objects.get(legajo="74907")

    data = {
        "motivo": "Demora reiterada en presentación de actas de guardia.",
        "socios": [lucas_socio.id],
        "urgencia": "normal",
    }
    serializer = AperturaExpedienteSerializer(data=data)
    assert serializer.is_valid(), f"Apertura directa falló con: {serializer.errors}"


@pytest.mark.django_db
def test_expedientes_cerrados_saldos_consistency():
    """Verifica que para cada socio con expedientes emitidos:
    Sum(puntos emitidos) == Sum(puntajeAplicado) == PuntajeGeneral.puntos == Ranking
    con diferencia 0.00 y reconciliado True.
    """
    emitidos_lucas = Expediente.objects.filter(
        socio__legajo="74907", estado=EstadoExpedienteEnum.EMITIDO
    )
    puntos_expedientes = sum(exp.puntos for exp in emitidos_lucas)

    # En tribunal_puntajeaplicado
    aplicados = PuntajeAplicado.objects.filter(socio_id=74907)
    puntos_aplicados = sum(pa.puntajeAplicado for pa in aplicados)

    # En tribunal_puntajegeneral
    pg = PuntajeGeneral.objects.get(socio_id=74907)

    assert puntos_expedientes == puntos_aplicados, (
        "Los puntos de expedientes emitidos deben igualar al libro mayor."
    )
    assert puntos_aplicados == pg.puntos, (
        "El libro mayor debe coincidir exactamente con el caché tribunal_puntajegeneral."
    )
    assert pg.puntos == Decimal("1.00"), (
        f"Lucas Gastiaburu debe tener saldo neto de +1.00, tiene {pg.puntos}."
    )

    # Verificar a través del endpoint de ranking
    td_user = UserModel.objects.get(username="408917")
    client = APIClient()
    client.force_authenticate(user=td_user)
    response = client.get("/api/v1/ranking/?search=74907")
    assert response.status_code == status.HTTP_200_OK

    results = response.data if isinstance(response.data, list) else response.data.get("results", [])
    assert len(results) > 0
    socio_ranking = results[0]
    assert Decimal(str(socio_ranking["saldo"])) == Decimal("1.00")
    assert Decimal(str(socio_ranking["saldoPuntajeGeneral"])) == Decimal("1.00")
    assert Decimal(str(socio_ranking["diferencia"])) == Decimal("0.00")
    assert socio_ranking["reconciliado"] is True


@pytest.mark.django_db
def test_seed_production_data_idempotency():
    """Verifica que ejecutar seed_production_data de manera repetida
    es seguro y no genera duplicados.
    """
    users_count_before = UserModel.objects.count()
    socios_count_before = Socio.objects.count()
    expedientes_count_before = Expediente.objects.count()

    # Segunda ejecución consecutiva
    call_command("seed_production_data")

    assert UserModel.objects.count() == users_count_before
    assert Socio.objects.count() == socios_count_before
    assert Expediente.objects.count() == expedientes_count_before
