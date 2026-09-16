"""Pruebas de rendimiento del endpoint de Ranking (SLA p95 ≤ 500ms)."""

import time

import pytest
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
    """Genera una muestra ampliada de socios para validar rendimiento bajo volumen."""
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
        for i in range(1, 101)  # 100 socios representativos
    ]
    Socio.objects.bulk_create(socios_bulk)

    estudios_bulk = [
        SocioEstudio(
            compositeKey=i * 100 + 1,
            socio_id=i,
            nroLegajo=80000 + i,
            codEspecialidad=1,
        )
        for i in range(1, 101)
    ]
    SocioEstudio.objects.bulk_create(estudios_bulk)

    ptj_gral_bulk = [
        PuntajeGeneral(
            idPuntajeGeneral=i,
            socio_id=i,
            puntos=float(i % 10),
        )
        for i in range(1, 101)
    ]
    PuntajeGeneral.objects.bulk_create(ptj_gral_bulk)

    ptj_apl_bulk = [
        PuntajeAplicado(
            idPuntajeAplicado=i,
            socio_id=i,
            puntajeAplicado=float(i % 10),
        )
        for i in range(1, 101)
    ]
    PuntajeAplicado.objects.bulk_create(ptj_apl_bulk)


@pytest.mark.django_db
class TestRankingResponseTimePerformance:
    """Verificación de tiempos de respuesta del endpoint de ranking bajo percentil 95."""

    def test_ranking_endpoint_p95_latency_under_500ms(self, padron_scale_data) -> None:
        client = APIClient()
        latencies_ms: list[float] = []

        # Ejecutar 20 consultas consecutivas midiendo latencia de extremo a extremo
        for _ in range(20):
            start = time.perf_counter()
            response = client.get("/api/v1/ranking/")
            elapsed = (time.perf_counter() - start) * 1000.0  # ms
            assert response.status_code == status.HTTP_200_OK
            latencies_ms.append(elapsed)

        latencies_sorted = sorted(latencies_ms)
        p95_index = int(len(latencies_sorted) * 0.95)
        p95_latency = latencies_sorted[p95_index]

        # El requerimiento S1-05 exige p95 ≤ 500 ms
        assert p95_latency <= 500.0, f"Latencia p95 ({p95_latency:.2f} ms) excedió los 500 ms"
