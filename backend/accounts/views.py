from django.conf import settings
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.serializers import LoginSerializer, SocioProfileSerializer
from core.services.demo_reset_service import reset_regularidad_database


class LoginView(APIView):
    """POST /api/v1/auth/login/ — RF-01-WS / RF-02-WS."""

    permission_classes = [AllowAny]
    authentication_classes = []

    def get_authenticate_header(self, request) -> str:
        # Sin este header DRF degrada cualquier 401 a 403 (`APIView.handle_exception`),
        # y CA1 exige 401 Unauthorized ante credenciales inválidas.
        return 'Bearer realm="api"'

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        # Un fallo de credenciales levanta AuthenticationFailed (401); un cuerpo
        # mal formado devuelve 400 sin llegar a consultar el padrón.
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data, status=status.HTTP_200_OK)


class MeView(APIView):
    """GET /api/v1/auth/me/ — perfil del usuario autenticado."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        socio = getattr(request.user, "socio", None)
        if socio is None or not socio.is_enabled:
            return Response(
                {"detail": "No posee un legajo de socio vigente."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return Response(SocioProfileSerializer(socio).data)


class ResetDemoDatabaseView(APIView):
    """POST /api/v1/auth/reset-demo-db/ — reinicia datos transaccionales en modo DEBUG."""

    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        if not settings.DEBUG:
            return Response(
                {"detail": "Esta acción solo está disponible en modo desarrollo."},
                status=status.HTTP_403_FORBIDDEN,
            )
        result = reset_regularidad_database()
        return Response(
            {
                "detail": "Base de datos reiniciada con 2 expedientes de demostración.",
                "expedientes": result["expedientes"],
            },
            status=status.HTTP_200_OK,
        )
