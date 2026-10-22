"""Serializadores para Eventos Institucionales, Asistencias y Apercibimientos (CA1 a CA10).

Implementa:
- EventoInstitucionalSerializer: Serialización completa con totales y convocados.
- EventoInstitucionalCreateSerializer: Validación de categorías, coherencia de subtipos,
  modalidad, ubicación requerida según modalidad, fecha fin opcional >= fecha programada,
  y despacho transaccional de convocatorias y notificaciones outbox.
- AsistenciaEventoSerializer: Serialización individual con motivo circunstanciado (CA10).
- AsistenciaEventoBulkUpdateSerializer / ReportarAsistenciaSerializer: Validación de motivo
  obligatorio/editable por convocado y procesamiento con AttendanceProcessingService.
- RegistroApercibimientoSerializer: Serialización del libro mayor de apercibimientos y regla 3:1.
"""

import logging
from typing import Any

from django.utils import timezone
from rest_framework import serializers

from expedientes.models import (
    AsistenciaEvento,
    AtencionFelicitacion,
    CategoriaEventoEnum,
    EstadoAsistenciaEventoEnum,
    EstadoEventoEnum,
    EventoConvocado,
    EventoInstitucional,
    MetodoCapturaAsistenciaEnum,
    ModalidadEventoEnum,
    ModoConvocatoriaEnum,
    SubtipoActividadEnum,
    SubtipoReunionEnum,
)
from expedientes.services.meeting_compliance_service import MeetingComplianceService
from expedientes.services.meeting_notice_notification_service import (
    MeetingNoticeNotificationService,
)
from socios.models import Role, Socio

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Asistencias Serializers
# ---------------------------------------------------------------------------


class AsistenciaEventoSerializer(serializers.ModelSerializer):
    """Serializador para registros individuales de asistencia con motivo circunstanciado (CA10)."""

    evento_id = serializers.IntegerField(source="evento.id", read_only=True)
    evento_titulo = serializers.CharField(source="evento.titulo", read_only=True)
    socio_id = serializers.IntegerField(source="socio.id", read_only=True)
    socio_nombre = serializers.SerializerMethodField()
    socio_legajo = serializers.CharField(source="socio.legajo", read_only=True)
    socio_email = serializers.EmailField(source="socio.email", read_only=True)
    socio_subcomision = serializers.CharField(
        source="socio.subcomision.name", default="", read_only=True
    )
    estado_asistencia_display = serializers.CharField(
        source="get_estado_asistencia_display", read_only=True
    )
    metodo_captura_display = serializers.CharField(
        source="get_metodo_captura_display", read_only=True
    )
    expediente_generado_numero = serializers.CharField(
        source="expediente_generado.numero", default=None, read_only=True
    )
    apercibimiento_generado_id = serializers.SerializerMethodField()

    class Meta:
        model = AsistenciaEvento
        fields = [
            "id",
            "evento_id",
            "evento_titulo",
            "socio_id",
            "socio_nombre",
            "socio_legajo",
            "socio_email",
            "socio_subcomision",
            "estado_asistencia",
            "estado_asistencia_display",
            "hora_registro",
            "hora_salida",
            "minutos_tardanza",
            "minutos_retiro_anticipado",
            "metodo_captura",
            "metodo_captura_display",
            "dispositivo_id",
            "motivo",
            "observaciones",
            "procesado_disciplinario",
            "expediente_generado",
            "expediente_generado_numero",
            "apercibimiento_generado_id",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "evento_id",
            "evento_titulo",
            "socio_id",
            "socio_nombre",
            "socio_legajo",
            "socio_email",
            "socio_subcomision",
            "estado_asistencia_display",
            "metodo_captura_display",
            "procesado_disciplinario",
            "expediente_generado",
            "expediente_generado_numero",
            "apercibimiento_generado_id",
            "created_at",
        ]

    def get_socio_nombre(self, obj: AsistenciaEvento) -> str:
        socio = obj.socio
        return f"{socio.first_name} {socio.last_name}".strip()

    def get_apercibimiento_generado_id(self, obj: AsistenciaEvento) -> int | None:
        return 1 if getattr(obj, "notificado", False) else None


