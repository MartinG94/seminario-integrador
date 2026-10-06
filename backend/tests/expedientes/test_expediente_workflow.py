"""Pruebas de apertura y trazabilidad del ciclo de vida de expedientes."""

import re
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier

import pytest
from django.core.exceptions import ValidationError
from django.db import connection, connections
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from expedientes.models import (
    CambioEstadoExpediente,
    DescargoExpediente,
    EstadoExpedienteEnum,
    Expediente,
    ExpedienteNumberSequence,
)
from expedientes.services.workflow_service import ExpedienteWorkflowService
from socios.models import Role

NUMERO_PATTERN = re.compile(r"^EXP-(\d{4})/(\d{4})$")


def _sequence_of(numero: str) -> int:
    match = NUMERO_PATTERN.match(numero)
    assert match, f"Formato de número inválido: {numero}"
    return int(match.group(1))


def _expire_deadline(expediente_id: int) -> None:
    """Simula el vencimiento del plazo de 5 días hábiles."""
    Expediente.objects.filter(pk=expediente_id).update(
        plazo_limite_at=timezone.now() - timedelta(seconds=1)
    )


@pytest.mark.django_db
class TestArt12States:
    def test_states_are_exactly_the_six_of_art_12_in_order(self) -> None:
        assert EstadoExpedienteEnum.labels == [
            "Expediente Creado",
            "En período de justificaciones",
            "Justificaciones en revisión",
            "En espera de resolución",
            "Pendiente de firma y envío",
            "Expedientes ya emitidos",
        ]

    def test_service_rejects_going_back_to_a_previous_state(self, make_socio) -> None:
        member = make_socio(legajo="72001")
        expediente = ExpedienteWorkflowService.open_expediente(
            motivo="Retroceso", socio_ids=[member.id], actor="72000"
        )
        ExpedienteWorkflowService.transition(
            expediente_id=expediente.pk,
            estado_nuevo=EstadoExpedienteEnum.JUSTIFICANDO,
            actor="72000",
            motivo="Avance",
        )

        with pytest.raises(ValidationError):
            ExpedienteWorkflowService.transition(
                expediente_id=expediente.pk,
                estado_nuevo=EstadoExpedienteEnum.CREADO,
                actor="72000",
                motivo="Retroceso",
            )

        expediente.refresh_from_db()
        assert expediente.estado == EstadoExpedienteEnum.JUSTIFICANDO
        assert expediente.cambios_estado.count() == 2

    def test_transition_requires_a_reason(self, make_socio) -> None:
        member = make_socio(legajo="72002")
        expediente = ExpedienteWorkflowService.open_expediente(
            motivo="Sin motivo", socio_ids=[member.id], actor="72000"
        )

        with pytest.raises(ValidationError):
            ExpedienteWorkflowService.transition(
                expediente_id=expediente.pk,
                estado_nuevo=EstadoExpedienteEnum.JUSTIFICANDO,
                actor="72000",
                motivo="   ",
            )

    def test_cannot_move_to_review_before_deadline_expires(self, make_socio) -> None:
        member = make_socio(legajo="72003")
        expediente = ExpedienteWorkflowService.open_expediente(
            motivo="Anticipo", socio_ids=[member.id], actor="72000"
        )
        ExpedienteWorkflowService.transition(
            expediente_id=expediente.pk,
            estado_nuevo=EstadoExpedienteEnum.JUSTIFICANDO,
            actor="72000",
            motivo="Avisos enviados",
        )

        with pytest.raises(ValidationError):
            ExpedienteWorkflowService.transition(
                expediente_id=expediente.pk,
                estado_nuevo=EstadoExpedienteEnum.REVISION_RESOLUCION,
                actor="72000",
                motivo="Anticipo de revisión",
            )

        expediente.refresh_from_db()
        assert expediente.estado == EstadoExpedienteEnum.JUSTIFICANDO
        assert expediente.cambios_estado.count() == 2

    def test_moves_to_review_once_deadline_expired(self, make_socio) -> None:
        member = make_socio(legajo="72004")
        expediente = ExpedienteWorkflowService.open_expediente(
            motivo="Vencido", socio_ids=[member.id], actor="72000"
        )
        ExpedienteWorkflowService.transition(
            expediente_id=expediente.pk,
            estado_nuevo=EstadoExpedienteEnum.JUSTIFICANDO,
            actor="72000",
            motivo="Avisos enviados",
        )
        _expire_deadline(expediente.pk)

        ExpedienteWorkflowService.transition(
            expediente_id=expediente.pk,
            estado_nuevo=EstadoExpedienteEnum.REVISION_RESOLUCION,
            actor="72000",
            motivo="Plazo vencido",
        )

        expediente.refresh_from_db()
        assert expediente.estado == EstadoExpedienteEnum.REVISION_RESOLUCION


