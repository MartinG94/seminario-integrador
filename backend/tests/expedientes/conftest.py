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


# --- Nómina del Tribunal en el padrón legado (S4-04) ---

CARGO_TITULAR_TD = 10
CARGO_SUPLENTE_TD = 11
CARGO_SOCIO_ORDINARIO = 12


@pytest.fixture
def make_legacy_socio(make_socio):
    """Crea la cuenta local y su ficha en `socio_lista` vinculada por `user_id`."""
    from datetime import datetime, timezone

    from padron.models import Socio as LegacySocio
    from padron.models import SocioEstadoHistorial
    from tests.legacy_schema import create_legacy_record

    def _make(
        nro_socio: int,
        social_year: int,
        cargo: int = CARGO_SOCIO_ORDINARIO,
        role: str = Role.SOCIO,
        grupo: int | None = None,
        is_enabled: bool = True,
        linked: bool = True,
    ) -> Socio:
        socio = make_socio(
            legajo=str(nro_socio), role=role, social_year=social_year, is_enabled=is_enabled
        )
        legacy = create_legacy_record(
            LegacySocio,
            nroSocio=nro_socio,
            apellido=socio.last_name,
            nombre=socio.first_name,
            anoSocial=social_year,
            idTipoSocio=cargo,
            user_id=socio.user_id if linked else None,
        )
        if grupo is not None:
            create_legacy_record(
                SocioEstadoHistorial,
                idGrupo=grupo,
                socio=legacy,
                fechaHora=datetime(2026, 3, 1, tzinfo=timezone.utc),
                codEstadoSocio=1,
                socio_motivoCambioEstado=1,
            )
        return socio

    return _make


@pytest.fixture
def tribunal_nomina(make_legacy_socio) -> dict[str, Socio]:
    """Nómina estatutaria completa: un titular y un suplente por 4.º, 5.º y 6.º año."""
    return {
        "t4": make_legacy_socio(81004, 4, CARGO_TITULAR_TD, Role.TD, grupo=59),
        "s4": make_legacy_socio(82004, 4, CARGO_SUPLENTE_TD, Role.TD, grupo=59),
        "t5": make_legacy_socio(81005, 5, CARGO_TITULAR_TD, Role.TD, grupo=58),
        "s5": make_legacy_socio(82005, 5, CARGO_SUPLENTE_TD, Role.TD, grupo=58),
        "t6": make_legacy_socio(81006, 6, CARGO_TITULAR_TD, Role.TD, grupo=57),
        "s6": make_legacy_socio(82006, 6, CARGO_SUPLENTE_TD, Role.TD, grupo=57),
    }
