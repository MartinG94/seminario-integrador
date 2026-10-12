"""Pruebas unitarias para el servicio de aplicación EvidenceService (TS3-04.3)."""

import uuid

import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone

from expedientes.domain.evidence_validator import EvidenceValidationError
from expedientes.models import (
    EstadoExpedienteEnum,
    Expediente,
)
from expedientes.services.evidence_service import EvidenceService
from socios.models import Role, Socio, Subcomision

User = get_user_model()


@pytest.mark.django_db
class TestEvidenceService:
    @pytest.fixture
    def setup_data(self):
        user = User.objects.create_user(
            username="74907",
            email="74907@aveit.test",
            password="secure_password_123",
        )
        sub = Subcomision.objects.create(name="Cómputos")
        socio = Socio.objects.create(
            user=user,
            legajo="74907",
            first_name="Lucas",
            last_name="Gastiaburu",
            email="74907@aveit.test",
            subcomision=sub,
            social_year=4,
            role=Role.SOCIO,
        )
        expediente = Expediente.objects.create(
            numero="EXP-2026/001",
            socio=socio,
            motivo="Prueba de descargo",
            estado=EstadoExpedienteEnum.JUSTIFICANDO,
            plazo_inicio_at=timezone.now(),
        )
        expediente.socios.add(socio)
        return {"user": user, "socio": socio, "expediente": expediente}

    def test_save_evidence_success(self, setup_data):
        socio = setup_data["socio"]
        expediente = setup_data["expediente"]
        content = b"%PDF-1.4 certificado medico valido"
        uploaded = SimpleUploadedFile("certificado.pdf", content, content_type="application/pdf")

        evidencia = EvidenceService.save_evidence(
            expediente=expediente,
            socio=socio,
            file_obj=uploaded,
        )

        assert isinstance(evidencia.id, uuid.UUID)
        assert evidencia.nombre_original == "certificado.pdf"
        assert evidencia.mime_type == "application/pdf"
        assert bytes(evidencia.contenido_blob) == content
        assert evidencia.es_vigente is True
        assert len(evidencia.sha256_hash) == 64

    def test_save_evidence_invalid_rejected(self, setup_data):
        socio = setup_data["socio"]
        expediente = setup_data["expediente"]
        content = b"MZ archivo ejecutable"
        uploaded = SimpleUploadedFile("virus.exe", content, content_type="application/x-msdownload")

        with pytest.raises(EvidenceValidationError):
            EvidenceService.save_evidence(
                expediente=expediente,
                socio=socio,
                file_obj=uploaded,
            )

    def test_mark_previous_versions_non_current(self, setup_data):
        socio = setup_data["socio"]
        expediente = setup_data["expediente"]
        content = b"%PDF-1.4 doc v1"
        uploaded = SimpleUploadedFile("doc1.pdf", content, content_type="application/pdf")

        ev1 = EvidenceService.save_evidence(expediente, socio, uploaded)
        assert ev1.es_vigente is True

        EvidenceService.mark_previous_versions_non_current(expediente, socio)
        ev1.refresh_from_db()
        assert ev1.es_vigente is False

    def test_record_download_audit(self, setup_data):
        socio = setup_data["socio"]
        user = setup_data["user"]
        expediente = setup_data["expediente"]
        content = b"%PDF-1.4 doc"
        uploaded = SimpleUploadedFile("doc.pdf", content, content_type="application/pdf")

        evidencia = EvidenceService.save_evidence(expediente, socio, uploaded)

        audit_entry = EvidenceService.record_download_audit(
            evidencia=evidencia,
            user=user,
            ip_address="127.0.0.1",
            user_agent="TestBrowser/1.0",
        )

        assert isinstance(audit_entry.id, uuid.UUID)
        assert audit_entry.evidencia == evidencia
        assert audit_entry.usuario == user.username
        assert audit_entry.rol == Role.SOCIO
        assert audit_entry.ip_address == "127.0.0.1"

    def test_save_evidence_duplicate_hash_rejected(self, setup_data):
        socio = setup_data["socio"]
        expediente = setup_data["expediente"]
        content = b"%PDF-1.4 documento unico para testear duplicados"
        uploaded1 = SimpleUploadedFile("original.pdf", content, content_type="application/pdf")
        uploaded2 = SimpleUploadedFile("copia.pdf", content, content_type="application/pdf")

        EvidenceService.save_evidence(expediente, socio, uploaded1)

        with pytest.raises(EvidenceValidationError) as exc:
            EvidenceService.save_evidence(expediente, socio, uploaded2)
        assert "ya fue incorporado como evidencia" in str(exc.value)
