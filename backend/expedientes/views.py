from django.db import transaction
from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import SolicitudT01
from .permissions import CanCreateT01
from .serializers import EmitirT01Serializer, SolicitudT01Serializer


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