@pytest.mark.django_db
class TestExpedienteNumbering:
    def test_numbers_stay_consecutive_after_a_failed_opening(self, make_socio) -> None:
        member = make_socio(legajo="73001")
        first = ExpedienteWorkflowService.open_expediente(
            motivo="Primero", socio_ids=[member.id], actor="73000"
        )

        with pytest.raises(ValidationError):
            ExpedienteWorkflowService.open_expediente(
                motivo="Socio inexistente", socio_ids=[999_999], actor="73000"
            )

        second = ExpedienteWorkflowService.open_expediente(
            motivo="Segundo", socio_ids=[member.id], actor="73000"
        )
        assert _sequence_of(second.numero) == _sequence_of(first.numero) + 1

    def test_number_uses_annual_format_with_current_year(self, make_socio) -> None:
        member = make_socio(legajo="73002")
        expediente = ExpedienteWorkflowService.open_expediente(
            motivo="Formato", socio_ids=[member.id], actor="73000"
        )

        match = NUMERO_PATTERN.match(expediente.numero)
        assert match
        assert int(match.group(2)) == timezone.localdate().year

    def test_format_numero_pads_to_four_digits_with_year(self) -> None:
        assert ExpedienteWorkflowService.format_numero(1, 2026) == "EXP-0001/2026"

    def test_counter_restarts_every_year(self) -> None:
        assert ExpedienteNumberSequence.next_value(2030) == 1
        assert ExpedienteNumberSequence.next_value(2030) == 2
        assert ExpedienteNumberSequence.next_value(2031) == 1
        assert ExpedienteNumberSequence.next_value(2030) == 3


@pytest.mark.skipif(
    connection.vendor != "mysql",
    reason="CA4 requiere bloqueo de filas real (MySQL/InnoDB).",
)
@pytest.mark.django_db(transaction=True)
def test_concurrent_openings_never_duplicate_numbers(make_socio) -> None:
    # Estado que deja la migración 0005; el flush de los tests transaccionales lo borra.
    ExpedienteNumberSequence.objects.get_or_create(year=timezone.localdate().year)
    member = make_socio(legajo="74001")
    workers = 8
    barrier = Barrier(workers)

    def open_one(index: int) -> str:
        try:
            barrier.wait()
            return ExpedienteWorkflowService.open_expediente(
                motivo=f"Concurrente {index}", socio_ids=[member.id], actor="74000"
            ).numero
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=workers) as pool:
        numbers = list(pool.map(open_one, range(workers)))

    sequences = sorted(_sequence_of(numero) for numero in numbers)
    assert len(set(numbers)) == workers
    assert sequences == list(range(sequences[0], sequences[0] + workers))
    assert Expediente.objects.filter(numero__in=numbers).count() == workers


