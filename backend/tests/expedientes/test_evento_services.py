"""Tests unitarios TDD para servicios de Eventos, Cumplimiento, Asistencia y Notificaciones.

Cubre:
- MeetingComplianceService: preaviso de 2 días hábiles y reporte en 72 hs hábiles.
- AttendanceStrategy: Manual, Biométrico y Factory.
- AttendanceProcessingService: graduación de escala decimal (-0.5, -1.0, -1.5, -2.0),
  inhibición ante eventos no sancionables e inmutabilidad de saldos.
- MeetingNoticeNotificationService: encolado en EmailOutbox con clave de idempotencia.
"""

import zoneinfo
from datetime import date, datetime, timedelta
from decimal import Decimal

import pytest
from django.utils import timezone

from expedientes.domain.attendance_strategy import (
    AttendanceStrategyFactory,
    BiometricAttendanceStrategy,
    ManualAttendanceStrategy,
)
from expedientes.domain.holiday_provider import InMemoryHolidayProvider
from expedientes.models import (
    AsistenciaEvento,
    CategoriaEventoEnum,
    EstadoAsistenciaEventoEnum,
    EventoInstitucional,
    MetodoCapturaAsistenciaEnum,
    ModalidadEventoEnum,
    ModoConvocatoriaEnum,
    SubtipoReunionEnum,
)
from expedientes.services.attendance_processing_service import AttendanceProcessingService
from expedientes.services.meeting_compliance_service import MeetingComplianceService
from expedientes.services.meeting_notice_notification_service import (
    MeetingNoticeNotificationService,
)
from notifications.models import EmailOutbox
from socios.models import Role


@pytest.fixture
def mock_holiday_provider():
    """Feriados en memoria para pruebas deterministas."""
    feriados = {
        date(2026, 5, 25),  # Lunes 25 de mayo de 2026
        date(2026, 7, 9),  # Jueves 9 de julio de 2026
    }
    return InMemoryHolidayProvider(feriados)


@pytest.fixture
def socio_convocante(make_socio):
    return make_socio(legajo="10001", role=Role.CD)


@pytest.fixture
def socio_uno(make_socio):
    return make_socio(legajo="10002", role=Role.SOCIO)


@pytest.fixture
def socio_dos(make_socio):
    return make_socio(legajo="10003", role=Role.SOCIO)


@pytest.fixture
def socio_tres(make_socio):
    return make_socio(legajo="10004", role=Role.SOCIO)


# ==============================================================================
# 1. Tests de MeetingComplianceService (CA1 / CA2 / CA8)
# ==============================================================================


