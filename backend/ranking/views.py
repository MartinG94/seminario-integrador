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
        "id",
        "+id",
        "-id",
        "saldo",
        "+saldo",
        "-saldo",
        "puntos",
        "+puntos",
        "-puntos",
        "merito",
        "+merito",
        "-merito",
        "sancion",
        "+sancion",
        "-sancion",
        "apellido",
        "+apellido",
        "-apellido",
        "nombre",
        "+nombre",
        "-nombre",
        "legajo",
        "+legajo",
        "-legajo",
        "subcomision",
        "+subcomision",
        "-subcomision",
        "diferencia",
        "+diferencia",
        "-diferencia",
        "reconciliado",
        "+reconciliado",
        "-reconciliado",
    }

    def get(self, request: Request) -> Response:
        """Consultar nómina ordenada y reconciliada de socios."""
        categoria = request.query_params.get("categoria") or request.query_params.get(
            "filtroCategoria"
        )
        cat_clean = None
        if categoria is not None and categoria.strip():
            c_val = categoria.strip().upper()
            if c_val not in ("ACTIVO", "PASIVO"):
                return Response(
                    {
                        "error": (
                            f"Categoría '{categoria}' inválida. "
                            "Valores permitidos: 'ACTIVO', 'PASIVO'."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            cat_clean = c_val

        sort_param = (
            request.query_params.get("ordering")
            or request.query_params.get("order_by")
            or request.query_params.get("sort")
            or request.query_params.get("criterioOrden")
        )
        direction_param = request.query_params.get("direction") or request.query_params.get("dir")
        order_param = request.query_params.get("order")

        # Si order es 'asc', 'desc', etc., actúa como modificador de dirección;
        # si no, y no hay sort_param, actúa como fallback de campo.
        if order_param:
            ord_lower = order_param.strip().lower()
            if ord_lower in ("asc", "desc", "ascending", "descending"):
                if not direction_param:
                    direction_param = ord_lower
            elif not sort_param:
                sort_param = order_param

        ordering = sort_param
        ord_clean = None
        if ordering is not None and ordering.strip():
            dir_clean = direction_param.strip().lower() if direction_param else ""
            is_desc = bool(dir_clean in ("desc", "descending"))

            raw_tokens = [tok.strip().lower() for tok in ordering.split(",") if tok.strip()]
            order_tokens = []
            for tok in raw_tokens:
                if is_desc and not tok.startswith(("-", "+")):
                    tok = f"-{tok}"
                order_tokens.append(tok)

            invalid_tokens = [tok for tok in order_tokens if tok not in self.VALID_ORDERING_FIELDS]
            if invalid_tokens:
                allowed_str = ", ".join(sorted(self.VALID_ORDERING_FIELDS))
                return Response(
                    {
                        "error": (
                            f"Campo(s) de ordenamiento no válido(s): {', '.join(invalid_tokens)}. "
                            f"Opciones permitidas: {allowed_str}."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            ord_clean = ",".join(order_tokens)

        reconciliado_param = request.query_params.get("reconciliado")
        reconciliado_bool = None
        if reconciliado_param is not None and reconciliado_param.strip():
            rec_lower = reconciliado_param.strip().lower()
            if rec_lower in ("true", "1", "si", "sí", "yes"):
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

        subcomision = request.query_params.get("subcomision") or request.query_params.get(
            "filtroSubcomision"
        )
        if subcomision is not None and not subcomision.strip():
            subcomision = None

        search = (
            request.query_params.get("search")
            or request.query_params.get("q")
            or request.query_params.get("filtroTexto")
        )
        if search is not None and not search.strip():
            search = None

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
