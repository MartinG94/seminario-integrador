"""Vistas de API REST para reportes e informes institucionales del SGD-AVEIT (SCRUM-63).

Provee:
- ReportesT01View: KPIs y distribuciones del Tablero de Gestión por T01.
- ReportesReunionesView: KPIs y gráficos del Tablero de Gestión por Reuniones.
- ReportesSubcomisionesListView: Lista de subcomisiones para el selector de reportes.
- ReportesSubcomisionView: Balance e interacciones intra/inter de una subcomisión.
- ReportesHistoricoRecordsView: Cuadro de Honor con récord histórico y serie temporal.
- ExpedienteClasificacionPatchView: Clasificación por concepto por parte del Tribunal de Disciplina.
- ReportesResumenView: Resumen analítico de los 7 KPIs institucionales.
- ReportesExportCSVView: Exportación descargable en CSV con UTF-8 BOM y hash SHA256.
"""

import csv
import hashlib
import io

from django.http import HttpResponse
from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from expedientes.models import ClasificacionExpedienteEnum, Expediente
from expedientes.permissions import CanViewReportes
from expedientes.services.reportes_service import ReportesMetricsService, ReportesService
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


class ReportesResumenView(APIView):
    """Devuelve el resumen analítico de los 7 KPIs institucionales con filtros combinables."""

    permission_classes = [permissions.IsAuthenticated, CanViewReportes]

    def get(self, request: Request) -> Response:
        anio = request.query_params.get("anio")
        cuatrimestre = request.query_params.get("cuatrimestre")
        fecha_desde = request.query_params.get("fecha_desde")
        fecha_hasta = request.query_params.get("fecha_hasta")
        subcomision_id = request.query_params.get("subcomision_id")
        concepto = request.query_params.get("concepto")

        data = ReportesMetricsService.calculate_resumen(
            anio=anio,
            cuatrimestre=cuatrimestre,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            subcomision_id=subcomision_id,
            concepto=concepto,
        )

        return Response(data, status=status.HTTP_200_OK)


class ReportesExportCSVView(APIView):
    """Exportación en formato CSV institucional con firma SHA256 y BOM UTF-8."""

    permission_classes = [permissions.IsAuthenticated, CanViewReportes]

    def get(self, request: Request) -> HttpResponse:
        seccion = request.query_params.get("seccion", "subcomisiones").strip().lower()
        anio = request.query_params.get("anio")
        cuatrimestre = request.query_params.get("cuatrimestre")
        fecha_desde = request.query_params.get("fecha_desde")
        fecha_hasta = request.query_params.get("fecha_hasta")
        subcomision_id = request.query_params.get("subcomision_id")
        concepto = request.query_params.get("concepto")

        data = ReportesMetricsService.calculate_resumen(
            anio=anio,
            cuatrimestre=cuatrimestre,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            subcomision_id=subcomision_id,
            concepto=concepto,
        )

        buffer = io.StringIO()
        # Inserción de UTF-8 Byte Order Mark para compatibilidad directa con Excel en español
        buffer.write("\ufeff")
        writer = csv.writer(buffer, delimiter=",", quoting=csv.QUOTE_MINIMAL)

        if seccion == "autoridades":
            writer.writerow(
                [
                    "Legajo",
                    "Autoridad",
                    "Subcomisión",
                    "Rol",
                    "Total Pedidos",
                    "Sanciones",
                    "Méritos",
                    "En Trámite",
                    "Emitidos",
                    "Tasa Emisión (%)",
                ]
            )
            for row in data["pedidos_por_autoridad"]:
                writer.writerow(
                    [
                        row["legajo"],
                        row["nombre_completo"],
                        row["subcomision"],
                        row["rol_display"],
                        row["total_pedidos"],
                        row["sanciones"],
                        row["meritos"],
                        row["en_tramite"],
                        row["emitidos"],
                        row["tasa_emision_pct"],
                    ]
                )
        elif seccion == "conceptos":
            writer.writerow(
                [
                    "Código",
                    "Concepto",
                    "Total Expedientes",
                    "Sanciones",
                    "Méritos",
                    "En Trámite",
                    "Emitidos",
                ]
            )
            for row in data["agrupacion_por_concepto"]:
                writer.writerow(
                    [
                        row["concepto"],
                        row["nombre"],
                        row["total"],
                        row["sanciones"],
                        row["meritos"],
                        row["en_tramite"],
                        row["emitidos"],
                    ]
                )
        elif seccion == "balance":
            writer.writerow(
                [
                    "Subcomisión",
                    "Total Socios",
                    "Puntos Positivos",
                    "Puntos Negativos",
                    "Saldo Neto",
                    "Socios Alerta (<= -7)",
                    "Socios Riesgo (<= -10)",
                    "Saldo Pasivos (1°-3°)",
                    "Saldo Activos (4°-6°)",
                ]
            )
            for row in data["balance_subcomisiones_y_categorias"]:
                pas_saldo = row["desglose_categorias"]["pasivo"]["saldo_neto"]
                act_saldo = row["desglose_categorias"]["activo"]["saldo_neto"]
                writer.writerow(
                    [
                        row["subcomision_nombre"],
                        row["total_socios"],
                        row["puntos_positivos"],
                        row["puntos_negativos"],
                        row["saldo_neto"],
                        row["socios_alerta_preventiva"],
                        row["socios_riesgo_estatutario"],
                        pas_saldo,
                        act_saldo,
                    ]
                )
        else:  # 'subcomisiones' por defecto
            seccion = "subcomisiones"
            writer.writerow(
                [
                    "Subcomisión",
                    "Total Expedientes",
                    "Expedientes Intra",
                    "Expedientes Inter",
                    "Imputaciones Intra",
                    "Imputaciones Inter",
                    "Conceptos Predominantes",
                ]
            )
            for row in data["pedidos_por_subcomision"]:
                conceptos_str = ", ".join(
                    f"{k}: {v}" for k, v in row["desglose_por_concepto"].items()
                )
                writer.writerow(
                    [
                        row["subcomision_nombre"],
                        row["total_expedientes"],
                        row["expedientes_intra"],
                        row["expedientes_inter"],
                        row["imputaciones_intra"],
                        row["imputaciones_inter"],
                        conceptos_str,
                    ]
                )

        csv_content = buffer.getvalue()
        csv_bytes = csv_content.encode("utf-8")
        sha256_hash = hashlib.sha256(csv_bytes).hexdigest()

        timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
        filename = f"reporte_{seccion}_{timestamp}.csv"

        response = HttpResponse(csv_bytes, content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        response["X-Report-SHA256"] = sha256_hash
        return response
