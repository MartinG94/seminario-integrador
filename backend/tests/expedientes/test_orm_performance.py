"""Pruebas de rendimiento ORM y límites estrictos de consultas SQL (SCRUM-120 / T-87.04).

Valida la erradicación de patrones N+1 y complejidad constante O(1):
1. Eventos institucionales: totales de asistencia anotados (<= 3 queries).
2. Expedientes: defer("contenido_blob") en prefetch de evidencias.
3. Antecedentes: Subquery correlacionada indexada para fecha de emisión (1 query).
4. Antecedentes referenciados: build_expedientes_referenciados_detalle en 1 query.
5. Reportes por subcomisión: batching de puntajes sobre tribunal_puntajegeneral.
"""

import hashlib
from datetime import timedelta
from decimal import Decimal

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone
from rest_framework import status

from expedientes.models import (
    AsistenciaEvento,
    CambioEstadoExpediente,
    CategoriaEventoEnum,
    EstadoAsistenciaEventoEnum,
    EstadoEventoEnum,
    EstadoExpedienteEnum,
    EventoInstitucional,
    EvidenciaDescargo,
    Expediente,
    ModalidadEventoEnum,
    SubtipoReunionEnum,
)
from expedientes.services.reportes_service import ReportesService
from expedientes.services.t03_valuation_service import (
    build_expedientes_referenciados_detalle,
)
from ranking.models import PuntajeGeneral
from socios.models import Role
from tests.legacy_schema import create_legacy_record


@pytest.fixture
def create_evento_con_asistencias(make_socio, subcomision):
    """Crea un EventoInstitucional con un número arbitrario de asistencias."""
    counter = [0]

    def _create(titulo: str = "Evento Test", cant_asistencias: int = 10) -> EventoInstitucional:
        counter[0] += 1
        convocante = make_socio(legajo=f"90{counter[0]:04d}")
        ahora = timezone.now()
        evento = EventoInstitucional.objects.create(
            titulo=titulo,
            descripcion="Descripción del evento para test de rendimiento",
            categoria=CategoriaEventoEnum.REUNION,
            tipo=SubtipoReunionEnum.ORDINARIA,
            modalidad=ModalidadEventoEnum.PRESENCIAL_SEDE,
            lugar="Sede Central AVEIT",
            fecha_publicacion=ahora,
            fecha_programada=ahora + timedelta(days=5),
            estado=EstadoEventoEnum.PROGRAMADA,
            convocante=convocante,
            subcomision=subcomision,
        )
        estados = [
            EstadoAsistenciaEventoEnum.PRESENTE,
            EstadoAsistenciaEventoEnum.AUSENTE,
            EstadoAsistenciaEventoEnum.JUSTIFICADO,
            EstadoAsistenciaEventoEnum.TARDE_LEVE,
        ]
        for i in range(cant_asistencias):
            counter[0] += 1
            socio = make_socio(legajo=f"91{counter[0]:04d}")
            AsistenciaEvento.objects.create(
                evento=evento,
                socio=socio,
                estado_asistencia=estados[i % len(estados)],
            )
        return evento

    return _create


@pytest.fixture
def create_expediente_emitido(make_socio):
    """Crea un expediente emitido con registro formal de cambio de estado hacia emitido."""
    counter = [0]

    def _create(numero: str = "EXP-0100/2026") -> Expediente:
        counter[0] += 1
        imputado = make_socio(legajo=f"92{counter[0]:04d}")
        expediente = Expediente.objects.create(
            numero=numero,
            socio=imputado,
            motivo="Causa emitida de antecedente",
            puntos=Decimal("-1.00"),
            estado=EstadoExpedienteEnum.EMITIDO,
        )
        expediente.socios.add(imputado)
        cambio = CambioEstadoExpediente.objects.create(
            expediente=expediente,
            estado_anterior=EstadoExpedienteEnum.REVISION_RESOLUCION,
            estado_nuevo=EstadoExpedienteEnum.EMITIDO,
        )
        CambioEstadoExpediente.objects.filter(pk=cambio.pk).update(
            fecha_hora=timezone.now() - timedelta(days=10)
        )
        return expediente

    return _create