class TestMeetingComplianceService:
    """Pruebas del cálculo de plazos de preaviso y reporte."""

    def test_preaviso_valido_dos_dias_habiles_intermedios(self, mock_holiday_provider):
        """Publicado un martes a las 10:00 -> vence jueves a las 10:00."""
        tz = zoneinfo.ZoneInfo("America/Argentina/Cordoba")
        # Martes 5 de mayo de 2026
        publicacion = datetime(2026, 5, 5, 10, 0, tzinfo=tz)
        # Inicio el jueves 7 de mayo de 2026 a las 18:00 (más de 2 días hábiles)
        inicio_valido = datetime(2026, 5, 7, 18, 0, tzinfo=tz)

        es_valido, motivo = MeetingComplianceService.validate_notice_period(
            fecha_publicacion=publicacion,
            fecha_programada=inicio_valido,
            holiday_provider=mock_holiday_provider,
        )
        assert es_valido is True
        assert motivo is None

    def test_preaviso_invalido_menos_de_dos_dias_habiles(self, mock_holiday_provider):
        """Publicado un martes para el miércoles -> preaviso insuficiente."""
        tz = zoneinfo.ZoneInfo("America/Argentina/Cordoba")
        publicacion = datetime(2026, 5, 5, 10, 0, tzinfo=tz)
        inicio_invalido = datetime(2026, 5, 6, 18, 0, tzinfo=tz)

        es_valido, motivo = MeetingComplianceService.validate_notice_period(
            fecha_publicacion=publicacion,
            fecha_programada=inicio_invalido,
            holiday_provider=mock_holiday_provider,
        )
        assert es_valido is False
        assert "menos de 2 días hábiles" in motivo

    def test_preaviso_con_fin_de_semana_y_feriado(self, mock_holiday_provider):
        """Preaviso con feriado: se salta sáb, dom y lunes feriado."""
        tz = zoneinfo.ZoneInfo("America/Argentina/Cordoba")
        # Viernes 22 de mayo de 2026 a las 10:00
        publicacion = datetime(2026, 5, 22, 10, 0, tzinfo=tz)
        # Martes 26 (día 1 hábil), Miércoles 27 (día 2 hábil) -> vence miércoles a las 10:00
        inicio_martes = datetime(2026, 5, 26, 18, 0, tzinfo=tz)
        inicio_miercoles = datetime(2026, 5, 27, 11, 0, tzinfo=tz)

        valido_martes, _ = MeetingComplianceService.validate_notice_period(
            fecha_publicacion=publicacion,
            fecha_programada=inicio_martes,
            holiday_provider=mock_holiday_provider,
        )
        assert valido_martes is False  # Solo transcurrió 1 día hábil (el martes)

        valido_miercoles, _ = MeetingComplianceService.validate_notice_period(
            fecha_publicacion=publicacion,
            fecha_programada=inicio_miercoles,
            holiday_provider=mock_holiday_provider,
        )
        assert valido_miercoles is True

    def test_reporte_valido_dentro_de_72_horas_habiles_desde_cierre(self, mock_holiday_provider):
        """Reporte elevado a las 48 hs hábiles del cierre efectivo."""
        tz = zoneinfo.ZoneInfo("America/Argentina/Cordoba")
        cierre = datetime(2026, 5, 5, 20, 0, tzinfo=tz)
        reporte = datetime(2026, 5, 7, 19, 0, tzinfo=tz)  # Jueves (2 días después)

        es_valido, motivo = MeetingComplianceService.validate_reporting_deadline(
            fecha_reporte=reporte,
            fecha_hora_cierre_efectivo=cierre,
            holiday_provider=mock_holiday_provider,
        )
        assert es_valido is True
        assert motivo is None

    def test_reporte_extemporaneo_mas_de_72_horas_habiles(self, mock_holiday_provider):
        """Reporte elevado después de las 72 hs hábiles (3 días hábiles)."""
        tz = zoneinfo.ZoneInfo("America/Argentina/Cordoba")
        cierre = datetime(2026, 5, 5, 20, 0, tzinfo=tz)  # Martes 20:00
        # 3 días hábiles: Mié (1), Jue (2), Vie (3) -> Viernes 20:00
        reporte_tarde = datetime(2026, 5, 8, 21, 0, tzinfo=tz)  # Viernes 21:00

        es_valido, motivo = MeetingComplianceService.validate_reporting_deadline(
            fecha_reporte=reporte_tarde,
            fecha_hora_cierre_efectivo=cierre,
            holiday_provider=mock_holiday_provider,
        )
        assert es_valido is False
        assert "72 horas hábiles" in motivo

    def test_fallback_reporting_deadline_a_fecha_programada(self, mock_holiday_provider):
        """Si fecha_fin y fecha_hora_cierre_efectivo son None, usa fecha_programada."""
        tz = zoneinfo.ZoneInfo("America/Argentina/Cordoba")
        inicio = datetime(2026, 5, 5, 18, 0, tzinfo=tz)
        reporte = datetime(2026, 5, 7, 12, 0, tzinfo=tz)

        es_valido, motivo = MeetingComplianceService.validate_reporting_deadline(
            fecha_reporte=reporte,
            fecha_programada=inicio,
            fecha_fin=None,
            fecha_hora_cierre_efectivo=None,
            holiday_provider=mock_holiday_provider,
        )
        assert es_valido is True


