"""Consulta propia de asientos y respaldos; todos los datos salen del mismo SELECT."""

from decimal import Decimal
from typing import Any, Literal, TypedDict

from django.db import connection, transaction


class HistoricalCaseReference(TypedDict):
    id: int
    number: str
    recorded_at: str | None
    state: Literal["emitido"]


class AppliedResolution(TypedDict):
    id: int
    text: str
    regulations: list[str]


class ManagedCaseReference(TypedDict):
    id: int
    number: str
    state: Literal["emitido"]


class PointsHistoryEntry(TypedDict):
    movement_id: int
    applied_points: float
    historical_case: HistoricalCaseReference
    resolution: AppliedResolution
    managed_case: ManagedCaseReference | None


class PointsHistory(TypedDict):
    points_balance: float
    entries: list[PointsHistoryEntry]


class InvalidPointsHistory(ValueError):
    """Un asiento o referencia no acredita un respaldo completo y propio."""


_HISTORY_QUERY = """
    SELECT
        p.idPuntajeAplicado AS movement_id, p.puntajeAplicado AS applied_points,
        p.socio_id AS recipient_number,
        e.idExpediente AS historical_case_id, e.nroExpediente AS historical_case_number,
        e.fechaHora AS recorded_at, e.estadoExpediente_id AS historical_state_id,
        s.nombre AS historical_state_label,
        r.idDatosResolucion AS resolution_id, r.consideracion AS resolution_text,
        r.reglamento1, r.reglamento2, r.reglamento3,
        mo.fixture_key AS movement_fixture_key, mo.owned AS movement_owned,
        he.fixture_key AS historical_fixture_key, he.profile AS historical_profile,
        re.fixture_key AS resolution_fixture_key, re.profile AS resolution_profile,
        mo.profile AS movement_profile,
        ho.namespace AS history_namespace, ho.object_key AS history_key,
        ho.owned AS history_owned,
        ro.namespace AS resolution_namespace, ro.object_key AS resolution_key,
        ro.owned AS resolution_owned,
        co.namespace AS managed_namespace, co.object_key AS managed_key,
        co.owned AS managed_owned,
        lo.namespace AS link_namespace, lo.object_key AS link_key, lo.owned AS link_owned,
        m.id AS managed_case_id, m.numero AS managed_case_number,
        m.estado AS managed_case_state, m.socio_id AS managed_primary_recipient,
        involved.id AS managed_link_id, involved.socio_id AS managed_linked_recipient
    FROM tribunal_puntajeaplicado p
    LEFT JOIN tribunal_expediente e ON e.idExpediente = p.expediente_id
    LEFT JOIN tribunal_estadoexpediente s ON s.idEstadoExpediente = e.estadoExpediente_id
    LEFT JOIN tribunal_datosresolucion r ON r.idDatosResolucion = e.dataRes_id
    LEFT JOIN core_demofixtureownership mo
        ON mo.namespace = %s AND mo.object_key = CAST(p.idPuntajeAplicado AS CHAR)
    LEFT JOIN core_demofixtureownership he
        ON he.namespace = 'tribunal_expediente' AND he.object_key = CAST(e.idExpediente AS CHAR)
    LEFT JOIN core_demofixtureownership re
        ON re.namespace = 'tribunal_datosresolucion'
        AND re.object_key = CAST(r.idDatosResolucion AS CHAR)
    LEFT JOIN core_demofixtureownership ho
        ON RIGHT(mo.fixture_key, 9) = '.movement' AND ho.profile = mo.profile
        AND ho.fixture_key = CONCAT(LEFT(mo.fixture_key, CHAR_LENGTH(mo.fixture_key)-9), '.history')
    LEFT JOIN core_demofixtureownership ro
        ON RIGHT(mo.fixture_key, 9) = '.movement' AND ro.profile = mo.profile
        AND ro.fixture_key = CONCAT(
            LEFT(mo.fixture_key, CHAR_LENGTH(mo.fixture_key)-9), '.resolution')
    LEFT JOIN core_demofixtureownership co
        ON RIGHT(mo.fixture_key, 9) = '.movement' AND co.profile = mo.profile
        AND co.fixture_key = LEFT(mo.fixture_key, CHAR_LENGTH(mo.fixture_key)-9)
    LEFT JOIN expedientes_expediente m ON m.id = CAST(co.object_key AS SIGNED)
    LEFT JOIN core_demofixtureownership lo
        ON RIGHT(mo.fixture_key, 9) = '.movement' AND lo.profile = mo.profile
        AND lo.fixture_key = CONCAT(
            LEFT(mo.fixture_key, CHAR_LENGTH(mo.fixture_key)-9), '.link.', CAST(%s AS CHAR))
    LEFT JOIN expedientes_expediente_socios involved
        ON involved.expediente_id = m.id AND involved.socio_id = %s
    WHERE p.socio_id = %s
    ORDER BY p.idPuntajeAplicado
"""


