"""Pruebas unitarias de integración para seeds de eventos, asistencias y apercibimientos (Spec 005).

Verifica:
1. Siembra consistente de los casos testigo institucionales:
   - Reunión Ordinaria en Sede convocada por Grupo G58.
   - Reunión Extraordinaria Virtual con Meet convocada por Subcomisión Cómputos.
   - Jornada de Mantenimiento Externa convocada por listas ad-hoc con fecha fin opcional (None).
2. Asistencias individuales con motivos explicativos circunstanciados y capturas manual/biométrica.
3. Libro mayor de apercibimientos: casos PENDIENTES (terna 3:1 de CA4) y CONSOLIDADOS históricos.
4. Idempotencia estricta en ejecuciones repetidas.
"""

import pytest
from django.core.management import call_command

from expedientes.models import (
    AsistenciaEvento,
    CategoriaEventoEnum,
    EstadoAsistenciaEventoEnum,
    EstadoEventoEnum,
    EstadoRegistroApercibimientoEnum,
    EventoInstitucional,
    MetodoCapturaAsistenciaEnum,
    ModalidadEventoEnum,
    ModoConvocatoriaEnum,
    RegistroApercibimiento,
    SubtipoActividadEnum,
    SubtipoReunionEnum,
)


@pytest.fixture(autouse=True)
def run_seed_data(db):
    """Ejecuta seed_production_data asegurando estado representativo en la BD."""
    call_command("seed_production_data")


