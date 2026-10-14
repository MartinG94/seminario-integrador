"""Tests unitarios TDD para modelos ORM de Eventos, Asistencias y Apercibimientos.

Cubre:
- EventoInstitucional: categorías, subtipos, modalidades, fecha_fin opcional.
- AsistenciaEvento: captura, motivo circunstanciado y unicidad por socio/evento.
- RegistroApercibimiento: libro mayor, PENDIENTE/CONSOLIDADO y terna.
- Aliases retrocompatibles: Reunion y AsistenciaReunion.
"""

import uuid
from datetime import timedelta
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone

from expedientes.models import (
    AsistenciaEvento,
    AsistenciaReunion,
    CategoriaEventoEnum,
    EstadoAsistenciaEventoEnum,
    EstadoEventoEnum,
    EstadoExpedienteEnum,
    EventoInstitucional,
    Expediente,
    MetodoCapturaAsistenciaEnum,
    ModalidadEventoEnum,
    ModoConvocatoriaEnum,
    RegistroApercibimiento,
    Reunion,
    SubtipoActividadEnum,
    SubtipoReunionEnum,
)
from socios.models import Role


@pytest.fixture
def socio_organizador(make_socio):
    """Crea un socio activo para pruebas de convocante."""
    return make_socio(legajo="9901", role=Role.CD)


@pytest.fixture
def socio_asistente(make_socio):
    """Crea un socio asistente para pruebas de asistencia."""
    return make_socio(legajo="9902", role=Role.SOCIO)