# ==============================================================================
# 2. Tests de Patrón Strategy para Asistencia
# ==============================================================================


class TestAttendanceStrategies:
    """Pruebas para ManualAttendanceStrategy y BiometricAttendanceStrategy."""

    def test_manual_strategy_marks_and_unreported_absent(self):
        """ManualStrategy tipifica presentes, tardanzas y convierte no reportados en ausentes."""
        evento = EventoInstitucional(
            titulo="Reunión Prueba",
            categoria=CategoriaEventoEnum.REUNION,
            tipo=SubtipoReunionEnum.ORDINARIA,
            fecha_programada=timezone.now(),
        )
        strategy = ManualAttendanceStrategy()
        marcaciones = [
            {
                "socio_id": 1,
                "estado_asistencia": EstadoAsistenciaEventoEnum.PRESENTE,
                "motivo": "A tiempo",
            },
            {
                "socio_id": 2,
                "estado_asistencia": EstadoAsistenciaEventoEnum.TARDE_LEVE,
                "minutos_tardanza": 25,
                "motivo": "Demora bondi",
            },
        ]
        convocados = [1, 2, 3]

        records = strategy.process(
            evento=evento, marcaciones=marcaciones, convocados_ids=convocados
        )
        assert len(records) == 3

        dto_s1 = next(r for r in records if r.socio_id == 1)
        assert dto_s1.estado_asistencia == EstadoAsistenciaEventoEnum.PRESENTE
        assert dto_s1.motivo == "A tiempo"

        dto_s2 = next(r for r in records if r.socio_id == 2)
        assert dto_s2.estado_asistencia == EstadoAsistenciaEventoEnum.TARDE_LEVE
        assert dto_s2.minutos_tardanza == 25

        dto_s3 = next(r for r in records if r.socio_id == 3)
        assert dto_s3.estado_asistencia == EstadoAsistenciaEventoEnum.AUSENTE
        assert "no reportado" in dto_s3.motivo

    def test_biometric_strategy_calculates_punctuality_and_tolerances(self):
        """BiometricStrategy clasifica según minutos transcurridos desde fecha_programada."""
        ahora = timezone.now()
        evento = EventoInstitucional(
            titulo="Reunión Biometría",
            categoria=CategoriaEventoEnum.REUNION,
            tipo=SubtipoReunionEnum.ORDINARIA,
            fecha_programada=ahora,
            tolerancia_tardanza_minutos=15,
        )
        strategy = BiometricAttendanceStrategy()

        marcaciones = [
            # Socio 1: Fichó a los 10 min -> PRESENTE (dentro de tolerancia de 15)
            {
                "socio_id": 1,
                "hora_registro": ahora + timedelta(minutes=10),
                "dispositivo_id": "RELOJ_01",
            },
            # Socio 2: Fichó a los 22 min -> TARDE_LEVE (15 < 22 <= 30)
            {
                "socio_id": 2,
                "hora_registro": ahora + timedelta(minutes=22),
                "dispositivo_id": "RELOJ_01",
            },
            # Socio 3: Fichó a los 40 min -> TARDE_GRAVE (> 30)
            {
                "socio_id": 3,
                "hora_registro": ahora + timedelta(minutes=40),
                "dispositivo_id": "RELOJ_01",
            },
            # Socio 4: No fichó -> AUSENTE
            {"socio_id": 4, "hora_registro": None},
        ]

        records = strategy.process(
            evento=evento, marcaciones=marcaciones, convocados_ids=[1, 2, 3, 4]
        )
        assert len(records) == 4

        s1 = next(r for r in records if r.socio_id == 1)
        assert s1.estado_asistencia == EstadoAsistenciaEventoEnum.PRESENTE
        assert s1.metodo_captura == MetodoCapturaAsistenciaEnum.BIOMETRICO

        s2 = next(r for r in records if r.socio_id == 2)
        assert s2.estado_asistencia == EstadoAsistenciaEventoEnum.TARDE_LEVE
        assert s2.minutos_tardanza == 22

        s3 = next(r for r in records if r.socio_id == 3)
        assert s3.estado_asistencia == EstadoAsistenciaEventoEnum.TARDE_GRAVE
        assert s3.minutos_tardanza == 40

        s4 = next(r for r in records if r.socio_id == 4)
        assert s4.estado_asistencia == EstadoAsistenciaEventoEnum.AUSENTE

    def test_factory_resolves_strategy_or_raises(self):
        s_manual = AttendanceStrategyFactory.get_strategy("MANUAL")
        assert isinstance(s_manual, ManualAttendanceStrategy)

        s_bio = AttendanceStrategyFactory.get_strategy(MetodoCapturaAsistenciaEnum.BIOMETRICO)
        assert isinstance(s_bio, BiometricAttendanceStrategy)

        with pytest.raises(ValueError):
            AttendanceStrategyFactory.get_strategy("INVALID_METODO")


