"""Servicio de aplicación para custodia, persistencia y auditoría de evidencias probatorias.

Implementa:
- Validación técnica y serialización a BLOB en base de datos.
- Preservación histórica de comprobantes previos ante correcciones en plazo.
- Pista de auditoría inmutable de accesos y descargas de evidencia (CA4).
"""

from typing import Any

from django.db import transaction

from accounts import audit
from expedientes.domain.evidence_validator import EvidenceValidationError, EvidenceValidator
from expedientes.models import (
    AuditoriaDescargaEvidencia,
    DescargoExpediente,
    EvidenciaDescargo,
    Expediente,
)
from socios.models import Role, Socio


class EvidenceService:
    """Orquestador de aplicación para la gestión protegida de evidencias probatorias."""

    @classmethod
    @transaction.atomic
    def save_evidence(
        cls,
        expediente: Expediente,
        socio: Socio,
        file_obj: Any,
        descargo: DescargoExpediente | None = None,
    ) -> EvidenciaDescargo:
        """
        Lee el archivo, valida sus magic bytes y metadatos, y persiste en LONGBLOB.
        """
        if hasattr(file_obj, "read"):
            content = file_obj.read()
            if hasattr(file_obj, "seek"):
                file_obj.seek(0)
        elif isinstance(file_obj, (bytes, bytearray)):
            content = bytes(file_obj)
        else:
            raise ValueError("file_obj debe ser un archivo o secuencia de bytes.")

        filename = getattr(file_obj, "name", "adjunto")
        validated = EvidenceValidator.validate_file(content=content, filename=filename)

        # Regla de no duplicación: verificar si ya existe evidencia vigente con el mismo hash
        duplicado = EvidenciaDescargo.objects.filter(
            expediente=expediente,
            es_vigente=True,
            sha256_hash=validated.sha256_hash,
        ).first()
        if duplicado:
            msg = (
                f"El archivo '{validated.filename}' ya fue incorporado "
                "como evidencia en este expediente."
            )
            raise EvidenceValidationError(msg)

        return EvidenciaDescargo.objects.create(
            expediente=expediente,
            descargo=descargo,
            socio=socio,
            contenido_blob=content,
            nombre_original=validated.filename,
            extension=validated.extension,
            mime_type=validated.mime_type,
            tamanio_bytes=validated.size_bytes,
            sha256_hash=validated.sha256_hash,
            es_vigente=True,
        )

    @classmethod
    def mark_previous_versions_non_current(cls, expediente: Expediente, socio: Socio) -> int:
        """
        Marca todas las evidencias vigentes anteriores de este socio en el expediente
        como no vigentes (es_vigente = False), garantizando preservación histórica.
        """
        return EvidenciaDescargo.objects.filter(
            expediente=expediente,
            socio=socio,
            es_vigente=True,
        ).update(es_vigente=False)

    @classmethod
    def record_download_audit(
        cls,
        evidencia: EvidenciaDescargo,
        user: Any,
        ip_address: str | None = None,
        user_agent: str = "",
        accion: str = "descarga",
    ) -> AuditoriaDescargaEvidencia:
        """
        Asienta una entrada inmutable en la tabla de auditoría de descargas (CA4)
        y registra el evento en el log de auditoría del sistema.
        Diferencia entre consulta en visor y descarga formal a disco.
        """
        username = getattr(user, "username", "ANON")
        socio = getattr(user, "socio", None)
        rol = socio.role if socio else (Role.ADMIN if user.is_staff else "DESCONOCIDO")

        action_name = "consulta" if accion.lower() in ["ver", "consulta", "visualizar"] else "descarga"

        # Registrar también en el módulo de auditoría de seguridad
        audit.log_access_granted(
            identifier=username,
            role=rol,
            resource=f"evidencia:{evidencia.id}:{action_name}",
        )

        prefix = "[CONSULTA] " if action_name == "consulta" else "[DESCARGA] "
        ua_clean = user_agent or ""
        if not ua_clean.startswith(("[CONSULTA]", "[DESCARGA]")):
            ua_formatted = f"{prefix}{ua_clean}"[:500]
        else:
            ua_formatted = ua_clean[:500]

        return AuditoriaDescargaEvidencia.objects.create(
            evidencia=evidencia,
            usuario=username,
            rol=rol,
            ip_address=ip_address,
            user_agent=ua_formatted,
        )
