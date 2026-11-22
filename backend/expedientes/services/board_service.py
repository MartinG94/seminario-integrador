"""Servicio de construcción del payload del tablero Kanban (S2-05 CA1).

Agrupa los expedientes por los 6 estados reglamentarios del Art. 12
y devuelve un diccionario estructurado listo para serialización JSON.
"""

from collections.abc import Iterable

from django.db.models import QuerySet

from expedientes.models import EstadoExpedienteEnum, Expediente
from expedientes.serializers import BoardExpedienteSerializer


def build_board_payload(
    qs: QuerySet | Iterable[Expediente],
    *,
    preview_limit: int | None = None,
    column_totals: dict[str, int] | None = None,
) -> dict:
    """Agrupa expedientes del queryset por los 6 estados canónicos.

    Retorna un dict con clave ``columns`` conteniendo una lista de 6 elementos,
    uno por cada estado reglamentario, en el orden oficial del Art. 12.
    Cuando ``preview_limit`` o ``column_totals`` son ``None``, preserva el
    comportamiento completo de serializar todos los expedientes recibidos.
    """
    if preview_limit is not None and preview_limit < 0:
        raise ValueError("preview_limit debe ser mayor o igual a 0.")

    counts_in_qs: dict[str, int] = {s.value: 0 for s in EstadoExpedienteEnum}
    board: dict[str, list] = {s.value: [] for s in EstadoExpedienteEnum}
    serializer_context: dict = {}

    for expediente in qs:
        estado = expediente.estado
        if estado not in board:
            continue
        counts_in_qs[estado] += 1
        if preview_limit is not None and len(board[estado]) >= preview_limit:
            continue
        board[estado].append(BoardExpedienteSerializer(expediente, context=serializer_context).data)

    columns = []
    for s in EstadoExpedienteEnum:
        cases = board[s.value]
        if column_totals is not None and s.value in column_totals:
            total_count = max(int(column_totals[s.value]), len(cases))
        else:
            total_count = counts_in_qs[s.value]
        columns.append(
            {
                "key": s.value,
                "label": s.label,
                "cases": cases,
                "total_count": total_count,
                "has_more": total_count > len(cases),
            }
        )

    return {"columns": columns}
