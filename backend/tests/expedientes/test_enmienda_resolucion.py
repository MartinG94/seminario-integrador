"""Pruebas unitarias e integración para enmienda trazable de resoluciones (SCRUM-103)."""

from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError

from expedientes.models import (
    EstadoExpedienteEnum,
    EstadoResolucionEnum,
    Resolucion,
)
from expedientes.services.enmienda_service import EnmiendaService
from expedientes.services.resolution_service import registrar_firma_resolucion
from ranking.models import PuntajeAplicado
from socios.models import Role


def enmendar_url(expediente_id: int) -> str:
    return f"/api/v1/expedientes/{expediente_id}/enmendar/"


def resolution_url(expediente_id: int) -> str:
    return f"/api/v1/expedientes/{expediente_id}/resolucion/"


def sign_url(expediente_id: int) -> str:
    return f"{resolution_url(expediente_id)}firmar/"


@pytest.mark.django_db
def test_solicitar_enmienda_crea_nueva_resolucion_version_2_y_registro_enmienda(
    causal_expediente, causal_vocal, make_socio
):
    causal_expediente.estado = EstadoExpedienteEnum.EMITIDO
    causal_expediente.puntos = Decimal("-3.00")
    causal_expediente.save()

    socio = make_socio(legajo="76060", role=Role.SOCIO)
    causal_expediente.socios.add(socio)

    res_v1 = Resolucion.objects.create(
        expediente=causal_expediente,
        version=1,
        plantilla_version="v1",
        estado=EstadoResolucionEnum.ISSUED,
        numero_expediente_snapshot=causal_expediente.numero,
        vistos="Vistos originales.",
        considerandos="Considerandos originales con error material.",
        articulos_resolutivos="Artículo 1: sancionar.",
        puntos_finales=Decimal("-3.00"),
        created_by=causal_vocal.user,
        issued_by=causal_vocal.user,
        contenido_hash="hash-version-1",
    )

    enmienda, res_v2 = EnmiendaService.solicitar_enmienda(
        expediente_id=causal_expediente.id,
        user=causal_vocal.user,
        motivo_enmienda="Error material en valoración de atenuantes presentados.",
        considerandos="Considerando rectificado con atenuante.",
        nuevos_puntajes=[{"socio_id": socio.id, "puntaje": -1.0}],
    )

    # 1. Verificar resolución previa intacta e inmutable
    res_v1.refresh_from_db()
    assert res_v1.version == 1
    assert res_v1.estado == EstadoResolucionEnum.ISSUED

    # 2. Verificar nueva resolución borrador versión 2
    assert res_v2.version == 2
    assert res_v2.estado == EstadoResolucionEnum.DRAFT
    assert res_v2.numero_expediente_snapshot == res_v1.numero_expediente_snapshot
    assert res_v2.considerandos == "Considerando rectificado con atenuante."
    assert res_v2.firmantes == []
    assert res_v2.puntos_finales == Decimal("-1.00")

    # 3. Registro de trazabilidad de enmienda
    assert enmienda.resolucion_anterior == res_v1
    assert enmienda.resolucion_nueva == res_v2
    assert enmienda.solicitado_por == causal_vocal.user
    assert "Error material" in enmienda.motivo_enmienda

    # 4. Retorno del expediente a PENDIENTE_CORREOS para nueva firma colegiada
    causal_expediente.refresh_from_db()
    assert causal_expediente.estado == EstadoExpedienteEnum.PENDIENTE_CORREOS
    cambio = causal_expediente.cambios_estado.first()
    assert cambio.estado_nuevo == EstadoExpedienteEnum.PENDIENTE_CORREOS
    assert "enmienda" in cambio.motivo.lower()


