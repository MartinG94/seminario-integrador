"""Vistas API REST para expedientes y descargos reglamentarios."""

from django.db import transaction
from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from expedientes.models import CambioEstadoExpediente, EstadoExpedienteEnum, Expediente
from expedientes.permissions import IsImputadoOrTribunal, IsTribunalOrDirectiva
from expedientes.serializers import (
    CaseNotificationAuditSerializer,
    DispatchNotificationResponseSerializer,
    ExpedienteListSerializer,
    PresentarDescargoSerializer,
)
from expedientes.services.opening_notification_service import (
    CaseNotificationQueryService,
    InvalidCaseStatusError,
    MissingSocioEmailError,
    OpeningNotificationService,
)


class MisExpedientesView(APIView):
    """Retorna la lista de expedientes asignados al socio autenticado."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request: Request) -> Response:
        socio = getattr(request.user, "socio", None)
        if not socio:
            return Response([], status=status.HTTP_200_OK)

        queryset = Expediente.objects.filter(socio=socio).select_related(
            "socio", "socio__subcomision"
        )
        serializer = ExpedienteListSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class PresentarDescargoView(APIView):
    """
    Endpoint para presentación de descargo reglamentario (CA2 y buzzer-beater CA5).

    Regla:
    - Evaluación de plazo en el servidor con select_for_update().
    - Acepta si now <= plazo_limite_at (inclusivo).
    - Rechaza con 409 Conflict si now > plazo_limite_at.
    - Valida titularidad del socio sobre el expediente.
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request: Request, pk: int) -> Response:
        socio = getattr(request.user, "socio", None)
        if not socio:
            raise PermissionDenied("El usuario autenticado no posee un perfil de socio vinculado.")

        serializer = PresentarDescargoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        now = timezone.now()

        with transaction.atomic():
            expediente = Expediente.objects.select_for_update().filter(id=pk).first()
            if not expediente:
                return Response(
                    {"detail": "Expediente no encontrado."},
                    status=status.HTTP_404_NOT_FOUND,
                )

            # Verificar titularidad (salvo staff o TD)
            if expediente.socio_id != socio.id and not request.user.is_staff:
                raise PermissionDenied(
                    "No tiene autorización para presentar descargo en este expediente."
                )

            # Si ya presentó descargo
            if expediente.descargo_presentado:
                return Response(
                    {"detail": "Ya existe un descargo formal registrado para este expediente."},
                    status=status.HTTP_409_CONFLICT,
                )

            # Si no está en estado 'justificando'
            if expediente.estado != EstadoExpedienteEnum.JUSTIFICANDO:
                msg = (
                    f"El expediente está en '{expediente.get_estado_display()}', "
                    "no admitiendo descargos."
                )
                return Response({"detail": msg}, status=status.HTTP_409_CONFLICT)

            # Verificación del plazo perentorio en servidor
            if not expediente.esta_en_plazo(ahora=now):
                return Response(
                    {
                        "detail": "El plazo perentorio de 5 días hábiles ha expirado.",
                        "plazo_limite_at": expediente.plazo_limite_at,
                        "server_time": now,
                    },
                    status=status.HTTP_409_CONFLICT,
                )

            # Registro exitoso del descargo
            validated_data = serializer.validated_data
            expediente.descargo_presentado = True
            expediente.descargo_tipo = validated_data["tipo"]
            expediente.descargo_causal = validated_data.get("causal", "")
            expediente.descargo_archivo = validated_data.get("archivo", "")
            expediente.descargo_texto = validated_data.get("texto", "")
            expediente.descargo_presentado_at = now
            expediente.save()

            CambioEstadoExpediente.objects.create(
                expediente=expediente,
                estado_anterior=expediente.estado,
                estado_nuevo=expediente.estado,
                actor=f"SOCIO_{socio.legajo}",
                motivo=f"Presentación formal de descargo {expediente.descargo_tipo}.",
            )

            return Response(
                {
                    "detail": "Descargo registrado dentro de los términos reglamentarios.",
                    "expediente_id": expediente.id,
                    "descargo_presentado_at": expediente.descargo_presentado_at,
                },
                status=status.HTTP_201_CREATED,
            )


