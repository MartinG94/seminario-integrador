"""Resolución por Asamblea Extraordinaria (Art. 95 del Estatuto, S4-04).

Cuando el Tribunal ordinario no puede intervenir (Casos A y B), CD o Administración
registran el acta en PDF de la Asamblea y la causa se emite recorriendo los estados
del Art. 12 con trazabilidad completa.
"""

from django.db import transaction

from expedientes.domain.evidence_validator import EvidenceValidationError, EvidenceValidator
from expedientes.models import EstadoExpedienteEnum, Expediente, ResolucionAsamblea
from expedientes.services.tribunal_composition_service import (
    ASSEMBLY_STATES,
    TribunalCompositionError,
    TribunalCompositionNotFound,
    TribunalCompositionService,
    TribunalCompositionStateError,
)
from expedientes.services.workflow_service import ExpedienteWorkflowService

PDF_MIME_TYPE = "application/pdf"
ASSEMBLY_MOTIVE = "Resolución por Asamblea Extraordinaria (Art. 95 del Estatuto)."


class AssemblyResolutionValidationError(TribunalCompositionError):
    pass


class AssemblyResolutionService:
    @staticmethod
    @transaction.atomic
    def register(*, expediente_id: int, user, content: bytes, filename: str) -> ResolucionAsamblea:
        expediente = Expediente.objects.select_for_update().filter(pk=expediente_id).first()
        if expediente is None:
            raise TribunalCompositionNotFound("Expediente no encontrado.")
        if ResolucionAsamblea.objects.filter(expediente=expediente).exists():
            raise TribunalCompositionStateError(
                "La causa ya tiene registrada su Resolución por Asamblea Extraordinaria."
            )
        if not TribunalCompositionService.requires_ad_hoc(expediente):
            raise TribunalCompositionStateError(
                "La causa no requiere intervención de Asamblea: la resuelve el Tribunal ordinario."
            )
        if expediente.estado not in ASSEMBLY_STATES:
            raise TribunalCompositionStateError(
                f"El expediente está en '{expediente.get_estado_display()}': la Resolución por "
                "Asamblea se registra una vez concluido el período de justificaciones."
            )
        try:
            validated = EvidenceValidator.validate_file(content, filename)
        except EvidenceValidationError as exc:
            raise AssemblyResolutionValidationError(str(exc)) from exc
        if validated.mime_type != PDF_MIME_TYPE:
            raise AssemblyResolutionValidationError("El acta de la Asamblea debe ser un PDF.")

        socio = getattr(user, "socio", None)
        resolucion = ResolucionAsamblea.objects.create(
            expediente=expediente,
            acta_blob=content,
            acta_nombre=validated.filename,
            acta_tamanio_bytes=validated.size_bytes,
            acta_sha256=validated.sha256_hash,
            registrada_por=user,
            registrada_por_legajo=socio.legajo if socio else user.get_username(),
        )
        while expediente.estado != EstadoExpedienteEnum.EMITIDO:
            expediente = ExpedienteWorkflowService.transition(
                expediente_id=expediente.pk,
                estado_nuevo=ExpedienteWorkflowService.NEXT_STATE[expediente.estado],
                actor=user.get_username(),
                motivo=ASSEMBLY_MOTIVE,
            )
        return resolucion
