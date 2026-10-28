"""Vistas de API REST para los reportes e indicadores institucionales del SGD-AVEIT (SCRUM-63)."""

from rest_framework import permissions, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from expedientes.models import ClasificacionExpedienteEnum, Expediente
from expedientes.services.reportes_service import ReportesService
from socios.models import Subcomision


class ReportesT01View(APIView):
    """Retorna los KPIs y distribuciones del Tablero de Gestión por T01."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request: Request) -> Response:
        subcom_id = request.query_params.get("subcomision_id")
        subcom_id_int = int(subcom_id) if subcom_id and subcom_id.isdigit() else None
        data = ReportesService.obtener_metricas_t01(subcomision_id=subcom_id_int)
        return Response(data, status=status.HTTP_200_OK)


class ReportesReunionesView(APIView):
    """Retorna los KPIs y gráficos del Tablero de Gestión por Reuniones."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request: Request) -> Response:
        subcom_id = request.query_params.get("subcomision_id")
        subcom_id_int = int(subcom_id) if subcom_id and subcom_id.isdigit() else None
        data = ReportesService.obtener_metricas_reuniones(subcomision_id=subcom_id_int)
        return Response(data, status=status.HTTP_200_OK)


class ReportesSubcomisionesListView(APIView):
    """Lista las subcomisiones disponibles para el selector de reportes."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request: Request) -> Response:
        subs = Subcomision.objects.all().order_by("name")
        data = [{"id": s.id, "nombre": s.name} for s in subs]
        return Response(data, status=status.HTTP_200_OK)


class ReportesSubcomisionView(APIView):
    """Retorna el balance, gráfico Intra vs Inter y nómina de socios de una subcomisión."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request: Request) -> Response:
        subcom_id = request.query_params.get("subcomision_id")
        if not subcom_id or not subcom_id.isdigit():
            # Por defecto seleccionamos Gestión Social y Ambiental
            gsa = Subcomision.objects.filter(name__icontains="Gestión Social").first()
            subcom_id_int = gsa.id if gsa else 6
        else:
            subcom_id_int = int(subcom_id)

        data = ReportesService.obtener_metricas_subcomision(subcomision_id=subcom_id_int)
        return Response(data, status=status.HTTP_200_OK)


class ReportesHistoricoRecordsView(APIView):
    """Retorna el Cuadro de Honor con el récord histórico de Diego Sánchez y serie 2013-2026."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request: Request) -> Response:
        data = ReportesService.obtener_historico_y_records()
        return Response(data, status=status.HTTP_200_OK)


class ExpedienteClasificacionPatchView(APIView):
    """Permite al Tribunal de Disciplina clasificar o reclasificar un expediente."""

    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request: Request, pk: int) -> Response:
        expediente = Expediente.objects.filter(pk=pk).first()
        if not expediente:
            return Response(
                {"error": "Expediente no encontrado."},
                status=status.HTTP_404_NOT_FOUND,
            )

        nueva_clasificacion = request.data.get("clasificacion")
        if nueva_clasificacion not in ClasificacionExpedienteEnum.values:
            opciones = ClasificacionExpedienteEnum.values
            return Response(
                {"error": f"Clasificación inválida. Opciones admitidas: {opciones}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        expediente.clasificacion = nueva_clasificacion
        expediente.save(update_fields=["clasificacion", "updated_at"])

        return Response(
            {
                "mensaje": "Clasificación actualizada correctamente por TD.",
                "expediente_id": expediente.pk,
                "numero": expediente.numero,
                "clasificacion": expediente.clasificacion,
            },
            status=status.HTTP_200_OK,
        )
