"""Vistas API REST para expedientes y descargos reglamentarios."""

from django.db import transaction
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from expedientes.models import (
    CambioEstadoExpediente,
    EstadoExpedienteEnum,
    Expediente,
    SolicitudT01,
)
from expedientes.permissions import CanCreateT01
from expedientes.serializers import (
    EmitirT01Serializer,
    ExpedienteListSerializer,
    PresentarDescargoSerializer,
    SolicitudT01Serializer,
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


REGLAMENTOS_VIGENTES = (
    "Estatuto AVEIT Reforma 2026",
    "Reglamento Procesal Disciplinario 2026",
    "Reglamento Interno de Disciplina",
)


class ReglamentosVigentesView(APIView):
    """Lista de reglamentos institucionales vigentes para respaldar un T01."""

    permission_classes = (CanCreateT01,)

    def get(self, request):
        return Response({"reglamentos": list(REGLAMENTOS_VIGENTES)})


class SolicitudT01CreateView(APIView):
    permission_classes = (CanCreateT01,)

    def post(self, request):
        serializer = SolicitudT01Serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        solicitud = serializer.save(solicitante=request.user.socio)
        return Response(SolicitudT01Serializer(solicitud).data, status=status.HTTP_201_CREATED)


class SolicitudT01DetailView(APIView):
    permission_classes = (CanCreateT01,)

    def get_object(self, request, pk):
        solicitud = get_object_or_404(SolicitudT01, pk=pk)
        if solicitud.solicitante_id != request.user.socio.pk:
            raise Http404
        return solicitud

    def get(self, request, pk):
        return Response(SolicitudT01Serializer(self.get_object(request, pk)).data)

    def patch(self, request, pk):
        solicitud = self.get_object(request, pk)
        serializer = SolicitudT01Serializer(solicitud, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        return Response(SolicitudT01Serializer(serializer.save()).data)


class SolicitudT01EmitView(APIView):
    permission_classes = (CanCreateT01,)

    @transaction.atomic
    def post(self, request, pk):
        solicitud = get_object_or_404(SolicitudT01.objects.select_for_update(), pk=pk)
        if solicitud.solicitante_id != request.user.socio.pk:
            raise Http404
        serializer = EmitirT01Serializer(data=request.data, context={"solicitud": solicitud})
        serializer.is_valid(raise_exception=True)
        solicitud = serializer.save()
        return Response(SolicitudT01Serializer(solicitud).data)
