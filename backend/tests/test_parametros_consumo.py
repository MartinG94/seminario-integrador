"""Los parámetros configurados rigen en el comportamiento real del sistema (Spec 010, T5)."""

from decimal import Decimal

import pytest
from django.test import override_settings

from core.models import ParametroSistema
from expedientes.domain.evidence_validator import EvidenceValidationError, EvidenceValidator
from ranking.domain.threshold_alerts import resolver_destinatarios_alerta_critica
from ranking.services import configured_threshold

PDF = b"%PDF-1.4 "


def set_param(clave: str, valor) -> None:
    ParametroSistema.objects.create(clave=clave, valor=valor)


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
