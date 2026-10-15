"""Pruebas unitarias y de persistencia para los modelos de Evidencia y Auditoría de Descargas.

Cubre TS3-04.2:
- Persistencia de archivos en BLOB (BinaryField MySQL).
- Relaciones con Expediente, DescargoExpediente y Socio.
- Preservación histórica (es_vigente = False).
- Pista de auditoría inmutable de descargas (AuditoriaDescargaEvidencia).
"""

import uuid

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from expedientes.models import (
    AuditoriaDescargaEvidencia,
    DescargoExpediente,
    EstadoExpedienteEnum,
    EvidenciaDescargo,
    Expediente,
    TipoDescargoEnum,
)
from socios.models import Role, Socio, Subcomision

User = get_user_model()


@pytest.mark.django_db
class TestEvidenceModels:
    @pytest.fixture
    def setup_data(self):
        user = User.objects.create_user(
            username="401234",
            email="carlos.gomez@aveit.frc.utn.edu.ar",
            password="test_password_123",
        )
        subcomision = Subcomision.objects.create(name="Cómputos")
        socio = Socio.objects.create(
            user=user,
            first_name="Carlos",
            last_name="Gomez",
            legajo="401234",
            email="carlos.gomez@aveit.frc.utn.edu.ar",
            subcomision=subcomision,
            role=Role.SOCIO,
            social_year=2,
            is_enabled=True,
        )
        expediente = Expediente.objects.create(
            numero="EXP-001/2026",
            socio=socio,
            motivo="Inasistencia a reunión obligatoria",
            estado=EstadoExpedienteEnum.JUSTIFICANDO,
            plazo_inicio_at=timezone.now(),
        )
        expediente.socios.add(socio)
        descargo = DescargoExpediente.objects.create(
            expediente=expediente,
            socio=socio,
            tipo=TipoDescargoEnum.T02_CERTIFICADO,
            causal="Enfermedad",
            texto="Adjunto certificado médico digital.",
        )
        return {
            "socio": socio,
            "expediente": expediente,
            "descargo": descargo,
        }

    def test_create_evidencia_descargo_blob(self, setup_data):
        socio = setup_data["socio"]
        expediente = setup_data["expediente"]
        descargo = setup_data["descargo"]

        blob_bytes = b"%PDF-1.4 contenido binario del certificado medico"
        evidencia = EvidenciaDescargo.objects.create(
            expediente=expediente,
            descargo=descargo,
            socio=socio,
            contenido_blob=blob_bytes,
            nombre_original="Certificado_Perez.pdf",
            extension=".pdf",
            mime_type="application/pdf",
            tamanio_bytes=len(blob_bytes),
            sha256_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            es_vigente=True,
        )

        assert isinstance(evidencia.id, uuid.UUID)
        assert bytes(evidencia.contenido_blob) == blob_bytes
        assert evidencia.es_vigente is True
        assert evidencia.expediente == expediente
        assert evidencia.descargo == descargo
        assert evidencia.socio == socio
        assert evidencia.tamanio_bytes == len(blob_bytes)

    def test_preservacion_historica_es_vigente(self, setup_data):
        socio = setup_data["socio"]
        expediente = setup_data["expediente"]

        blob1 = b"%PDF-1.4 version inicial"
        ev1 = EvidenciaDescargo.objects.create(
            expediente=expediente,
            socio=socio,
            contenido_blob=blob1,
            nombre_original="Certificado_v1.pdf",
            extension=".pdf",
            mime_type="application/pdf",
            tamanio_bytes=len(blob1),
            sha256_hash="hash1",
            es_vigente=True,
        )

        # Ante corrección, ev1 pasa a no vigente y se crea ev2
        ev1.es_vigente = False
        ev1.save(update_fields=["es_vigente"])

        blob2 = b"%PDF-1.4 version corregida con firma"
        ev2 = EvidenciaDescargo.objects.create(
            expediente=expediente,
            socio=socio,
            contenido_blob=blob2,
            nombre_original="Certificado_v2.pdf",
            extension=".pdf",
            mime_type="application/pdf",
            tamanio_bytes=len(blob2),
            sha256_hash="hash2",
            es_vigente=True,
        )

        evidencias = EvidenciaDescargo.objects.filter(expediente=expediente, socio=socio)
        assert evidencias.count() == 2
        assert evidencias.filter(es_vigente=True).count() == 1
        assert evidencias.filter(es_vigente=False).count() == 1
        assert ev2.es_vigente is True

    def test_auditoria_descarga_evidencia(self, setup_data):
        socio = setup_data["socio"]
        expediente = setup_data["expediente"]

        blob = b"%PDF-1.4 archivo para auditoria"
        evidencia = EvidenciaDescargo.objects.create(
            expediente=expediente,
            socio=socio,
            contenido_blob=blob,
            nombre_original="Doc.pdf",
            extension=".pdf",
            mime_type="application/pdf",
            tamanio_bytes=len(blob),
            sha256_hash="hash_auditoria",
            es_vigente=True,
        )

        auditoria = AuditoriaDescargaEvidencia.objects.create(
            evidencia=evidencia,
            usuario="juez_tribunal_1",
            rol="TD",
            ip_address="192.168.1.50",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        )

        assert isinstance(auditoria.id, uuid.UUID)
        assert auditoria.evidencia == evidencia
        assert auditoria.usuario == "juez_tribunal_1"
        assert auditoria.rol == "TD"
        assert auditoria.ip_address == "192.168.1.50"
        assert auditoria.fecha_hora is not None