@pytest.mark.django_db
class TestEventoInstitucionalModel:
    """Pruebas para el modelo EventoInstitucional."""

    def test_crear_reunion_valida_con_fecha_fin_opcional(self, socio_organizador):
        """Verifica la creación exitosa de una reunión con fecha_fin opcional (None)."""
        ahora = timezone.now()
        inicio = ahora + timedelta(days=3)

        evento = EventoInstitucional(
            titulo="Reunión Ordinaria de Cómputos",
            categoria=CategoriaEventoEnum.REUNION,
            tipo=SubtipoReunionEnum.ORDINARIA,
            modalidad=ModalidadEventoEnum.PRESENCIAL_SEDE,
            fecha_publicacion=ahora,
            fecha_programada=inicio,
            fecha_fin=None,  # Opcional
            convocante=socio_organizador,
            modo_convocatoria=ModoConvocatoriaEnum.GRUPO,
            grupo_convocado="G58",
        )
        evento.full_clean()
        evento.save()

        assert evento.id is not None
        assert evento.fecha_fin is None
        assert evento.categoria == CategoriaEventoEnum.REUNION
        assert evento.tipo == SubtipoReunionEnum.ORDINARIA
        assert evento.modalidad == ModalidadEventoEnum.PRESENCIAL_SEDE
        assert evento.lugar == "Sede Central AVEIT"
        assert evento.estado == EstadoEventoEnum.PROGRAMADA

    def test_crear_actividad_operativa_valida(self, socio_organizador):
        """Verifica la creación exitosa de una actividad operativa con modalidad externa."""
        ahora = timezone.now()
        inicio = ahora + timedelta(days=4)
        fin = inicio + timedelta(hours=3)

        actividad = EventoInstitucional(
            titulo="Jornada de Mantenimiento y Pintura",
            categoria=CategoriaEventoEnum.ACTIVIDAD,
            tipo=SubtipoActividadEnum.MANTENIMIENTO,
            modalidad=ModalidadEventoEnum.PRESENCIAL_EXTERNA,
            ubicacion="Predio Deportivo UTN - Cancha 2",
            lugar="Predio Deportivo",
            fecha_publicacion=ahora,
            fecha_programada=inicio,
            fecha_fin=fin,
            convocante=socio_organizador,
            modo_convocatoria=ModoConvocatoriaEnum.SUBCOMISION,
        )
        actividad.full_clean()
        actividad.save()

        assert actividad.id is not None
        assert actividad.categoria == CategoriaEventoEnum.ACTIVIDAD
        assert actividad.tipo == SubtipoActividadEnum.MANTENIMIENTO
        assert actividad.modalidad == ModalidadEventoEnum.PRESENCIAL_EXTERNA
        assert actividad.ubicacion == "Predio Deportivo UTN - Cancha 2"

    def test_rechazo_tipo_incoherente_con_categoria(self, socio_organizador):
        """Rechaza si se asigna un subtipo de actividad a una categoría REUNIÓN."""
        ahora = timezone.now()
        inicio = ahora + timedelta(days=3)

        evento_incoherente = EventoInstitucional(
            titulo="Reunión Inválida con tipo de Actividad",
            categoria=CategoriaEventoEnum.REUNION,
            tipo=SubtipoActividadEnum.MANTENIMIENTO,  # Incoherente
            modalidad=ModalidadEventoEnum.PRESENCIAL_SEDE,
            fecha_publicacion=ahora,
            fecha_programada=inicio,
            convocante=socio_organizador,
        )

        with pytest.raises(ValidationError) as exc_info:
            evento_incoherente.full_clean()

        assert "tipo" in exc_info.value.message_dict

    def test_rechazo_fecha_fin_anterior_a_fecha_programada(self, socio_organizador):
        """Rechaza cuando fecha_fin es anterior a fecha_programada."""
        ahora = timezone.now()
        inicio = ahora + timedelta(days=3)
        fin_invalida = inicio - timedelta(hours=1)

        evento_error = EventoInstitucional(
            titulo="Reunión con Fin Anterior",
            categoria=CategoriaEventoEnum.REUNION,
            tipo=SubtipoReunionEnum.EXTRAORDINARIA,
            fecha_publicacion=ahora,
            fecha_programada=inicio,
            fecha_fin=fin_invalida,
            convocante=socio_organizador,
        )

        with pytest.raises(ValidationError) as exc_info:
            evento_error.full_clean()

        assert "fecha_fin" in exc_info.value.message_dict

    def test_rechazo_fecha_publicacion_posterior_a_fecha_programada(self, socio_organizador):
        """Rechaza cuando fecha_publicacion es posterior a fecha_programada."""
        ahora = timezone.now()
        inicio = ahora - timedelta(hours=2)

        evento_error = EventoInstitucional(
            titulo="Reunión Publicada en el Pasado",
            categoria=CategoriaEventoEnum.REUNION,
            tipo=SubtipoReunionEnum.ORDINARIA,
            fecha_publicacion=ahora,
            fecha_programada=inicio,
            convocante=socio_organizador,
        )

        with pytest.raises(ValidationError) as exc_info:
            evento_error.full_clean()

        assert "fecha_publicacion" in exc_info.value.message_dict

    def test_modalidad_virtual_con_enlace(self, socio_organizador):
        """Verifica la configuración de una reunión virtual con enlace telemático."""
        ahora = timezone.now()
        inicio = ahora + timedelta(days=3)

        reunion_virtual = EventoInstitucional(
            titulo="Plenario Virtual de Directiva",
            categoria=CategoriaEventoEnum.REUNION,
            tipo=SubtipoReunionEnum.PLENARIO,
            modalidad=ModalidadEventoEnum.VIRTUAL,
            ubicacion="https://meet.google.com/aveit-scrum-50",
            fecha_publicacion=ahora,
            fecha_programada=inicio,
            convocante=socio_organizador,
        )
        reunion_virtual.full_clean()
        reunion_virtual.save()

        assert reunion_virtual.modalidad == ModalidadEventoEnum.VIRTUAL
        assert "meet.google.com" in reunion_virtual.ubicacion

    def test_alias_retrocompatibles_reunion(self):
        """Verifica que Reunion sea un alias exacto de EventoInstitucional."""
        assert Reunion is EventoInstitucional
        assert AsistenciaReunion is AsistenciaEvento


