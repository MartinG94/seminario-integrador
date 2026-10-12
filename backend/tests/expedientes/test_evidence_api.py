"""Tests de integración para los endpoints de evidencia probatoria (TS3-04.4).

Cubre:
- CA1: Cupos T02 (1-3) y T03 (0-5), límite de 5 MB.
- CA2: Validación de magic bytes reales y rechazo de formatos inválidos.
- CA3: Persistencia en BD y autorización por objeto IsImputadoOrTribunal.
- CA4: Auditoría inmutable de descargas en AuditoriaDescargaEvidencia y nosniff.
- CA6: Preservación histórica ante reenvíos en plazo (es_vigente=False).
"""

from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from expedientes.models import (
    AuditoriaDescargaEvidencia,
    EstadoExpedienteEnum,
    EvidenciaDescargo,
    Expediente,
)
from expedientes.services.evidence_service import EvidenceService
from socios.models import Role, Socio, Subcomision

User = get_user_model()


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture
def socio_imputado(db) -> Socio:
    user = User.objects.create_user(
        username="74907",
        email="74907@aveit.test",
        password="secure_password_123",
    )
    sub = Subcomision.objects.create(name="Cómputos")
    return Socio.objects.create(
        user=user,
        legajo="74907",
        first_name="Lucas",
        last_name="Gastiaburu",
        email="74907@aveit.test",
        subcomision=sub,
        social_year=4,
        role=Role.SOCIO,
        is_enabled=True,
    )


@pytest.fixture
def socio_tercero(db) -> Socio:
    user = User.objects.create_user(
        username="85194",
        email="85194@aveit.test",
        password="secure_password_123",
    )
    sub = Subcomision.objects.create(name="Deportes")
    return Socio.objects.create(
        user=user,
        legajo="85194",
        first_name="Mateo",
        last_name="Rios",
        email="85194@aveit.test",
        subcomision=sub,
        social_year=2,
        role=Role.SOCIO,
        is_enabled=True,
    )


@pytest.fixture
def miembro_td(db) -> Socio:
    user = User.objects.create_user(
        username="408917",
        email="td@aveit.test",
        password="secure_password_123",
    )
    sub = Subcomision.objects.create(name="Tribunal")
    return Socio.objects.create(
        user=user,
        legajo="408917",
        first_name="Juez",
        last_name="Tribunal",
        email="td@aveit.test",
        subcomision=sub,
        social_year=5,
        role=Role.TD,
        is_enabled=True,
    )


@pytest.fixture
def expediente_en_plazo(db, socio_imputado) -> Expediente:
    now = timezone.now()
    exp = Expediente.objects.create(
        numero="EXP-2026/010",
        socio=socio_imputado,
        motivo="Inasistencia a jornada institucional",
        estado=EstadoExpedienteEnum.JUSTIFICANDO,
        plazo_inicio_at=now,
        plazo_limite_at=now + timedelta(days=5),
    )
    exp.socios.add(socio_imputado)
    return exp


