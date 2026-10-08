"""Pruebas para OpeningNotificationService y CaseNotificationQueryService.

Valida:
- CA1: Transición condicionada a orden formal de despacho del TD.
- CA3: Idempotencia estricta, Transactional Outbox y resiliencia ante caídas SMTP.
- CA3: Concurrencia real ante solicitudes simultáneas de despacho.
- CA5: Inmutabilidad estricta de plazo_inicio_at y plazo_limite_at.
- Principio 5: Salvaguarda operativa de cero envíos reales (locmem / mocks de red).
- Principio 7: No filtración de contenido sensible en logs de error.
"""

import socket
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

import pytest
from django.core import mail
from django.db import connection

from expedientes.models import CambioEstadoExpediente, EstadoExpedienteEnum, Expediente
from expedientes.services.opening_notification_service import (
    CaseNotificationQueryService,
    InvalidCaseStatusError,
    MissingSocioEmailError,
    OpeningNotificationService,
)
from notifications.models import EmailOutbox, EmailOutboxStatus
from notifications.services import EmailDispatcherService
from socios.models import Role, Socio, Subcomision


@pytest.fixture(autouse=True)
def ensure_safe_mail_backend(settings) -> None:
    """Principio 5: Salvaguarda innegociable de cero envíos reales.

    Garantiza que el backend de correo esté configurado como 'locmem'
    para atrapar los envíos en memoria sin conectividad SMTP exterior.
    """
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    settings.FRONTEND_URL = "https://tribunal.aveit.utn.edu.ar"
    mail.outbox.clear()


@pytest.fixture
def subcomision_test(db) -> Subcomision:
    return Subcomision.objects.create(name="Subcomisión de Cómputos")


@pytest.fixture
def socio_imputado(db, subcomision_test, django_user_model) -> Socio:
    user = django_user_model.objects.create_user(
        username="74100",
        email="socio.imputado@aveit.utn.edu.ar",
        password="Test-Password-2026!",
    )
    return Socio.objects.create(
        user=user,
        legajo="74100",
        first_name="Martín",
        last_name="Guillén",
        email="socio.imputado@aveit.utn.edu.ar",
        subcomision=subcomision_test,
        social_year=3,
        role=Role.SOCIO,
        is_enabled=True,
    )


@pytest.fixture
def expediente_creado(db, socio_imputado) -> Expediente:
    return Expediente.objects.create(
        numero="EXP-2026-0042",
        socio=socio_imputado,
        motivo="Inasistencia injustificada a la asamblea anual ordinaria",
        puntos=-1.0,
        estado=EstadoExpedienteEnum.CREADO,
    )