@pytest.fixture
def create_expediente_con_evidencia(make_socio):
    """Crea un expediente con archivo adjunto binario simulado de tamaño configurable."""
    counter = [0]

    def _create(tamanio_bytes: int = 1024 * 1024) -> Expediente:
        counter[0] += 1
        imputado = make_socio(legajo=f"93{counter[0]:04d}")
        expediente = Expediente.objects.create(
            numero=f"EXP-EV{counter[0]:04d}/2026",
            socio=imputado,
            motivo="Causa para test de defer de evidencias",
            estado=EstadoExpedienteEnum.REVISION_RESOLUCION,
        )
        expediente.socios.add(imputado)
        blob = b"X" * tamanio_bytes
        EvidenciaDescargo.objects.create(
            expediente=expediente,
            socio=imputado,
            contenido_blob=blob,
            nombre_original="prueba.pdf",
            extension=".pdf",
            mime_type="application/pdf",
            tamanio_bytes=tamanio_bytes,
            sha256_hash=hashlib.sha256(blob).hexdigest(),
            es_vigente=True,
        )
        return expediente

    return _create


@pytest.mark.django_db
def test_eventos_listing_queries_are_constant(
    api_client, make_socio, create_evento_con_asistencias, django_assert_num_queries
):
    """Verifica que el listado de eventos no ejecute consultas N+1 por asistencias."""
    user_td = make_socio(legajo="79001", role=Role.TD).user
    api_client.force_authenticate(user=user_td)

    # 1. Creamos 2 eventos con 10 asistencias cada uno
    for i in range(2):
        create_evento_con_asistencias(titulo=f"Evento Base {i}", cant_asistencias=10)

    with CaptureQueriesContext(connection) as ctx:
        res = api_client.get("/api/v1/expedientes/eventos/?page=1&page_size=20")
    assert res.status_code == status.HTTP_200_OK
    baseline_queries = len(ctx.captured_queries)

    # Se exige un límite estricto de <= 3 consultas SQL en list (EARS-E06)
    assert baseline_queries <= 3, (
        f"Se esperaban <= 3 consultas SQL en listado de eventos, hubo {baseline_queries}."
    )

    # 2. Agregamos 5 eventos adicionales con 5 asistencias cada uno
    for i in range(5):
        create_evento_con_asistencias(titulo=f"Evento Extra {i}", cant_asistencias=5)

    # El número de consultas debe mantenerse IDÉNTICO (O(1))
    with django_assert_num_queries(baseline_queries):
        res2 = api_client.get("/api/v1/expedientes/eventos/?page=1&page_size=20")
    assert res2.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_expedientes_listing_defers_binary_blob(
    api_client, make_socio, create_expediente_con_evidencia
):
    """Verifica que el listado de expedientes no cargue el contenido_blob de EvidenciaDescargo."""
    user_td = make_socio(legajo="79003", role=Role.TD).user
    api_client.force_authenticate(user=user_td)

    # Creamos un expediente con un archivo adjunto simulado de 2 MB
    create_expediente_con_evidencia(tamanio_bytes=2 * 1024 * 1024)

    with CaptureQueriesContext(connection) as ctx:
        res = api_client.get("/api/v1/expedientes/gestion/?page=1&page_size=20")
    assert res.status_code == status.HTTP_200_OK

    # Inspeccionamos las consultas SQL capturadas: ninguna debe seleccionar contenido_blob
    evidencia_queries = [
        q["sql"]
        for q in ctx.captured_queries
        if "expedientes_evidencia_descargo" in q["sql"].lower()
    ]
    assert len(evidencia_queries) > 0, "No se ejecutó la consulta de prefetch de evidencias."
    for sql in evidencia_queries:
        assert "contenido_blob" not in sql.lower(), (
            "El campo binario contenido_blob fue seleccionado indebidamente."
        )