@pytest.mark.django_db
class TestSeedEventosYAsistencias:
    """Verifica que el seed inicial cumpla con todos los requisitos de datos institucionales."""

    def test_reunion_ordinaria_g58_sembrada(self):
        """Verifica la reunión ordinaria en sede para Grupo G58 con sus 4 asistencias."""
        reunion = EventoInstitucional.objects.filter(
            titulo="Reunión Ordinaria Mensual de Grupo G58"
        ).first()
        assert reunion is not None
        assert reunion.categoria == CategoriaEventoEnum.REUNION
        assert reunion.tipo == SubtipoReunionEnum.ORDINARIA
        assert reunion.modalidad == ModalidadEventoEnum.PRESENCIAL_SEDE
        assert reunion.estado == EstadoEventoEnum.CERRADA
        assert reunion.modo_convocatoria == ModoConvocatoriaEnum.GRUPO
        assert reunion.grupo_convocado == "G58"
        assert reunion.es_sancionable is True
        assert reunion.fecha_fin is not None

        # Asistencias asociadas (4 socios de G58)
        asistencias = AsistenciaEvento.objects.filter(evento=reunion)
        assert asistencias.count() == 4

        estados = {a.socio.legajo: a.estado_asistencia for a in asistencias}
        assert estados["770005"] == EstadoAsistenciaEventoEnum.PRESENTE
        assert estados["770006"] == EstadoAsistenciaEventoEnum.TARDE_LEVE
        assert estados["770007"] == EstadoAsistenciaEventoEnum.AUSENTE
        assert estados["770008"] == EstadoAsistenciaEventoEnum.PRESENTE

        # Verificar motivos circunstanciados no vacíos
        for a in asistencias:
            assert len(a.motivo.strip()) > 0

        # Verificar marcación biométrica en Héctor
        asist_hector = asistencias.get(socio__legajo="770008")
        assert asist_hector.metodo_captura == MetodoCapturaAsistenciaEnum.BIOMETRICO
        assert asist_hector.dispositivo_id == "BIO-SEDE-01"

    def test_reunion_extraordinaria_virtual_sembrada(self):
        """Verifica la reunión extraordinaria virtual con enlace telemático Meet."""
        reunion = EventoInstitucional.objects.filter(
            titulo="Reunión Extraordinaria de Coordinación Técnica de Cómputos"
        ).first()
        assert reunion is not None
        assert reunion.categoria == CategoriaEventoEnum.REUNION
        assert reunion.tipo == SubtipoReunionEnum.EXTRAORDINARIA
        assert reunion.modalidad == ModalidadEventoEnum.VIRTUAL
        assert reunion.estado == EstadoEventoEnum.PROGRAMADA
        assert reunion.modo_convocatoria == ModoConvocatoriaEnum.SUBCOMISION
        assert reunion.subcomision.name == "Cómputos"
        assert "meet.google.com" in reunion.ubicacion

    def test_jornada_mantenimiento_externa_fecha_fin_opcional(self):
        """Verifica jornada externa con convocatoria ad-hoc y fecha_fin opcional (CA8)."""
        actividad = EventoInstitucional.objects.filter(
            titulo="Jornada Operativa de Mantenimiento en Predio Deportivo"
        ).first()
        assert actividad is not None
        assert actividad.categoria == CategoriaEventoEnum.ACTIVIDAD
        assert actividad.tipo == SubtipoActividadEnum.MANTENIMIENTO
        assert actividad.modalidad == ModalidadEventoEnum.PRESENCIAL_EXTERNA
        assert actividad.fecha_fin is None  # Estrictamente opcional conforme a CA8
        assert actividad.modo_convocatoria == ModoConvocatoriaEnum.PERSONALIZADA
        assert actividad.estado == EstadoEventoEnum.CERRADA

        # Asistencias convocadas ad-hoc
        asistencias = AsistenciaEvento.objects.filter(evento=actividad)
        assert asistencias.count() == 4
        legajos = {a.socio.legajo for a in asistencias}
        assert legajos == {"770009", "770013", "770017", "74907"}

        # Verificar retiro anticipado leve de Malena Marea
        asist_malena = asistencias.get(socio__legajo="770013")
        assert asist_malena.estado_asistencia == EstadoAsistenciaEventoEnum.RETIRO_ANTICIPADO_LEVE
        assert asist_malena.minutos_retiro_anticipado == 25
        assert len(asist_malena.motivo.strip()) > 0

    def test_libro_mayor_apercibimientos_y_terna_3_a_1(self):
        """Verifica casos testigo de apercibimientos pendientes y terna consolidada."""
        # 1. Apercibimiento derivado de asistencia para Félix Fábula
        aperc_felix = RegistroApercibimiento.objects.filter(
            socio__legajo="770006",
            origen_tipo="REUNION_TARDANZA_LEVE",
        ).first()
        assert aperc_felix is not None
        assert aperc_felix.estado == EstadoRegistroApercibimientoEnum.PENDIENTE
        assert aperc_felix.asistencia is not None
        assert aperc_felix.asistencia.socio.legajo == "770006"

        # 2. Dos apercibimientos pendientes para Malena Marea (G60) listos para regla 3:1 (CA4)
        pendientes_malena = RegistroApercibimiento.objects.filter(
            socio__legajo="770013",
            estado=EstadoRegistroApercibimientoEnum.PENDIENTE,
        )
        assert pendientes_malena.count() == 2

        # 3. Terna consolidada histórica para Lucas Gastiaburu
        consolidados_lucas = RegistroApercibimiento.objects.filter(
            socio__legajo="74907",
            estado=EstadoRegistroApercibimientoEnum.CONSOLIDADO,
        )
        assert consolidados_lucas.count() == 3
        lote_id = consolidados_lucas.first().lote_consolidacion
        assert lote_id is not None
        for a in consolidados_lucas:
            assert a.lote_consolidacion == lote_id
            assert a.expediente_sancion is not None
            assert a.expediente_sancion.numero == "EXP-2026-001"

    def test_seed_idempotencia_total(self):
        """Verifica que ejecutar seed_production_data repetidamente no genere duplicados."""
        eventos_before = EventoInstitucional.objects.count()
        asistencias_before = AsistenciaEvento.objects.count()
        apercibimientos_before = RegistroApercibimiento.objects.count()

        # Segunda ejecución
        call_command("seed_production_data")

        assert EventoInstitucional.objects.count() == eventos_before
        assert AsistenciaEvento.objects.count() == asistencias_before
        assert RegistroApercibimiento.objects.count() == apercibimientos_before

    def test_comando_seed_eventos_asistencias_independiente(self):
        """Verifica la ejecución del comando específico seed_eventos_asistencias."""
        call_command("seed_eventos_asistencias")
        assert EventoInstitucional.objects.count() >= 3
        assert AsistenciaEvento.objects.count() >= 8
        assert RegistroApercibimiento.objects.count() >= 6