class DispatchCaseOpeningView(APIView):
    """Endpoint para que el Tribunal de Disciplina despache la notificación formal (CA1, CA3).

    - Protegido con IsAuthenticated e IsTribunalOrDirectiva.
    - Transiciona atómicamente a Estado 2 ('justificando').
    - Congela plazo_inicio_at y plazo_limite_at.
    - Encola en EmailOutbox con idempotency_key e intenta envío SMTP no bloqueante.
    """

    permission_classes = [permissions.IsAuthenticated, IsTribunalOrDirectiva]

    def post(self, request: Request, pk: int) -> Response:
        if not Expediente.objects.filter(pk=pk).exists():
            return Response(
                {"detail": "Expediente no encontrado."},
                status=status.HTTP_404_NOT_FOUND,
            )

        actor = getattr(getattr(request.user, "socio", None), "legajo", request.user.username)

        try:
            expediente, outbox = OpeningNotificationService.dispatch_opening(
                expediente_id=pk,
                actor=f"TD_{actor}",
            )
        except InvalidCaseStatusError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_409_CONFLICT,
            )
        except MissingSocioEmailError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        response_data = {
            "expediente_id": expediente.id,
            "numero": expediente.numero,
            "estado": expediente.estado,
            "plazo_inicio_at": expediente.plazo_inicio_at,
            "plazo_limite_at": expediente.plazo_limite_at,
            "outbox_id": outbox.id,
            "outbox_status": outbox.status,
            "idempotency_key": outbox.idempotency_key,
            "mensaje": "Notificación de apertura despachada correctamente.",
        }
        serializer = DispatchNotificationResponseSerializer(response_data)
        return Response(serializer.data, status=status.HTTP_200_OK)


# Backward-compatible alias for existing imports
DespacharNotificacionAperturaView = DispatchCaseOpeningView


class CaseNotificationAuditView(APIView):
    """Endpoint para que operadores del Tribunal consulten la bitácora outbox (CA3).

    - Protegido con IsAuthenticated e IsTribunalOrDirectiva.
    """

    permission_classes = [permissions.IsAuthenticated, IsTribunalOrDirectiva]

    def get(self, request: Request, pk: int) -> Response:
        if not Expediente.objects.filter(pk=pk).exists():
            return Response(
                {"detail": "Expediente no encontrado."},
                status=status.HTTP_404_NOT_FOUND,
            )

        notifications = CaseNotificationQueryService.get_case_notifications(expediente_id=pk)
        serializer = CaseNotificationAuditSerializer(notifications, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


# Backward-compatible alias for existing imports
ExpedienteNotificacionesView = CaseNotificationAuditView


class ExpedienteDetailView(APIView):
    """Endpoint seguro de detalle de causa para el enlace provisto en la notificación (CA4).

    - Protegido con IsAuthenticated e IsImputadoOrTribunal (RBAC por objeto).
    - 401 si es anónimo.
    - 403 si es un socio ajeno a la causa.
    - 200 si es el socio imputado o integra TD/CD/Admin.
    """

    permission_classes = [permissions.IsAuthenticated, IsImputadoOrTribunal]

    def get(self, request: Request, pk: int) -> Response:
        expediente = (
            Expediente.objects.filter(pk=pk).select_related("socio", "socio__subcomision").first()
        )
        if not expediente:
            return Response(
                {"detail": "Expediente no encontrado."},
                status=status.HTTP_404_NOT_FOUND,
            )

        self.check_object_permissions(request, expediente)
        serializer = ExpedienteListSerializer(expediente)
        return Response(serializer.data, status=status.HTTP_200_OK)
