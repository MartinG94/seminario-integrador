"""
Vistas de API REST para el envío de notificaciones y reintento de la cola Outbox.
"""

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from notifications.models import EmailOutboxStatus
from notifications.permissions import HasInternalServiceKeyOrAdmin
from notifications.serializers import (
    EmailOutboxResponseSerializer,
    RetryQueueResponseSerializer,
    SendEmailRequestSerializer,
)
from notifications.services import EmailDispatcherService


class SendEmailView(APIView):
    """
    Endpoint para el envío de correos electrónicos con resiliencia ante caídas de red.

    - Intento inmediato: Si el servidor SMTP responde, entrega el correo y retorna 200 OK.
    - Fallback Outbox: Si falla la conexión SMTP, encola el correo y retorna 202 Accepted.
    - Idempotencia: Si se provee `idempotency_key`, previene envíos duplicados.
    """

    permission_classes = [HasInternalServiceKeyOrAdmin]

    def post(self, request, *args, **kwargs) -> Response:
        serializer = SendEmailRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        outbox, created = EmailDispatcherService.create_or_get_outbox(serializer.validated_data)

        # Si ya había sido enviado (idempotencia)
        if outbox.status == EmailOutboxStatus.SENT:
            return Response(
                EmailOutboxResponseSerializer(outbox).data,
                status=status.HTTP_200_OK,
            )

        # Intento de despacho inmediato
        success = EmailDispatcherService.dispatch(outbox)

        response_data = EmailOutboxResponseSerializer(outbox).data
        if success:
            return Response(response_data, status=status.HTTP_200_OK)

        return Response(response_data, status=status.HTTP_202_ACCEPTED)


class RetryEmailQueueView(APIView):
    """
    Endpoint para disparar el reintento de mensajes pendientes en la cola Outbox.
    """

    permission_classes = [HasInternalServiceKeyOrAdmin]

    def post(self, request, *args, **kwargs) -> Response:
        try:
            batch_size = int(request.query_params.get("batch_size", 50))
        except (ValueError, TypeError):
            batch_size = 50

        force = request.query_params.get("force", "false").lower() in ("true", "1")

        result = EmailDispatcherService.process_pending_queue(batch_size=batch_size, force=force)
        return Response(
            RetryQueueResponseSerializer(result).data,
            status=status.HTTP_200_OK,
        )