class AsistenciaItemInputSerializer(serializers.Serializer):
    """Valida cada registro de asistencia con motivo circunstanciado obligatorio (CA10)."""

    ESTADO_ALIASES: dict[str, str] = {
        "AUSENTE_INJUSTIFICADO": EstadoAsistenciaEventoEnum.AUSENTE,
        "TARDANZA_LEVE": EstadoAsistenciaEventoEnum.TARDE_LEVE,
        "TARDANZA_GRAVE": EstadoAsistenciaEventoEnum.TARDE_GRAVE,
        "RETIRO_ANTICIPADO": EstadoAsistenciaEventoEnum.RETIRO_ANTICIPADO_GRAVE,
    }

    socio_id = serializers.IntegerField(
        required=True,
        help_text="ID del socio convocado.",
    )
    estado_asistencia = serializers.CharField(
        required=True,
        help_text="Estado tipificado de la asistencia.",
    )
    motivo = serializers.CharField(
        required=True,
        allow_blank=False,
        trim_whitespace=True,
        help_text=(
            "Motivo u observación circunstanciada obligatoria para justificar o explicar "
            "el estado (CA10)."
        ),
    )
    hora_registro = serializers.DateTimeField(required=False, allow_null=True)
    hora_salida = serializers.DateTimeField(required=False, allow_null=True)
    minutos_tardanza = serializers.IntegerField(required=False, default=0, min_value=0)
    minutos_retiro_anticipado = serializers.IntegerField(required=False, default=0, min_value=0)
    observaciones = serializers.CharField(required=False, allow_blank=True, default="")

    def validate_estado_asistencia(self, value: str) -> str:
        normalized = self.ESTADO_ALIASES.get(value, value)
        if normalized not in EstadoAsistenciaEventoEnum.values:
            raise serializers.ValidationError(
                f"Estado de asistencia '{value}' inválido. "
                f"Opciones: {EstadoAsistenciaEventoEnum.values}"
            )
        return normalized

    def validate_socio_id(self, value: int) -> int:
        if not Socio.objects.filter(pk=value).exists():
            raise serializers.ValidationError(
                f"El socio con ID {value} no existe en el padrón institucional."
            )
        return value

    def validate_motivo(self, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise serializers.ValidationError(
                "El motivo circunstanciado es obligatorio para cada convocado (CA10)."
            )
        return cleaned


class AsistenciaEventoBulkUpdateSerializer(serializers.Serializer):
    """Payload para cargar, actualizar o reportar asistencias masivamente en un evento."""

    asistencias = AsistenciaItemInputSerializer(
        many=True,
        required=True,
        allow_empty=False,
        help_text="Lista de asistencias con motivo circunstanciado por socio convocado.",
    )
    metodo_captura = serializers.ChoiceField(
        choices=MetodoCapturaAsistenciaEnum.choices,
        default=MetodoCapturaAsistenciaEnum.MANUAL,
        required=False,
        help_text="Estrategia de captura empleada.",
    )
    estrategia = serializers.ChoiceField(
        choices=MetodoCapturaAsistenciaEnum.choices,
        required=False,
        write_only=True,
        help_text="Alias de estrategia de captura empleada.",
    )
    fecha_reporte = serializers.DateTimeField(
        required=False,
        allow_null=True,
        help_text="Timestamp formal del reporte (opcional, default ahora).",
    )
    fecha_hora_cierre_efectivo = serializers.DateTimeField(
        required=False,
        allow_null=True,
        help_text="Timestamp real de finalización efectiva de la reunión.",
    )
    cerrar_evento = serializers.BooleanField(
        required=False,
        default=True,
        help_text="Indica si debe marcarse el evento como CERRADO tras el procesamiento.",
    )

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        if "estrategia" in attrs and attrs["estrategia"]:
            attrs["metodo_captura"] = attrs.pop("estrategia")
        return attrs


ReportarAsistenciaSerializer = AsistenciaEventoBulkUpdateSerializer


# ---------------------------------------------------------------------------
# Evento Institucional Serializers
# ---------------------------------------------------------------------------


class EventoInstitucionalSerializer(serializers.ModelSerializer):
    """Serializador para listado y detalle exhaustivo de eventos institucionales."""

    categoria_display = serializers.CharField(source="get_categoria_display", read_only=True)
    modalidad_display = serializers.CharField(source="get_modalidad_display", read_only=True)
    estado_display = serializers.CharField(source="get_estado_display", read_only=True)
    modo_convocatoria_display = serializers.CharField(
        source="get_modo_convocatoria_display", read_only=True
    )
    convocante_nombre = serializers.SerializerMethodField()
    convocante_legajo = serializers.CharField(source="convocante.legajo", read_only=True)
    subcomision_nombre = serializers.CharField(
        source="subcomision.name", default=None, read_only=True
    )
    reportado_por_nombre = serializers.SerializerMethodField()

    total_convocados = serializers.SerializerMethodField()
    total_presentes = serializers.SerializerMethodField()
    total_ausentes = serializers.SerializerMethodField()

    class Meta:
        model = EventoInstitucional
        fields = [
            "id",
            "titulo",
            "descripcion",
            "categoria",
            "categoria_display",
            "tipo",
            "modalidad",
            "modalidad_display",
            "ubicacion",
            "lugar",
            "fecha_publicacion",
            "fecha_programada",
            "fecha_fin",
            "fecha_hora_cierre_efectivo",
            "fecha_reporte",
            "tolerancia_tardanza_minutos",
            "tolerancia_retiro_minutos",
            "estado",
            "estado_display",
            "modo_convocatoria",
            "modo_convocatoria_display",
            "grupo_convocado",
            "subcomision",
            "subcomision_nombre",
            "convocante",
            "convocante_nombre",
            "convocante_legajo",
            "reportado_por",
            "reportado_por_nombre",
            "es_obligatoria",
            "es_sancionable",
            "motivo_no_sancionable",
            "detalle_tarea",
            "puntos_sancion",
            "motivo_cancelacion",
            "estado_social_convocado",
            "total_convocados",
            "total_presentes",
            "total_ausentes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "categoria_display",
            "modalidad_display",
            "estado_display",
            "modo_convocatoria_display",
            "convocante_nombre",
            "convocante_legajo",
            "subcomision_nombre",
            "reportado_por_nombre",
            "detalle_tarea",
            "puntos_sancion",
            "motivo_cancelacion",
            "estado_social_convocado",
            "total_convocados",
            "total_presentes",
            "total_ausentes",
            "created_at",
            "updated_at",
        ]

    def get_convocante_nombre(self, obj: EventoInstitucional) -> str:
        if not obj.convocante:
            return ""
        return f"{obj.convocante.first_name} {obj.convocante.last_name}".strip()

    def get_reportado_por_nombre(self, obj: EventoInstitucional) -> str | None:
        if not obj.reportado_por:
            return None
        return f"{obj.reportado_por.first_name} {obj.reportado_por.last_name}".strip()

    def get_total_convocados(self, obj: EventoInstitucional) -> int:
        return obj.asistencias.count()

    def get_total_presentes(self, obj: EventoInstitucional) -> int:
        return obj.asistencias.filter(
            estado_asistencia__in=[
                EstadoAsistenciaEventoEnum.PRESENTE,
                EstadoAsistenciaEventoEnum.JUSTIFICADO,
                EstadoAsistenciaEventoEnum.TARDE_LEVE,
                EstadoAsistenciaEventoEnum.TARDE_GRAVE,
            ]
        ).count()

    def get_total_ausentes(self, obj: EventoInstitucional) -> int:
        return obj.asistencias.filter(estado_asistencia=EstadoAsistenciaEventoEnum.AUSENTE).count()


class EventoInstitucionalCreateSerializer(serializers.ModelSerializer):
    """Serializador para dar de alta y publicar eventos institucionales (CA1, CA8, CA9, CA10)."""

    convocante = serializers.PrimaryKeyRelatedField(
        queryset=Socio.objects.all(),
        required=False,
        allow_null=True,
        help_text="Socio organizador convocante (si se omite, se infiere del usuario autenticado).",
    )
    fecha_fin = serializers.DateTimeField(
        required=False,
        allow_null=True,
        default=None,
        help_text="Fecha y hora de finalización estrictamente opcional (CA8).",
    )
    fecha_publicacion = serializers.DateTimeField(
        required=False,
        help_text="Timestamp de publicación. Si se omite, se asigna ahora.",
    )
    socios_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        default=list,
        help_text="Lista ad-hoc de IDs de socios a convocar para modo PERSONALIZADA.",
    )
    notificar = serializers.BooleanField(
        required=False,
        default=False,
        write_only=True,
        help_text="Indica si debe despacharse la notificación formal inmediatamente al crear.",
    )
    detalle_tarea = serializers.CharField(
        required=False,
        allow_blank=True,
        default="",
        help_text="Instrucciones concretas y especificación de la tarea para Actividades.",
    )
    puntos_sancion = serializers.DecimalField(
        max_digits=4,
        decimal_places=2,
        required=False,
        allow_null=True,
        default=None,
        help_text=(
            "Puntaje de penalidad por inasistencia o incumplimiento personalizables "
            "para Actividades."
        ),
    )
    estado_social_convocado = serializers.ChoiceField(
        choices=[("JUNIORS", "Juniors"), ("SENIORS", "Seniors")],
        required=False,
        allow_null=True,
        default=None,
        help_text="Filtro de cohorte social cuando modo_convocatoria es ESTADO_SOCIAL.",
    )

    class Meta:
        model = EventoInstitucional
        fields = [
            "id",
            "titulo",
            "descripcion",
            "categoria",
            "tipo",
            "modalidad",
            "ubicacion",
            "lugar",
            "fecha_publicacion",
            "fecha_programada",
            "fecha_fin",
            "tolerancia_tardanza_minutos",
            "tolerancia_retiro_minutos",
            "modo_convocatoria",
            "grupo_convocado",
            "estado_social_convocado",
            "subcomision",
            "convocante",
            "es_obligatoria",
            "es_sancionable",
            "motivo_no_sancionable",
            "detalle_tarea",
            "puntos_sancion",
            "socios_ids",
            "notificar",
        ]
        read_only_fields = ["id", "es_sancionable", "motivo_no_sancionable"]

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        categoria = attrs.get("categoria")
        tipo = attrs.get("tipo")
        modalidad = attrs.get("modalidad")
        ubicacion = attrs.get("ubicacion")
        fecha_programada = attrs.get("fecha_programada")
        fecha_fin = attrs.get("fecha_fin")
        fecha_publicacion = attrs.get("fecha_publicacion") or timezone.now()
        modo_convocatoria = attrs.get("modo_convocatoria", ModoConvocatoriaEnum.PERSONALIZADA)
        grupo_convocado = attrs.get("grupo_convocado")
        subcomision = attrs.get("subcomision")

        errors: dict[str, str] = {}

        # 1. Coherencia categoría vs tipo (CA9)
        if categoria == CategoriaEventoEnum.REUNION:
            if tipo not in SubtipoReunionEnum.values:
                errors["tipo"] = (
                    f"El subtipo '{tipo}' no corresponde a una REUNION. "
                    f"Opciones: {SubtipoReunionEnum.values}"
                )
        elif categoria == CategoriaEventoEnum.ACTIVIDAD:
            if tipo not in SubtipoActividadEnum.values:
                errors["tipo"] = (
                    f"El subtipo '{tipo}' no corresponde a una ACTIVIDAD. "
                    f"Opciones: {SubtipoActividadEnum.values}"
                )

        # 2. Coherencia cronológica (CA8)
        if fecha_fin is not None and fecha_programada is not None and fecha_fin < fecha_programada:
            errors["fecha_fin"] = (
                "La fecha de finalización no puede ser anterior a la fecha programada."
            )

        if (
            fecha_publicacion is not None
            and fecha_programada is not None
            and fecha_publicacion > fecha_programada
        ):
            errors["fecha_publicacion"] = (
                "La fecha de publicación no puede ser posterior a la fecha programada."
            )

        # 3. Modalidad y ubicación/enlace (CA10)
        if modalidad == ModalidadEventoEnum.PRESENCIAL_EXTERNA and not (
            ubicacion and ubicacion.strip()
        ):
            errors["ubicacion"] = (
                "Para la modalidad presencial externa es obligatorio indicar la ubicación o "
                "dirección."
            )
        elif modalidad == ModalidadEventoEnum.VIRTUAL and not (ubicacion and ubicacion.strip()):
            errors["ubicacion"] = (
                "Para la modalidad virtual es obligatorio indicar el enlace de videoconferencia."
            )

        # 4. Validación de convocatoria
        if modo_convocatoria == ModoConvocatoriaEnum.GRUPO and not (
            grupo_convocado and grupo_convocado.strip()
        ):
            errors["grupo_convocado"] = "Debe indicar el grupo social convocado (ej. G58)."
        elif modo_convocatoria == ModoConvocatoriaEnum.SUBCOMISION and subcomision is None:
            errors["subcomision"] = "Debe indicar la subcomisión convocada."
        elif modo_convocatoria == ModoConvocatoriaEnum.ESTADO_SOCIAL and not attrs.get(
            "estado_social_convocado"
        ):
            errors["estado_social_convocado"] = (
                "Debe indicar el estado social convocado (JUNIORS o SENIORS)."
            )

        # 5. Validación de detalle de tarea para actividades
        if categoria == CategoriaEventoEnum.ACTIVIDAD:
            detalle = attrs.get("detalle_tarea", "")
            if not (detalle and detalle.strip()):
                errors["detalle_tarea"] = (
                    "Para actividades operativas es obligatorio detallar la tarea asignada."
                )

        # 6. Normalización de puntos de sanción
        if attrs.get("puntos_sancion") is not None:
            attrs["puntos_sancion"] = -abs(attrs["puntos_sancion"])

        if errors:
            raise serializers.ValidationError(errors)

        return attrs

    def create(self, validated_data: dict[str, Any]) -> EventoInstitucional:
        socios_ids: list[int] = validated_data.pop("socios_ids", [])
        notificar: bool = validated_data.pop("notificar", False)
        request = self.context.get("request")

        # Asignar convocante si no viene en el payload
        if "convocante" not in validated_data or validated_data.get("convocante") is None:
            if request and hasattr(request.user, "socio"):
                validated_data["convocante"] = request.user.socio
            else:
                primer_cd = Socio.objects.filter(role__in=[Role.CD, Role.ADMIN]).first()
                if primer_cd:
                    validated_data["convocante"] = primer_cd
                else:
                    raise serializers.ValidationError(
                        {"convocante": "No se pudo inferir el convocante del evento."}
                    )

        # Fecha de publicación y estado inicial
        if (
            "fecha_publicacion" not in validated_data
            or validated_data.get("fecha_publicacion") is None
        ):
            validated_data["fecha_publicacion"] = timezone.now()

        if notificar:
            validated_data["estado"] = EstadoEventoEnum.NOTIFICADO
        else:
            validated_data["estado"] = EstadoEventoEnum.CREADO

        # Lugar por defecto según modalidad
        modalidad = validated_data.get("modalidad")
        if modalidad == ModalidadEventoEnum.PRESENCIAL_SEDE and not validated_data.get("lugar"):
            validated_data["lugar"] = "Sede Central AVEIT"
        elif modalidad == ModalidadEventoEnum.VIRTUAL and not validated_data.get("lugar"):
            validated_data["lugar"] = "Plataforma Virtual"
        elif modalidad == ModalidadEventoEnum.PRESENCIAL_EXTERNA and not validated_data.get(
            "lugar"
        ):
            validated_data["lugar"] = validated_data.get("ubicacion") or "Ubicación Externa"

        # Evaluar plazo de preaviso para determinar sancionabilidad (CA1 / CA2)
        fecha_pub = validated_data["fecha_publicacion"]
        fecha_prog = validated_data["fecha_programada"]
        es_sancionable, motivo_no = MeetingComplianceService.validate_notice_period(
            fecha_publicacion=fecha_pub,
            fecha_programada=fecha_prog,
        )
        validated_data["es_sancionable"] = es_sancionable
        validated_data["motivo_no_sancionable"] = motivo_no

        evento = EventoInstitucional.objects.create(**validated_data)

        # Resolver e instanciar convocados y asistencias iniciales
        convocados = MeetingNoticeNotificationService.resolve_convocados(
            evento, socios_ids=socios_ids
        )
        if convocados:
            EventoConvocado.objects.bulk_create(
                [EventoConvocado(evento=evento, socio_id=s.id) for s in convocados],
                ignore_conflicts=True,
            )
            for socio in convocados:
                AsistenciaEvento.objects.get_or_create(
                    evento=evento,
                    socio=socio,
                    defaults={
                        "estado_asistencia": EstadoAsistenciaEventoEnum.AUSENTE,
                        "motivo": "Convocado al evento",
                        "metodo_captura": MetodoCapturaAsistenciaEnum.MANUAL,
                    },
                )

        # Despachar notificaciones al Outbox si se solicitó notificar inmediatamente (CA7)
        if notificar:
            try:
                MeetingNoticeNotificationService.enqueue_meeting_notices(
                    evento=evento,
                    socios_ids=socios_ids,
                    auto_dispatch=True,
                )
            except Exception as exc:
                logger.warning(
                    "Error encolando notificaciones de convocatoria para evento %s: %s",
                    evento.id,
                    exc,
                )

        return evento

    def to_representation(self, instance: EventoInstitucional) -> dict[str, Any]:
        """Devuelve la representación canónica completa del evento institucional."""
        return EventoInstitucionalSerializer(instance, context=self.context).data


# ---------------------------------------------------------------------------
# Control de Llamados y Felicitaciones (atencionFelicitacion)
# ---------------------------------------------------------------------------


class AtencionFelicitacionSerializer(serializers.ModelSerializer):
    """Serializador para consulta del libro de llamados de atención y felicitaciones por socio."""

    socio_id = serializers.IntegerField(source="socio.id", read_only=True)
    socio_nombre = serializers.SerializerMethodField()
    socio_legajo = serializers.CharField(source="socio.legajo", read_only=True)
    pendientes = serializers.IntegerField(source="llamadosAtencion", read_only=True)
    estado = serializers.CharField(read_only=True)

    class Meta:
        model = AtencionFelicitacion
        fields = [
            "socio_id",
            "socio_nombre",
            "socio_legajo",
            "llamadosAtencion",
            "felicitaciones",
            "pendientes",
            "estado",
        ]
        read_only_fields = fields

    def get_socio_nombre(self, obj: AtencionFelicitacion) -> str:
        socio = obj.socio
        return f"{socio.first_name} {socio.last_name}".strip()


# Alias retrocompatible
RegistroApercibimientoSerializer = AtencionFelicitacionSerializer
