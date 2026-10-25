"""Pruebas de la API de búsqueda de un antecedente por número (S4-03, RF-16 y RF-20)."""

from datetime import UTC, datetime

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from expedientes.models import (
    CambioEstadoExpediente,
    DescargoExpediente,
    EstadoExpedienteEnum,
    Expediente,
    SolicitudT01,
    TipoDescargoEnum,
)
from socios.models import Role

pytestmark = pytest.mark.django_db

URL = "/api/v1/expedientes/antecedentes/"
CARD_FIELDS = {"id", "numero", "fecha_emision", "motivo", "reglamento_invocado"}


def _client(user) -> APIClient:
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def emitido(t03_descargo) -> Expediente:
    expediente = Expediente.objects.create(
        numero="EXP-0007/2026",
        socio=t03_descargo.socio,
        motivo="Inasistencia a la reunión plenaria",
        estado=EstadoExpedienteEnum.EMITIDO,
    )
    cambio = CambioEstadoExpediente.objects.create(
        expediente=expediente,
        estado_anterior=EstadoExpedienteEnum.PENDIENTE_CORREOS,
        estado_nuevo=EstadoExpedienteEnum.EMITIDO,
    )
    CambioEstadoExpediente.objects.filter(pk=cambio.pk).update(
        fecha_hora=datetime(2026, 9, 15, 12, tzinfo=UTC)
    )
    return expediente


@pytest.mark.parametrize("numero", ["7/2026", "007/2026", "EXP-0007/2026"])
def test_tribunal_member_gets_card_200(tribunal_member, emitido, numero) -> None:
    response = _client(tribunal_member.user).get(URL, {"numero": numero})

    assert response.status_code == status.HTTP_200_OK
    assert set(response.data) == CARD_FIELDS
    assert response.data["id"] == emitido.id
    assert response.data["numero"] == "EXP-0007/2026"
    assert response.data["motivo"] == "Inasistencia a la reunión plenaria"
    assert response.data["fecha_emision"].startswith("2026-09-15")


def test_regulation_comes_from_t01_request(tribunal_member, emitido, make_socio) -> None:
    SolicitudT01.objects.create(
        solicitante=make_socio(legajo="77050"),
        tipo_accion=SolicitudT01.TipoAccion.SANCTION,
        causal="Art. 86 del Reglamento Interno",
        puntos=-1,
        destinatarios_socios_ids=[emitido.socio_id],
        estado=SolicitudT01.Estado.ISSUED,
        expediente=emitido,
    )

    response = _client(tribunal_member.user).get(URL, {"numero": "7/2026"})

    assert response.data["reglamento_invocado"] == "Art. 86 del Reglamento Interno"


def test_regulation_defaults_like_the_case_table(tribunal_member, emitido) -> None:
    response = _client(tribunal_member.user).get(URL, {"numero": "7/2026"})

    assert response.data["reglamento_invocado"] == "Reglamento Procesal Disciplinario 2026"


def test_medical_case_card_has_no_descargo_text_causal_or_evidence(
    tribunal_member, t03_descargo, make_evidencia
) -> None:
    emitido = Expediente.objects.create(
        numero="EXP-0904/2026",
        socio=t03_descargo.socio,
        motivo="Inasistencia a la reunión plenaria",
        estado=EstadoExpedienteEnum.EMITIDO,
    )
    descargo = DescargoExpediente.objects.create(
        expediente=emitido,
        socio=emitido.socio,
        tipo=TipoDescargoEnum.T02_CERTIFICADO,
        causal="Enfermedad certificada: gastroenteritis aguda",
        texto="Adjunto certificado médico con diagnóstico y reposo.",
    )
    make_evidencia(emitido, emitido.socio, descargo=descargo, nombre="certificado-medico.pdf")

    response = _client(tribunal_member.user).get(URL, {"numero": "904/2026"})

    assert response.status_code == status.HTTP_200_OK
    assert set(response.data) == CARD_FIELDS
    rendered = repr(dict(response.data)).lower()
    for sensitive in ("gastroenteritis", "certificado", "diagnóstico", "reposo"):
        assert sensitive not in rendered


def test_not_emitted_case_404(tribunal_member, emitido) -> None:
    Expediente.objects.filter(pk=emitido.pk).update(estado=EstadoExpedienteEnum.PENDIENTE_CORREOS)

    response = _client(tribunal_member.user).get(URL, {"numero": "7/2026"})

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.data["detail"] == "No hay un expediente emitido con ese número."


def test_unknown_case_404(tribunal_member) -> None:
    response = _client(tribunal_member.user).get(URL, {"numero": "999/2026"})

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.data["detail"] == "No hay un expediente emitido con ese número."


@pytest.mark.parametrize("params", [{}, {"numero": ""}, {"numero": "  "}, {"numero": "7-2026"}])
def test_empty_or_malformed_number_400(tribunal_member, params) -> None:
    response = _client(tribunal_member.user).get(URL, params)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "número de expediente" in response.data["detail"]


@pytest.mark.parametrize("role", [Role.CD, Role.ADMIN, Role.SOCIO, Role.FISCALIZADORA])
def test_non_tribunal_roles_403(make_socio, emitido, role) -> None:
    other = make_socio(legajo="77051", role=role)

    response = _client(other.user).get(URL, {"numero": "7/2026"})

    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_anonymous_401(emitido) -> None:
    response = APIClient().get(URL, {"numero": "7/2026"})

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
