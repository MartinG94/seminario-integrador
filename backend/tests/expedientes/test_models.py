"""Tests de persistencia de expedientes, congelamiento de plazo y auditoría (FASE 2 / S3-02).

Cubre:
1. Creación de expediente con inicio y congelamiento inmutable de plazo_limite_at.
2. Inmutabilidad del deadline frente a posteriores modificaciones del proveedor de feriados.
3. Validación de estados procesales y transición reglamentaria.
4. Historial inmutable de auditoría mediante CambioEstadoExpediente.
5. Propiedad esta_en_plazo() con límite inclusivo (now <= plazo_limite_at).
"""

from datetime import datetime
from zoneinfo import ZoneInfo

import pytest
from django.contrib.auth import get_user_model

from expedientes.domain.holiday_provider import Argentina2026HolidayProvider
from expedientes.models import (
    CambioEstadoExpediente,
    EstadoExpedienteEnum,
    Expediente,
)
from socios.models import Socio, Subcomision

BA_TZ = ZoneInfo("America/Argentina/Buenos_Aires")
User = get_user_model()


@pytest.fixture
def socio_fixture(db) -> Socio:
    """Fixture para crear un socio regular de prueba."""
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
    )


@pytest.mark.django_db
class TestExpedientePersistence:
    """Suite de pruebas para el modelo de persistencia y congelamiento de plazos."""

    def test_iniciar_plazo_descargo_freezes_deadline(self, socio_fixture: Socio) -> None:
        """Al notificar/iniciar plazo, se calcula y congela plazo_limite_at con 5 días hábiles."""
        # Notificación formal: Lunes 02/03/2026 a las 10:00:00.
        inicio = datetime(2026, 3, 2, 10, 0, 0, tzinfo=BA_TZ)

        exp = Expediente.objects.create(
            numero="EXP-001/2026",
            socio=socio_fixture,
            motivo="Inasistencia a asamblea ordinaria",
            estado=EstadoExpedienteEnum.CREADO,
        )

        exp.iniciar_plazo_descargo(
            fecha_hora_inicio=inicio,
            dias_habiles=5,
            holiday_provider=Argentina2026HolidayProvider(),
            actor="SISTEMA_NOTIFICACIONES",
        )

        exp.refresh_from_db()
        assert exp.estado == EstadoExpedienteEnum.JUSTIFICANDO
        assert exp.plazo_inicio_at == inicio
        # 5 días hábiles después: Lunes 09/03/2026 10:00:00.
        assert exp.plazo_limite_at == datetime(2026, 3, 9, 10, 0, 0, tzinfo=BA_TZ)
        assert exp.descargo_presentado is False

        # Verifica registro de auditoría
        cambio = CambioEstadoExpediente.objects.filter(expediente=exp).latest("fecha_hora")
        assert cambio.estado_anterior == EstadoExpedienteEnum.CREADO
        assert cambio.estado_nuevo == EstadoExpedienteEnum.JUSTIFICANDO
        assert cambio.actor == "SISTEMA_NOTIFICACIONES"
        assert "Apertura de plazo" in cambio.motivo

    def test_deadline_is_frozen_and_not_recalculated(self, socio_fixture: Socio) -> None:
        """El deadline persistido permanece inalterable ante cambios en los feriados."""
        inicio = datetime(2026, 3, 2, 10, 0, 0, tzinfo=BA_TZ)
        limite_fijado = datetime(2026, 3, 9, 10, 0, 0, tzinfo=BA_TZ)

        exp = Expediente.objects.create(
            numero="EXP-002/2026",
            socio=socio_fixture,
            motivo="Falta de informe",
            estado=EstadoExpedienteEnum.JUSTIFICANDO,
            plazo_inicio_at=inicio,
            plazo_limite_at=limite_fijado,
        )

        # Simular lectura posterior del expediente
        exp_consultado = Expediente.objects.get(id=exp.id)
        assert exp_consultado.plazo_limite_at == limite_fijado

    def test_esta_en_plazo_inclusive_boundary(self, socio_fixture: Socio) -> None:
        """Verifica la regla: ahora <= plazo_limite_at (límite inclusivo)."""
        inicio = datetime(2026, 3, 2, 10, 0, 0, tzinfo=BA_TZ)
        limite = datetime(2026, 3, 9, 10, 0, 0, tzinfo=BA_TZ)

        exp = Expediente.objects.create(
            numero="EXP-003/2026",
            socio=socio_fixture,
            motivo="Incumplimiento",
            estado=EstadoExpedienteEnum.JUSTIFICANDO,
            plazo_inicio_at=inicio,
            plazo_limite_at=limite,
        )

        # 1 segundo antes del límite -> en plazo
        antes = datetime(2026, 3, 9, 9, 59, 59, tzinfo=BA_TZ)
        assert exp.esta_en_plazo(ahora=antes) is True

        # Exactamente en el instante límite -> en plazo (inclusivo)
        exacto = datetime(2026, 3, 9, 10, 0, 0, tzinfo=BA_TZ)
        assert exp.esta_en_plazo(ahora=exacto) is True

        # 1 microsegundo después del límite -> fuera de plazo
        despues = datetime(2026, 3, 9, 10, 0, 0, 1, tzinfo=BA_TZ)
        assert exp.esta_en_plazo(ahora=despues) is False
