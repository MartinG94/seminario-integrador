"""Pruebas unitarias e integración para enmienda trazable de resoluciones (SCRUM-103)."""

from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError

from expedientes.models import (
    DecisionCausalDescargo,
    DescargoExpediente,
    EstadoExpedienteEnum,
    EstadoResolucionEnum,
    Resolucion,
    TipoDescargoEnum,
)
from expedientes.serializers import ExpedienteListSerializer
from expedientes.services.enmienda_service import EnmiendaService
from expedientes.services.resolution_service import (
    ExpedienteConsolidatedDecisionProvider,
    emitir_resolucion,
    registrar_firma_resolucion,
)
from ranking.models import PuntajeAplicado
from socios.models import Role


def enmendar_url(expediente_id: int) -> str:
    return f"/api/v1/expedientes/{expediente_id}/enmendar/"


def resolution_url(expediente_id: int) -> str:
    return f"/api/v1/expedientes/{expediente_id}/resolucion/"


def sign_url(expediente_id: int) -> str:
    return f"{resolution_url(expediente_id)}firmar/"


@pytest.fixture(autouse=True)
def numero_socio_titular(request):
    """El libro mayor usa el N° de socio institucional (SCRUM-114) como clave."""
    if "causal_imputado" not in request.fixturenames:
        return
    titular = request.getfixturevalue("causal_imputado")
    titular.numero_socio = 76001
    titular.save(update_fields=["numero_socio"])


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

    socio = make_socio(legajo="76070", role=Role.SOCIO, numero_socio=76070)
    causal_expediente.socios.add(socio)

    # Registro contable previo en el libro mayor (-3.00 pts)
    with connection.cursor() as cursor:
        cursor.execute(
            "INSERT INTO tribunal_puntajeaplicado (puntajeAplicado, socio_id, expediente_id) "
            "VALUES (%s, %s, %s)",
            [-3.0, socio.numero_socio, causal_expediente.id],
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
        PuntajeAplicado.objects.filter(
            expediente_id=causal_expediente.id, socio_id=socio.numero_socio
        )
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


@pytest.mark.django_db
def test_emitir_enmienda_preserva_puntos_finales_sobre_decision_causal_previa(
    causal_expediente, causal_vocal, make_socio
):
    """emitir_resolucion sobre enmienda preserva puntos_finales sobre DecisionCausalDescargo."""
    causal_expediente.estado = EstadoExpedienteEnum.EMITIDO
    causal_expediente.puntos = Decimal("-3.00")
    causal_expediente.save()

    socio = make_socio(legajo="76101", role=Role.SOCIO, numero_socio=76101)
    causal_expediente.socios.add(socio)

    descargo = DescargoExpediente.objects.create(
        expediente=causal_expediente,
        socio=socio,
        tipo=TipoDescargoEnum.T02_CERTIFICADO,
        es_vigente=True,
        texto="Descargo inicial.",
        puntaje_ratificado="-3.0",
    )
    DecisionCausalDescargo.objects.create(
        expediente=causal_expediente,
        descargo=descargo,
        version=1,
        decision="REJECTED",
        regla_sugerida="REJECTED",
        fundamento="Se mantiene puntaje original de -3.00.",
        autor=causal_vocal.user,
        descargo_snapshot={"puntaje_final": "-3.00"},
    )

    Resolucion.objects.create(
        expediente=causal_expediente,
        version=1,
        plantilla_version="v1",
        estado=EstadoResolucionEnum.ISSUED,
        numero_expediente_snapshot=causal_expediente.numero,
        vistos="Vistos.",
        considerandos="Considerandos v1.",
        articulos_resolutivos="Artículo 1.",
        puntos_finales=Decimal("-3.00"),
        created_by=causal_vocal.user,
        issued_by=causal_vocal.user,
    )

    _, res_v2 = EnmiendaService.solicitar_enmienda(
        expediente_id=causal_expediente.id,
        user=causal_vocal.user,
        motivo_enmienda="Corrección de puntaje final a -1.00 por atenuante.",
        nuevos_puntajes=[{"socio_id": socio.id, "puntaje": -1.0}],
    )

    emitida = emitir_resolucion(res_v2, causal_vocal.user, ExpedienteConsolidatedDecisionProvider())
    emitida.refresh_from_db()
    assert emitida.estado == EstadoResolucionEnum.ISSUED
    assert emitida.puntos_finales == Decimal("-1.00")


@pytest.mark.django_db
def test_enmienda_contra_asientos_omite_socio_excluido(causal_expediente, causal_vocal, make_socio):
    """aplicar_contra_asientos_opcion_b omite aplicar nuevo puntaje a socio excluido."""
    from django.db import connection

    causal_expediente.estado = EstadoExpedienteEnum.EMITIDO
    causal_expediente.puntos = Decimal("-2.00")
    causal_expediente.save()

    socio_activo = make_socio(legajo="76102", role=Role.SOCIO, numero_socio=76102)
    socio_excluido = make_socio(legajo="76103", role=Role.SOCIO, numero_socio=76103)
    causal_expediente.socios.add(socio_activo, socio_excluido)

    DescargoExpediente.objects.create(
        expediente=causal_expediente,
        socio=socio_activo,
        tipo=TipoDescargoEnum.T02_CERTIFICADO,
        es_vigente=True,
        puntaje_ratificado="-2.00",
    )
    DescargoExpediente.objects.create(
        expediente=causal_expediente,
        socio=socio_excluido,
        tipo=TipoDescargoEnum.T02_CERTIFICADO,
        es_vigente=False,
        esta_excluido=True,
        motivo_exclusion="Excluido fundadamente antes de emitir.",
        puntaje_ratificado="0.00",
    )

    with connection.cursor() as cursor:
        cursor.execute(
            "INSERT INTO tribunal_puntajeaplicado (puntajeAplicado, socio_id, expediente_id) "
            "VALUES (%s, %s, %s)",
            [-2.0, socio_activo.numero_socio, causal_expediente.id],
        )

    Resolucion.objects.create(
        expediente=causal_expediente,
        version=1,
        plantilla_version="v1",
        estado=EstadoResolucionEnum.ISSUED,
        numero_expediente_snapshot=causal_expediente.numero,
        vistos="Vistos.",
        considerandos="Considerandos v1.",
        articulos_resolutivos="Artículo 1.",
        puntos_finales=Decimal("-2.00"),
        created_by=causal_vocal.user,
        issued_by=causal_vocal.user,
    )

    _, res_v2 = EnmiendaService.solicitar_enmienda(
        expediente_id=causal_expediente.id,
        user=causal_vocal.user,
        motivo_enmienda="Rectificación de puntaje solo para socio activo.",
        nuevos_puntajes=[{"socio_id": socio_activo.id, "puntaje": -1.0}],
    )

    emitir_resolucion(res_v2, causal_vocal.user, ExpedienteConsolidatedDecisionProvider())

    asientos_activo = [
        Decimal(str(a.puntajeAplicado))
        for a in PuntajeAplicado.objects.filter(
            expediente_id=causal_expediente.id, socio_id=socio_activo.numero_socio
        )
    ]
    asientos_excluido = list(
        PuntajeAplicado.objects.filter(
            expediente_id=causal_expediente.id, socio_id=socio_excluido.numero_socio
        )
    )
    assert sum(asientos_activo) == Decimal("-1.00")
    assert len(asientos_excluido) == 0


@pytest.mark.django_db
def test_expediente_list_serializer_expone_puntaje_ratificado_tras_enmienda(
    causal_expediente, causal_vocal, make_socio, rf
):
    """ExpedienteListSerializer.get_descargos prioriza d.puntaje_ratificado actualizado."""
    causal_expediente.estado = EstadoExpedienteEnum.EMITIDO
    causal_expediente.puntos = Decimal("-3.00")
    causal_expediente.save()

    socio = make_socio(legajo="76104", role=Role.SOCIO)
    causal_expediente.socios.add(socio)

    descargo = DescargoExpediente.objects.create(
        expediente=causal_expediente,
        socio=socio,
        tipo=TipoDescargoEnum.T02_CERTIFICADO,
        es_vigente=True,
        texto="Descargo.",
        puntaje_ratificado="-3.00",
    )
    DecisionCausalDescargo.objects.create(
        expediente=causal_expediente,
        descargo=descargo,
        version=1,
        decision="REJECTED",
        regla_sugerida="REJECTED",
        fundamento="Rechazo inicial.",
        autor=causal_vocal.user,
        descargo_snapshot={"puntaje_final": "-3.00"},
    )

    Resolucion.objects.create(
        expediente=causal_expediente,
        version=1,
        plantilla_version="v1",
        estado=EstadoResolucionEnum.ISSUED,
        numero_expediente_snapshot=causal_expediente.numero,
        vistos="Vistos.",
        considerandos="Considerandos.",
        articulos_resolutivos="Artículo 1.",
        puntos_finales=Decimal("-3.00"),
        created_by=causal_vocal.user,
        issued_by=causal_vocal.user,
    )

    EnmiendaService.solicitar_enmienda(
        expediente_id=causal_expediente.id,
        user=causal_vocal.user,
        motivo_enmienda="Ajuste de puntaje a -0.50 tras revisión.",
        nuevos_puntajes=[{"socio_id": socio.id, "puntaje": -0.5}],
    )

    request = rf.get("/")
    request.user = causal_vocal.user
    causal_expediente.refresh_from_db()
    data = ExpedienteListSerializer(causal_expediente, context={"request": request}).data
    assert len(data["descargos"]) == 1
    assert data["descargos"][0]["puntaje_ratificado"] == -0.5


@pytest.mark.django_db
def test_enmienda_individual_con_llamado_atencion_y_articulos_personalizados(
    causal_expediente, causal_vocal, make_socio
):
    from django.db import connection

    causal_expediente.estado = EstadoExpedienteEnum.EMITIDO
    causal_expediente.puntos = Decimal("-2.00")
    causal_expediente.save()

    socio = make_socio(legajo="76105", role=Role.SOCIO, numero_socio=76105)
    causal_expediente.socios.add(socio)

    with connection.cursor() as cursor:
        cursor.execute(
            "INSERT INTO tribunal_puntajeaplicado (puntajeAplicado, socio_id, expediente_id) "
            "VALUES (%s, %s, %s)",
            [-2.0, socio.numero_socio, causal_expediente.id],
        )

    Resolucion.objects.create(
        expediente=causal_expediente,
        version=1,
        plantilla_version="v1",
        estado=EstadoResolucionEnum.ISSUED,
        numero_expediente_snapshot=causal_expediente.numero,
        vistos="Vistos.",
        considerandos="Considerandos.",
        articulos_resolutivos="Artículo 1: sanción inicial.",
        puntos_finales=Decimal("-2.00"),
        created_by=causal_vocal.user,
        issued_by=causal_vocal.user,
    )

    _, res_v2 = EnmiendaService.solicitar_enmienda(
        expediente_id=causal_expediente.id,
        user=causal_vocal.user,
        motivo_enmienda="Sustitución de quita por llamado de atención individual.",
        articulos_resolutivos="Artículo 1: Aplicar llamado de atención al socio.",
        nuevos_puntajes=[{"socio_id": socio.id, "puntaje": "LLAMADO_ATENCION"}],
    )

    assert res_v2.puntos_finales == Decimal("0.00")
    assert res_v2.medidas == ["Llamado de atención"]
    assert res_v2.articulos_resolutivos == "Artículo 1: Aplicar llamado de atención al socio."

    descargo = DescargoExpediente.objects.get(expediente=causal_expediente, socio=socio)
    assert descargo.puntaje_ratificado == "LLAMADO_ATENCION"

    emitida = emitir_resolucion(res_v2, causal_vocal.user, ExpedienteConsolidatedDecisionProvider())
    assert emitida.estado == EstadoResolucionEnum.ISSUED
    assert emitida.medidas == ["Llamado de atención"]

    asientos = [
        Decimal(str(a.puntajeAplicado))
        for a in PuntajeAplicado.objects.filter(
            expediente_id=causal_expediente.id, socio_id=socio.numero_socio
        )
    ]
    assert sum(asientos) == Decimal("0.00")
