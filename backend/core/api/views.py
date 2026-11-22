"""Endpoints del panel de administración (Spec 011) y lecturas públicas de parámetros."""

from __future__ import annotations

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsAdminComputos
from core.api.serializers import (
    AssignTribunalMemberSerializer,
    ParameterValueSerializer,
    TribunalCandidateSerializer,
    TribunalMemberSerializer,
    change_payload,
    parameter_payload,
)
from core.domain.system_parameters import (
    CATALOG,
    ParameterDefinition,
    ParameterValidationError,
    UnknownParameterError,
    get_definition,
)
from core.services.system_parameters import SystemParameterService
from core.services.tribunal_members import (
    TribunalMemberError,
    TribunalMemberNotFound,
    TribunalMemberService,
)

UNKNOWN_PARAMETER_DETAIL = "El parámetro solicitado no existe."
NOT_A_MEMBER_DETAIL = "El socio no integra el Tribunal de Disciplina."


def _definition_or_none(clave: str) -> ParameterDefinition | None:
    try:
        return get_definition(clave)
    except UnknownParameterError:
        return None


class AdminView(APIView):
    permission_classes = [IsAuthenticated, IsAdminComputos]


class SystemParameterListView(AdminView):
    """GET /api/v1/admin/parametros/ — parámetros con su valor vigente (RF-02)."""

    def get(self, request: Request) -> Response:
        return Response([parameter_payload(definition) for definition in CATALOG])


class SystemParameterDetailView(AdminView):
    """PUT /api/v1/admin/parametros/<clave>/ — registra un valor nuevo (RF-03 a RF-05)."""

    def put(self, request: Request, clave: str) -> Response:
        definition = _definition_or_none(clave)
        if definition is None:
            return Response({"detail": UNKNOWN_PARAMETER_DETAIL}, status=status.HTTP_404_NOT_FOUND)
        serializer = ParameterValueSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"valor": [f"Indicá un valor para {definition.etiqueta}."]},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            SystemParameterService.set(clave, serializer.validated_data["valor"], user=request.user)
        except ParameterValidationError as exc:
            return Response({"valor": [str(exc)]}, status=status.HTTP_400_BAD_REQUEST)
        return Response(parameter_payload(definition))


class SystemParameterHistoryView(AdminView):
    """GET /api/v1/admin/parametros/<clave>/historial/ — auditoría del parámetro (RF-04)."""

    def get(self, request: Request, clave: str) -> Response:
        if _definition_or_none(clave) is None:
            return Response({"detail": UNKNOWN_PARAMETER_DETAIL}, status=status.HTTP_404_NOT_FOUND)
        return Response([change_payload(c) for c in SystemParameterService.history(clave)])


class AttachmentLimitsView(APIView):
    """GET /api/v1/parametros/adjuntos/ — límites vigentes para quien carga comprobantes."""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        limits = SystemParameterService.attachment_limits()
        return Response(
            {
                "tamano_maximo_mb": limits.tamano_maximo_mb,
                "cantidad_maxima": limits.cantidad_maxima,
            }
        )


class ThresholdsView(APIView):
    """GET /api/v1/parametros/umbrales/ — umbrales vigentes para las vistas que los resaltan."""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        preventivo, activo = SystemParameterService.preventive_threshold()
        return Response(
            {
                "umbral_critico": format(SystemParameterService.critical_threshold(), "f"),
                "umbral_preventivo": format(preventivo, "f"),
                "umbral_preventivo_activo": activo,
            }
        )


class DeadlinesView(APIView):
    """GET /api/v1/parametros/plazos/ — plazos vigentes para textos y ayudas de la UI."""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        from expedientes.models import ParametroPlazoApelacion

        return Response(
            {
                "plazo_descargo_dias_habiles": SystemParameterService.descargo_business_days(),
                "plazo_apelacion_dias_habiles": ParametroPlazoApelacion.vigente(),
            }
        )


class TribunalCandidateListView(AdminView):
    """GET /api/v1/admin/usuarios-td/candidatos/?search= — Socios Ordinarios elegibles."""

    def get(self, request: Request) -> Response:
        candidatos = TribunalMemberService.candidates(request.query_params.get("search", ""))
        return Response(TribunalCandidateSerializer(candidatos, many=True).data)


class TribunalMemberListView(AdminView):
    """GET y POST /api/v1/admin/usuarios-td/ — nómina y alta de miembros (RF-10, RF-11)."""

    def get(self, request: Request) -> Response:
        return Response(TribunalMemberSerializer(TribunalMemberService.members(), many=True).data)

    def post(self, request: Request) -> Response:
        serializer = AssignTribunalMemberSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            socio = TribunalMemberService.assign(
                socio_id=serializer.validated_data["socio_id"], actor=request.user
            )
        except TribunalMemberError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(TribunalMemberSerializer(socio).data, status=status.HTTP_201_CREATED)


class TribunalMemberDetailView(AdminView):
    """DELETE /api/v1/admin/usuarios-td/<socio_id>/ — revoca el rol TD (RF-12)."""

    def delete(self, request: Request, socio_id: int) -> Response:
        try:
            TribunalMemberService.revoke(socio_id=socio_id, actor=request.user)
        except TribunalMemberNotFound:
            return Response({"detail": NOT_A_MEMBER_DETAIL}, status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)
