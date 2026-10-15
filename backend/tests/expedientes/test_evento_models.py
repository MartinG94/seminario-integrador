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
    AtencionFelicitacion,
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
class TestAtencionFelicitacionModel:
    """Pruebas para el modelo AtencionFelicitacion (atencionFelicitacion)."""

    def test_crear_atencion_felicitacion_por_defecto(self, socio_asistente):
        """Crea un registro de atencionFelicitacion con contadores en 0."""
        registro = AtencionFelicitacion.objects.create(
            socio=socio_asistente,
        )
        assert registro.socio == socio_asistente
        assert registro.llamadosAtencion == 0
        assert registro.felicitaciones == 0
        assert registro.pendientes == 0
        assert registro.nroSocio == socio_asistente.id

    def test_incremento_llamados_y_felicitaciones(self, socio_asistente):
        """Verifica la persistencia y conteo de llamados y felicitaciones."""
        registro = AtencionFelicitacion.objects.create(
            socio=socio_asistente,
            llamadosAtencion=2,
            felicitaciones=1,
        )
        assert registro.llamadosAtencion == 2
        assert registro.felicitaciones == 1
        assert registro.pendientes == 2
        assert registro.estado == "PENDIENTE"


@pytest.mark.django_db
class TestEventoConvocadoModel:
    """Pruebas para el modelo EventoConvocado (tribunal_evento_convocado)."""

    def test_convocar_socio_a_evento_y_unicidad(self, socio_organizador, socio_asistente):
        """Verifica que un socio pueda ser convocado y no duplicarse en el mismo evento."""
        from expedientes.models import EventoConvocado
        from django.db import IntegrityError

        ahora = timezone.now()
        evento = EventoInstitucional.objects.create(
            titulo="Reunión Citación Exclusiva",
            categoria=CategoriaEventoEnum.REUNION,
            tipo=SubtipoReunionEnum.ORDINARIA,
            fecha_publicacion=ahora,
            fecha_programada=ahora + timedelta(days=3),
            convocante=socio_organizador,
            modo_convocatoria=ModoConvocatoriaEnum.PERSONALIZADA,
        )

        convocado = EventoConvocado.objects.create(
            evento=evento,
            socio=socio_asistente,
        )
        assert convocado.id is not None
        assert convocado.evento == evento
        assert convocado.socio == socio_asistente

        with pytest.raises((ValidationError, IntegrityError)):
            dup = EventoConvocado(evento=evento, socio=socio_asistente)
            dup.full_clean()
            dup.save()

