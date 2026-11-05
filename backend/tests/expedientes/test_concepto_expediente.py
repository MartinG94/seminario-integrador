"""Tests para la clasificación de concepto institucional de expedientes por el TD (Milestone 1).

Verifica:
1. Modelo Expediente: concepto default None, catálogo de 13 conceptos ConceptoExpedienteEnum.
2. Guardrail de Workflow: transición a EMITIDO bloqueada con ValidationError si concepto es None.
3. Exposición en serializadores:
   ExpedienteVisorSerializer, BoardExpedienteSerializer y ExpedienteListSerializer.
4. Endpoint PATCH /api/v1/expedientes/<id>/:
   - Autorizado para roles TD, CD y ADMIN.
   - Denegado (403 Forbidden) para SOCIO y FISCALIZADORA.
   - Rechazo de opciones inválidas con 400 Bad Request.
   - Actualización exitosa de concepto (y combinación con urgencia).
5. Transición API a EMITIDO con validación de concepto.
"""

import pytest
from django.core.exceptions import ValidationError
from rest_framework import status

from expedientes.models import (
    CambioEstadoExpediente,
    ConceptoExpedienteEnum,
    EstadoExpedienteEnum,
    Expediente,
    UrgenciaExpedienteEnum,
)
from expedientes.serializers import (
    BoardExpedienteSerializer,
    ExpedienteListSerializer,
    ExpedienteVisorSerializer,
)
from expedientes.services.workflow_service import ExpedienteWorkflowService
from socios.models import Role


@pytest.fixture
def td_socio(make_socio):
    """Socio con rol Tribunal de Disciplina."""
    return make_socio(legajo="11239", role=Role.TD, email="td_test@aveit.test")


@pytest.fixture
def cd_socio(make_socio):
    """Socio con rol Comisión Directiva."""
    return make_socio(legajo="11240", role=Role.CD, email="cd_test@aveit.test")


@pytest.fixture
def admin_socio(make_socio):
    """Socio con rol Administrador."""
    return make_socio(legajo="11241", role=Role.ADMIN, email="admin_test@aveit.test")


@pytest.fixture
def fiscalizadora_socio(make_socio):
    """Socio con rol Comisión Fiscalizadora."""
    return make_socio(legajo="11242", role=Role.FISCALIZADORA, email="fisc_test@aveit.test")


@pytest.fixture
def regular_socio(make_socio):
    """Socio ordinario sin facultades de gestión."""
    return make_socio(legajo="12999", role=Role.SOCIO, email="socio_test@aveit.test")


@pytest.fixture
def expediente_base(regular_socio):
    """Expediente recién creado para pruebas."""
    return Expediente.objects.create(
        numero="EXP-2026-0001",
        socio=regular_socio,
        motivo="Falta injustificada a reunión general",
        estado=EstadoExpedienteEnum.CREADO,
    )


@pytest.mark.django_db
class TestConceptoExpedienteModel:
    """Pruebas unitarias de dominio y persistencia para concepto en Expediente."""

    def test_default_concepto_is_none(self, regular_socio):
        exp = Expediente.objects.create(
            numero="EXP-2026-0010",
            socio=regular_socio,
            motivo="Causa sin clasificar",
            estado=EstadoExpedienteEnum.CREADO,
        )
        assert exp.concepto is None
        assert exp.get_concepto_display() is None or exp.get_concepto_display() == ""

    def test_workflow_service_open_expediente_defaults_concepto_none(self, regular_socio):
        exp = ExpedienteWorkflowService.open_expediente(
            motivo="Apertura estándar por el Tribunal",
            socio_ids=[regular_socio.pk],
            actor="Tribunal de Disciplina",
        )
        assert exp.concepto is None

    def test_all_catalog_choices_accepted(self, regular_socio):
        expected_choices = [
            ("CD", "CD — Comisión Directiva"),
            ("TD", "TD — Tribunal de Disciplina"),
            ("GSA", "GSA — Gestión Social y Ambiental"),
            ("GVP", "GVP — Grupo de Viaje / Gestión de Viaje"),
            ("COMP", "COMP — Cómputos"),
            ("RRHH", "RRHH — Recursos Humanos"),
            ("RRII", "RRII — Relaciones Institucionales"),
            ("PRENSA", "PRENSA — Prensa y Difusión"),
            ("MANT", "MANT — Mantenimiento"),
            ("EVENTOS", "EVENTOS — Organización y Eventos"),
            ("RIFAS", "RIFAS — Rifas"),
            ("ASAMBLEA", "ASAMBLEA — Asamblea General"),
            ("OTROS", "OTROS — Otros Conceptos Institucionales"),
        ]
        assert list(ConceptoExpedienteEnum.choices) == expected_choices

        for code, label in expected_choices:
            exp = Expediente.objects.create(
                numero=f"EXP-2026-CHOICE-{code}",
                socio=regular_socio,
                motivo=f"Prueba concepto {code}",
                concepto=code,
            )
            exp.refresh_from_db()
            assert exp.concepto == code
            assert exp.get_concepto_display() == label


