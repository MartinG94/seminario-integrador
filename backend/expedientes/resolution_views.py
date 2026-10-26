from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import permissions, status
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from expedientes.models import Expediente, Resolucion
from expedientes.permissions import CanTransitionExpedientes
from expedientes.resolution_serializers import ResolucionSerializer
from expedientes.services.resolution_pdf import build_resolution_preview_pdf
from expedientes.services.resolution_service import (
    DictamenNoCerradoError,
    UnavailableClosedDecisionProvider,
    emitir_resolucion,
)


class ResolucionView(APIView):
    permission_classes = [permissions.IsAuthenticated, CanTransitionExpedientes]

    def get(self, request, expediente_id):
        resolucion = (
            Resolucion.objects.filter(expediente_id=expediente_id)
            .order_by("-version")
            .first()
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
        return Response(ResolucionSerializer(resolucion).data, status=status.HTTP_201_CREATED)

    def patch(self, request, expediente_id):
        resolucion = (
            Resolucion.objects.filter(expediente_id=expediente_id)
            .order_by("-version")
            .first()
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
        return Response(ResolucionSerializer(serializer.save()).data)


class ResolucionEmitirView(APIView):
    permission_classes = [permissions.IsAuthenticated, CanTransitionExpedientes]

    @transaction.atomic
    def post(self, request, expediente_id):
        resolucion = (
            Resolucion.objects.filter(expediente_id=expediente_id)
            .order_by("-version")
            .first()
        )
        if not resolucion:
            return Response(
                {"detail": "Resolución no encontrada."},
                status=status.HTTP_404_NOT_FOUND,
            )
        try:
            emitida = emitir_resolucion(
                resolucion, request.user, UnavailableClosedDecisionProvider()
            )
        except DictamenNoCerradoError as exc:
            raise DRFValidationError({"dictamen": str(exc)}) from exc
        return Response(ResolucionSerializer(emitida).data)


class ResolucionPreviewView(APIView):
    permission_classes = [permissions.IsAuthenticated, CanTransitionExpedientes]

    def get(self, request, expediente_id):
        resolucion = (
            Resolucion.objects.filter(expediente_id=expediente_id)
            .order_by("-version")
            .first()
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