@pytest.mark.django_db
def test_antecedentes_catalogo_single_query(
    api_client, make_socio, create_expediente_emitido, django_assert_num_queries
):
    """Verifica que el catálogo de antecedentes no ejecute N consultas para fecha_emision."""
    socio_td = make_socio(legajo="79002", role=Role.TD)
    user = socio_td.user
    user.socio = socio_td
    api_client.force_authenticate(user=user)

    for i in range(25):
        create_expediente_emitido(numero=f"EXP-{100 + i}/2026")

    # Debe ejecutarse en exactamente UNA consulta SQL
    with django_assert_num_queries(1):
        res = api_client.get("/api/v1/expedientes/antecedentes/?catalogo=1")
    assert res.status_code == status.HTTP_200_OK
    assert len(res.json()) >= 25
    assert all("fecha_emision" in item for item in res.json())


@pytest.mark.django_db
def test_expedientes_referenciados_detalle_constant_query(
    create_expediente_emitido, django_assert_num_queries
):
    """Verifica que build_expedientes_referenciados_detalle ejecute 1 consulta."""
    expedientes = [create_expediente_emitido(numero=f"EXP-{200 + i}/2026") for i in range(10)]
    ids = [exp.id for exp in expedientes]

    with django_assert_num_queries(1):
        resultado = build_expedientes_referenciados_detalle(ids)

    assert len(resultado) == 10
    assert all("fecha_emision" in item for item in resultado)


@pytest.mark.django_db
def test_subcomision_metrics_batch_query(make_socio, subcomision):
    """Verifica que obtener_metricas_subcomision no ejecute consultas en bucle."""
    socios = [
        make_socio(legajo=f"79{100 + i:03d}", role=Role.SOCIO, social_year=2) for i in range(10)
    ]
    for s in socios:
        create_legacy_record(
            PuntajeGeneral,
            socio_id=int(s.user.username),
            puntos=Decimal("15.50"),
        )

    with CaptureQueriesContext(connection) as ctx:
        metricas = ReportesService.obtener_metricas_subcomision(subcomision.id)

    assert "tabla_socios" in metricas
    # Verificar cuántas consultas SQL se ejecutaron sobre tribunal_puntajegeneral
    pg_queries = [
        q["sql"] for q in ctx.captured_queries if "tribunal_puntajegeneral" in q["sql"].lower()
    ]
    # Con batching debe ser como máximo 1 consulta SQL, nunca 1 por cada socio (10)
    assert len(pg_queries) <= 1, (
        f"Se ejecutaron {len(pg_queries)} queries a puntajegeneral; se esperaba <= 1 en batch."
    )


@pytest.mark.django_db
def test_involucrados_subcomision_preloaded(api_client, make_socio, subcomision):
    """Verifica que el listado de expedientes precargue subcomision en socios sin queries N+1."""
    user_td = make_socio(legajo="79004", role=Role.TD).user
    api_client.force_authenticate(user=user_td)

    # Creamos 3 expedientes con 2 socios involucrados cada uno
    for i in range(3):
        imputado1 = make_socio(legajo=f"7941{i}")
        imputado2 = make_socio(legajo=f"7942{i}")
        exp = Expediente.objects.create(
            numero=f"EXP-SUB{i:02d}/2026",
            socio=imputado1,
            motivo="Causa test subcomision prefetch",
            estado=EstadoExpedienteEnum.REVISION_RESOLUCION,
        )
        exp.socios.add(imputado1, imputado2)

    with CaptureQueriesContext(connection) as ctx:
        res = api_client.get("/api/v1/expedientes/gestion/?page=1&page_size=20")
    assert res.status_code == status.HTTP_200_OK

    # Verificar que en el prefetch de socios se use select_related('subcomision')
    socio_prefetch_queries = [
        q["sql"]
        for q in ctx.captured_queries
        if "socios_socio" in q["sql"].lower() and "socios_subcomision" in q["sql"].lower()
    ]
    assert len(socio_prefetch_queries) >= 1, (
        "El prefetch de socios involucrados debe hacer JOIN con subcomision para precargarla."
    )
