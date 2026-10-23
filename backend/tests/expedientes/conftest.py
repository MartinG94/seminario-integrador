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
def make_evidencia():
    """Crea un comprobante vigente; sin `descargo`, queda huérfano del socio."""

    def _make(
        expediente: Expediente,
        socio: Socio,
        descargo: DescargoExpediente | None = None,
        nombre: str = "certificado.pdf",
    ) -> EvidenciaDescargo:
        return EvidenciaDescargo.objects.create(
            expediente=expediente,
            descargo=descargo,
            socio=socio,
            contenido_blob=PDF_BYTES,
            nombre_original=nombre,
            extension=".pdf",
            mime_type="application/pdf",
            tamanio_bytes=len(PDF_BYTES),
            sha256_hash=hashlib.sha256(PDF_BYTES).hexdigest(),
        )

    return _make


@pytest.fixture
def causal_evidencia(causal_descargo, make_evidencia) -> EvidenciaDescargo:
    return make_evidencia(
        causal_descargo.expediente, causal_descargo.socio, descargo=causal_descargo
    )


@pytest.fixture
def multiactor(causal_descargo, make_socio, make_evidencia) -> dict:
    """Expediente con dos imputados T02 y comprobantes vinculados y huérfanos cruzados."""
    expediente = causal_descargo.expediente
    otro = make_socio(legajo="76004")
    expediente.socios.add(otro)
    otro_descargo = DescargoExpediente.objects.create(
        expediente=expediente,
        socio=otro,
        tipo=TipoDescargoEnum.T02_CERTIFICADO,
        causal="Actividad laboral",
    )
    return {
        "descargo": causal_descargo,
        "otro_descargo": otro_descargo,
        "vinculada": make_evidencia(
            expediente, causal_descargo.socio, descargo=causal_descargo, nombre="propia.pdf"
        ),
        "huerfana": make_evidencia(expediente, causal_descargo.socio, nombre="huerfana.pdf"),
        "ajena_vinculada": make_evidencia(
            expediente, otro, descargo=otro_descargo, nombre="ajena.pdf"
        ),
        "ajena_huerfana": make_evidencia(expediente, otro, nombre="ajena-huerfana.pdf"),
    }


# --- Expediente originado en un T01 (PB-02) ---


@pytest.fixture
def t01_solicitante(make_socio) -> Socio:
    return make_socio(legajo="78001", role=Role.FISCALIZADORA, social_year=5)


@pytest.fixture
def t01_involucrados(make_socio) -> list[Socio]:
    return [make_socio(legajo="78002"), make_socio(legajo="78003")]


@pytest.fixture
def t01_expediente(t01_solicitante, t01_involucrados) -> Expediente:
    """Expediente CREADO vinculado a una solicitud T01 emitida (versión original inmutable)."""
    from decimal import Decimal

    from django.utils import timezone

    from expedientes.models import SolicitudT01

    expediente = Expediente.objects.create(
        numero="EXP-0701/2026",
        socio=t01_involucrados[0],
        motivo="Uso indebido del laboratorio",
        puntos=Decimal("-2"),
        estado=EstadoExpedienteEnum.CREADO,
    )
    expediente.socios.set(t01_involucrados)
    SolicitudT01.objects.create(
        estado=SolicitudT01.Estado.ISSUED,
        solicitante=t01_solicitante,
        destinatarios_socios_ids=[s.id for s in t01_involucrados],
        tipo_accion=SolicitudT01.TipoAccion.SANCTION,
        titulo="Uso indebido del laboratorio",
        puntos=Decimal("-2"),
        motivo="Uso indebido del laboratorio",
        snapshot_emitido={"puntos": "-2.00", "titulo": "Uso indebido del laboratorio"},
        numero_expediente="T01-2026-PB02TEST0001",
        expediente=expediente,
        issued_at=timezone.now(),
    )
    return expediente
