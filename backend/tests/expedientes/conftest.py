"""Fixtures compartidas para las pruebas de decisión por causal T02 (S4-02)."""

import hashlib

import pytest

from expedientes.models import (
    DescargoExpediente,
    EstadoExpedienteEnum,
    EvidenciaDescargo,
    Expediente,
    TipoDescargoEnum,
)
from socios.models import Role, Socio

PDF_BYTES = b"%PDF-1.4 certificado medico"


@pytest.fixture
def causal_imputado(make_socio) -> Socio:
    return make_socio(legajo="76001", role=Role.SOCIO)


@pytest.fixture
def causal_vocal(make_socio) -> Socio:
    return make_socio(legajo="76002", role=Role.TD, social_year=5)


@pytest.fixture
def causal_expediente(causal_imputado) -> Expediente:
    expediente = Expediente.objects.create(
        numero="EXP-0601/2026",
        socio=causal_imputado,
        motivo="Inasistencia a reunión plenaria",
        estado=EstadoExpedienteEnum.REVISION_RESOLUCION,
    )
    expediente.socios.add(causal_imputado)
    return expediente


@pytest.fixture
def causal_descargo(causal_expediente, causal_imputado) -> DescargoExpediente:
    return DescargoExpediente.objects.create(
        expediente=causal_expediente,
        socio=causal_imputado,
        tipo=TipoDescargoEnum.T02_CERTIFICADO,
        causal="Enfermedad certificada por profesional médico",
        texto="Adjunto certificado médico del día de la reunión.",
    )


@pytest.fixture
def causal_evidencia(causal_descargo) -> EvidenciaDescargo:
    return EvidenciaDescargo.objects.create(
        expediente=causal_descargo.expediente,
        descargo=causal_descargo,
        socio=causal_descargo.socio,
        contenido_blob=PDF_BYTES,
        nombre_original="certificado.pdf",
        extension=".pdf",
        mime_type="application/pdf",
        tamanio_bytes=len(PDF_BYTES),
        sha256_hash=hashlib.sha256(PDF_BYTES).hexdigest(),
    )