def _managed_reference(
    row: dict[str, Any], *, institutional_number: int, local_socio_id: int | None
) -> ManagedCaseReference | None:
    fixture_key = row["movement_fixture_key"]
    markers = (
        (fixture_key, ".movement"),
        (row["historical_fixture_key"], ".history"),
        (row["resolution_fixture_key"], ".resolution"),
    )
    if not any(key is not None and key.endswith(suffix) for key, suffix in markers):
        return None
    if fixture_key is None or not fixture_key.endswith(".movement"):
        raise InvalidPointsHistory
    base_key = fixture_key.removesuffix(".movement")
    if (
        row["historical_fixture_key"] != f"{base_key}.history"
        or row["resolution_fixture_key"] != f"{base_key}.resolution"
        or row["movement_profile"] != row["historical_profile"]
        or row["movement_profile"] != row["resolution_profile"]
        or not row["movement_owned"]
        or not row["history_owned"]
        or not row["resolution_owned"]
        or not row["managed_owned"]
        or not row["link_owned"]
        or row["history_namespace"] != "tribunal_expediente"
        or row["history_key"] != str(row["historical_case_id"])
        or row["resolution_namespace"] != "tribunal_datosresolucion"
        or row["resolution_key"] != str(row["resolution_id"])
        or row["managed_namespace"] != "expedientes_expediente"
        or row["managed_case_id"] is None
        or row["managed_key"] != str(row["managed_case_id"])
        or row["managed_case_state"] != "emitido"
        or not row["managed_case_number"]
        or row["managed_linked_recipient"] != local_socio_id
        or row["link_namespace"] != "expedientes_expediente_socios"
        or row["link_key"] != str(row["managed_link_id"])
        or f"Ref: {row['managed_case_number']}, fixture [{base_key}]" not in row["resolution_text"]
        or f"nroSocio {institutional_number}," not in row["resolution_text"]
    ):
        raise InvalidPointsHistory
    return {
        "id": row["managed_case_id"],
        "number": row["managed_case_number"],
        "state": "emitido",
    }


@transaction.atomic
def read_own_points_history(institutional_number: int, local_socio_id: int | None) -> PointsHistory:
    """LEFT JOIN y saldo del mismo listado: ningún asiento roto se omite ni se inventa."""
    with connection.cursor() as cursor:
        cursor.execute(
            _HISTORY_QUERY,
            ["tribunal_puntajeaplicado", local_socio_id, local_socio_id, institutional_number],
        )
        columns = [column[0] for column in cursor.description]
        rows = [dict(zip(columns, row, strict=True)) for row in cursor.fetchall()]
    entries: list[PointsHistoryEntry] = []
    total = Decimal("0.00")
    seen: set[int] = set()
    for row in rows:
        if (
            row["movement_id"] in seen
            or row["recipient_number"] != institutional_number
            or row["historical_case_id"] is None
            or not row["historical_case_number"]
            or row["historical_state_id"] != 6
            or not row["historical_state_label"]
            or row["historical_state_label"].strip().casefold() != "emitido"
            or row["resolution_id"] is None
            or not row["resolution_text"]
            or not row["resolution_text"].strip()
            or not row["reglamento1"]
            or not row["reglamento1"].strip()
        ):
            raise InvalidPointsHistory
        points = Decimal(row["applied_points"])
        if not points.is_finite():
            raise InvalidPointsHistory
        seen.add(row["movement_id"])
        total += points
        entries.append(
            {
                "movement_id": row["movement_id"],
                "applied_points": float(points),
                "historical_case": {
                    "id": row["historical_case_id"],
                    "number": row["historical_case_number"],
                    "recorded_at": row["recorded_at"].isoformat()
                    if row["recorded_at"] is not None
                    else None,
                    "state": "emitido",
                },
                "resolution": {
                    "id": row["resolution_id"],
                    "text": row["resolution_text"],
                    "regulations": [
                        row[column]
                        for column in ("reglamento1", "reglamento2", "reglamento3")
                        if row[column] and row[column].strip()
                    ],
                },
                "managed_case": _managed_reference(
                    row, institutional_number=institutional_number, local_socio_id=local_socio_id
                ),
            }
        )
    return {"points_balance": float(total), "entries": entries}
