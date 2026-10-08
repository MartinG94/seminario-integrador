"""Tests de dominio y persistencia para el calendario institucional de días hábiles.

Cubre:
- CA1: Exclusión estricta de fines de semana y feriados.
- CA2: Versionado, vigencia y auditoría de cambios.
- CA3: Un plazo iniciado conserva la versión de calendario aplicada de forma inmutable.
- CA4: Zona horaria America/Argentina/Buenos_Aires preservada.
"""

from datetime import date, datetime
from zoneinfo import ZoneInfo

import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError

from expedientes.domain.holiday_provider import DbHolidayProvider
from expedientes.models import (
    CalendarioVersion,
    EstadoExpedienteEnum,
    Expediente,
    FeriadoExcepcion,
    TipoFeriadoEnum,
)
from socios.models import Role, Socio, Subcomision

User = get_user_model()
TZ_BA = ZoneInfo("America/Argentina/Buenos_Aires")


@pytest.fixture
def subcomision(db):
    return Subcomision.objects.create(name="Cómputos")


@pytest.fixture
def admin_user(db, subcomision):
    user = User.objects.create_user(
        username="admin_computos",
        email="admin@aveit.org.ar",
        password="secure_password_2026",
    )
    Socio.objects.create(
        user=user,
        first_name="Admin",
        last_name="Computos",
        legajo="ADM-001",
        email="admin@aveit.org.ar",
        subcomision=subcomision,
        social_year=4,
        role=Role.ADMIN,
        is_enabled=True,
    )
    return user


@pytest.fixture
def socio_imputado(db, subcomision):
    user = User.objects.create_user(
        username="socio_imputado",
        email="imputado@aveit.org.ar",
        password="secure_password_2026",
    )
    return Socio.objects.create(
        user=user,
        first_name="Juan",
        last_name="Perez",
        legajo="SOC-1234",
        email="imputado@aveit.org.ar",
        subcomision=subcomision,
        social_year=2,
        role=Role.SOCIO,
        is_enabled=True,
    )


@pytest.fixture
def calendario_v1(db, admin_user):
    cal, _ = CalendarioVersion.objects.get_or_create(
        version=1,
        defaults={
            "nombre": "Calendario AVEIT 2026 - Inicial",
            "vigencia_desde": date(2026, 1, 1),
            "vigencia_hasta": None,
            "activa": True,
            "motivo_cambio": "Versión inicial del calendario con feriados nacionales 2026.",
            "creado_por": admin_user,
        },
    )
    FeriadoExcepcion.objects.get_or_create(
        calendario_version=cal,
        fecha=date(2026, 10, 12),
        defaults={
            "descripcion": "Día del Respeto a la Diversidad Cultural",
            "tipo": TipoFeriadoEnum.NACIONAL,
            "es_laborable": False,
        },
    )
    return cal


@pytest.mark.django_db
class TestCalendarioVersionModel:
    def test_version_unique_constraint(self, calendario_v1, admin_user):
        """No se pueden crear dos versiones con el mismo número de versión."""
        with pytest.raises(IntegrityError):
            CalendarioVersion.objects.create(
                version=1,
                nombre="Duplicado",
                vigencia_desde=date(2026, 2, 1),
                motivo_cambio="Intento de duplicación",
                creado_por=admin_user,
            )

    def test_feriado_unique_per_version(self, calendario_v1):
        """No se puede registrar dos veces la misma fecha dentro de la misma versión."""
        with pytest.raises(IntegrityError):
            FeriadoExcepcion.objects.create(
                calendario_version=calendario_v1,
                fecha=date(2026, 10, 12),
                descripcion="Feriado duplicado",
                tipo=TipoFeriadoEnum.NACIONAL,
            )

    def test_feriado_same_date_allowed_in_different_versions(self, calendario_v1, admin_user):
        """La misma fecha puede existir en versiones distintas de calendario."""
        v2 = CalendarioVersion.objects.create(
            version=2,
            nombre="Calendario AVEIT 2026 - v2",
            vigencia_desde=date(2026, 10, 1),
            motivo_cambio="Revisión de feriados de octubre.",
            creado_por=admin_user,
        )
        f2 = FeriadoExcepcion.objects.create(
            calendario_version=v2,
            fecha=date(2026, 10, 12),
            descripcion="Día del Respeto a la Diversidad Cultural (revalidado)",
            tipo=TipoFeriadoEnum.NACIONAL,
        )
        assert f2.id is not None


