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
CARD_FIELDS = {
    "id",
    "numero",
    "titulo",
    "fecha_emision",
    "motivo",
    "puntos",
    "tipo_accion",
    "reglamento_invocado",
}


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


def test_common_socio_role_403(make_socio, emitido) -> None:
    other = make_socio(legajo="77051", role=Role.SOCIO)

    response = _client(other.user).get(URL, {"numero": "7/2026"})

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.parametrize("role", [Role.CD, Role.ADMIN, Role.FISCALIZADORA])
def test_authorized_roles_can_access(make_socio, emitido, role) -> None:
    auth_user = make_socio(legajo=f"7705{role}", role=role)

    response = _client(auth_user.user).get(URL, {"numero": "7/2026"})

    assert response.status_code == status.HTTP_200_OK
    assert response.data["id"] == emitido.id


def test_anonymous_401(emitido) -> None:
    response = APIClient().get(URL, {"numero": "7/2026"})

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_catalogo_lista_expedientes_emitidos(tribunal_member, emitido) -> None:
    # Expediente no emitido no debe aparecer
    Expediente.objects.create(
        numero="EXP-9999/2026",
        socio=emitido.socio,
        motivo="En tramite",
        estado=EstadoExpedienteEnum.JUSTIFICANDO,
    )

    response = _client(tribunal_member.user).get(URL, {"catalogo": "1"})

    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.data, list)
    numeros = [item["numero"] for item in response.data]
    assert "EXP-0007/2026" in numeros
    assert "EXP-9999/2026" not in numeros


def test_catalogo_filtra_por_tipo_sanction_y_merit(tribunal_member, make_socio) -> None:
    socio = make_socio(legajo="77088")
    sancion = Expediente.objects.create(
        numero="EXP-0101/2026",
        socio=socio,
        motivo="Falta grave",
        puntos=-2,
        estado=EstadoExpedienteEnum.EMITIDO,
    )
    merito = Expediente.objects.create(
        numero="EXP-0102/2026",
        socio=socio,
        motivo="Reconocimiento institucional",
        puntos=3,
        estado=EstadoExpedienteEnum.EMITIDO,
    )

    client = _client(tribunal_member.user)
    res_sancion = client.get(URL, {"catalogo": "1", "tipo": "SANCTION"})
    assert res_sancion.status_code == status.HTTP_200_OK
    sancion_ids = [item["id"] for item in res_sancion.data]
    assert sancion.id in sancion_ids
    assert merito.id not in sancion_ids

    res_merito = client.get(URL, {"catalogo": "1", "tipo": "MERIT"})
    assert res_merito.status_code == status.HTTP_200_OK
    merito_ids = [item["id"] for item in res_merito.data]
    assert merito.id in merito_ids
    assert sancion.id not in merito_ids


def test_catalogo_filtra_por_search_y_exclude_id(tribunal_member, make_socio) -> None:
    socio_especial = make_socio(legajo="99441")
    socio_especial.first_name = "Alfonso"
    socio_especial.last_name = "Quijano"
    socio_especial.save(update_fields=["first_name", "last_name"])
    exp1 = Expediente.objects.create(
        numero="EXP-0301/2026",
        titulo="Investigación de laboratorio",
        socio=socio_especial,
        motivo="Rotura de probeta",
        estado=EstadoExpedienteEnum.EMITIDO,
    )
    exp2 = Expediente.objects.create(
        numero="EXP-0302/2026",
        titulo="Otra causa distinta",
        socio=socio_especial,
        motivo="Llegada tarde",
        estado=EstadoExpedienteEnum.EMITIDO,
    )

    client = _client(tribunal_member.user)
    # Búsqueda por texto (nombre/apellido/título/motivo)
    res_search = client.get(URL, {"catalogo": "1", "search": "Quijano"})
    assert res_search.status_code == status.HTTP_200_OK
    ids_found = [item["id"] for item in res_search.data]
    assert exp1.id in ids_found
    assert exp2.id in ids_found

    # Exclusión de id
    res_exclude = client.get(URL, {"catalogo": "1", "search": "Quijano", "exclude_id": exp1.id})
    assert res_exclude.status_code == status.HTTP_200_OK
    ids_exclude = [item["id"] for item in res_exclude.data]
    assert exp1.id not in ids_exclude
    assert exp2.id in ids_exclude
