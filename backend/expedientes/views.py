"""Vistas API REST para expedientes y descargos reglamentarios."""

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from expedientes.models import (
    CambioEstadoExpediente,
    DescargoExpediente,
    EstadoExpedienteEnum,
    Expediente,
)
from expedientes.permissions import CanOpenExpedientes, CanTransitionExpedientes
from expedientes.serializers import (
    AperturaExpedienteSerializer,
    ExpedienteListSerializer,
    PresentarDescargoSerializer,
    TransicionExpedienteSerializer,
)
from expedientes.services.workflow_service import ExpedienteWorkflowService


def _actor_for_user(user) -> str:
    return user.get_username()


class ExpedienteCollectionView(APIView):
    permission_classes = [CanOpenExpedientes]

    def get(self, request: Request) -> Response:
        queryset = Expediente.objects.select_related(
            "socio", "socio__subcomision"
        ).prefetch_related("socios", "cambios_estado", "descargos")
        return Response(
            ExpedienteListSerializer(queryset, many=True, context={"request": request}).data
        )

    def post(self, request: Request) -> Response:
        serializer = AperturaExpedienteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            expediente = ExpedienteWorkflowService.open_expediente(
                motivo=serializer.validated_data["motivo"],
                socio_ids=serializer.validated_data["socios"],
                actor=_actor_for_user(request.user),
            )
        except IntegrityError as exc:
            raise DRFValidationError("No se pudo asignar el número de expediente.") from exc
        expediente = (
            Expediente.objects.select_related("socio", "socio__subcomision")
            .prefetch_related("socios", "cambios_estado", "descargos")
            .get(pk=expediente.pk)
        )
        return Response(
            ExpedienteListSerializer(expediente, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class TransicionExpedienteView(APIView):
    permission_classes = [CanTransitionExpedientes]

    def post(self, request: Request, pk: int) -> Response:
        serializer = TransicionExpedienteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            expediente = ExpedienteWorkflowService.transition(
                expediente_id=pk,
                estado_nuevo=serializer.validated_data["estado"],
                actor=_actor_for_user(request.user),
                motivo=serializer.validated_data["motivo"],
            )
        except Expediente.DoesNotExist as exc:
            raise NotFound("Expediente no encontrado.") from exc
        except ValidationError as exc:
            raise DRFValidationError(
                exc.message_dict if hasattr(exc, "message_dict") else exc.messages
            )
        expediente = (
            Expediente.objects.select_related("socio", "socio__subcomision")
            .prefetch_related("socios", "cambios_estado", "descargos")
            .get(pk=expediente.pk)
        )
        return Response(ExpedienteListSerializer(expediente, context={"request": request}).data)


class MisExpedientesView(APIView):
    """Retorna la lista de expedientes asignados al socio autenticado."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request: Request) -> Response:
        socio = getattr(request.user, "socio", None)
        if not socio:
            return Response([], status=status.HTTP_200_OK)

        queryset = (
            Expediente.objects.filter(Q(socio=socio) | Q(socios=socio))
            .distinct()
            .select_related("socio", "socio__subcomision")
            .prefetch_related("socios", "cambios_estado", "descargos")
        )
        serializer = ExpedienteListSerializer(queryset, many=True, context={"request": request})
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
            if (
                not expediente.socios.filter(pk=socio.pk).exists()
                and expediente.socio_id != socio.id
            ):
                raise PermissionDenied(
                    "No tiene autorización para presentar descargo en este expediente."
                )

            # Si ya presentó descargo
            if DescargoExpediente.objects.filter(expediente=expediente, socio=socio).exists() or (
                expediente.descargo_presentado and expediente.socio_id == socio.id
            ):
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
            DescargoExpediente.objects.create(
                expediente=expediente,
                socio=socio,
                tipo=validated_data["tipo"],
                causal=validated_data.get("causal", ""),
                archivo=validated_data.get("archivo", ""),
                texto=validated_data.get("texto", ""),
            )
            expediente.descargo_presentado = (
                expediente.descargos.count() >= expediente.socios.count()
            )
            fields_to_update = ["descargo_presentado"]
            if expediente.socio_id == socio.id:
                expediente.descargo_tipo = validated_data["tipo"]
                expediente.descargo_causal = validated_data.get("causal", "")
                expediente.descargo_archivo = validated_data.get("archivo", "")
                expediente.descargo_texto = validated_data.get("texto", "")
                expediente.descargo_presentado_at = now
                fields_to_update.extend(
                    [
                        "descargo_tipo",
                        "descargo_causal",
                        "descargo_archivo",
                        "descargo_texto",
                        "descargo_presentado_at",
                    ]
                )
            expediente.save(update_fields=fields_to_update)

            CambioEstadoExpediente.objects.create(
                expediente=expediente,
                estado_anterior=expediente.estado,
                estado_nuevo=expediente.estado,
                actor=f"SOCIO_{socio.legajo}",
                motivo=f"Presentación formal de descargo {validated_data['tipo']}.",
            )

            return Response(
                {
                    "detail": "Descargo registrado dentro de los términos reglamentarios.",
                    "expediente_id": expediente.id,
                    "descargo_presentado_at": now,
                },
                status=status.HTTP_201_CREATED,
            )
