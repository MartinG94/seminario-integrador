"""Vistas API para la exclusión fundada de involucrados (SCRUM-102)."""

from django.core.exceptions import PermissionDenied, ValidationError
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from expedientes.permissions import CanTransitionExpedientes
from expedientes.services.exclusion_service import ExclusionInvolucradoService


class ExcluirInvolucradoView(APIView):
    """Permite a un miembro del TD dictar la exclusión fundada de un socio imputado."""

    permission_classes = [permissions.IsAuthenticated, CanTransitionExpedientes]

    def post(self, request, pk: int, socio_id: int):
        motivo = request.data.get("motivo", "")
        try:
            resultado = ExclusionInvolucradoService.excluir_involucrado(
                expediente_id=pk,
                socio_id=socio_id,
                user=request.user,
                motivo=motivo,
            )
        except PermissionDenied as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_403_FORBIDDEN)
        except ValidationError as exc:
            msg = exc.messages[0] if hasattr(exc, "messages") else str(exc)
            return Response({"detail": msg}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        descargo = resultado["descargo"]
        socio = resultado["socio"]
        expediente = resultado["expediente"]

        nro_socio = getattr(socio, "numero_socio", None) or socio.legajo

        return Response(
            {
                "success": True,
                "mensaje": f"Socio {nro_socio} excluido fundadamente del expediente.",
                "expediente_id": expediente.id,
                "expediente_estado": expediente.estado,
                "expediente_archivado": resultado["expediente_archivado"],
                "activos_restantes_count": resultado["activos_restantes_count"],
                "socio_id": socio.id,
                "socio_numero_socio": socio.numero_socio,
                "socio_legajo": socio.legajo,
                "esta_excluido": descargo.esta_excluido,
                "motivo_exclusion": descargo.motivo_exclusion,
                "excluido_at": descargo.excluido_at.isoformat() if descargo.excluido_at else None,
            },
            status=status.HTTP_200_OK,
        )
