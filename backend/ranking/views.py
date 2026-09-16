"""Vistas API REST para el Ranking Reconciliado (SGD-AVEIT)."""

from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from ranking.serializers import RankingSocioSerializer
from ranking.services import (
    filter_ranking_queryset,
    get_reconciled_ranking_queryset,
    order_ranking_queryset,
)


class RankingListView(APIView):
    """
    Endpoint GET /api/v1/ranking/ y /api/ranking/
    Retorna la lista completa del Ranking Oficial Reconciliado con soporte para:
    - Filtro por categoría estatutaria (ACTIVO / PASIVO)
    - Filtro por subcomisión (nombre o id)
    - Búsqueda textual (q o search sobre nombre, apellido, legajo)
    - Ordenamiento por saldo, apellido, nombre o legajo
    - Filtro opcional por reconciliado (true / false)
    """

    permission_classes = (AllowAny,)
    authentication_classes = ()

    VALID_ORDERING_FIELDS = {
        "saldo",
        "+saldo",
        "-saldo",
        "apellido",
        "+apellido",
        "-apellido",
        "nombre",
        "+nombre",
        "-nombre",
        "legajo",
        "+legajo",
        "-legajo",
    }

    def get(self, request: Request) -> Response:
        """Consultar nómina ordenada y reconciliada de socios."""
        categoria = request.query_params.get("categoria")
        if categoria:
            cat_clean = categoria.strip().upper()
            if cat_clean not in ("ACTIVO", "PASIVO"):
                return Response(
                    {
                        "error": (
                            f"Categoría '{categoria}' inválida. "
                            "Valores permitidos: 'ACTIVO', 'PASIVO'."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            cat_clean = None

        ordering = request.query_params.get("ordering") or request.query_params.get("order_by")
        if ordering:
            ord_clean = ordering.strip()
            if ord_clean not in self.VALID_ORDERING_FIELDS:
                allowed_str = ", ".join(sorted(self.VALID_ORDERING_FIELDS))
                return Response(
                    {
                        "error": (
                            f"Campo de ordenamiento '{ordering}' no válido. "
                            f"Opciones permitidas: {allowed_str}."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            ord_clean = None

        reconciliado_param = request.query_params.get("reconciliado")
        reconciliado_bool = None
        if reconciliado_param is not None:
            rec_lower = reconciliado_param.strip().lower()
            if rec_lower in ("true", "1", "si", "yes"):
                reconciliado_bool = True
            elif rec_lower in ("false", "0", "no"):
                reconciliado_bool = False
            else:
                return Response(
                    {
                        "error": (
                            f"Valor de 'reconciliado' inválido: '{reconciliado_param}'. "
                            "Valores permitidos: 'true', 'false'."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        subcomision = request.query_params.get("subcomision")
        search = request.query_params.get("search") or request.query_params.get("q")

        # 1. Obtener queryset optimizado (sin N+1)
        qs = get_reconciled_ranking_queryset()

        # 2. Aplicar filtros
        qs = filter_ranking_queryset(
            qs,
            categoria=cat_clean,
            subcomision=subcomision,
            search=search,
            reconciliado=reconciliado_bool,
        )

        # 3. Aplicar ordenamiento
        qs = order_ranking_queryset(qs, ordering=ord_clean)

        # 4. Serializar al contrato RankingSocio
        serializer = RankingSocioSerializer(qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
