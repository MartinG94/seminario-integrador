"""Core views for SGD-AVEIT."""

import logging

from django.db import DatabaseError, OperationalError, connection
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

logger = logging.getLogger(__name__)


class HealthCheckView(APIView):
    """Endpoint de comprobación de salud para Docker, Kubernetes y monitor de uptime."""

    permission_classes = (AllowAny,)
    authentication_classes = ()

    def get(self, request: Request) -> Response:
        """Verificar la conectividad operativa con la base de datos MySQL 8.0."""
        try:
            connection.ensure_connection()
            response = Response(
                {"status": "ok", "db": "connected"},
                status=status.HTTP_200_OK,
            )
        except (OperationalError, DatabaseError) as err:
            logger.error("Healthcheck: database connectivity error: %s", err)
            response = Response(
                {"status": "error", "db": "unavailable"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except Exception as err:
            logger.exception("Healthcheck: unexpected internal error: %s", err)
            response = Response(
                {"status": "error", "db": "unavailable"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        response["Cache-Control"] = "no-cache, no-store, must-revalidate"
        return response
