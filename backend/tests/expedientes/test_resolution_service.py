from datetime import datetime, timezone
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError

from expedientes.domain.closed_decision import ClosedDecision
from expedientes.models import (
    ComposicionTribunal,
    CondicionIntegranteEnum,
    DecisionCausalDescargo,
    DescargoExpediente,
    EstadoExpedienteEnum,
    EstadoResolucionEnum,
    IntegranteComposicion,
    Resolucion,
)
from expedientes.services.resolution_service import (
    DictamenNoCerradoError,
    ExpedienteConsolidatedDecisionProvider,
    emitir_resolucion,
    obtener_firmantes_resolucion,
    obtener_firmantes_td_por_anio_social,
    registrar_firma_resolucion,
)
from notifications.models import EmailOutbox
from ranking.domain.threshold_alerts import AlertaSanitizer
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
    assert decision.puntos_finales == Decimal("0.00")
    assert decision.resultado == "SANCTION"


@pytest.mark.django_db
@pytest.mark.django_db
def test_firmantes_td_inicia_vacio_y_cero_hardcodeo(causal_expediente, causal_vocal):
    assert obtener_firmantes_td_por_anio_social() == []
    resolucion = Resolucion.objects.create(
        expediente=causal_expediente,
        plantilla_version="resolucion-2026.1",
        numero_expediente_snapshot=causal_expediente.numero,
        vistos="Vistos.",
        considerandos="Considerandos.",
        articulos_resolutivos="Artículo 1.",
        created_by=causal_vocal.user,
    )
    assert obtener_firmantes_resolucion(resolucion) == []
    assert obtener_firmantes_td_por_anio_social(resolucion) == []


@pytest.mark.django_db
def test_registrar_firma_resolucion_exitoso_y_por_anio_social(
    causal_expediente, causal_vocal, make_socio
):
    resolucion = Resolucion.objects.create(
        expediente=causal_expediente,
        plantilla_version="resolucion-2026.1",
        numero_expediente_snapshot=causal_expediente.numero,
        vistos="Vistos.",
        considerandos="Considerandos.",
        articulos_resolutivos="Artículo 1.",
        created_by=causal_vocal.user,
    )
    socio_4 = make_socio(legajo="40001", role=Role.TD, social_year=4)
    socio_4.first_name = "Ana"
    socio_4.last_name = "Perez"
    socio_4.save()

    resolucion = registrar_firma_resolucion(resolucion, socio_4.user)
    assert len(resolucion.firmantes) == 1
    firma = resolucion.firmantes[0]
    assert firma["legajo"] == "40001"
    assert firma["full_name"] == "Ana Perez"
    assert firma["social_year"] == 4
    assert firma["user_id"] == socio_4.user.id
    assert "40001 - Ana Perez" in firma["etiqueta"]
    assert resolucion.estado == EstadoResolucionEnum.DRAFT


@pytest.mark.django_db
def test_registrar_firma_rechaza_duplicado_de_usuario_o_anio_social(
    causal_expediente, causal_vocal, make_socio
):
    resolucion = Resolucion.objects.create(
        expediente=causal_expediente,
        plantilla_version="resolucion-2026.1",
        numero_expediente_snapshot=causal_expediente.numero,
        vistos="Vistos.",
        considerandos="Considerandos.",
        articulos_resolutivos="Artículo 1.",
        created_by=causal_vocal.user,
    )
    socio_4 = make_socio(legajo="40001", role=Role.TD, social_year=4)
    registrar_firma_resolucion(resolucion, socio_4.user)

    # Intento de firmar dos veces por el mismo usuario
    with pytest.raises(ValidationError):
        registrar_firma_resolucion(resolucion, socio_4.user)

    # Intento de firmar por otro usuario con el mismo año social
    socio_4_otro = make_socio(legajo="40002", role=Role.TD, social_year=4)
    with pytest.raises(ValidationError):
        registrar_firma_resolucion(resolucion, socio_4_otro.user)