@pytest.mark.django_db
class TestConceptoExpedienteWorkflow:
    """Pruebas del guardrail de workflow para el concepto institucional."""

    def test_transition_to_emitido_fails_when_concepto_is_none(self, regular_socio):
        # Expediente en estado previo PENDIENTE_CORREOS
        exp = Expediente.objects.create(
            numero="EXP-2026-WF-01",
            socio=regular_socio,
            motivo="Causa lista para emisión",
            estado=EstadoExpedienteEnum.PENDIENTE_CORREOS,
            concepto=None,
        )
        CambioEstadoExpediente.objects.create(
            expediente=exp,
            estado_anterior=EstadoExpedienteEnum.ESPERA_RESOLUCION,
            estado_nuevo=EstadoExpedienteEnum.PENDIENTE_CORREOS,
            actor="Tribunal",
            motivo="Aprobación previa",
        )

        with pytest.raises(ValidationError) as exc_info:
            ExpedienteWorkflowService.transition(
                expediente_id=exp.pk,
                estado_nuevo=EstadoExpedienteEnum.EMITIDO,
                actor="Presidente TD",
                motivo="Emisión definitiva de resolución",
            )

        assert "concepto" in exc_info.value.message_dict
        expected_msg = (
            "El Tribunal debe clasificar el concepto del expediente "
            "(GSA, GVP, CD, etc.) antes de emitirlo."
        )
        assert expected_msg in exc_info.value.message_dict["concepto"]

    def test_transition_to_emitido_succeeds_when_concepto_is_assigned(self, regular_socio):
        exp = Expediente.objects.create(
            numero="EXP-2026-WF-02",
            socio=regular_socio,
            motivo="Causa clasificada por TD",
            estado=EstadoExpedienteEnum.PENDIENTE_CORREOS,
            concepto=ConceptoExpedienteEnum.GSA,
        )
        CambioEstadoExpediente.objects.create(
            expediente=exp,
            estado_anterior=EstadoExpedienteEnum.ESPERA_RESOLUCION,
            estado_nuevo=EstadoExpedienteEnum.PENDIENTE_CORREOS,
            actor="Tribunal",
            motivo="Aprobación previa",
        )

        emitted_exp = ExpedienteWorkflowService.transition(
            expediente_id=exp.pk,
            estado_nuevo=EstadoExpedienteEnum.EMITIDO,
            actor="Presidente TD",
            motivo="Emisión definitiva con concepto asignado",
        )

        assert emitted_exp.estado == EstadoExpedienteEnum.EMITIDO
        assert emitted_exp.concepto == ConceptoExpedienteEnum.GSA

    def test_intermediate_transitions_do_not_require_concepto(self, regular_socio):
        exp = ExpedienteWorkflowService.open_expediente(
            motivo="Apertura de causa",
            socio_ids=[regular_socio.pk],
            actor="Tribunal",
        )
        assert exp.estado == EstadoExpedienteEnum.CREADO
        assert exp.concepto is None

        # CREADO -> JUSTIFICANDO no requiere concepto
        exp = ExpedienteWorkflowService.transition(
            expediente_id=exp.pk,
            estado_nuevo=EstadoExpedienteEnum.JUSTIFICANDO,
            actor="Tribunal",
            motivo="Pase a justificaciones",
        )
        assert exp.estado == EstadoExpedienteEnum.JUSTIFICANDO
        assert exp.concepto is None


@pytest.mark.django_db
class TestConceptoExpedienteSerializers:
    """Verifica exposición de concepto y concepto_display en serializadores."""

    def test_visor_serializer_exposes_concepto(self, regular_socio):
        exp = Expediente.objects.create(
            numero="EXP-2026-SER-01",
            socio=regular_socio,
            motivo="Causa para visor",
            concepto=ConceptoExpedienteEnum.GVP,
        )
        data = ExpedienteVisorSerializer(exp).data
        assert "concepto" in data
        assert data["concepto"] == "GVP"
        assert "concepto_display" in data
        assert data["concepto_display"] == "GVP — Grupo de Viaje / Gestión de Viaje"

    def test_visor_serializer_with_null_concepto(self, regular_socio):
        exp = Expediente.objects.create(
            numero="EXP-2026-SER-02",
            socio=regular_socio,
            motivo="Causa sin concepto",
            concepto=None,
        )
        data = ExpedienteVisorSerializer(exp).data
        assert "concepto" in data
        assert data["concepto"] is None
        assert "concepto_display" in data
        assert not data["concepto_display"]

    def test_list_serializer_exposes_concepto(self, regular_socio):
        exp = Expediente.objects.create(
            numero="EXP-2026-SER-03",
            socio=regular_socio,
            motivo="Causa para listado",
            concepto=ConceptoExpedienteEnum.COMP,
        )
        data = ExpedienteListSerializer(exp).data
        assert "concepto" in data
        assert data["concepto"] == "COMP"
        assert "concepto_display" in data
        assert data["concepto_display"] == "COMP — Cómputos"

    def test_board_serializer_exposes_concepto(self, regular_socio):
        exp = Expediente.objects.create(
            numero="EXP-2026-SER-04",
            socio=regular_socio,
            motivo="Causa para tablero Kanban",
            concepto=ConceptoExpedienteEnum.TD,
        )
        data = BoardExpedienteSerializer(exp).data
        assert "concepto" in data
        assert data["concepto"] == "TD"
        assert "concepto_display" in data
        assert data["concepto_display"] == "TD — Tribunal de Disciplina"