# ==============================================================================
# 3. Tests de AttendanceProcessingService (CA2 / CA3 / CA5 / CA9 / CA10)
# ==============================================================================


@pytest.mark.django_db
class TestAttendanceProcessingService:
    """Pruebas del orquestador transaccional de asistencias y graduación."""

    def test_reunion_sancionable_graduaciones_escala_decimal(
        self, socio_convocante, socio_uno, socio_dos, socio_tres, mock_holiday_provider
    ):
        """Verifica la escala de 0.0 (presente), -0.5 (tardanza grave) y -1.0 (falta ordinaria)."""
        tz = zoneinfo.ZoneInfo("America/Argentina/Cordoba")
        # Publicado con 3 días hábiles de preaviso
        pub = datetime(2026, 5, 5, 10, 0, tzinfo=tz)
        prog = datetime(2026, 5, 8, 18, 0, tzinfo=tz)
        cierre = datetime(2026, 5, 8, 20, 0, tzinfo=tz)
        rep = datetime(2026, 5, 9, 10, 0, tzinfo=tz)

        evento = EventoInstitucional.objects.create(
            titulo="Reunión Ordinaria Mayo",
            categoria=CategoriaEventoEnum.REUNION,
            tipo=SubtipoReunionEnum.ORDINARIA,
            modalidad=ModalidadEventoEnum.PRESENCIAL_SEDE,
            fecha_publicacion=pub,
            fecha_programada=prog,
            fecha_fin=prog + timedelta(hours=2),
            convocante=socio_convocante,
            modo_convocatoria=ModoConvocatoriaEnum.PERSONALIZADA,
            es_obligatoria=True,
        )

        marcaciones = [
            {
                "socio_id": socio_uno.id,
                "estado_asistencia": EstadoAsistenciaEventoEnum.PRESENTE,
                "motivo": "Presente",
            },
            {
                "socio_id": socio_dos.id,
                "estado_asistencia": EstadoAsistenciaEventoEnum.TARDE_GRAVE,
                "minutos_tardanza": 35,
                "motivo": "Llegó 35 min tarde",
            },
            {
                "socio_id": socio_tres.id,
                "estado_asistencia": EstadoAsistenciaEventoEnum.AUSENTE,
                "motivo": "Faltó sin aviso",
            },
        ]

        result = AttendanceProcessingService.process_event_attendance(
            evento_id=evento.id,
            marcaciones=marcaciones,
            fecha_reporte=rep,
            fecha_hora_cierre_efectivo=cierre,
            holiday_provider=mock_holiday_provider,
        )

        assert result["es_sancionable"] is True
        assert len(result["expedientes_creados"]) == 2  # socio_dos (-0.5) y socio_tres (-1.0)

        # Verificar socio_uno: sin expediente ni apercibimiento
        asist_1 = AsistenciaEvento.objects.get(evento=evento, socio=socio_uno)
        assert asist_1.expediente_generado is None
        assert asist_1.apercibimiento_generado is None

        # Verificar socio_dos: expediente de tardanza grave por -0.50
        asist_2 = AsistenciaEvento.objects.get(evento=evento, socio=socio_dos)
        assert asist_2.expediente_generado is not None
        assert asist_2.expediente_generado.puntos == Decimal("-0.50")
        assert "Llegó 35 min tarde" in asist_2.motivo

        # Verificar socio_tres: expediente por inasistencia ordinaria por -1.00
        asist_3 = AsistenciaEvento.objects.get(evento=evento, socio=socio_tres)
        assert asist_3.expediente_generado is not None
        assert asist_3.expediente_generado.puntos == Decimal("-1.00")
        assert "Faltó sin aviso" in asist_3.motivo

    def test_reunion_extraordinaria_aplica_escala_1_5_puntos(
        self, socio_convocante, socio_uno, mock_holiday_provider
    ):
        """Inasistencia a Extraordinaria genera expediente de -1.50 puntos (Art. 85.b)."""
        tz = zoneinfo.ZoneInfo("America/Argentina/Cordoba")
        pub = datetime(2026, 5, 5, 10, 0, tzinfo=tz)
        prog = datetime(2026, 5, 8, 18, 0, tzinfo=tz)

        evento = EventoInstitucional.objects.create(
            titulo="Reunión Extraordinaria de CD",
            categoria=CategoriaEventoEnum.REUNION,
            tipo=SubtipoReunionEnum.EXTRAORDINARIA,
            fecha_publicacion=pub,
            fecha_programada=prog,
            convocante=socio_convocante,
            es_obligatoria=True,
        )

        marcaciones = [
            {
                "socio_id": socio_uno.id,
                "estado_asistencia": EstadoAsistenciaEventoEnum.AUSENTE,
                "motivo": "Ausente a Extraordinaria",
            },
        ]

        result = AttendanceProcessingService.process_event_attendance(
            evento_id=evento.id,
            marcaciones=marcaciones,
            fecha_reporte=prog + timedelta(hours=12),
            holiday_provider=mock_holiday_provider,
        )

        assert result["es_sancionable"] is True
        asist = AsistenciaEvento.objects.get(evento=evento, socio=socio_uno)
        assert asist.expediente_generado.puntos == Decimal("-1.50")

    def test_asamblea_aplica_escala_2_0_puntos(
        self, socio_convocante, socio_uno, mock_holiday_provider
    ):
        """Inasistencia a Asamblea genera expediente de -2.00 puntos (Art. 85.c)."""
        tz = zoneinfo.ZoneInfo("America/Argentina/Cordoba")
        pub = datetime(2026, 5, 5, 10, 0, tzinfo=tz)
        prog = datetime(2026, 5, 8, 18, 0, tzinfo=tz)

        evento = EventoInstitucional.objects.create(
            titulo="Asamblea General Ordinaria",
            categoria=CategoriaEventoEnum.REUNION,
            tipo=SubtipoReunionEnum.ASAMBLEA,
            fecha_publicacion=pub,
            fecha_programada=prog,
            convocante=socio_convocante,
            es_obligatoria=True,
        )

        marcaciones = [
            {
                "socio_id": socio_uno.id,
                "estado_asistencia": EstadoAsistenciaEventoEnum.AUSENTE,
                "motivo": "Ausente Asamblea",
            },
        ]

        AttendanceProcessingService.process_event_attendance(
            evento_id=evento.id,
            marcaciones=marcaciones,
            fecha_reporte=prog + timedelta(hours=10),
            holiday_provider=mock_holiday_provider,
        )

        asist = AsistenciaEvento.objects.get(evento=evento, socio=socio_uno)
        assert asist.expediente_generado.puntos == Decimal("-2.00")

    def test_evento_no_sancionable_inhibe_apertura_de_expedientes_y_apercibimientos(
        self, socio_convocante, socio_uno, socio_dos, mock_holiday_provider
    ):
        """Evento extemporáneo (CA2): guarda asistencias pero 0 sanciones."""
        tz = zoneinfo.ZoneInfo("America/Argentina/Cordoba")
        # Publicado el mismo día (menos de 2 días de preaviso)
        pub = datetime(2026, 5, 5, 10, 0, tzinfo=tz)
        prog = datetime(2026, 5, 5, 18, 0, tzinfo=tz)

        evento = EventoInstitucional.objects.create(
            titulo="Reunión Imprevista Extemporánea",
            categoria=CategoriaEventoEnum.REUNION,
            tipo=SubtipoReunionEnum.ORDINARIA,
            fecha_publicacion=pub,
            fecha_programada=prog,
            convocante=socio_convocante,
            es_obligatoria=True,
        )

        marcaciones = [
            {
                "socio_id": socio_uno.id,
                "estado_asistencia": EstadoAsistenciaEventoEnum.TARDE_LEVE,
                "motivo": "Llegó tarde",
            },
            {
                "socio_id": socio_dos.id,
                "estado_asistencia": EstadoAsistenciaEventoEnum.AUSENTE,
                "motivo": "No fue",
            },
        ]

        result = AttendanceProcessingService.process_event_attendance(
            evento_id=evento.id,
            marcaciones=marcaciones,
            fecha_reporte=prog + timedelta(hours=2),
            holiday_provider=mock_holiday_provider,
        )

        assert result["es_sancionable"] is False
        assert "menos de 2 días hábiles" in result["motivo_no_sancionable"]
        assert len(result["expedientes_creados"]) == 0
        assert len(result["apercibimientos_creados"]) == 0

        # Asistencias estadísticas sin sanciones vinculadas
        asist_1 = AsistenciaEvento.objects.get(evento=evento, socio=socio_uno)
        asist_2 = AsistenciaEvento.objects.get(evento=evento, socio=socio_dos)
        assert asist_1.expediente_generado is None
        assert asist_1.apercibimiento_generado is None
        assert asist_2.expediente_generado is None
        assert asist_2.apercibimiento_generado is None


