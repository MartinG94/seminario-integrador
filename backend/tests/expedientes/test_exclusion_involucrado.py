"""Pruebas del servicio de exclusión fundada de socios involucrados (SCRUM-102, EARS-102)."""

import pytest
from django.core.exceptions import PermissionDenied, ValidationError

from expedientes.models import (
    CambioEstadoExpediente,
    EstadoExpedienteEnum,
)
from expedientes.serializers.visor_serializers import ExpedienteVisorSerializer
from expedientes.services.exclusion_service import ExclusionInvolucradoService
from notifications.models import EmailOutbox
from socios.models import Role, Socio

VALID_GROUNDS = "El socio no fue notificado oportunamente de la citación a la reunión plenaria."


@pytest.fixture
def imputado_secundario(make_socio) -> Socio:
    return make_socio(legajo="76003", role=Role.SOCIO)


@pytest.mark.django_db
class TestExclusionInvolucradoService:
    def test_excluir_involucrado_exitoso_parcial(
        self, causal_expediente, causal_imputado, imputado_secundario, causal_vocal
    ) -> None:
        """Expediente con 2 imputados: se excluye uno, el expediente continúa activo."""
        causal_expediente.socios.add(imputado_secundario)

        resultado = ExclusionInvolucradoService.excluir_involucrado(
            expediente_id=causal_expediente.id,
            socio_id=causal_imputado.id,
            user=causal_vocal.user,
            motivo=VALID_GROUNDS,
        )

        assert resultado["expediente_archivado"] is False
        assert resultado["activos_restantes_count"] == 1

        descargo = resultado["descargo"]
        assert descargo.esta_excluido is True
        assert descargo.motivo_exclusion == VALID_GROUNDS
        assert descargo.excluido_por == causal_vocal.user
        assert descargo.excluido_at is not None
        assert descargo.es_vigente is False

        causal_expediente.refresh_from_db()
        assert causal_expediente.estado == EstadoExpedienteEnum.REVISION_RESOLUCION

        # Se despacha notificación vía EmailOutbox
        outbox = EmailOutbox.objects.filter(
            metadata__tipo="EXCLUSION_INVOLUCRADO",
            metadata__socio_id=causal_imputado.id,
        ).first()
        assert outbox is not None
        assert VALID_GROUNDS in outbox.body_text
        assert "Desestimación" in outbox.subject or "Exclusión" in outbox.subject

    def test_excluir_ultimo_involucrado_cierra_administrativamente(
        self, causal_expediente, causal_imputado, causal_vocal
    ) -> None:
        """Si se excluye al último socio, pasa directo a EMITIDO (Causa archivada)."""
        resultado = ExclusionInvolucradoService.excluir_involucrado(
            expediente_id=causal_expediente.id,
            socio_id=causal_imputado.id,
            user=causal_vocal.user,
            motivo=VALID_GROUNDS,
        )

        assert resultado["expediente_archivado"] is True
        assert resultado["activos_restantes_count"] == 0

        causal_expediente.refresh_from_db()
        assert causal_expediente.estado == EstadoExpedienteEnum.EMITIDO
        assert causal_expediente.puntos == 0

        # Registrado en CambioEstadoExpediente sin exigir 3 firmas (Decisión PO 12/11/2026)
        cambio = CambioEstadoExpediente.objects.filter(
            expediente=causal_expediente,
            estado_nuevo=EstadoExpedienteEnum.EMITIDO,
        ).first()
        assert cambio is not None
        assert (
            "Sin efecto / Expediente archivado" in cambio.motivo
            or "archivada" in cambio.motivo.lower()
            or "archivado" in cambio.motivo.lower()
        )

    def test_excluir_involucrado_rechaza_rol_no_autorizado(
        self, causal_expediente, causal_imputado, imputado_secundario
    ) -> None:
        """Un socio común sin rol TD no puede dictar la exclusión de otro socio."""
        with pytest.raises(PermissionDenied) as exc:
            ExclusionInvolucradoService.excluir_involucrado(
                expediente_id=causal_expediente.id,
                socio_id=causal_imputado.id,
                user=imputado_secundario.user,
                motivo=VALID_GROUNDS,
            )
        assert "Tribunal de Disciplina" in str(exc.value)

    def test_excluir_involucrado_rechaza_motivo_insuficiente(
        self, causal_expediente, causal_imputado, causal_vocal
    ) -> None:
        """Un motivo con menos de 10 caracteres debe ser rechazado."""
        with pytest.raises(ValidationError) as exc:
            ExclusionInvolucradoService.excluir_involucrado(
                expediente_id=causal_expediente.id,
                socio_id=causal_imputado.id,
                user=causal_vocal.user,
                motivo="error",
            )
        assert "al menos 10 caracteres" in str(exc.value)

    def test_excluir_involucrado_rechaza_expediente_ya_emitido(
        self, causal_expediente, causal_imputado, causal_vocal
    ) -> None:
        """No se puede excluir a un socio de un expediente ya finalizado/emitido."""
        causal_expediente.estado = EstadoExpedienteEnum.EMITIDO
        causal_expediente.save(update_fields=["estado"])

        with pytest.raises(ValidationError) as exc:
            ExclusionInvolucradoService.excluir_involucrado(
                expediente_id=causal_expediente.id,
                socio_id=causal_imputado.id,
                user=causal_vocal.user,
                motivo=VALID_GROUNDS,
            )
        assert "ya emitido o cerrado" in str(exc.value)

    def test_excluir_involucrado_rechaza_socio_ya_excluido(
        self, causal_expediente, causal_imputado, imputado_secundario, causal_vocal
    ) -> None:
        """No se puede volver a excluir a un socio que ya está excluido en causa activa."""
        causal_expediente.socios.add(imputado_secundario)
        ExclusionInvolucradoService.excluir_involucrado(
            expediente_id=causal_expediente.id,
            socio_id=causal_imputado.id,
            user=causal_vocal.user,
            motivo=VALID_GROUNDS,
        )

        with pytest.raises(ValidationError) as exc:
            ExclusionInvolucradoService.excluir_involucrado(
                expediente_id=causal_expediente.id,
                socio_id=causal_imputado.id,
                user=causal_vocal.user,
                motivo="Segundo intento de exclusión sobre el mismo socio.",
            )
        assert "ya fue excluido previamente" in str(exc.value)

    def test_excluir_involucrado_rechaza_socio_no_imputado(
        self, causal_expediente, imputado_secundario, causal_vocal
    ) -> None:
        """Rechaza intentar excluir a un socio que no pertenece a la causa."""
        with pytest.raises(ValidationError) as exc:
            ExclusionInvolucradoService.excluir_involucrado(
                expediente_id=causal_expediente.id,
                socio_id=imputado_secundario.id,
                user=causal_vocal.user,
                motivo=VALID_GROUNDS,
            )
        assert "no se encuentra involucrado" in str(exc.value)