@pytest.mark.django_db
class TestExpedienteWorkflow:
    def test_authorized_member_opens_numbered_expediente_with_multiple_socios(
        self, api_client: APIClient, make_socio
    ) -> None:
        authority = make_socio(legajo="71001", role=Role.FISCALIZADORA)
        first_member = make_socio(legajo="71002")
        second_member = make_socio(legajo="71003")
        api_client.force_authenticate(user=authority.user)

        response = api_client.post(
            "/api/v1/expedientes/gestion/",
            {
                "motivo": "Inasistencia a reunión obligatoria",
                "socios": [first_member.id, second_member.id],
            },
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["numero"].startswith("EXP-")
        assert data["estado"] == EstadoExpedienteEnum.CREADO
        assert {member["id"] for member in data["socios"]} == {
            first_member.id,
            second_member.id,
        }
        assert data["historial"][0]["actor"] == authority.user.username
        assert data["historial"][0]["estado_nuevo"] == EstadoExpedienteEnum.CREADO
        assert data["historial"][0]["motivo"] == "Inasistencia a reunión obligatoria"
        assert data["historial"][0]["fecha_hora"]

    def test_number_is_unique_and_increasing_for_sequential_creations(
        self, api_client: APIClient, make_socio
    ) -> None:
        authority = make_socio(legajo="71004", role=Role.TD)
        member = make_socio(legajo="71005")
        api_client.force_authenticate(user=authority.user)
        payload = {"motivo": "Motivo", "socios": [member.id]}

        numbers = [
            api_client.post("/api/v1/expedientes/gestion/", payload, format="json").json()["numero"]
            for _ in range(2)
        ]

        assert numbers[0] != numbers[1]
        assert _sequence_of(numbers[1]) == _sequence_of(numbers[0]) + 1

    def test_client_cannot_choose_the_number(self, api_client: APIClient, make_socio) -> None:
        authority = make_socio(legajo="71016", role=Role.CD)
        member = make_socio(legajo="71017")
        api_client.force_authenticate(user=authority.user)

        response = api_client.post(
            "/api/v1/expedientes/gestion/",
            {"numero": "EXP-9999/2026", "motivo": "Motivo", "socios": [member.id]},
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["numero"] != "EXP-9999/2026"

    @pytest.mark.parametrize(
        ("role", "is_enabled"),
        [
            (Role.SOCIO, True),
            (Role.ADMIN, True),
            (Role.TD, False),
        ],
    )
    def test_only_enabled_authorities_can_open_expediente(
        self, api_client: APIClient, make_socio, role: str, is_enabled: bool
    ) -> None:
        requester = make_socio(legajo="71006", role=role, is_enabled=is_enabled)
        member = make_socio(legajo="71018")
        api_client.force_authenticate(user=requester.user)

        response = api_client.post(
            "/api/v1/expedientes/gestion/",
            {"motivo": "No autorizado", "socios": [member.id]},
            format="json",
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert not Expediente.objects.exists()

    def test_only_tribunal_can_transition_manually(self, api_client: APIClient, make_socio) -> None:
        directiva = make_socio(legajo="71019", role=Role.CD)
        member = make_socio(legajo="71020")
        expediente = ExpedienteWorkflowService.open_expediente(
            motivo="Motivo", socio_ids=[member.id], actor="71019"
        )
        api_client.force_authenticate(user=directiva.user)

        response = api_client.post(
            f"/api/v1/expedientes/{expediente.pk}/estado/",
            {"estado": EstadoExpedienteEnum.JUSTIFICANDO, "motivo": "Avance"},
            format="json",
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        expediente.refresh_from_db()
        assert expediente.estado == EstadoExpedienteEnum.CREADO

    def test_transition_rejects_skipped_states_without_audit_record(
        self, api_client: APIClient, make_socio
    ) -> None:
        tribunal = make_socio(legajo="71007", role=Role.TD)
        member = make_socio(legajo="71008")
        api_client.force_authenticate(user=tribunal.user)
        created = api_client.post(
            "/api/v1/expedientes/gestion/",
            {"motivo": "Prueba", "socios": [member.id]},
            format="json",
        ).json()

        response = api_client.post(
            f"/api/v1/expedientes/{created['id']}/estado/",
            {"estado": EstadoExpedienteEnum.ESPERA_RESOLUCION, "motivo": "Salto"},
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert CambioEstadoExpediente.objects.filter(expediente_id=created["id"]).count() == 1

    def test_next_state_records_actor_time_and_reason(
        self, api_client: APIClient, make_socio
    ) -> None:
        tribunal = make_socio(legajo="71009", role=Role.TD)
        member = make_socio(legajo="71010")
        api_client.force_authenticate(user=tribunal.user)
        created = api_client.post(
            "/api/v1/expedientes/gestion/",
            {"motivo": "Apertura", "socios": [member.id]},
            format="json",
        ).json()

        response = api_client.post(
            f"/api/v1/expedientes/{created['id']}/estado/",
            {
                "estado": EstadoExpedienteEnum.JUSTIFICANDO,
                "motivo": "Notificación despachada",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        change = CambioEstadoExpediente.objects.latest("fecha_hora")
        assert change.estado_anterior == EstadoExpedienteEnum.CREADO
        assert change.estado_nuevo == EstadoExpedienteEnum.JUSTIFICANDO
        assert change.actor == tribunal.user.username
        assert change.motivo == "Notificación despachada"
        assert change.fecha_hora

    def test_workflow_accepts_exactly_the_six_sequential_states(
        self, api_client: APIClient, make_socio
    ) -> None:
        tribunal = make_socio(legajo="71014", role=Role.TD)
        member = make_socio(legajo="71015")
        api_client.force_authenticate(user=tribunal.user)
        created = api_client.post(
            "/api/v1/expedientes/gestion/",
            {"motivo": "Recorrido", "socios": [member.id]},
            format="json",
        ).json()

        states = [
            EstadoExpedienteEnum.JUSTIFICANDO,
            EstadoExpedienteEnum.REVISION_RESOLUCION,
            EstadoExpedienteEnum.ESPERA_RESOLUCION,
            EstadoExpedienteEnum.PENDIENTE_CORREOS,
            EstadoExpedienteEnum.EMITIDO,
        ]
        for state in states:
            response = api_client.post(
                f"/api/v1/expedientes/{created['id']}/estado/",
                {"estado": state, "motivo": f"Avance a {state}"},
                format="json",
            )
            assert response.status_code == status.HTTP_200_OK
            if state == EstadoExpedienteEnum.JUSTIFICANDO:
                _expire_deadline(created["id"])

        response = api_client.post(
            f"/api/v1/expedientes/{created['id']}/estado/",
            {"estado": EstadoExpedienteEnum.EMITIDO, "motivo": "Repetición"},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert len(EstadoExpedienteEnum.choices) == 6

    def test_secondary_implicated_member_can_submit_private_descargo(
        self, api_client: APIClient, make_socio
    ) -> None:
        authority = make_socio(legajo="71011", role=Role.TD)
        first_member = make_socio(legajo="71012")
        second_member = make_socio(legajo="71013")
        api_client.force_authenticate(user=authority.user)
        created = api_client.post(
            "/api/v1/expedientes/gestion/",
            {"motivo": "Causa compartida", "socios": [first_member.id, second_member.id]},
            format="json",
        ).json()
        api_client.force_authenticate(user=authority.user)
        api_client.post(
            f"/api/v1/expedientes/{created['id']}/estado/",
            {"estado": EstadoExpedienteEnum.JUSTIFICANDO, "motivo": "Avisos enviados"},
            format="json",
        )
        api_client.force_authenticate(user=second_member.user)

        response = api_client.get("/api/v1/expedientes/mis-expedientes/")

        assert response.status_code == status.HTTP_200_OK
        assert any(item["id"] == created["id"] for item in response.json())
        response = api_client.post(
            f"/api/v1/expedientes/{created['id']}/descargo/",
            {"tipo": "T03_EXTRAORDINARIO", "texto": "Mi descargo personal."},
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert DescargoExpediente.objects.filter(
            expediente_id=created["id"], socio=second_member
        ).exists()
        response = api_client.get("/api/v1/expedientes/mis-expedientes/")
        assert response.status_code == status.HTTP_200_OK
        item = next(entry for entry in response.json() if entry["id"] == created["id"])
        assert item["descargo_texto"] == "Mi descargo personal."


@pytest.mark.django_db
def test_listing_uses_constant_queries(api_client: APIClient, make_socio) -> None:
    from django.test.utils import CaptureQueriesContext

    authority = make_socio(legajo="75001", role=Role.TD)
    members = [make_socio(legajo=f"7501{i}") for i in range(3)]
    api_client.force_authenticate(user=authority.user)

    def count_queries() -> int:
        with CaptureQueriesContext(connection) as context:
            response = api_client.get("/api/v1/expedientes/gestion/")
        assert response.status_code == status.HTTP_200_OK
        return len(context)

    ExpedienteWorkflowService.open_expediente(
        motivo="Uno", socio_ids=[members[0].id], actor="75001"
    )
    baseline = count_queries()
    for index in range(4):
        ExpedienteWorkflowService.open_expediente(
            motivo=f"Más {index}", socio_ids=[m.id for m in members], actor="75001"
        )

    assert count_queries() == baseline
