"""Core views for SGD-AVEIT."""

from django.db import DatabaseError, OperationalError, connection
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView


class HealthCheckView(APIView):
    """Endpoint de comprobación de salud para Docker, Kubernetes y monitor de uptime."""

    permission_classes = (AllowAny,)
    authentication_classes = ()

    def get(self, request: Request) -> Response:
        """Verificar la conectividad operativa con la base de datos MySQL 8.0."""
        try:
            connection.ensure_connection()
            return Response(
                {"status": "ok", "db": "connected"},
                status=status.HTTP_200_OK,
            )
        except (OperationalError, DatabaseError) as err:
            return Response(
                {"status": "error", "db": str(err)},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except Exception as err:
            return Response(
                {"status": "error", "db": f"Unexpected database error: {err}"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
