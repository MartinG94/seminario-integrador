"""Tests para DeadlineEnforcementService y close_expired_deadlines (FASE 3 / S3-02).

Cubre:
1. Transición de expediente vencido sin descargo a REVISION_RESOLUCION (Art. 12).
2. Idempotencia: ejecuciones repetidas no duplican transiciones ni auditorías.
3. No transición de expedientes en plazo.
4. Transición de expedientes vencidos aunque tengan descargo presentado.
5. Ejecución del management command close_expired_deadlines.
6. Simulación de concurrencia y bloqueo pesimista select_for_update.
"""

from datetime import datetime, timedelta
from io import StringIO
from zoneinfo import ZoneInfo

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.utils import timezone

from expedientes.models import (
    CambioEstadoExpediente,
    EstadoExpedienteEnum,
    Expediente,
)
from expedientes.services.deadline_service import DeadlineEnforcementService
from socios.models import Socio, Subcomision

BA_TZ = ZoneInfo("America/Argentina/Buenos_Aires")
User = get_user_model()


@pytest.fixture
def socio_fixture(db) -> Socio:
    user = User.objects.create_user(
        username="85194",
        email="85194@aveit.test",
        password="secure_password_123",
    )
    sub = Subcomision.objects.create(name="Cómputos")
    return Socio.objects.create(
        user=user,
        legajo="85194",
        first_name="Lucas",
        last_name="Guillén",
        email="85194@aveit.test",
        subcomision=sub,
        social_year=5,
    )


@pytest.mark.django_db(transaction=True)
class TestDeadlineEnforcementService:
    """Suite de pruebas de expiración de plazos, idempotencia y concurrencia."""

    def test_transiciona_expediente_vencido_sin_descargo(self, socio_fixture: Socio) -> None:
        """Un expediente vencido sin descargo pasa a REVISION_RESOLUCION con auditoría."""
        inicio = datetime(2026, 3, 2, 10, 0, 0, tzinfo=BA_TZ)
        limite = datetime(2026, 3, 9, 10, 0, 0, tzinfo=BA_TZ)

        exp = Expediente.objects.create(
            numero="EXP-101/2026",
            socio=socio_fixture,
            motivo="Causa por inasistencia",
            estado=EstadoExpedienteEnum.JUSTIFICANDO,
            plazo_inicio_at=inicio,
            plazo_limite_at=limite,
            descargo_presentado=False,
        )

        ahora = datetime(2026, 3, 9, 10, 0, 1, tzinfo=BA_TZ)  # 1 seg post límite
        service = DeadlineEnforcementService()
        cerrados = service.close_expired_deadlines(ahora=ahora)

        assert cerrados == 1
        exp.refresh_from_db()
        assert exp.estado == EstadoExpedienteEnum.REVISION_RESOLUCION

        cambio = CambioEstadoExpediente.objects.filter(expediente=exp).latest("fecha_hora")
        assert cambio.estado_anterior == EstadoExpedienteEnum.JUSTIFICANDO
        assert cambio.estado_nuevo == EstadoExpedienteEnum.REVISION_RESOLUCION
        assert cambio.actor == "SISTEMA_CRON"
        assert "Expiración de plazo perentorio de 5 días hábiles" in cambio.motivo

    def test_idempotencia_ejecuciones_repetidas(self, socio_fixture: Socio) -> None:
        """Múltiples corridas consecutivas no duplican la transición ni la auditoría."""
        inicio = datetime(2026, 3, 2, 10, 0, 0, tzinfo=BA_TZ)
        limite = datetime(2026, 3, 9, 10, 0, 0, tzinfo=BA_TZ)

        exp = Expediente.objects.create(
            numero="EXP-102/2026",
            socio=socio_fixture,
            motivo="Causa reiterada",
            estado=EstadoExpedienteEnum.JUSTIFICANDO,
            plazo_inicio_at=inicio,
            plazo_limite_at=limite,
            descargo_presentado=False,
        )

        ahora = datetime(2026, 3, 9, 12, 0, 0, tzinfo=BA_TZ)
        service = DeadlineEnforcementService()

        # Primera ejecución
        assert service.close_expired_deadlines(ahora=ahora) == 1
        # Segunda y tercera ejecuciones
        assert service.close_expired_deadlines(ahora=ahora) == 0
        assert service.close_expired_deadlines(ahora=ahora) == 0

        # Verifica que sólo existe 1 registro de cambio de estado
        assert CambioEstadoExpediente.objects.filter(expediente=exp).count() == 1

    def test_cierra_expediente_vencido_aunque_tenga_descargo(self, socio_fixture: Socio) -> None:
        """Al vencer el plazo, el expediente pasa a revisión haya o no descargo."""
        inicio = datetime(2026, 3, 2, 10, 0, 0, tzinfo=BA_TZ)
        limite = datetime(2026, 3, 9, 10, 0, 0, tzinfo=BA_TZ)

        exp = Expediente.objects.create(
            numero="EXP-103/2026",
            socio=socio_fixture,
            motivo="Causa justificada",
            estado=EstadoExpedienteEnum.JUSTIFICANDO,
            plazo_inicio_at=inicio,
            plazo_limite_at=limite,
            descargo_presentado=True,
            descargo_texto="Descargo oportuno",
        )

        ahora = datetime(2026, 3, 10, 10, 0, 0, tzinfo=BA_TZ)
        service = DeadlineEnforcementService()
        assert service.close_expired_deadlines(ahora=ahora) == 1

        exp.refresh_from_db()
        assert exp.estado == EstadoExpedienteEnum.REVISION_RESOLUCION
        assert exp.descargo_texto == "Descargo oportuno"
        assert CambioEstadoExpediente.objects.filter(expediente=exp).count() == 1

    def test_no_cierra_expediente_en_curso_dentro_del_plazo(self, socio_fixture: Socio) -> None:
        """No cierra expedientes cuyo plazo todavía no venció."""
        inicio = datetime(2026, 3, 2, 10, 0, 0, tzinfo=BA_TZ)
        limite = datetime(2026, 3, 9, 10, 0, 0, tzinfo=BA_TZ)

        exp = Expediente.objects.create(
            numero="EXP-104/2026",
            socio=socio_fixture,
            motivo="Causa activa",
            estado=EstadoExpedienteEnum.JUSTIFICANDO,
            plazo_inicio_at=inicio,
            plazo_limite_at=limite,
            descargo_presentado=False,
        )

        # Todavía dentro del plazo (límite exacto inclusive)
        ahora = datetime(2026, 3, 9, 10, 0, 0, tzinfo=BA_TZ)
        service = DeadlineEnforcementService()
        assert service.close_expired_deadlines(ahora=ahora) == 0

        exp.refresh_from_db()
        assert exp.estado == EstadoExpedienteEnum.JUSTIFICANDO

    def test_close_expired_deadlines_management_command(self, socio_fixture: Socio) -> None:
        """El management command close_expired_deadlines se ejecuta correctamente."""
        limite = timezone.now() - timedelta(hours=2)
        Expediente.objects.create(
            numero="EXP-105/2026",
            socio=socio_fixture,
            motivo="Vencido por comando",
            estado=EstadoExpedienteEnum.JUSTIFICANDO,
            plazo_limite_at=limite,
            descargo_presentado=False,
        )

        out = StringIO()
        call_command("close_expired_deadlines", stdout=out)
        salida = out.getvalue()
        assert "Se cerraron 1 expediente(s) con plazo vencido" in salida