@pytest.mark.django_db
def test_solicitar_enmienda_rechaza_motivo_menor_a_10_caracteres(causal_expediente, causal_vocal):
    causal_expediente.estado = EstadoExpedienteEnum.EMITIDO
    causal_expediente.save()

    Resolucion.objects.create(
        expediente=causal_expediente,
        version=1,
        plantilla_version="v1",
        estado=EstadoResolucionEnum.ISSUED,
        numero_expediente_snapshot=causal_expediente.numero,
        vistos="Vistos.",
        considerandos="Considerandos.",
        articulos_resolutivos="Artículos.",
        created_by=causal_vocal.user,
    )

    with pytest.raises(ValidationError) as exc:
        EnmiendaService.solicitar_enmienda(
            expediente_id=causal_expediente.id,
            user=causal_vocal.user,
            motivo_enmienda="Corto",
        )
    assert "al menos 10 caracteres" in str(exc.value)


@pytest.mark.django_db
def test_solicitar_enmienda_rechaza_expediente_no_emitido(causal_expediente, causal_vocal):
    causal_expediente.estado = EstadoExpedienteEnum.JUSTIFICANDO
    causal_expediente.save()

    with pytest.raises(ValidationError) as exc:
        EnmiendaService.solicitar_enmienda(
            expediente_id=causal_expediente.id,
            user=causal_vocal.user,
            motivo_enmienda="Intento de enmienda en estado prematuro.",
        )
    assert "emitida" in str(exc.value).lower()


@pytest.mark.django_db
def test_solicitar_enmienda_rechaza_si_ya_existe_borrador_pendiente(
    causal_expediente, causal_vocal
):
    causal_expediente.estado = EstadoExpedienteEnum.EMITIDO
    causal_expediente.save()

    Resolucion.objects.create(
        expediente=causal_expediente,
        version=1,
        plantilla_version="v1",
        estado=EstadoResolucionEnum.ISSUED,
        numero_expediente_snapshot=causal_expediente.numero,
        vistos="Vistos.",
        considerandos="Considerandos.",
        articulos_resolutivos="Artículos.",
        created_by=causal_vocal.user,
    )

    # Primera enmienda
    EnmiendaService.solicitar_enmienda(
        expediente_id=causal_expediente.id,
        user=causal_vocal.user,
        motivo_enmienda="Primera solicitud válida de enmienda.",
    )

    # Intento de solicitar otra mientras la versión 2 sigue en DRAFT
    with pytest.raises(ValidationError) as exc:
        EnmiendaService.solicitar_enmienda(
            expediente_id=causal_expediente.id,
            user=causal_vocal.user,
            motivo_enmienda="Segunda solicitud redundante sin firmar la previa.",
        )
    assert "Ya existe una enmienda en borrador" in str(exc.value)