@pytest.mark.django_db
class TestVisorConExclusion:
    def test_visor_expone_involucrado_excluido_y_timeline(
        self, causal_expediente, causal_imputado, causal_vocal, rf
    ) -> None:
        """El visor autorizado debe rotular al socio excluido y agregar el hito en el timeline."""
        ExclusionInvolucradoService.excluir_involucrado(
            expediente_id=causal_expediente.id,
            socio_id=causal_imputado.id,
            user=causal_vocal.user,
            motivo=VALID_GROUNDS,
        )

        request = rf.get(f"/api/v1/expedientes/{causal_expediente.id}/")
        request.user = causal_vocal.user

        serializer = ExpedienteVisorSerializer(
            causal_expediente,
            context={"request": request},
        )
        data = serializer.data

        # Involucrado rotulado como EXCLUIDO
        involucrados = data["involucrados"]
        assert len(involucrados) == 1
        inv = involucrados[0]
        assert inv["esta_excluido"] is True
        assert inv["motivo_exclusion"] == VALID_GROUNDS
        assert inv["estado_descargo"] == "EXCLUIDO"
        assert inv["estado_descargo_display"] == "Excluido del Expediente"

        # Timeline contiene el hito de exclusión
        timeline = data["timeline"]
        hitos_exclusion = [h for h in timeline if h["tipo"] == "EXCLUSION_INVOLUCRADO"]
        assert len(hitos_exclusion) >= 1
        hito = hitos_exclusion[0]
        assert "excluido del expediente" in hito["titulo"].lower()
        assert VALID_GROUNDS in hito["descripcion"]
