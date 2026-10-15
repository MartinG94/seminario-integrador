"""Dominio puro para validación binaria, detección de tipos MIME y cuotas de evidencia.

Implementa los requisitos de CA1 y CA2:
- Magic bytes para PDF, JPEG y PNG.
- Límite máximo de 5 MB (5.242.880 bytes).
- Sanitización de nombre de archivo contra path traversal.
- Cálculo de hash inmutable SHA-256.
- Control de cupos documentales por modalidad procesal (T02: 1 a 3; T03: 0 a 5).
"""

import hashlib
import os
import re
from dataclasses import dataclass

MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB (5.242.880 bytes)

# Firmas binarias oficiales (magic bytes)
MAGIC_BYTES_MAP: list[tuple[bytes, str, list[str]]] = [
    (b"%PDF", "application/pdf", [".pdf"]),
    (b"\xff\xd8\xff", "image/jpeg", [".jpg", ".jpeg"]),
    (b"\x89PNG\r\n\x1a\n", "image/png", [".png"]),
]

ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}


class EvidenceValidationError(ValueError):
    """Excepción de dominio para fallas de validación procesal o binaria de comprobantes."""

    pass


@dataclass(frozen=True)
class ValidatedEvidence:
    """Representación inmutable de una evidencia validada en dominio."""

    filename: str
    extension: str
    mime_type: str
    size_bytes: int
    sha256_hash: str


class EvidenceValidator:
    """Servicio de dominio para la validación técnica y procesal de evidencias probatorias."""

    @classmethod
    def sanitize_filename(cls, filename: str) -> str:
        """Sanitiza el nombre de archivo eliminando rutas de directorios y caracteres peligrosos."""
        base_name = os.path.basename(filename or "").strip()
        base_name = base_name.replace("\\", "/").split("/")[-1]
        # Conservar caracteres seguros (alfanuméricos, espacios, guiones, puntos y guiones bajos)
        sanitized = re.sub(r"[^\w\s\.\-]", "_", base_name, flags=re.UNICODE)
        sanitized = sanitized.strip(". ")
        return sanitized or "comprobante_adjunto"

    @classmethod
    def validate_file(cls, content: bytes, filename: str) -> ValidatedEvidence:
        """
        Valida el contenido binario, detecta tipo MIME por magic bytes y calcula metadatos.

        Raises:
            EvidenceValidationError si el archivo está vacío, supera 5 MB, tiene formato
            no admitido o presenta inconsistencia entre cabecera y extensión.
        """
        size_bytes = len(content)
        if size_bytes == 0:
            raise EvidenceValidationError("El archivo se encuentra vacío.")

        if size_bytes > MAX_FILE_SIZE_BYTES:
            msg = (
                f"El archivo excede el tamaño máximo permitido de 5 MB "
                f"({size_bytes} bytes recibidos)."
            )
            raise EvidenceValidationError(msg)

        # 1. Detección por magic bytes reales
        detected_mime: str | None = None
        valid_extensions: list[str] = []
        for magic, mime, exts in MAGIC_BYTES_MAP:
            if content.startswith(magic):
                detected_mime = mime
                valid_extensions = exts
                break

        if not detected_mime:
            raise EvidenceValidationError(
                "Tipo de archivo no permitido. Solo se admiten archivos PDF, JPG, JPEG y PNG."
            )

        # 2. Sanitización y validación de extensión
        clean_name = cls.sanitize_filename(filename)
        _, ext = os.path.splitext(clean_name)
        ext_lower = ext.lower()

        if ext_lower not in valid_extensions:
            msg = (
                f"La extensión '{ext_lower or 'desconocida'}' no coincide con el tipo "
                f"de archivo detectado ({detected_mime})."
            )
            raise EvidenceValidationError(msg)

        # 3. Hash SHA-256
        sha256_hash = hashlib.sha256(content).hexdigest()

        return ValidatedEvidence(
            filename=clean_name,
            extension=ext_lower,
            mime_type=detected_mime,
            size_bytes=size_bytes,
            sha256_hash=sha256_hash,
        )

    @classmethod
    def validate_quota(cls, tipo_descargo: str, count: int) -> None:
        """
        Valida que la cantidad de documentos respete los límites de la modalidad procesal.

        - T02: mínimo 1 obligatorio, máximo 3.
        - T03: opcional (0 a 5).
        """
        if tipo_descargo == "T02_CERTIFICADO":
            if count < 1:
                msg = (
                    "Debe adjuntar al menos 1 comprobante para la causal tipificada "
                    "(Formulario T02)."
                )
                raise EvidenceValidationError(msg)
            if count > 3:
                raise EvidenceValidationError(
                    "El Formulario T02 admite un máximo de 3 comprobantes probatorios."
                )
        elif tipo_descargo == "T03_EXTRAORDINARIO":
            if count < 0:
                raise EvidenceValidationError("La cantidad de comprobantes no puede ser negativa.")
            if count > 5:
                raise EvidenceValidationError(
                    "El Formulario T03 admite un máximo de 5 comprobantes probatorios."
                )