@pytest.mark.django_db
class TestDbHolidayProvider:
    def test_is_holiday_detects_configured_date(self, calendario_v1):
        provider = DbHolidayProvider(version=calendario_v1)
        assert provider.is_holiday(date(2026, 10, 12)) is True
        assert provider.is_holiday(date(2026, 10, 13)) is False


@pytest.mark.django_db
class TestExpedienteCalendarVersionImmutability:
    def test_iniciar_plazo_freezes_calendar_version(
        self, db, socio_imputado, calendario_v1, admin_user
    ):
        """CA3: Al iniciar un plazo, se congela la versión aplicada de forma inmutable."""
        exp = Expediente.objects.create(
            numero="EXP-001/2026",
            socio=socio_imputado,
            motivo="Inasistencia a jornada",
            estado=EstadoExpedienteEnum.CREADO,
        )

        start_time = datetime(2026, 10, 8, 14, 30, tzinfo=TZ_BA)
        deadline = exp.iniciar_plazo_descargo(
            fecha_hora_inicio=start_time,
            dias_habiles=5,
            calendario_version=calendario_v1,
        )

        exp.refresh_from_db()
        assert exp.calendario_version == calendario_v1
        assert exp.plazo_inicio_at == start_time
        assert exp.plazo_limite_at == deadline

        # Cómputo:
        # Jueves 08/10 -> día 1: Viernes 09/10
        # Sábado 10/10 (inhábil)
        # Domingo 11/10 (inhábil)
        # Lunes 12/10 (feriado en v1 -> inhábil)
        # día 2: Martes 13/10
        # día 3: Miércoles 14/10
        # día 4: Jueves 15/10
        # día 5: Viernes 16/10 a las 14:30
        assert deadline == datetime(2026, 10, 16, 14, 30, tzinfo=TZ_BA)

        # Ahora creamos una nueva versión v2 donde el lunes 12/10 NO es feriado
        v2 = CalendarioVersion.objects.create(
            version=2,
            nombre="Calendario AVEIT 2026 - v2 sin feriado 12/10",
            vigencia_desde=date(2026, 10, 10),
            activa=True,
            motivo_cambio="Reclasificación de feriado 12 de octubre",
            creado_por=admin_user,
        )
        assert v2.version == 2
        calendario_v1.activa = False
        calendario_v1.save(update_fields=["activa"])

        # Verificar que el expediente mantiene la versión v1 y su plazo original intacto
        exp.refresh_from_db()
        assert exp.calendario_version == calendario_v1
        assert exp.plazo_limite_at == datetime(2026, 10, 16, 14, 30, tzinfo=TZ_BA)

    def test_iniciar_plazo_default_uses_active_version(self, db, socio_imputado, calendario_v1):
        """Si no se pasa versión explícita, se toma la versión activa de la BD."""
        exp = Expediente.objects.create(
            numero="EXP-002/2026",
            socio=socio_imputado,
            motivo="Demora injustificada",
            estado=EstadoExpedienteEnum.CREADO,
        )
        start_time = datetime(2026, 10, 8, 9, 0, 0, tzinfo=TZ_BA)
        deadline = exp.iniciar_plazo_descargo(
            fecha_hora_inicio=start_time,
            dias_habiles=5,
        )
        exp.refresh_from_db()
        assert exp.calendario_version == calendario_v1
        assert exp.plazo_limite_at == deadline
        assert deadline.tzinfo == TZ_BA
        assert deadline.time() == start_time.time()
