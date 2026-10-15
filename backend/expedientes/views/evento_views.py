"""ViewSets y endpoints REST para Eventos, Asistencias y Apercibimientos (CA1 a CA10).

Implementa:
- EventoInstitucionalViewSet: CRUD con RBAC (CD, TD, Fiscalizadora y Admin).
- Action /asistencias/: Listado y carga masiva de asistencias con motivo circunstanciado.
- Action /reportar-asistencia/: Carga y graduación disciplinaria (CA2, CA3, CA5, CA9, CA10).
- Action /procesar-asistencias/: Orquestación transaccional y consolidación 3:1.
- RegistroApercibimientoViewSet: Consulta del libro mayor con aislamiento RBAC.
- SocioApercibimientosView: Endpoint /api/v1/expedientes/socios/{id}/apercibimientos/.
"""

import logging
from typing import Any

from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from expedientes.models import (
    AtencionFelicitacion,
    EstadoEventoEnum,
    EventoInstitucional,
    MetodoCapturaAsistenciaEnum,
)
from expedientes.permissions import CanManageEventos
from expedientes.serializers.evento_serializers import (
    AsistenciaEventoBulkUpdateSerializer,
    AsistenciaEventoSerializer,
    EventoInstitucionalCreateSerializer,
    EventoInstitucionalSerializer,
    RegistroApercibimientoSerializer,
    ReportarAsistenciaSerializer,
)
from expedientes.services.attendance_processing_service import (
    AttendanceProcessingService,
)
from expedientes.services.meeting_compliance_service import MeetingComplianceService
from expedientes.services.meeting_notice_notification_service import (
    MeetingNoticeNotificationService,
)
from socios.models import Role, Socio

logger = logging.getLogger(__name__)


class EventoInstitucionalViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión integral de eventos institucionales (reuniones y actividades).

    Permisos RBAC:
    - Listar y detalle (GET): Socios y todo usuario autenticado.
    - Crear, actualizar, eliminar y procesar (POST, PUT, PATCH, DELETE):
      Comisión Directiva, Administradores, Tribunal de Disciplina y Fiscalizadora.
    """

    queryset = (
        EventoInstitucional.objects.select_related("convocante", "subcomision", "reportado_por")
        .prefetch_related("asistencias__socio")
        .order_by("-fecha_programada")
    )

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [permissions.IsAuthenticated()]
        return [CanManageEventos()]

    def get_serializer_class(self):
        if self.action == "create":
            return EventoInstitucionalCreateSerializer
        return EventoInstitucionalSerializer

    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        evento = serializer.save()
        output_serializer = EventoInstitucionalSerializer(
            evento, context=self.get_serializer_context()
        )
        headers = self.get_success_headers(output_serializer.data)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def get_queryset(self):
        qs = super().get_queryset()
        params = self.request.query_params

        categoria = params.get("categoria")
        if categoria:
            qs = qs.filter(categoria=categoria)

        tipo = params.get("tipo")
        if tipo:
            qs = qs.filter(tipo=tipo)

        modalidad = params.get("modalidad")
        if modalidad:
            qs = qs.filter(modalidad=modalidad)

        estado = params.get("estado")
        if estado:
            qs = qs.filter(estado=estado)

        es_sancionable = params.get("es_sancionable")
        if es_sancionable is not None:
            if es_sancionable.lower() in ("true", "1", "yes"):
                qs = qs.filter(es_sancionable=True)
            elif es_sancionable.lower() in ("false", "0", "no"):
                qs = qs.filter(es_sancionable=False)

        modo_convocatoria = params.get("modo_convocatoria")
        if modo_convocatoria:
            qs = qs.filter(modo_convocatoria=modo_convocatoria)

        grupo_convocado = params.get("grupo_convocado")
        if grupo_convocado:
            qs = qs.filter(grupo_convocado__iexact=grupo_convocado)

        subcomision_id = params.get("subcomision_id") or params.get("subcomision")
        if subcomision_id:
            qs = qs.filter(subcomision_id=subcomision_id)

        fecha_desde = params.get("fecha_desde")
        if fecha_desde:
            qs = qs.filter(fecha_programada__gte=fecha_desde)

        fecha_hasta = params.get("fecha_hasta")
        if fecha_hasta:
            qs = qs.filter(fecha_programada__lte=fecha_hasta)

        mis_eventos = params.get("mis_eventos")
        if mis_eventos and mis_eventos.lower() in ("true", "1", "yes"):
            if hasattr(self.request.user, "socio"):
                qs = qs.filter(convocante=self.request.user.socio)

        # Transiciones automáticas de ciclo de vida
        ahora = timezone.now()
        limite_preaviso = ahora + timezone.timedelta(days=2)

        # 1. Anulación automática: Si estaba en CREADO y falta menos de 2 días hábiles (o ya inició)
        qs.filter(
            estado=EstadoEventoEnum.CREADO,
            fecha_programada__lte=limite_preaviso,
        ).update(
            estado=EstadoEventoEnum.ANULADO,
            motivo_cancelacion=(
                "Anulado automáticamente por falta de notificación dentro del plazo "
                "mínimo reglamentario de 2 días hábiles."
            ),
        )

        # 2. Apertura automática: Si estaba notificado y pasó la hora de inicio sin tener fecha fin
        qs.filter(
            estado=EstadoEventoEnum.NOTIFICADO,
            fecha_fin__isnull=True,
            fecha_programada__lte=ahora,
        ).update(estado=EstadoEventoEnum.ABIERTO)

        # 3. En curso automático: Si estaba notificado y pasó inicio pero fecha fin es futura
        qs.filter(
            estado=EstadoEventoEnum.NOTIFICADO,
            fecha_fin__isnull=False,
            fecha_programada__lte=ahora,
            fecha_fin__gt=ahora,
        ).update(estado=EstadoEventoEnum.EN_CURSO)

        search = params.get("search")
        if search:
            search_clean = search.strip()
            qs = qs.filter(
                Q(titulo__icontains=search_clean)
                | Q(descripcion__icontains=search_clean)
                | Q(lugar__icontains=search_clean)
                | Q(ubicacion__icontains=search_clean)
            )

        return qs

    @action(
        detail=True,
        methods=["get", "post", "put", "patch"],
        url_path="asistencias",
    )
    def asistencias(self, request: Request, pk: str | None = None) -> Response:
        """
        GET: Lista todos los convocados y sus asistencias para este evento.
        POST / PUT / PATCH: Carga masiva o actualización de asistencias con motivo circunstanciado.
        """
        evento = self.get_object()

        if request.method == "GET":
            asistencias_qs = evento.asistencias.select_related(
                "socio", "expediente_generado"
            ).order_by("socio__legajo")
            serializer = AsistenciaEventoSerializer(asistencias_qs, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        # Carga masiva con motivo circunstanciado
        serializer = AsistenciaEventoBulkUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        socio_actor = getattr(request.user, "socio", None)
        actor_name = (
            f"{socio_actor.first_name} {socio_actor.last_name}"
            if socio_actor
            else request.user.get_username()
        )

        resultado = AttendanceProcessingService.process_event_attendance(
            evento_id=evento.id,
            marcaciones=data["asistencias"],
            metodo_captura=data.get("metodo_captura", MetodoCapturaAsistenciaEnum.MANUAL),
            actor=actor_name,
            reportado_por_id=socio_actor.id if socio_actor else None,
            fecha_reporte=data.get("fecha_reporte"),
            fecha_hora_cierre_efectivo=data.get("fecha_hora_cierre_efectivo"),
            cerrar_evento=data.get("cerrar_evento", True),
        )

        return Response(resultado, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="reportar-asistencia")
    def reportar_asistencia(self, request: Request, pk: str | None = None) -> Response:
        """Reporta asistencia y genera actuaciones según la escala reglamentaria (CA10)."""
        evento = self.get_object()
        serializer = ReportarAsistenciaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        socio_actor = getattr(request.user, "socio", None)
        actor_name = (
            f"{socio_actor.first_name} {socio_actor.last_name}"
            if socio_actor
            else request.user.get_username()
        )

        resultado = AttendanceProcessingService.process_event_attendance(
            evento_id=evento.id,
            marcaciones=data["asistencias"],
            metodo_captura=data.get("metodo_captura", MetodoCapturaAsistenciaEnum.MANUAL),
            actor=actor_name,
            reportado_por_id=socio_actor.id if socio_actor else None,
            fecha_reporte=data.get("fecha_reporte"),
            fecha_hora_cierre_efectivo=data.get("fecha_hora_cierre_efectivo"),
            cerrar_evento=data.get("cerrar_evento", True),
        )

        return Response(resultado, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="procesar-asistencias")
    def procesar_asistencias(self, request: Request, pk: str | None = None) -> Response:
        """Ejecuta el procesamiento disciplinario transaccional y consolida 3:1.

        Si se pasa payload de asistencias lo actualiza; si no, procesa las ya guardadas.
        """
        evento = self.get_object()
        raw_marcaciones = request.data.get("asistencias")

        if raw_marcaciones:
            serializer = AsistenciaEventoBulkUpdateSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            marcaciones = serializer.validated_data["asistencias"]
            metodo = serializer.validated_data.get(
                "metodo_captura", MetodoCapturaAsistenciaEnum.MANUAL
            )
            fecha_rep = serializer.validated_data.get("fecha_reporte")
            fecha_cierre = serializer.validated_data.get("fecha_hora_cierre_efectivo")
            cerrar = serializer.validated_data.get("cerrar_evento", True)
        else:
            marcaciones = [
                {
                    "socio_id": a.socio_id,
                    "estado_asistencia": a.estado_asistencia,
                    "motivo": a.motivo or "Sin motivo circunstanciado",
                    "minutos_tardanza": a.minutos_tardanza,
                    "minutos_retiro_anticipado": a.minutos_retiro_anticipado,
                    "hora_registro": a.hora_registro.isoformat() if a.hora_registro else None,
                    "hora_salida": a.hora_salida.isoformat() if a.hora_salida else None,
                    "observaciones": a.observaciones,
                }
                for a in evento.asistencias.all()
            ]
            metodo = MetodoCapturaAsistenciaEnum.MANUAL
            fecha_rep = None
            fecha_cierre = None
            cerrar = True

        socio_actor = getattr(request.user, "socio", None)
        actor_name = (
            f"{socio_actor.first_name} {socio_actor.last_name}"
            if socio_actor
            else request.user.get_username()
        )

        resultado = AttendanceProcessingService.process_event_attendance(
            evento_id=evento.id,
            marcaciones=marcaciones,
            metodo_captura=metodo,
            actor=actor_name,
            reportado_por_id=socio_actor.id if socio_actor else None,
            fecha_reporte=fecha_rep,
            fecha_hora_cierre_efectivo=fecha_cierre,
            cerrar_evento=cerrar,
        )

        return Response(resultado, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="notificar")
    def notificar(self, request: Request, pk: str | None = None) -> Response:
        """
        Despacha las notificaciones formales por correo a los citados y pasa de CREADO a NOTIFICADO.
        """
        evento = self.get_object()
        if evento.estado not in [EstadoEventoEnum.CREADO]:
            return Response(
                {
                    "detail": (
                        "El evento no puede notificarse porque se encuentra en estado "
                        f"'{evento.get_estado_display()}'."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        ahora = timezone.now()
        es_sancionable, motivo_no = MeetingComplianceService.validate_notice_period(
            fecha_publicacion=ahora,
            fecha_programada=evento.fecha_programada,
        )
        evento.fecha_publicacion = ahora
        evento.es_sancionable = es_sancionable
        evento.motivo_no_sancionable = motivo_no
        evento.estado = EstadoEventoEnum.NOTIFICADO
        evento.save()

        outbox_items = MeetingNoticeNotificationService.enqueue_meeting_notices(
            evento=evento, auto_dispatch=True
        )
        return Response(
            {
                "detail": (
                    f"Convocatoria notificada formalmente. Se encolaron {len(outbox_items)} avisos."
                ),
                "evento": EventoInstitucionalSerializer(
                    evento, context=self.get_serializer_context()
                ).data,
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"], url_path="anular")
    def anular(self, request: Request, pk: str | None = None) -> Response:
        """
        Anula un evento. Si ya estaba NOTIFICADO, despacha avisos de disculpas a los citados.
        """
        evento = self.get_object()
        if evento.estado in [EstadoEventoEnum.FINALIZADO, EstadoEventoEnum.ANULADO]:
            return Response(
                {
                    "detail": (
                        f"No se puede anular un evento en estado '{evento.get_estado_display()}'."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        motivo = (request.data.get("motivo") or "").strip() or None
        estaba_notificado = evento.estado in [
            EstadoEventoEnum.NOTIFICADO,
            EstadoEventoEnum.EN_CURSO,
            EstadoEventoEnum.ABIERTO,
        ]

        evento.estado = EstadoEventoEnum.ANULADO
        evento.motivo_cancelacion = (
            motivo or "Cancelación formal dispuesta por la autoridad convocante."
        )
        evento.save()

        if estaba_notificado:
            MeetingNoticeNotificationService.send_cancellation_notices(
                evento=evento, motivo=motivo, auto_dispatch=True
            )

        return Response(
            {
                "detail": "Evento anulado correctamente.",
                "evento": EventoInstitucionalSerializer(
                    evento, context=self.get_serializer_context()
                ).data,
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"], url_path="fijar-hora-fin")
    def fijar_hora_fin(self, request: Request, pk: str | None = None) -> Response:
        """
        Registra la fecha y hora de finalización para eventos en estado ABIERTO o sin fin.
        """
        evento = self.get_object()
        fecha_fin_str = request.data.get("fecha_fin")
        if not fecha_fin_str:
            return Response(
                {"fecha_fin": "La fecha y hora de finalización es obligatoria."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        fecha_fin = parse_datetime(fecha_fin_str)
        if not fecha_fin:
            return Response(
                {"fecha_fin": "Formato de fecha y hora inválido. Use formato ISO 8601."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if timezone.is_naive(fecha_fin):
            fecha_fin = timezone.make_aware(fecha_fin)

        if fecha_fin < evento.fecha_programada:
            return Response(
                {
                    "fecha_fin": (
                        "La fecha y hora de finalización no puede ser anterior a la hora de inicio."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        evento.fecha_fin = fecha_fin
        evento.tieneHoraFin = True
        if not evento.fecha_hora_cierre_efectivo:
            evento.fecha_hora_cierre_efectivo = fecha_fin

        ahora = timezone.now()
        if fecha_fin <= ahora:
            evento.estado = EstadoEventoEnum.FINALIZADO
        else:
            evento.estado = EstadoEventoEnum.EN_CURSO
        evento.save()

        return Response(
            {
                "detail": "Fecha de finalización registrada exitosamente.",
                "evento": EventoInstitucionalSerializer(
                    evento, context=self.get_serializer_context()
                ).data,
            },
            status=status.HTTP_200_OK,
        )


class RegistroApercibimientoViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet de sólo lectura para consultar el libro de llamados de atención y felicitaciones (CA4).

    Aislamiento RBAC:
    - Socios ordinarios sólo pueden ver sus propios llamados y felicitaciones.
    - Directiva, Tribunal y Admin pueden ver todos y filtrar por socio.
    """

    queryset = AtencionFelicitacion.objects.select_related("socio").all()
    serializer_class = RegistroApercibimientoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        socio = getattr(user, "socio", None)
        role = socio.role if socio else ""

        # Aislamiento RBAC
        is_management = user.is_staff or (socio and role in (Role.CD, Role.TD, Role.ADMIN))

        if not is_management:
            if not socio:
                return qs.none()
            return qs.filter(socio=socio)

        # Filtros para autoridades
        params = self.request.query_params
        socio_id = params.get("socio_id") or params.get("socio")
        if socio_id:
            qs = qs.filter(socio_id=socio_id)

        search = params.get("search")
        if search:
            search_clean = search.strip()
            qs = qs.filter(
                Q(socio__legajo__icontains=search_clean)
                | Q(socio__first_name__icontains=search_clean)
                | Q(socio__last_name__icontains=search_clean)
            )

        return qs


class SocioApercibimientosView(APIView):
    """
    Endpoint dedicado /api/v1/expedientes/socios/{id}/apercibimientos/.
    Retorna el estado de llamados de atención y felicitaciones de un socio.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request: Request, socio_id: int) -> Response:
        socio_solicitado = get_object_or_404(Socio, pk=socio_id)
        user = request.user
        socio_auth = getattr(user, "socio", None)
        role = socio_auth.role if socio_auth else ""

        is_management = user.is_staff or (socio_auth and role in (Role.CD, Role.TD, Role.ADMIN))

        if not is_management:
            if not socio_auth or socio_auth.id != socio_id:
                raise PermissionDenied(
                    "No posee autorización para consultar los apercibimientos de otro socio."
                )

        atencion, _ = AtencionFelicitacion.objects.get_or_create(socio=socio_solicitado)
        serializer = RegistroApercibimientoSerializer(atencion)
        return Response([serializer.data], status=status.HTTP_200_OK)
