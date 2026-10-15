"""Pruebas unitarias para la validación de dominio de evidencias y comprobantes.

Cubre:
- CA1: Límites y formatos (PDF, JPG, PNG <= 5 MB; cupos T02: 1-3, T03: 0-5).
- CA2: Detección por magic bytes reales, cálculo SHA-256 y sanitización de nombres.
"""

import pytest

from expedientes.domain.evidence_validator import (
    MAX_FILE_SIZE_BYTES,
    EvidenceValidationError,
    EvidenceValidator,
    ValidatedEvidence,
)


class TestEvidenceValidator:
    def test_valid_pdf_file(self):
        content = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF"
        result = EvidenceValidator.validate_file(
            content=content,
            filename="Certificado_Medico_2026.pdf",
        )
        assert isinstance(result, ValidatedEvidence)
        assert result.mime_type == "application/pdf"
        assert result.extension == ".pdf"
        assert result.filename == "Certificado_Medico_2026.pdf"
        assert result.size_bytes == len(content)
        assert len(result.sha256_hash) == 64

    def test_valid_jpeg_file(self):
        content = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01" + (b"\x00" * 100)
        result = EvidenceValidator.validate_file(
            content=content,
            filename="foto_constancia.jpg",
        )
        assert result.mime_type == "image/jpeg"
        assert result.extension == ".jpg"
        assert result.filename == "foto_constancia.jpg"

    def test_valid_jpeg_with_jpeg_extension(self):
        content = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01" + (b"\x00" * 100)
        result = EvidenceValidator.validate_file(
            content=content,
            filename="foto_receta.JPEG",
        )
        assert result.mime_type == "image/jpeg"
        assert result.extension == ".jpeg"

    def test_valid_png_file(self):
        content = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR" + (b"\x00" * 50)
        result = EvidenceValidator.validate_file(
            content=content,
            filename="constancia_examen.png",
        )
        assert result.mime_type == "image/png"
        assert result.extension == ".png"
        assert result.filename == "constancia_examen.png"

    def test_reject_empty_file(self):
        with pytest.raises(EvidenceValidationError, match="El archivo se encuentra vacío"):
            EvidenceValidator.validate_file(content=b"", filename="vacio.pdf")

    def test_reject_oversized_file(self):
        content = b"%PDF" + (b"\x00" * (MAX_FILE_SIZE_BYTES + 10))
        with pytest.raises(
            EvidenceValidationError, match="excede el tamaño máximo permitido de 5 MB"
        ):
            EvidenceValidator.validate_file(content=content, filename="pesado.pdf")

    def test_reject_unsupported_magic_bytes_exe(self):
        # Ejecutable Windows MZ
        content = b"MZ\x90\x00\x03\x00\x00\x00"
        with pytest.raises(EvidenceValidationError, match="Tipo de archivo no permitido"):
            EvidenceValidator.validate_file(content=content, filename="script.exe")

    def test_reject_spoofed_extension(self):
        # Archivo con extensión .pdf pero cabeceras de texto plano o ejecutable
        content = b"Este es un texto que pretende ser PDF"
        with pytest.raises(EvidenceValidationError, match="Tipo de archivo no permitido"):
            EvidenceValidator.validate_file(content=content, filename="falso.pdf")

    def test_reject_mismatched_magic_bytes_and_extension(self):
        # Contenido PNG pero extensión declarada .pdf
        content = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
        with pytest.raises(EvidenceValidationError, match="no coincide"):
            EvidenceValidator.validate_file(content=content, filename="imagen.pdf")

    def test_sanitize_filename_traversal(self):
        content = b"%PDF-1.4 sample content"
        result = EvidenceValidator.validate_file(
            content=content,
            filename="../../../etc/passwd.pdf",
        )
        assert "/" not in result.filename
        assert "\\" not in result.filename
        assert "passwd.pdf" in result.filename

    def test_validate_quota_t02_valid(self):
        # T02 admite entre 1 y 3 documentos
        EvidenceValidator.validate_quota(tipo_descargo="T02_CERTIFICADO", count=1)
        EvidenceValidator.validate_quota(tipo_descargo="T02_CERTIFICADO", count=2)
        EvidenceValidator.validate_quota(tipo_descargo="T02_CERTIFICADO", count=3)

    def test_validate_quota_t02_missing_evidence(self):
        with pytest.raises(EvidenceValidationError, match="al menos 1 comprobante"):
            EvidenceValidator.validate_quota(tipo_descargo="T02_CERTIFICADO", count=0)

    def test_validate_quota_t02_exceeded(self):
        with pytest.raises(EvidenceValidationError, match="máximo de 3 comprobantes"):
            EvidenceValidator.validate_quota(tipo_descargo="T02_CERTIFICADO", count=4)

    def test_validate_quota_t03_valid(self):
        # T03 admite entre 0 y 5 documentos
        EvidenceValidator.validate_quota(tipo_descargo="T03_EXTRAORDINARIO", count=0)
        EvidenceValidator.validate_quota(tipo_descargo="T03_EXTRAORDINARIO", count=1)
        EvidenceValidator.validate_quota(tipo_descargo="T03_EXTRAORDINARIO", count=5)

    def test_validate_quota_t03_exceeded(self):
        with pytest.raises(EvidenceValidationError, match="máximo de 5 comprobantes"):
            EvidenceValidator.validate_quota(tipo_descargo="T03_EXTRAORDINARIO", count=6)