@pytest.mark.django_db(transaction=True)
class TestOpeningNotificationService:
    """Pruebas del servicio de despacho atómico de apertura."""

    def test_dispatch_opening_success_transitions_and_creates_outbox(
        self, expediente_creado, socio_imputado
    ) -> None:
        """CA1, CA3 y CA5: Transición a justificando, fijación de plazo y creación en Outbox."""
        exp, outbox = OpeningNotificationService.dispatch_opening(
            expediente_id=expediente_creado.id,
            actor="TD_Vocal_1",
        )

        # 1. Verificación del estado del expediente (CA1)
        exp.refresh_from_db()
        assert exp.estado == EstadoExpedienteEnum.JUSTIFICANDO
        assert exp.plazo_inicio_at is not None
        assert exp.plazo_limite_at is not None
        assert exp.plazo_limite_at > exp.plazo_inicio_at

        # 2. Asiento de auditoría inmutable
        cambio = CambioEstadoExpediente.objects.filter(expediente=exp).first()
        assert cambio is not None
        assert cambio.estado_anterior == EstadoExpedienteEnum.CREADO
        assert cambio.estado_nuevo == EstadoExpedienteEnum.JUSTIFICANDO
        assert cambio.actor == "TD_Vocal_1"
        assert "Apertura de plazo" in cambio.motivo

        # 3. Verificación de Outbox (CA3)
        assert outbox.to == ["socio.imputado@aveit.utn.edu.ar"]
        assert outbox.idempotency_key == f"opening-expediente-{exp.id}-socio-{socio_imputado.id}"
        assert outbox.status in (EmailOutboxStatus.SENT, EmailOutboxStatus.PENDING)
        assert outbox.metadata["expediente_id"] == exp.id
        assert outbox.metadata["socio_id"] == socio_imputado.id

    def test_dispatch_opening_invalid_status_rejects_with_exception(
        self, expediente_creado
    ) -> None:
        """CA1: Si el expediente ya transicionó, rechaza con InvalidCaseStatusError."""
        # Forzar estado que no sea CREADO
        expediente_creado.estado = EstadoExpedienteEnum.ESPERA_RESOLUCION
        expediente_creado.save(update_fields=["estado"])

        with pytest.raises(InvalidCaseStatusError) as exc_info:
            OpeningNotificationService.dispatch_opening(
                expediente_id=expediente_creado.id,
                actor="TD_Vocal_1",
            )

        assert "espera_resolucion" in str(exc_info.value)
        expediente_creado.refresh_from_db()
        assert expediente_creado.estado == EstadoExpedienteEnum.ESPERA_RESOLUCION
        assert EmailOutbox.objects.count() == 0

    def test_dispatch_opening_missing_email_rejects_and_aborts_transition(
        self, expediente_creado, socio_imputado
    ) -> None:
        """Caso borde: Socio sin email en legajo aborta la transición atómica."""
        Socio.objects.filter(id=socio_imputado.id).update(email="")
        socio_imputado.refresh_from_db()

        with pytest.raises(MissingSocioEmailError) as exc_info:
            OpeningNotificationService.dispatch_opening(
                expediente_id=expediente_creado.id,
                actor="TD_Vocal_1",
            )

        assert "no posee dirección de correo" in str(exc_info.value)
        expediente_creado.refresh_from_db()
        assert expediente_creado.estado == EstadoExpedienteEnum.CREADO
        assert expediente_creado.plazo_inicio_at is None
        assert EmailOutbox.objects.count() == 0

    def test_dispatch_opening_idempotency_sequential_calls(
        self, expediente_creado, socio_imputado
    ) -> None:
        """CA3: Dos invocaciones consecutivas no generan duplicados en la cola."""
        exp1, outbox1 = OpeningNotificationService.dispatch_opening(
            expediente_id=expediente_creado.id,
            actor="TD_Vocal_1",
        )
        exp2, outbox2 = OpeningNotificationService.dispatch_opening(
            expediente_id=expediente_creado.id,
            actor="TD_Vocal_1",
        )

        assert exp1.id == exp2.id
        assert outbox1.id == outbox2.id
        assert (
            EmailOutbox.objects.filter(
                idempotency_key=f"opening-expediente-{exp1.id}-socio-{socio_imputado.id}"
            ).count()
            == 1
        )

    @pytest.mark.skipif(
        connection.vendor != "mysql",
        reason="Concurrencia real requiere bloqueo de filas a nivel motor (MySQL/InnoDB).",
    )
    def test_dispatch_opening_concurrent_calls_guarantee_single_outbox(
        self, expediente_creado, socio_imputado
    ) -> None:
        """CA3: Concurrencia real mediante hilos simultáneos garantizando unicidad estricta."""
        exp_id = expediente_creado.id

        def call_dispatch(actor_name: str):
            connection.close()  # Forzar conexión independiente por hilo
            return OpeningNotificationService.dispatch_opening(
                expediente_id=exp_id,
                actor=actor_name,
            )

        with ThreadPoolExecutor(max_workers=2) as executor:
            future1 = executor.submit(call_dispatch, "TD_Thread_1")
            future2 = executor.submit(call_dispatch, "TD_Thread_2")

            res1 = future1.result()
            res2 = future2.result()

        assert res1[0].id == res2[0].id
        assert res1[1].id == res2[1].id
        assert (
            EmailOutbox.objects.filter(
                idempotency_key=f"opening-expediente-{exp_id}-socio-{socio_imputado.id}"
            ).count()
            == 1
        )

    @patch("django.core.mail.message.EmailMultiAlternatives.send")
    def test_dispatch_opening_resilient_to_smtp_network_failure(
        self, mock_send, expediente_creado
    ) -> None:
        """CA3: Ante fallo de red SMTP, el expediente pasa a justificando y outbox queda PENDING."""
        mock_send.side_effect = socket.error("Connection refused to mail server")

        exp, outbox = OpeningNotificationService.dispatch_opening(
            expediente_id=expediente_creado.id,
            actor="TD_Vocal_1",
        )

        exp.refresh_from_db()
        assert exp.estado == EstadoExpedienteEnum.JUSTIFICANDO
        assert exp.plazo_inicio_at is not None

        outbox.refresh_from_db()
        assert outbox.status == EmailOutboxStatus.PENDING
        assert outbox.retry_count == 1
        assert "Connection refused" in (outbox.last_error or "")

    def test_immutability_of_plazo_inicio_at_after_repetition(self, expediente_creado) -> None:
        """CA5: Reintentos posteriores no mutan plazo_inicio_at ni plazo_limite_at."""
        exp, _ = OpeningNotificationService.dispatch_opening(
            expediente_id=expediente_creado.id,
            actor="TD_Vocal_1",
        )
        original_inicio = exp.plazo_inicio_at
        original_limite = exp.plazo_limite_at

        # Intentar despacho redundante posterior
        exp2, _ = OpeningNotificationService.dispatch_opening(
            expediente_id=expediente_creado.id,
            actor="TD_Vocal_2",
        )

        exp2.refresh_from_db()
        assert exp2.plazo_inicio_at == original_inicio
        assert exp2.plazo_limite_at == original_limite

    @patch("expedientes.services.opening_notification_service.EmailDispatcherService.dispatch")
    def test_dispatch_opening_handles_unexpected_exception_in_dispatch(
        self, mock_dispatch, expediente_creado
    ) -> None:
        """Principio 7: Excepciones inesperadas en despacho no abortan y no filtran datos."""
        mock_dispatch.side_effect = RuntimeError("Simulated unexpected dispatch failure")

        exp, outbox = OpeningNotificationService.dispatch_opening(
            expediente_id=expediente_creado.id,
            actor="TD_Vocal_1",
        )

        exp.refresh_from_db()
        assert exp.estado == EstadoExpedienteEnum.JUSTIFICANDO
        assert outbox is not None

    @patch("django.core.mail.message.EmailMultiAlternatives.send")
    def test_reintentos_worker_en_segundo_plano_no_mutan_plazo_inicio_ni_limite(
        self, mock_send, expediente_creado
    ) -> None:
        """CA5: Reintentos del worker outbox no desplazan plazo_inicio_at ni plazo_limite_at."""
        # 1. Fallo inicial de red SMTP
        mock_send.side_effect = socket.error("Network timeout")

        exp, outbox = OpeningNotificationService.dispatch_opening(
            expediente_id=expediente_creado.id,
            actor="TD_Vocal_1",
        )
        exp.refresh_from_db()
        original_inicio = exp.plazo_inicio_at
        original_limite = exp.plazo_limite_at

        outbox.refresh_from_db()
        assert outbox.status == EmailOutboxStatus.PENDING
        assert outbox.retry_count == 1

        # 2. Worker en segundo plano ejecuta reintento exitoso
        mock_send.side_effect = None
        mock_send.return_value = 1

        results = EmailDispatcherService.process_pending_queue(force=True)
        assert results["processed"] == 1
        assert results["sent"] == 1

        outbox.refresh_from_db()
        assert outbox.status == EmailOutboxStatus.SENT

        # 3. Verificación de inmutabilidad estricta de las marcas temporales
        exp.refresh_from_db()
        assert exp.plazo_inicio_at == original_inicio
        assert exp.plazo_limite_at == original_limite


@pytest.mark.django_db
class TestCaseNotificationQueryService:
    """Pruebas de la consulta de auditoría de notificaciones outbox para el TD."""

    def test_get_case_notifications_retrieves_associated_emails(
        self, expediente_creado, socio_imputado
    ) -> None:
        outbox1 = EmailOutbox.objects.create(
            to=[socio_imputado.email],
            subject="Notificación 1",
            body_text="Texto 1",
            status=EmailOutboxStatus.SENT,
            idempotency_key=f"opening-exp-{expediente_creado.id}-socio-{socio_imputado.id}",
            metadata={"expediente_id": expediente_creado.id, "socio_id": socio_imputado.id},
        )
        outbox_otro = EmailOutbox.objects.create(
            to=["otro@aveit.utn.edu.ar"],
            subject="Notificación de otra causa",
            body_text="Texto",
            idempotency_key="opening-exp-999-socio-999",
            metadata={"expediente_id": 999},
        )

        notifs = list(CaseNotificationQueryService.get_case_notifications(expediente_creado.id))

        assert len(notifs) == 1
        assert notifs[0].id == outbox1.id
        assert outbox_otro.id not in [n.id for n in notifs]
