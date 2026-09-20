"""Pruebas de rendimiento del endpoint de Ranking (SLA p95 ≤ 500ms)."""

import math
import time

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from rest_framework import status
from rest_framework.test import APIClient

from ranking.models import (
    PuntajeAplicado,
    PuntajeGeneral,
    Socio,
    SocioEstudio,
    Subcomision,
    TipoSocio,
)


@pytest.fixture
def padron_scale_data(db) -> None:
    """Genera 515 socios con cinco movimientos cada uno y saldos mixtos."""
    sub = Subcomision.objects.create(codSubcomision=1, nombre="Cómputos")
    tipo = TipoSocio.objects.create(idTipoSocio=1, nombre="Socio Ordinario")

    socios_bulk = [
        Socio(
            nroSocio=i,
            nombre=f"Nombre_{i}",
            apellido=f"Apellido_{i}",
            anoSocial=(i % 6) + 1,
            subcomision=sub,
            tipoSocio=tipo,
        )
        for i in range(1, 516)
    ]
    Socio.objects.bulk_create(socios_bulk)

    estudios_bulk = [
        SocioEstudio(
            compositeKey=i * 100 + 1,
            socio_id=i,
            nroLegajo=80000 + i,
            codEspecialidad=1,
        )
        for i in range(1, 516)
    ]
    SocioEstudio.objects.bulk_create(estudios_bulk)

    # Cinco movimientos por socio: totales +3, -3 y 0; ambos estados de reconciliacion.
    movement_patterns = (
        (5.0, -1.5, 0.5, -2.0, 1.0),
        (-5.0, 1.5, -0.5, 2.0, -1.0),
        (2.0, -2.0, 0.5, -1.5, 1.0),
    )
    ptj_gral_bulk = []
    ptj_apl_bulk = []
    for i in range(1, 516):
        movements = movement_patterns[(i - 1) % len(movement_patterns)]
        historical_balance = sum(movements)
        ptj_gral_bulk.append(
            PuntajeGeneral(
                idPuntajeGeneral=i,
                socio_id=i,
                puntos=historical_balance + (0.5 if i % 2 else 0.0),
            )
        )
        for offset, points in enumerate(movements):
            ptj_apl_bulk.append(
                PuntajeAplicado(
                    idPuntajeAplicado=(i - 1) * len(movements) + offset + 1,
                    socio_id=i,
                    puntajeAplicado=points,
                )
            )
    PuntajeGeneral.objects.bulk_create(ptj_gral_bulk)
    PuntajeAplicado.objects.bulk_create(ptj_apl_bulk)
    assert Socio.objects.count() == 515
    assert PuntajeAplicado.objects.count() == 2575


@pytest.mark.django_db
class TestRankingResponseTimePerformance:
    """Benchmark secuencial compatible con SQLite; validar CA4 tambien en MySQL 8 (CI)."""

    def test_ranking_endpoint_p95_latency_under_500ms(self, padron_scale_data) -> None:
        client = APIClient()
        latencies_ms: list[float] = []

        # Calentamiento excluido de las mediciones.
        for _ in range(5):
            response = client.get("/api/v1/ranking/")
            assert response.status_code == status.HTTP_200_OK
            assert len(response.json()) == 515

        data = response.json()
        assert any(item["saldo"] > 0 for item in data)
        assert any(item["saldo"] < 0 for item in data)
        assert any(item["saldo"] == 0 for item in data)
        assert {item["reconciliado"] for item in data} == {True, False}

        # APIClient mide el procesamiento interno, sin red ni servidor HTTP real.
        # El contexto y las aserciones quedan fuera del intervalo cronometrado;
        # la captura SQL permanece activa durante cada GET para detectar N+1.
        for _ in range(100):
            with CaptureQueriesContext(connection) as queries:
                start = time.perf_counter()
                response = client.get("/api/v1/ranking/")
                elapsed = (time.perf_counter() - start) * 1000.0
            assert response.status_code == status.HTTP_200_OK
            assert len(response.json()) == 515
            assert len(queries.captured_queries) == 1
            latencies_ms.append(elapsed)

        # Percentil empirico nearest-rank: posicion ceil(0.95 * N), indice desde cero.
        # Con N=100 selecciona el valor 95 de la lista ordenada (indice 94).
        latencies_sorted = sorted(latencies_ms)
        p95_index = math.ceil(len(latencies_sorted) * 0.95) - 1
        p95_latency = latencies_sorted[p95_index]
        print(
            f"CA4: motor={connection.vendor}, socios=515, movimientos=2575, "
            f"mediciones={len(latencies_ms)}, consultas/GET=1, p95={p95_latency:.2f} ms"
        )
        assert p95_latency <= 500.0, f"Latencia p95 ({p95_latency:.2f} ms) excedio los 500 ms"
