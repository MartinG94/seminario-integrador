"""Los parámetros configurados rigen en el comportamiento real del sistema (Spec 012, T5)."""

from decimal import Decimal

import pytest
from django.test import override_settings

from core.models import SystemParameterChange
from expedientes.domain.evidence_validator import EvidenceValidationError, EvidenceValidator
from ranking.domain.threshold_alerts import resolver_destinatarios_alerta_critica
from ranking.services import configured_threshold

PDF = b"%PDF-1.4 "


def set_param(clave: str, valor) -> None:
    SystemParameterChange.objects.create(key=clave, value=valor)


@pytest.mark.django_db
def test_threshold_config_uses_configured_preventive_values() -> None:
    assert configured_threshold().preventivo_activo is False

    set_param("umbral_preventivo", "-8.5")
    set_param("umbral_preventivo_activo", True)

    config = configured_threshold()
    assert config.umbral_preventivo == Decimal("-8.5")
    assert config.preventivo_activo is True
    assert config.umbral_critico == Decimal("-10.0")


@pytest.mark.django_db
@override_settings(CD_EMAIL="cd@aveit.test", TRIBUNAL_EMAIL="tribunal@aveit.test")
def test_critical_alert_recipients_follow_configured_emails() -> None:
    assert resolver_destinatarios_alerta_critica("s@aveit.test") == [
        "s@aveit.test",
        "cd@aveit.test",
        "tribunal@aveit.test",
    ]

    set_param("email_tribunal_disciplina", "td.nuevo@aveit.test")

    assert resolver_destinatarios_alerta_critica("s@aveit.test") == [
        "s@aveit.test",
        "cd@aveit.test",
        "td.nuevo@aveit.test",
    ]


def test_evidence_validator_honours_custom_limits() -> None:
    content = PDF + b"\x00" * (2 * 1024 * 1024)
    EvidenceValidator.validate_file(content, "a.pdf", max_bytes=3 * 1024 * 1024)
    with pytest.raises(EvidenceValidationError, match="1 MB"):
        EvidenceValidator.validate_file(content, "a.pdf", max_bytes=1024 * 1024)

    EvidenceValidator.validate_quota("T03_OTRO", 7, max_count=8)
    with pytest.raises(EvidenceValidationError, match="máximo de 2"):
        EvidenceValidator.validate_quota("T03_OTRO", 3, max_count=2)


@pytest.mark.django_db
def test_evidence_service_reads_configured_size_limit(make_socio) -> None:
    from expedientes.services.evidence_service import EvidenceService

    set_param("adjuntos_tamano_maximo_mb", 1)
    socio = make_socio()
    archivo = PDF + b"\x00" * (2 * 1024 * 1024)

    with pytest.raises(EvidenceValidationError, match="1 MB"):
        EvidenceService.save_evidence(expediente=None, socio=socio, file_obj=archivo)


# --- Revisión PR #78: consumo real desde la base en cada servicio ---


@pytest.mark.django_db
def test_preventive_crossing_is_evaluated_with_db_thresholds() -> None:
    from ranking.services import evaluate_socio_threshold_crossing

    sin_activar = evaluate_socio_threshold_crossing(
        socio_id=1, saldo_anterior=Decimal("-4"), saldo_nuevo=Decimal("-6")
    )
    assert sin_activar.alerta_generada is None

    set_param("umbral_preventivo", "-5")
    set_param("umbral_preventivo_activo", True)

    resultado = evaluate_socio_threshold_crossing(
        socio_id=1, saldo_anterior=Decimal("-4"), saldo_nuevo=Decimal("-6")
    )
    assert resultado.esta_en_zona_preventiva is True
    assert resultado.alerta_generada is not None
    assert resultado.alerta_generada.tipo.value == "PREVENTIVA"


@pytest.mark.django_db
def test_presentar_descargo_serializer_uses_configured_quantity() -> None:
    from uuid import uuid4

    from expedientes.serializers import PresentarDescargoSerializer

    def payload(cantidad: int) -> dict:
        return {
            "tipo": "T03_EXTRAORDINARIO",
            "texto": "Descargo extraordinario con comprobantes.",
            "evidencia_ids": [str(uuid4()) for _ in range(cantidad)],
        }

    assert not PresentarDescargoSerializer(data=payload(6)).is_valid()

    set_param("adjuntos_cantidad_maxima", 8)
    assert PresentarDescargoSerializer(data=payload(8)).is_valid()
    rechazo = PresentarDescargoSerializer(data=payload(9))
    assert not rechazo.is_valid()
    assert "máximo de 8" in str(rechazo.errors["evidencia_ids"])