@pytest.mark.django_db
class TestAsistenciaEventoModel:
    """Pruebas para el modelo AsistenciaEvento."""

    def test_crear_asistencia_con_motivo_circunstanciado(self, socio_organizador, socio_asistente):
        """Verifica la persistencia de asistencia con motivo circunstanciado individual."""
        ahora = timezone.now()
        evento = EventoInstitucional.objects.create(
            titulo="Reunión Ordinaria",
            categoria=CategoriaEventoEnum.REUNION,
            tipo=SubtipoReunionEnum.ORDINARIA,
            fecha_publicacion=ahora,
            fecha_programada=ahora + timedelta(days=3),
            convocante=socio_organizador,
        )

        asistencia = AsistenciaEvento(
            evento=evento,
            socio=socio_asistente,
            estado_asistencia=EstadoAsistenciaEventoEnum.PRESENTE,
            hora_registro=ahora + timedelta(days=3, minutes=5),
            metodo_captura=MetodoCapturaAsistenciaEnum.MANUAL,
            motivo="Presente dentro de los 15 minutos de tolerancia reglamentaria.",
        )
        asistencia.full_clean()
        asistencia.save()

        assert asistencia.id is not None
        assert asistencia.motivo == "Presente dentro de los 15 minutos de tolerancia reglamentaria."
        assert asistencia.procesado_disciplinario is False

    def test_unicidad_asistencia_por_evento_y_socio(self, socio_organizador, socio_asistente):
        """No se pueden duplicar registros de asistencia para el mismo socio y evento."""
        ahora = timezone.now()
        evento = EventoInstitucional.objects.create(
            titulo="Reunión Test Duplicado",
            categoria=CategoriaEventoEnum.REUNION,
            tipo=SubtipoReunionEnum.ORDINARIA,
            fecha_publicacion=ahora,
            fecha_programada=ahora + timedelta(days=3),
            convocante=socio_organizador,
        )

        AsistenciaEvento.objects.create(
            evento=evento,
            socio=socio_asistente,
            estado_asistencia=EstadoAsistenciaEventoEnum.PRESENTE,
            motivo="Primera marcación",
        )

        asistencia_duplicada = AsistenciaEvento(
            evento=evento,
            socio=socio_asistente,
            estado_asistencia=EstadoAsistenciaEventoEnum.AUSENTE,
            motivo="Segunda marcación duplicada",
        )

        with pytest.raises(ValidationError):
            asistencia_duplicada.full_clean()


@pytest.mark.django_db
class TestRegistroApercibimientoModel:
    """Pruebas para el modelo RegistroApercibimiento."""

    def test_crear_apercibimiento_pendiente(self, socio_asistente):
        """Crea un apercibimiento en estado PENDIENTE."""
        apercibimiento = RegistroApercibimiento(
            socio=socio_asistente,
            origen_tipo="REUNION_TARDANZA_LEVE",
            fecha_hecho=timezone.now().date(),
            motivo="Tardanza leve de 20 minutos en Reunión Ordinaria (Art. 100.a).",
            articulo_reglamento="Art. 100.a",
        )
        apercibimiento.full_clean()
        apercibimiento.save()

        assert apercibimiento.id is not None
        assert apercibimiento.estado == "PENDIENTE"
        assert apercibimiento.lote_consolidacion is None
        assert apercibimiento.expediente_sancion is None

    def test_consolidacion_valida_con_uuid_y_expediente(self, socio_asistente, socio_organizador):
        """Verifica que el estado CONSOLIDADO requiera lote_consolidacion y expediente_sancion."""
        expediente = Expediente.objects.create(
            numero="EXP-2026-9999",
            socio=socio_asistente,
            estado=EstadoExpedienteEnum.CREADO,
            puntos=Decimal("-1.00"),
            motivo="Acumulación de tres apercibimientos (Art. 83 R.I.)",
        )

        lote = uuid.uuid4()
        apercibimiento = RegistroApercibimiento(
            socio=socio_asistente,
            origen_tipo="REUNION_TARDANZA_LEVE",
            fecha_hecho=timezone.now().date(),
            motivo="Tardanza consolidada en terna",
            estado="CONSOLIDADO",
            lote_consolidacion=lote,
            expediente_sancion=expediente,
            fecha_consolidacion=timezone.now(),
        )
        apercibimiento.full_clean()
        apercibimiento.save()

        assert apercibimiento.estado == "CONSOLIDADO"
        assert apercibimiento.lote_consolidacion == lote
        assert apercibimiento.expediente_sancion == expediente

    def test_rechazo_consolidado_sin_lote_o_expediente(self, socio_asistente):
        """Rechaza estado CONSOLIDADO si falta lote_consolidacion o expediente_sancion."""
        apercibimiento_invalido = RegistroApercibimiento(
            socio=socio_asistente,
            origen_tipo="REUNION_TARDANZA_LEVE",
            fecha_hecho=timezone.now().date(),
            motivo="Consolidación incompleta",
            estado="CONSOLIDADO",
            lote_consolidacion=None,
            expediente_sancion=None,
        )

        with pytest.raises(ValidationError):
            apercibimiento_invalido.full_clean()
