from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import permissions, status
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from expedientes.models import CambioEstadoExpediente, EstadoExpedienteEnum, Expediente, Resolucion
from expedientes.permissions import CanTransitionExpedientes
from expedientes.resolution_serializers import ResolucionSerializer
from expedientes.services.resolution_pdf import build_resolution_preview_pdf
from expedientes.services.resolution_service import (
    DictamenNoCerradoError,
    ExpedienteConsolidatedDecisionProvider,
    emitir_resolucion,
    registrar_firma_resolucion,
)


class ResolucionView(APIView):
    permission_classes = [permissions.IsAuthenticated, CanTransitionExpedientes]

    def get(self, request, expediente_id):
        resolucion = (
            Resolucion.objects.filter(expediente_id=expediente_id).order_by("-version").first()
        )
        if not resolucion:
            return Response(
                {"detail": "Resolución no encontrada."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(ResolucionSerializer(resolucion).data)

    @transaction.atomic
    def post(self, request, expediente_id):
        expediente = get_object_or_404(Expediente, pk=expediente_id)
        if Resolucion.objects.filter(expediente=expediente).exists():
            return Response(
                {"detail": "Ya existe una resolución para el expediente."},
                status=status.HTTP_409_CONFLICT,
            )
        serializer = ResolucionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        resolucion = serializer.save(
            expediente=expediente,
            created_by=request.user,
            numero_expediente_snapshot=expediente.numero,
        )

        if expediente.estado in (
            EstadoExpedienteEnum.REVISION_RESOLUCION,
            EstadoExpedienteEnum.ESPERA_RESOLUCION,
        ):
            estado_anterior = expediente.estado
            expediente.estado = EstadoExpedienteEnum.PENDIENTE_CORREOS
            expediente.save(update_fields=["estado", "updated_at"])
            actor_name = (
                request.user.username
                if getattr(request.user, "username", None)
                else str(request.user)
            )
            CambioEstadoExpediente.objects.create(
                expediente=expediente,
                estado_anterior=estado_anterior,
                estado_nuevo=EstadoExpedienteEnum.PENDIENTE_CORREOS,
                actor=actor_name,
                motivo="Resolución oficial generada y enviada a pendiente de firma.",
            )

        reglamentos = request.data.get("reglamentos_respaldantes")
        if isinstance(reglamentos, list):
            resolucion.reglamentos_respaldantes = reglamentos
            resolucion.save(update_fields=["reglamentos_respaldantes", "updated_at"])
            if hasattr(expediente, "solicitud_t01") and expediente.solicitud_t01:
                expediente.solicitud_t01.reglamentos_respaldantes = reglamentos
                expediente.solicitud_t01.save(
                    update_fields=["reglamentos_respaldantes", "updated_at"]
                )

        expedientes = request.data.get("expedientes_referenciados")
        if isinstance(expedientes, list):
            resolucion.expedientes_referenciados = expedientes
            resolucion.save(update_fields=["expedientes_referenciados", "updated_at"])

        return Response(ResolucionSerializer(resolucion).data, status=status.HTTP_201_CREATED)

    @transaction.atomic
    def patch(self, request, expediente_id):
        resolucion = (
            Resolucion.objects.filter(expediente_id=expediente_id).order_by("-version").first()
        )
        if not resolucion:
            return Response(
                {"detail": "Resolución no encontrada."},
                status=status.HTTP_404_NOT_FOUND,
            )
        if resolucion.estado == "ISSUED":
            return Response(
                {"detail": "Una resolución emitida es inmutable."},
                status=status.HTTP_409_CONFLICT,
            )
        serializer = ResolucionSerializer(resolucion, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        resolucion_guardada = serializer.save()

        expediente = resolucion.expediente
        if expediente and expediente.estado in (
            EstadoExpedienteEnum.REVISION_RESOLUCION,
            EstadoExpedienteEnum.ESPERA_RESOLUCION,
        ):
            estado_anterior = expediente.estado
            expediente.estado = EstadoExpedienteEnum.PENDIENTE_CORREOS
            expediente.save(update_fields=["estado", "updated_at"])
            actor_name = (
                request.user.username
                if getattr(request.user, "username", None)
                else str(request.user)
            )
            CambioEstadoExpediente.objects.create(
                expediente=expediente,
                estado_anterior=estado_anterior,
                estado_nuevo=EstadoExpedienteEnum.PENDIENTE_CORREOS,
                actor=actor_name,
                motivo="Resolución oficial generada y enviada a pendiente de firma.",
            )

        reglamentos = request.data.get("reglamentos_respaldantes")
        if isinstance(reglamentos, list):
            resolucion_guardada.reglamentos_respaldantes = reglamentos
            resolucion_guardada.save(update_fields=["reglamentos_respaldantes", "updated_at"])
            if hasattr(expediente, "solicitud_t01") and expediente.solicitud_t01:
                expediente.solicitud_t01.reglamentos_respaldantes = reglamentos
                expediente.solicitud_t01.save(
                    update_fields=["reglamentos_respaldantes", "updated_at"]
                )

        expedientes = request.data.get("expedientes_referenciados")
        if isinstance(expedientes, list):
            resolucion_guardada.expedientes_referenciados = expedientes
            resolucion_guardada.save(update_fields=["expedientes_referenciados", "updated_at"])

        return Response(ResolucionSerializer(resolucion_guardada).data)


class ResolucionFirmarView(APIView):
    permission_classes = [permissions.IsAuthenticated, CanTransitionExpedientes]

    def post(self, request, expediente_id):
        resolucion = (
            Resolucion.objects.filter(expediente_id=expediente_id).order_by("-version").first()
        )
        if not resolucion:
            return Response(
                {"detail": "Resolución no encontrada."},
                status=status.HTTP_404_NOT_FOUND,
            )
        try:
            resolucion = registrar_firma_resolucion(resolucion, request.user)
        except ValidationError as exc:
            msg = exc.message_dict if hasattr(exc, "message_dict") else exc.messages
            raise DRFValidationError(msg) from exc
        return Response(ResolucionSerializer(resolucion).data, status=status.HTTP_200_OK)


class ResolucionEmitirView(APIView):
    permission_classes = [permissions.IsAuthenticated, CanTransitionExpedientes]

    @transaction.atomic
    def post(self, request, expediente_id):
        resolucion = (
            Resolucion.objects.filter(expediente_id=expediente_id).order_by("-version").first()
        )
        if not resolucion:
            return Response(
                {"detail": "Resolución no encontrada."},
                status=status.HTTP_404_NOT_FOUND,
            )
        try:
            emitida = emitir_resolucion(
                resolucion, request.user, ExpedienteConsolidatedDecisionProvider()
            )
        except DictamenNoCerradoError as exc:
            raise DRFValidationError({"dictamen": str(exc)}) from exc
        return Response(ResolucionSerializer(emitida).data)


class ResolucionPreviewView(APIView):
    permission_classes = [permissions.IsAuthenticated, CanTransitionExpedientes]

    def get(self, request, expediente_id):
        resolucion = (
            Resolucion.objects.filter(expediente_id=expediente_id).order_by("-version").first()
        )
        if not resolucion:
            return Response(
                {"detail": "Resolución no encontrada."},
                status=status.HTTP_404_NOT_FOUND,
            )

        response = HttpResponse(
            build_resolution_preview_pdf(resolucion), content_type="application/pdf"
        )
        response["Content-Disposition"] = (
            f'inline; filename="resolucion-preview-{expediente_id}.pdf"'
        )
        return response
