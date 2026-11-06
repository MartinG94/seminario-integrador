"""Vistas para el Visor Autorizado de Expedientes (US S4-01 / SCRUM-51)."""

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from expedientes.models import AuditoriaConsultaExpediente, Expediente
from expedientes.permissions import IsImputadoOrTribunal
from expedientes.serializers.visor_serializers import ExpedienteVisorSerializer
from expedientes.services.deadline_service import DeadlineEnforcementService


class ExpedienteVisorView(APIView):
    """Vista dedicada de pantalla completa para visor de causas (CA1 a CA4)."""

    permission_classes = [IsAuthenticated, IsImputadoOrTribunal]

    def get(self, request, pk: int) -> Response:
        DeadlineEnforcementService().close_expired_deadlines()
        expediente = get_object_or_404(
            Expediente.objects.select_related("socio", "solicitud_t01").prefetch_related(
                "socios",
                "descargos__socio",
                "descargos__decisiones_causal",
                "descargos__versiones",
                "evidencias__socio",
                "cambios_estado",
            ),
            pk=pk,
        )

        # Autorización por objeto RBAC (TD, CD, ADMIN o Socio Imputado titular/co-imputado)
        self.check_object_permissions(request, expediente)

        # Registro inmutable de auditoría de consulta en base de datos (CA3)
        self._registrar_auditoria_consulta(request, expediente)

        serializer = ExpedienteVisorSerializer(expediente, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def _registrar_auditoria_consulta(self, request, expediente: Expediente) -> None:
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(",")[0].strip()
        else:
            ip_address = request.META.get("REMOTE_ADDR")

        user = request.user
        socio = getattr(user, "socio", None)
        legajo = str(socio.legajo) if socio and socio.legajo else ""
        nombre = f"{user.first_name} {user.last_name}".strip() or user.username
        rol = getattr(user, "role", "SOCIO")

        AuditoriaConsultaExpediente.objects.create(
            expediente=expediente,
            user=user,
            legajo=legajo,
            nombre=nombre,
            rol=rol,
            ip_address=ip_address,
        )