@pytest.mark.django_db
def test_emision_resolucion_enmendada_genera_contraasientos_opcion_b_en_libro_mayor(
    causal_expediente, causal_vocal, make_socio
):
    from django.db import connection

    causal_expediente.estado = EstadoExpedienteEnum.EMITIDO
    causal_expediente.puntos = Decimal("-3.00")
    causal_expediente.save()

    socio = make_socio(legajo="76070", role=Role.SOCIO)
    causal_expediente.socios.add(socio)

    # Registro contable previo en el libro mayor (-3.00 pts)
    with connection.cursor() as cursor:
        cursor.execute(
            "INSERT INTO tribunal_puntajeaplicado (puntajeAplicado, socio_id, expediente_id) "
            "VALUES (%s, %s, %s)",
            [-3.0, socio.id, causal_expediente.id],
        )

    Resolucion.objects.create(
        expediente=causal_expediente,
        version=1,
        plantilla_version="v1",
        estado=EstadoResolucionEnum.ISSUED,
        numero_expediente_snapshot=causal_expediente.numero,
        vistos="Vistos.",
        considerandos="Considerandos sanción inicial.",
        articulos_resolutivos="Artículo 1: sancionar.",
        puntos_finales=Decimal("-3.00"),
        created_by=causal_vocal.user,
        issued_by=causal_vocal.user,
    )

    # Solicitar enmienda con rectificación a -1.00 pts
    _, res_v2 = EnmiendaService.solicitar_enmienda(
        expediente_id=causal_expediente.id,
        user=causal_vocal.user,
        motivo_enmienda="Atenuación fundada de sanción por hecho nuevo.",
        nuevos_puntajes=[{"socio_id": socio.id, "puntaje": -1.0}],
    )

    s4 = make_socio(legajo="40001", role=Role.TD, social_year=4)
    s5 = make_socio(legajo="50001", role=Role.TD, social_year=5)
    s6 = make_socio(legajo="60001", role=Role.TD, social_year=6)

    # Firmar la enmienda con los 3 años sociales
    registrar_firma_resolucion(res_v2, s4.user)
    registrar_firma_resolucion(res_v2, s5.user)
    registrar_firma_resolucion(res_v2, s6.user)

    res_v2.refresh_from_db()
    assert res_v2.estado == EstadoResolucionEnum.ISSUED

    # Verificar libro mayor (tribunal_puntajeaplicado) bajo Opción B:
    asientos = list(
        PuntajeAplicado.objects.filter(expediente_id=causal_expediente.id, socio_id=socio.id)
    )
    # Debe haber exactamente 3 asientos:
    # 1. Asiento inicial: -3.00
    # 2. Reversión íntegra: +3.00
    # 3. Asiento definitivo rectificado: -1.00
    assert len(asientos) == 3
    valores = [Decimal(str(a.puntajeAplicado)) for a in asientos]
    assert Decimal("-3.00") in valores
    assert Decimal("3.00") in valores
    assert Decimal("-1.00") in valores
    # Suma neta debe ser exactamente el puntaje enmendado (-1.00)
    assert sum(valores) == Decimal("-1.00")


@pytest.mark.django_db
def test_enmendar_resolucion_api_endpoint_exitoso(
    causal_expediente, causal_vocal, make_socio, authenticate
):
    causal_expediente.estado = EstadoExpedienteEnum.EMITIDO
    causal_expediente.save()

    socio = make_socio(legajo="76080", role=Role.SOCIO)
    causal_expediente.socios.add(socio)

    Resolucion.objects.create(
        expediente=causal_expediente,
        version=1,
        plantilla_version="v1",
        estado=EstadoResolucionEnum.ISSUED,
        numero_expediente_snapshot=causal_expediente.numero,
        vistos="Vistos.",
        considerandos="Considerando inicial.",
        articulos_resolutivos="Artículo 1.",
        puntos_finales=Decimal("-2.00"),
        created_by=causal_vocal.user,
    )

    client = authenticate(causal_vocal)
    payload = {
        "motivo_enmienda": "Rectificación formal por subsanación documental.",
        "considerandos": "Considerando rectificado.",
        "nuevos_puntajes": [{"socio_id": socio.id, "puntaje": -0.5}],
    }
    response = client.post(enmendar_url(causal_expediente.id), payload, format="json")
    assert response.status_code == 201
    data = response.data
    assert data["motivo_enmienda"] == payload["motivo_enmienda"]
    assert data["resolucion_nueva_detalle"]["version"] == 2
    assert data["resolucion_nueva_detalle"]["estado"] == "DRAFT"

    causal_expediente.refresh_from_db()
    assert causal_expediente.estado == "pendiente_correos"


@pytest.mark.django_db
def test_enmendar_resolucion_api_rechaza_rol_no_autorizado(
    causal_expediente, make_socio, authenticate
):
    causal_expediente.estado = EstadoExpedienteEnum.EMITIDO
    causal_expediente.save()

    socio_comun = make_socio(legajo="76090", role=Role.SOCIO)
    client = authenticate(socio_comun)

    payload = {"motivo_enmienda": "Intento no autorizado de enmienda."}
    response = client.post(enmendar_url(causal_expediente.id), payload, format="json")
    assert response.status_code == 403