@pytest.mark.django_db
def test_completar_tres_firmas_emite_resolucion_y_transiciona_expediente(
    causal_expediente, causal_vocal, make_socio
):
    causal_expediente.estado = EstadoExpedienteEnum.PENDIENTE_CORREOS
    causal_expediente.puntos = Decimal("-2.00")
    causal_expediente.save()

    resolucion = Resolucion.objects.create(
        expediente=causal_expediente,
        plantilla_version="resolucion-2026.1",
        numero_expediente_snapshot=causal_expediente.numero,
        vistos="Vistos.",
        considerandos="Considerandos.",
        articulos_resolutivos="Artículo 1.",
        created_by=causal_vocal.user,
    )
    s4 = make_socio(legajo="40001", role=Role.TD, social_year=4)
    s5 = make_socio(legajo="50001", role=Role.TD, social_year=5)
    s6 = make_socio(legajo="60001", role=Role.TD, social_year=6)

    registrar_firma_resolucion(resolucion, s4.user)
    resolucion.refresh_from_db()
    assert resolucion.estado == EstadoResolucionEnum.DRAFT

    registrar_firma_resolucion(resolucion, s5.user)
    resolucion.refresh_from_db()
    assert resolucion.estado == EstadoResolucionEnum.DRAFT

    registrar_firma_resolucion(resolucion, s6.user)
    resolucion.refresh_from_db()
    assert resolucion.estado == EstadoResolucionEnum.ISSUED
    assert resolucion.contenido_hash

    causal_expediente.refresh_from_db()
    assert causal_expediente.estado == EstadoExpedienteEnum.EMITIDO


@pytest.mark.django_db
def test_registrar_firma_con_es_suplente_explicito_agrega_sup_a_etiqueta(
    causal_expediente, causal_vocal, make_socio
):
    resolucion = Resolucion.objects.create(
        expediente=causal_expediente,
        plantilla_version="resolucion-2026.1",
        numero_expediente_snapshot=causal_expediente.numero,
        vistos="Vistos.",
        considerandos="Considerandos.",
        articulos_resolutivos="Artículo 1.",
        created_by=causal_vocal.user,
    )
    s4 = make_socio(legajo="40001", role=Role.TD, social_year=4)
    s4.first_name = "Facundo"
    s4.last_name = "Gomez"
    s4.save()

    resolucion = registrar_firma_resolucion(resolucion, s4.user, es_suplente=True)
    assert len(resolucion.firmantes) == 1
    firma = resolucion.firmantes[0]
    assert firma["es_suplente"] is True
    assert firma["condicion"] == "SUPLENTE"
    assert firma["etiqueta"].endswith(" (Sup.)")
    assert "40001 - Facundo Gomez" in firma["etiqueta"]


@pytest.mark.django_db
def test_registrar_firma_infiere_suplente_desde_composicion_tribunal(
    causal_expediente, causal_vocal, make_socio
):
    resolucion = Resolucion.objects.create(
        expediente=causal_expediente,
        plantilla_version="resolucion-2026.1",
        numero_expediente_snapshot=causal_expediente.numero,
        vistos="Vistos.",
        considerandos="Considerandos.",
        articulos_resolutivos="Artículo 1.",
        created_by=causal_vocal.user,
    )
    s5 = make_socio(legajo="50002", role=Role.TD, social_year=5)
    s5.first_name = "Lucia"
    s5.last_name = "Vera"
    s5.save()

    # Estampar ComposicionTribunal donde s5 es Suplente
    composicion = ComposicionTribunal.objects.create(expediente=causal_expediente)
    IntegranteComposicion.objects.create(
        composicion=composicion,
        anio_social=5,
        socio=s5,
        condicion=CondicionIntegranteEnum.SUPLENTE,
        nro_socio=int(s5.legajo),
        nombre_completo="Lucia Vera",
        grupo="G58",
    )

    resolucion = registrar_firma_resolucion(resolucion, s5.user)
    firma = resolucion.firmantes[0]
    assert firma["es_suplente"] is True
    assert firma["condicion"] == "SUPLENTE"
    assert firma["etiqueta"].endswith(" (Sup.)")


