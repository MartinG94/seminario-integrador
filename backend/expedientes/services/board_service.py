"""Servicio de construcción del payload del tablero Kanban (S2-05 CA1).

Agrupa los expedientes por los 6 estados reglamentarios del Art. 12
y devuelve un diccionario estructurado listo para serialización JSON.
"""

from django.db.models import QuerySet

from expedientes.models import EstadoExpedienteEnum
from expedientes.serializers import BoardExpedienteSerializer


def build_board_payload(qs: QuerySet) -> dict:
    """Agrupa expedientes del queryset por los 6 estados canónicos.

    Retorna un dict con clave ``columns`` conteniendo una lista de 6 elementos,
    uno por cada estado reglamentario, en el orden oficial del Art. 12.
    """
    board: dict[str, list] = {s.value: [] for s in EstadoExpedienteEnum}
    for expediente in qs:
        board[expediente.estado].append(BoardExpedienteSerializer(expediente).data)
    return {
        "columns": [
            {
                "key": s.value,
                "label": s.label,
                "cases": board[s.value],
            }
            for s in EstadoExpedienteEnum
        ]
    }
