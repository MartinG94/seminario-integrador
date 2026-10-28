"""Vistas API REST para reportes e informes analíticos institucionales.

Provee:
- ReportesResumenView: Resumen analítico de los 7 KPIs institucionales.
- ReportesExportCSVView: Exportación descargable en CSV con UTF-8 BOM y trazabilidad SHA256.
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

from expedientes.permissions import CanViewReportes
from expedientes.services.reportes_service import ReportesMetricsService


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