@pytest.mark.django_db
def test_registrar_firma_permite_especificar_anio_social_ad_hoc(
    causal_expediente, causal_vocal, make_socio
):
    resolucion = Resolucion.objects.create(
        expediente=causal_expediente,
        plantilla_version="resolucion-2026.1",
        numero_expediente_snapshot=causal_expediente.numero,
        vistos="Vistos.",
        considerandos="Considerandos.",
        articulos_resolutivos="Artículo 1.",
        created_by=causal_vocal.user,
    )
    s4 = make_socio(legajo="40001", role=Role.TD, social_year=4)

    # El socio tiene año social 4 en su perfil, pero firma en representación ad-hoc de 6.° año
    resolucion = registrar_firma_resolucion(resolucion, s4.user, anio_social=6)
    firma = resolucion.firmantes[0]
    assert firma["social_year"] == 6
    assert firma["anio_social"] == 6


@pytest.mark.django_db
def test_registrar_firma_rechaza_anio_social_invalido(causal_expediente, causal_vocal, make_socio):
    resolucion = Resolucion.objects.create(
        expediente=causal_expediente,
        plantilla_version="resolucion-2026.1",
        numero_expediente_snapshot=causal_expediente.numero,
        vistos="Vistos.",
        considerandos="Considerandos.",
        articulos_resolutivos="Artículo 1.",
        created_by=causal_vocal.user,
    )
    s4 = make_socio(legajo="40001", role=Role.TD, social_year=4)

    with pytest.raises(ValidationError) as exc:
        registrar_firma_resolucion(resolucion, s4.user, anio_social=2)
    assert "El año social debe ser 4, 5 o 6" in str(exc.value)


@pytest.mark.django_db
def test_emitir_resolucion_despacha_correos_idempotentes_sin_duplicados(
    causal_expediente, causal_vocal, make_socio
):
    causal_expediente.estado = EstadoExpedienteEnum.PENDIENTE_CORREOS
    causal_expediente.puntos = Decimal("-2.50")
    causal_expediente.save()

    resolucion = Resolucion.objects.create(
        expediente=causal_expediente,
        plantilla_version="resolucion-2026.1",
        numero_expediente_snapshot=causal_expediente.numero,
        vistos="Vistos de prueba.",
        considerandos="Considerando sanción formal.",
        articulos_resolutivos="Artículo 1: sancionar con -2.50 puntos.",
        created_by=causal_vocal.user,
    )
    s4 = make_socio(legajo="40001", role=Role.TD, social_year=4)
    s5 = make_socio(legajo="50001", role=Role.TD, social_year=5)
    s6 = make_socio(legajo="60001", role=Role.TD, social_year=6)

    # Involucrar a un socio activo
    socio_activo = make_socio(legajo="76050", email="activo@aveit.test", numero_socio=76050)
    causal_expediente.socios.add(socio_activo)

    # 1. Firmar las 3 firmas -> emite automáticamente
    registrar_firma_resolucion(resolucion, s4.user)
    registrar_firma_resolucion(resolucion, s5.user)
    registrar_firma_resolucion(resolucion, s6.user)

    resolucion.refresh_from_db()
    assert resolucion.estado == EstadoResolucionEnum.ISSUED

    # 2. Verificar que EmailOutbox contenga notificaciones para socio activo, CD y TD
    outbox_emails = list(
        EmailOutbox.objects.filter(
            idempotency_key__startswith=f"resolucion-emision-{resolucion.id}-"
        )
    )
    assert len(outbox_emails) >= 3

    # Claves de idempotencia esperadas
    idempotency_keys = {e.idempotency_key for e in outbox_emails}
    assert any("cd" in k for k in idempotency_keys)
    assert any("td" in k for k in idempotency_keys)
    assert any(str(socio_activo.id) in k or "activo@aveit.test" in k for k in idempotency_keys)

    # 3. Verificar que no contengan términos médicos (EARS-100.3)
    for email_entry in outbox_emails:
        AlertaSanitizer.assert_no_sensitive_data(email_entry.subject)
        AlertaSanitizer.assert_no_sensitive_data(email_entry.body_text)

    # 4. Re-ejecución idempotente: no debe crear duplicados
    conteo_inicial = EmailOutbox.objects.filter(
        idempotency_key__startswith=f"resolucion-emision-{resolucion.id}-"
    ).count()

    from expedientes.services.resolution_service import despachar_notificaciones_resolucion_emitida

    despachar_notificaciones_resolucion_emitida(resolucion)

    conteo_reintento = EmailOutbox.objects.filter(
        idempotency_key__startswith=f"resolucion-emision-{resolucion.id}-"
    ).count()
    assert conteo_reintento == conteo_inicial


