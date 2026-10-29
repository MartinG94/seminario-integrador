from decimal import Decimal
from io import BytesIO

import pytest
from pypdf import PdfReader

from expedientes.models import Resolucion
from socios.models import Role


def preview_url(expediente_id: int) -> str:
    return f"/api/v1/expedientes/{expediente_id}/resolucion/preview/"


def create_resolution(expediente, user, **overrides):
    values = {
        "expediente": expediente,
        "version": overrides.pop("version", 1),
        "plantilla_version": overrides.pop("plantilla_version", "resolucion-2026.1"),
        "numero_expediente_snapshot": expediente.numero,
        "vistos": overrides.pop("vistos", "Vistos públicos."),
        "considerandos": overrides.pop("considerandos", "Considerandos públicos."),
        "articulos_resolutivos": overrides.pop("articulos_resolutivos", "Artículo 1 público."),
        "created_by": user,
        "puntos_finales": overrides.pop("puntos_finales", Decimal("1.00")),
        "medidas": overrides.pop("medidas", []),
    }
    values.update(overrides)
    return Resolucion.objects.create(**values)


def extract_pdf_text(response) -> str:
    reader = PdfReader(BytesIO(response.content))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


@pytest.mark.django_db
def test_preview_requiere_autenticacion(api_client, causal_expediente):
    assert api_client.get(preview_url(causal_expediente.pk)).status_code == 401


@pytest.mark.django_db
def test_preview_rechaza_usuario_sin_permiso(make_socio, authenticate, causal_expediente):
    socio = make_socio(legajo="76101", role=Role.SOCIO)
    assert authenticate(socio).get(preview_url(causal_expediente.pk)).status_code == 403


@pytest.mark.django_db
def test_preview_devuelve_404_si_no_hay_resolucion(causal_expediente, causal_vocal, authenticate):
    response = authenticate(causal_vocal).get(preview_url(causal_expediente.pk))
    assert response.status_code == 404


@pytest.mark.django_db
def test_preview_devuelve_pdf_del_ultimo_version(causal_expediente, causal_vocal, authenticate):
    create_resolution(causal_expediente, causal_vocal.user, version=1)
    create_resolution(
        causal_expediente,
        causal_vocal.user,
        version=2,
        plantilla_version="resolucion-2026.2",
        vistos="Vistos de la versión dos.",
    )

    response = authenticate(causal_vocal).get(preview_url(causal_expediente.pk))

    assert response.status_code == 200
    assert response["Content-Type"] == "application/pdf"
    assert response["Content-Disposition"].startswith("inline;")
    assert response.content.startswith(b"%PDF")
    text = extract_pdf_text(response)
    assert "EXP-0601/2026" in text
    assert "Versión de resolución: 2" in text
    assert "resolucion-2026.2" in text
    assert "VISTOS" in text
    assert "CONSIDERANDOS" in text
    assert "ARTÍCULOS RESOLUTIVOS" in text


@pytest.mark.django_db
def test_preview_de_borrador_es_identificada_y_no_persiste_cambios(
    causal_expediente, causal_vocal, authenticate
):
    resolucion = create_resolution(causal_expediente, causal_vocal.user)
    before = {
        "estado": resolucion.estado,
        "issued_at": resolucion.issued_at,
        "contenido_hash": resolucion.contenido_hash,
        "puntos_finales": resolucion.puntos_finales,
        "medidas": resolucion.medidas,
        "updated_at": resolucion.updated_at,
    }

    response = authenticate(causal_vocal).get(preview_url(causal_expediente.pk))
    resolucion.refresh_from_db()

    assert response.status_code == 200
    assert "BORRADOR - SIN VALIDEZ OFICIAL" in extract_pdf_text(response)
    assert {key: getattr(resolucion, key) for key in before} == before


@pytest.mark.django_db
def test_preview_no_incluye_medidas_privadas_ni_votos_nominales(
    causal_expediente, causal_vocal, authenticate
):
    private_text = "ADJUNTO PRIVADO - VOTO NOMINAL CONFIDENCIAL"
    create_resolution(
        causal_expediente,
        causal_vocal.user,
        medidas=[private_text],
        vistos="Solo contenido público.",
        considerandos="Solo considerandos públicos.",
        articulos_resolutivos="Solo artículos públicos.",
    )

    response = authenticate(causal_vocal).get(preview_url(causal_expediente.pk))

    assert response.status_code == 200
    text = extract_pdf_text(response)
    assert private_text not in text


@pytest.mark.django_db
def test_preview_preserva_texto_extenso_en_varias_paginas(
    causal_expediente, causal_vocal, authenticate
):
    resolucion = create_resolution(
        causal_expediente,
        causal_vocal.user,
        vistos="MARCADOR-INICIO " + ("Vistos extensos. " * 180),
        considerandos=("Considerandos extensos. " * 180) + " MARCADOR-MEDIO ",
        articulos_resolutivos=("Artículos resolutivos extensos. " * 180) + " MARCADOR-FINAL",
    )
    issued_at = resolucion.issued_at
    contenido_hash = resolucion.contenido_hash

    response = authenticate(causal_vocal).get(preview_url(causal_expediente.pk))

    assert response.status_code == 200
    assert response.content.startswith(b"%PDF")
    text = extract_pdf_text(response)
    assert len(PdfReader(BytesIO(response.content)).pages) >= 2
    assert "MARCADOR-INICIO" in text
    assert "MARCADOR-MEDIO" in text
    assert "MARCADOR-FINAL" in text

    resolucion.refresh_from_db()
    assert resolucion.estado == "DRAFT"
    assert resolucion.issued_at == issued_at
    assert resolucion.contenido_hash == contenido_hash