@pytest.mark.django_db
def test_opening_notification_uses_configured_descargo_deadline(make_socio, settings) -> None:
    from expedientes.domain.calendar import compute_business_deadline
    from expedientes.domain.holiday_provider import DbHolidayProvider
    from expedientes.models import EstadoExpedienteEnum, Expediente
    from expedientes.services.opening_notification_service import OpeningNotificationService

    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    set_param("plazo_descargo_dias_habiles", 8)
    socio = make_socio(legajo="74100")
    expediente = Expediente.objects.create(
        numero="EXP-2026-0801",
        socio=socio,
        motivo="Inasistencia",
        puntos=-1.0,
        estado=EstadoExpedienteEnum.CREADO,
    )

    exp, outbox = OpeningNotificationService.dispatch_opening(
        expediente_id=expediente.id, actor="TD"
    )

    exp.refresh_from_db()
    assert exp.plazo_limite_at == compute_business_deadline(
        start_at=exp.plazo_inicio_at, business_days=8, holiday_provider=DbHolidayProvider()
    )
    assert "8 días hábiles administrativos" in outbox.body_text
    assert "5 días hábiles" not in outbox.body_text


@pytest.mark.django_db
def test_evidence_upload_enforces_quota_even_without_descargo_type(
    make_socio, authenticate
) -> None:
    from datetime import timedelta

    from django.core.files.uploadedfile import SimpleUploadedFile
    from django.utils import timezone

    from expedientes.models import EstadoExpedienteEnum, Expediente

    set_param("adjuntos_cantidad_maxima", 1)
    socio = make_socio(legajo="74101")
    expediente = Expediente.objects.create(
        numero="EXP-2026-0802",
        socio=socio,
        motivo="Inasistencia",
        puntos=-1.0,
        estado=EstadoExpedienteEnum.JUSTIFICANDO,
        plazo_inicio_at=timezone.now() - timedelta(days=1),
        plazo_limite_at=timezone.now() + timedelta(days=3),
    )
    client = authenticate(socio)
    url = f"/api/v1/expedientes/{expediente.id}/evidencia/"

    primero = client.post(
        url,
        {"archivos": [SimpleUploadedFile("a.pdf", PDF + b"a", "application/pdf")]},
        format="multipart",
    )
    segundo = client.post(
        url,
        {"archivos": [SimpleUploadedFile("b.pdf", PDF + b"b", "application/pdf")]},
        format="multipart",
    )

    assert primero.status_code == 201, primero.data
    assert segundo.status_code == 400
    assert "máximo de 1" in segundo.data["detail"]


@pytest.mark.django_db
@override_settings(CD_EMAIL="cd@aveit.test", COMISION_DIRECTIVA_EMAIL="otro@aveit.test")
def test_cd_email_has_a_single_environment_fallback() -> None:
    from core.services.system_parameters import SystemParameterService

    assert SystemParameterService.email("email_comision_directiva") == "cd@aveit.test"
    set_param("email_comision_directiva", "cd.panel@aveit.test")
    assert SystemParameterService.email("email_comision_directiva") == "cd.panel@aveit.test"


@pytest.mark.django_db
def test_public_threshold_and_deadline_endpoints(make_socio, authenticate, api_client) -> None:
    assert api_client.get("/api/v1/parametros/umbrales/").status_code == 401

    client = authenticate(make_socio(legajo="74102"))
    inicial = client.get("/api/v1/parametros/umbrales/")
    assert inicial.status_code == 200
    assert inicial.data == {
        "umbral_critico": "-10.0",
        "umbral_preventivo": "-7.0",
        "umbral_preventivo_activo": False,
    }

    set_param("umbral_preventivo", "-2")
    set_param("umbral_preventivo_activo", True)
    set_param("plazo_descargo_dias_habiles", 9)

    assert client.get("/api/v1/parametros/umbrales/").data["umbral_preventivo"] == "-2"
    assert client.get("/api/v1/parametros/umbrales/").data["umbral_preventivo_activo"] is True
    plazos = client.get("/api/v1/parametros/plazos/").data
    assert plazos == {"plazo_descargo_dias_habiles": 9, "plazo_apelacion_dias_habiles": 5}