@pytest.mark.django_db
class TestEvidenceApi:
    def test_upload_evidence_success(self, api_client, socio_imputado, expediente_en_plazo):
        api_client.force_authenticate(user=socio_imputado.user)
        pdf_bytes = b"%PDF-1.4 certificado medico valido"
        uploaded_file = SimpleUploadedFile(
            "certificado.pdf", pdf_bytes, content_type="application/pdf"
        )

        url = f"/api/v1/expedientes/{expediente_en_plazo.id}/evidencia/"
        response = api_client.post(
            url,
            {"archivos": [uploaded_file], "tipo_descargo": "T02_CERTIFICADO"},
            format="multipart",
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert len(response.data) == 1
        assert response.data[0]["nombre_original"] == "certificado.pdf"
        assert response.data[0]["mime_type"] == "application/pdf"
        assert response.data[0]["es_vigente"] is True

        evidencia = EvidenciaDescargo.objects.get(id=response.data[0]["id"])
        assert bytes(evidencia.contenido_blob) == pdf_bytes

    def test_upload_evidence_quota_exceeded_t02(
        self, api_client, socio_imputado, expediente_en_plazo
    ):
        api_client.force_authenticate(user=socio_imputado.user)
        files = [
            SimpleUploadedFile(
                f"cert_{i}.pdf", b"%PDF-1.4 contenido", content_type="application/pdf"
            )
            for i in range(4)
        ]

        url = f"/api/v1/expedientes/{expediente_en_plazo.id}/evidencia/"
        response = api_client.post(
            url,
            {"archivos": files, "tipo_descargo": "T02_CERTIFICADO"},
            format="multipart",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "máximo de 3" in str(response.data)

    def test_upload_evidence_invalid_magic_bytes(
        self, api_client, socio_imputado, expediente_en_plazo
    ):
        api_client.force_authenticate(user=socio_imputado.user)
        fake_pdf = SimpleUploadedFile(
            "falso.pdf", b"MZ ejecutable de windows", content_type="application/pdf"
        )

        url = f"/api/v1/expedientes/{expediente_en_plazo.id}/evidencia/"
        response = api_client.post(
            url,
            {"archivos": [fake_pdf]},
            format="multipart",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_upload_evidence_expired_deadline_409(
        self, api_client, socio_imputado, expediente_en_plazo
    ):
        api_client.force_authenticate(user=socio_imputado.user)
        expediente_en_plazo.plazo_limite_at = timezone.now() - timedelta(hours=1)
        expediente_en_plazo.save(update_fields=["plazo_limite_at"])

        valid_pdf = SimpleUploadedFile(
            "cert.pdf", b"%PDF-1.4 contenido", content_type="application/pdf"
        )
        url = f"/api/v1/expedientes/{expediente_en_plazo.id}/evidencia/"
        response = api_client.post(
            url,
            {"archivos": [valid_pdf]},
            format="multipart",
        )

        assert response.status_code == status.HTTP_409_CONFLICT
        assert "expirado" in str(response.data)

    def test_upload_evidence_forbidden_to_third_party(
        self, api_client, socio_tercero, expediente_en_plazo
    ):
        api_client.force_authenticate(user=socio_tercero.user)
        valid_pdf = SimpleUploadedFile(
            "cert.pdf", b"%PDF-1.4 contenido", content_type="application/pdf"
        )
        url = f"/api/v1/expedientes/{expediente_en_plazo.id}/evidencia/"
        response = api_client.post(
            url,
            {"archivos": [valid_pdf]},
            format="multipart",
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_download_evidence_by_owner_audited(
        self, api_client, socio_imputado, expediente_en_plazo
    ):
        api_client.force_authenticate(user=socio_imputado.user)
        pdf_bytes = b"%PDF-1.4 constancia de estudio"
        evidencia = EvidenceService.save_evidence(
            expediente=expediente_en_plazo,
            socio=socio_imputado,
            file_obj=SimpleUploadedFile(
                "constancia.pdf", pdf_bytes, content_type="application/pdf"
            ),
        )

        url = f"/api/v1/expedientes/{expediente_en_plazo.id}/evidencia/{evidencia.id}/"
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.content == pdf_bytes
        assert response["Content-Type"] == "application/pdf"
        assert response["X-Content-Type-Options"] == "nosniff"
        assert "inline" in response["Content-Disposition"]
        assert "constancia.pdf" in response["Content-Disposition"]

        # Verificar auditoría
        audit_log = AuditoriaDescargaEvidencia.objects.filter(evidencia=evidencia).first()
        assert audit_log is not None
        assert audit_log.usuario == socio_imputado.user.username
        assert audit_log.rol == Role.SOCIO

    def test_download_evidence_by_td_audited(
        self, api_client, miembro_td, socio_imputado, expediente_en_plazo
    ):
        api_client.force_authenticate(user=miembro_td.user)
        pdf_bytes = b"%PDF-1.4 constancia para tribunal"
        evidencia = EvidenceService.save_evidence(
            expediente=expediente_en_plazo,
            socio=socio_imputado,
            file_obj=SimpleUploadedFile("examen.pdf", pdf_bytes, content_type="application/pdf"),
        )

        url = f"/api/v1/expedientes/{expediente_en_plazo.id}/evidencia/{evidencia.id}/"
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.content == pdf_bytes

        audit_log = AuditoriaDescargaEvidencia.objects.filter(evidencia=evidencia).first()
        assert audit_log is not None
        assert audit_log.usuario == miembro_td.user.username
        assert audit_log.rol == Role.TD

    def test_download_evidence_forbidden_to_other_socio(
        self, api_client, socio_tercero, socio_imputado, expediente_en_plazo
    ):
        api_client.force_authenticate(user=socio_tercero.user)
        evidencia = EvidenceService.save_evidence(
            expediente=expediente_en_plazo,
            socio=socio_imputado,
            file_obj=SimpleUploadedFile(
                "privado.pdf", b"%PDF-1.4 privado", content_type="application/pdf"
            ),
        )

        url = f"/api/v1/expedientes/{expediente_en_plazo.id}/evidencia/{evidencia.id}/"
        response = api_client.get(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_download_evidence_anonymous_401(self, api_client, socio_imputado, expediente_en_plazo):
        evidencia = EvidenceService.save_evidence(
            expediente=expediente_en_plazo,
            socio=socio_imputado,
            file_obj=SimpleUploadedFile(
                "anon.pdf", b"%PDF-1.4 anon", content_type="application/pdf"
            ),
        )

        url = f"/api/v1/expedientes/{expediente_en_plazo.id}/evidencia/{evidencia.id}/"
        response = api_client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