# ==============================================================================
# 4. Tests de MeetingNoticeNotificationService (CA7)
# ==============================================================================


@pytest.mark.django_db
class TestMeetingNoticeNotificationService:
    """Pruebas del encolador transaccional de correos Outbox."""

    def test_enqueue_meeting_notices_creates_outbox_with_idempotency(
        self, socio_convocante, socio_uno, socio_dos
    ):
        """Verifica la generación de correos Outbox con clave de idempotencia por socio."""
        ahora = timezone.now()
        inicio = ahora + timedelta(days=3)

        evento = EventoInstitucional.objects.create(
            titulo="Convocatoria Plenario General",
            categoria=CategoriaEventoEnum.REUNION,
            tipo=SubtipoReunionEnum.PLENARIO,
            modalidad=ModalidadEventoEnum.VIRTUAL,
            ubicacion="https://meet.google.com/aveit-test",
            fecha_publicacion=ahora,
            fecha_programada=inicio,
            convocante=socio_convocante,
            modo_convocatoria=ModoConvocatoriaEnum.PERSONALIZADA,
            es_obligatoria=True,
            es_sancionable=True,
        )

        outboxes = MeetingNoticeNotificationService.enqueue_meeting_notices(
            evento=evento,
            socios_ids=[socio_uno.id, socio_dos.id],
        )

        assert len(outboxes) == 2
        for ob in outboxes:
            assert "Convocatoria Institucional" in ob.subject
            assert "https://meet.google.com/aveit-test" in ob.body_text
            assert "OBLIGATORIA Y SANCIONABLE" in ob.body_text

        # Reintento: idempotencia no debe crear filas duplicadas
        outboxes_retry = MeetingNoticeNotificationService.enqueue_meeting_notices(
            evento=evento,
            socios_ids=[socio_uno.id, socio_dos.id],
        )
        assert len(outboxes_retry) == 2
        assert EmailOutbox.objects.filter(metadata__evento_id=evento.id).count() == 2