@pytest.mark.django_db
class TestConceptoExpedienteApi:
    """Pruebas de endpoints para actualización de concepto y transiciones."""

    def test_patch_concepto_authorized_td(self, td_socio, expediente_base, authenticate):
        client = authenticate(td_socio)
        response = client.patch(
            f"/api/v1/expedientes/{expediente_base.pk}/",
            {"concepto": "GSA"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK, response.data
        assert response.data["concepto"] == "GSA"
        assert response.data["concepto_display"] == "GSA — Gestión Social y Ambiental"

        expediente_base.refresh_from_db()
        assert expediente_base.concepto == ConceptoExpedienteEnum.GSA

    def test_patch_concepto_authorized_cd(self, cd_socio, expediente_base, authenticate):
        client = authenticate(cd_socio)
        response = client.patch(
            f"/api/v1/expedientes/{expediente_base.pk}/",
            {"concepto": "CD"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["concepto"] == "CD"

        expediente_base.refresh_from_db()
        assert expediente_base.concepto == ConceptoExpedienteEnum.CD

    def test_patch_concepto_authorized_admin(self, admin_socio, expediente_base, authenticate):
        client = authenticate(admin_socio)
        response = client.patch(
            f"/api/v1/expedientes/{expediente_base.pk}/",
            {"concepto": "COMP"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["concepto"] == "COMP"

        expediente_base.refresh_from_db()
        assert expediente_base.concepto == ConceptoExpedienteEnum.COMP

    def test_patch_concepto_forbidden_for_regular_socio(
        self, regular_socio, expediente_base, authenticate
    ):
        client = authenticate(regular_socio)
        response = client.patch(
            f"/api/v1/expedientes/{expediente_base.pk}/",
            {"concepto": "GSA"},
            format="json",
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_patch_concepto_forbidden_for_fiscalizadora(
        self, fiscalizadora_socio, expediente_base, authenticate
    ):
        client = authenticate(fiscalizadora_socio)
        response = client.patch(
            f"/api/v1/expedientes/{expediente_base.pk}/",
            {"concepto": "GSA"},
            format="json",
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_patch_invalid_concepto_rejected(self, td_socio, expediente_base, authenticate):
        client = authenticate(td_socio)
        response = client.patch(
            f"/api/v1/expedientes/{expediente_base.pk}/",
            {"concepto": "CONCEPTO_INEXISTENTE"},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "concepto" in response.data

    def test_patch_simultaneous_urgencia_and_concepto(
        self, td_socio, expediente_base, authenticate
    ):
        client = authenticate(td_socio)
        response = client.patch(
            f"/api/v1/expedientes/{expediente_base.pk}/",
            {"urgencia": "urgente", "concepto": "EVENTOS"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["urgencia"] == "urgente"
        assert response.data["concepto"] == "EVENTOS"

        expediente_base.refresh_from_db()
        assert expediente_base.urgencia == UrgenciaExpedienteEnum.URGENTE
        assert expediente_base.concepto == ConceptoExpedienteEnum.EVENTOS

    def test_api_transition_to_emitido_blocks_unclassified_concepto(
        self, td_socio, regular_socio, authenticate
    ):
        client = authenticate(td_socio)
        exp = Expediente.objects.create(
            numero="EXP-2026-API-EMIT-01",
            socio=regular_socio,
            motivo="Listo para emitir",
            estado=EstadoExpedienteEnum.PENDIENTE_CORREOS,
            concepto=None,
        )

        response = client.post(
            f"/api/v1/expedientes/{exp.pk}/transicionar/",
            {"to_status": "emitido", "justificacion": "Emisión final por TD"},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "concepto" in response.data

    def test_api_transition_to_emitido_succeeds_with_classified_concepto(
        self, td_socio, regular_socio, authenticate
    ):
        client = authenticate(td_socio)
        exp = Expediente.objects.create(
            numero="EXP-2026-API-EMIT-02",
            socio=regular_socio,
            motivo="Listo para emitir con concepto",
            estado=EstadoExpedienteEnum.PENDIENTE_CORREOS,
            concepto=ConceptoExpedienteEnum.GSA,
        )

        response = client.post(
            f"/api/v1/expedientes/{exp.pk}/transicionar/",
            {"to_status": "emitido", "justificacion": "Emisión final con GSA"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        exp.refresh_from_db()
        assert exp.estado == EstadoExpedienteEnum.EMITIDO