@pytest.mark.django_db
def test_emitir_resolucion_no_envia_correo_a_socio_excluido(
    causal_expediente, causal_vocal, make_socio
):
    causal_expediente.estado = EstadoExpedienteEnum.PENDIENTE_CORREOS
    causal_expediente.puntos = Decimal("-1.00")
    causal_expediente.save()

    resolucion = Resolucion.objects.create(
        expediente=causal_expediente,
        plantilla_version="resolucion-2026.1",
        numero_expediente_snapshot=causal_expediente.numero,
        vistos="Vistos.",
        considerandos="Considerando.",
        articulos_resolutivos="Artículo 1.",
        created_by=causal_vocal.user,
    )
    s4 = make_socio(legajo="40001", role=Role.TD, social_year=4)
    s5 = make_socio(legajo="50001", role=Role.TD, social_year=5)
    s6 = make_socio(legajo="60001", role=Role.TD, social_year=6)

    # Involucrar a un socio pero marcarlo como excluido
    socio_excluido = make_socio(legajo="76051", email="excluido@aveit.test")
    causal_expediente.socios.add(socio_excluido)
    DescargoExpediente.objects.create(
        expediente=causal_expediente,
        socio=socio_excluido,
        esta_excluido=True,
        motivo_exclusion="Exclusión previa formal",
    )

    registrar_firma_resolucion(resolucion, s4.user)
    registrar_firma_resolucion(resolucion, s5.user)
    registrar_firma_resolucion(resolucion, s6.user)

    resolucion.refresh_from_db()
    outbox_emails = EmailOutbox.objects.filter(
        idempotency_key__startswith=f"resolucion-emision-{resolucion.id}-"
    )
    # Ningún email debe tener como destinatario al socio excluido
    for e in outbox_emails:
        assert "excluido@aveit.test" not in e.to
        assert "excluido@aveit.test" not in e.idempotency_key
        assert (e.metadata or {}).get("socio_id") != socio_excluido.id


@pytest.mark.django_db
def test_emitir_resolucion_mantiene_pendiente_correos_si_falla_despacho(
    causal_expediente, causal_vocal, monkeypatch
):
    causal_expediente.estado = EstadoExpedienteEnum.PENDIENTE_CORREOS
    causal_expediente.puntos = Decimal("-1.00")
    causal_expediente.save()

    resolucion = Resolucion.objects.create(
        expediente=causal_expediente,
        plantilla_version="resolucion-2026.1",
        numero_expediente_snapshot=causal_expediente.numero,
        vistos="Vistos.",
        considerandos="Considerando.",
        articulos_resolutivos="Artículo 1.",
        created_by=causal_vocal.user,
    )

    monkeypatch.setattr(
        "expedientes.services.resolution_service.EmailDispatcherService.dispatch",
        lambda outbox: False,
    )

    emitida = emitir_resolucion(
        resolucion, causal_vocal.user, ExpedienteConsolidatedDecisionProvider()
    )
    assert emitida.estado == EstadoResolucionEnum.ISSUED

    causal_expediente.refresh_from_db()
    assert causal_expediente.estado == EstadoExpedienteEnum.PENDIENTE_CORREOS
