"""Versionado de descargos al presentar, corregir y retirar (SCRUM-49 / S3-05, tareas T5 a T7).

Cubre, a través de la API pública:
1. Alta: versión 1 ``PRESENTADO`` con el contenido enviado.
2. Corrección en plazo: versión nueva ``CORREGIDO``; la anterior queda intacta.
3. Cambio de modalidad T03 -> T02: reemplaza el descargo vigente y queda como versión.
4. Juego de evidencias por versión (la historia no se reescribe).
5. Copias ``Expediente.descargo_*`` sincronizadas con la última versión.
6. Fuera de plazo: ninguna versión nueva.
7. Retiro lógico: sin borrado físico, con versión ``RETIRADO``.
8. Re-presentación tras el retiro: la numeración continúa.
"""

from datetime import timedelta

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from rest_framework import status

from expedientes.models import (
    CambioEstadoExpediente,
    DescargoExpediente,
    DescargoVersion,
    EstadoExpedienteEnum,
    EvidenciaDescargo,
    Expediente,
    OperacionDescargoEnum,
    TipoDescargoEnum,
)
from socios.models import Role

T03 = TipoDescargoEnum.T03_EXTRAORDINARIO
T02 = TipoDescargoEnum.T02_CERTIFICADO


@pytest.fixture
def socio(make_socio):
    return make_socio(legajo="74907")


@pytest.fixture
def expediente(socio):
    exp = Expediente.objects.create(
        numero="EXP-601/2026",
        socio=socio,
        motivo="Versionado de descargos",
        estado=EstadoExpedienteEnum.JUSTIFICANDO,
        plazo_inicio_at=timezone.now() - timedelta(days=1),
        plazo_limite_at=timezone.now() + timedelta(days=3),
    )
    exp.socios.add(socio)
    return exp


@pytest.fixture
def client(api_client, socio):
    api_client.force_authenticate(user=socio.user)
    return api_client


def _url(expediente: Expediente) -> str:
    return f"/api/v1/expedientes/{expediente.id}/descargo/"


def _evidencia(expediente: Expediente, socio, nombre: str, hash_char: str) -> EvidenciaDescargo:
    return EvidenciaDescargo.objects.create(
        expediente=expediente,
        socio=socio,
        contenido_blob=b"%PDF-1.4 prueba",
        nombre_original=nombre,
        extension=".pdf",
        mime_type="application/pdf",
        tamanio_bytes=15,
        sha256_hash=hash_char * 64,
    )


@pytest.mark.django_db(transaction=True)
class TestVersionadoAlPresentarYCorregir:
    def test_alta_crea_version_1_presentado_con_el_contenido_enviado(
        self, client, socio, expediente
    ) -> None:
        response = client.post(
            _url(expediente),
            {"tipo": T03, "causal": "Otro", "texto": "Primera exposición."},
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED
        version = DescargoVersion.objects.get(descargo__expediente=expediente)
        assert version.numero == 1
        assert version.operacion == OperacionDescargoEnum.PRESENTADO
        assert version.tipo == T03
        assert version.causal == "Otro"
        assert version.texto == "Primera exposición."
        assert version.actor == f"SOCIO_{socio.legajo}"

    def test_correccion_en_plazo_crea_version_nueva_y_conserva_la_anterior(
        self, client, expediente
    ) -> None:
        client.post(_url(expediente), {"tipo": T03, "texto": "Texto v1."}, format="json")

        response = client.post(_url(expediente), {"tipo": T03, "texto": "Texto v2."}, format="json")

        assert response.status_code == status.HTTP_200_OK
        versiones = list(DescargoVersion.objects.filter(descargo__expediente=expediente))
        assert [(v.numero, v.operacion, v.texto) for v in versiones] == [
            (1, OperacionDescargoEnum.PRESENTADO, "Texto v1."),
            (2, OperacionDescargoEnum.CORREGIDO, "Texto v2."),
        ]
        assert DescargoExpediente.objects.filter(expediente=expediente).count() == 1

    def test_cambio_de_t03_a_t02_reemplaza_el_vigente_y_queda_como_version(
        self, client, expediente
    ) -> None:
        client.post(_url(expediente), {"tipo": T03, "texto": "Descargo libre."}, format="json")

        response = client.post(
            _url(expediente), {"tipo": T02, "archivo": "certificado.pdf"}, format="json"
        )

        assert response.status_code == status.HTTP_200_OK
        v1, v2 = DescargoVersion.objects.filter(descargo__expediente=expediente)
        assert (v1.tipo, v1.texto) == (T03, "Descargo libre.")
        assert (v2.tipo, v2.archivo, v2.operacion) == (
            T02,
            "certificado.pdf",
            OperacionDescargoEnum.CORREGIDO,
        )
        assert DescargoExpediente.objects.get(expediente=expediente).tipo == T02

    def test_cada_version_conserva_su_propio_juego_de_evidencias(
        self, client, socio, expediente
    ) -> None:
        ev_a = _evidencia(expediente, socio, "a.pdf", "a")
        ev_b = _evidencia(expediente, socio, "b.pdf", "b")

        client.post(
            _url(expediente),
            {"tipo": T03, "texto": "Con A.", "evidencia_ids": [str(ev_a.id)]},
            format="json",
        )
        client.post(
            _url(expediente),
            {"tipo": T03, "texto": "Con B.", "evidencia_ids": [str(ev_b.id)]},
            format="json",
        )

        v1, v2 = DescargoVersion.objects.filter(descargo__expediente=expediente)
        assert list(v1.evidencias.all()) == [ev_a]
        assert list(v2.evidencias.all()) == [ev_b]
        ev_a.refresh_from_db()
        assert ev_a.es_vigente is False

    def test_copias_del_expediente_siguen_la_ultima_version(self, client, expediente) -> None:
        client.post(_url(expediente), {"tipo": T03, "texto": "Texto v1."}, format="json")
        client.post(_url(expediente), {"tipo": T03, "texto": "Texto v2."}, format="json")

        expediente.refresh_from_db()
        ultima = DescargoVersion.objects.filter(descargo__expediente=expediente).last()
        assert expediente.descargo_texto == ultima.texto == "Texto v2."
        assert expediente.descargo_tipo == ultima.tipo

    def test_envio_fuera_de_plazo_no_crea_versiones(self, client, expediente) -> None:
        expediente.plazo_limite_at = timezone.now() - timedelta(minutes=1)
        expediente.save(update_fields=["plazo_limite_at"])

        response = client.post(_url(expediente), {"tipo": T03, "texto": "Tarde."}, format="json")

        assert response.status_code == status.HTTP_409_CONFLICT
        assert not DescargoVersion.objects.filter(descargo__expediente=expediente).exists()


@pytest.mark.django_db(transaction=True)
class TestRetiroLogicoYRepresentacion:
    def test_retiro_no_elimina_filas_y_registra_version_retirado(
        self, client, socio, expediente
    ) -> None:
        evidencia = _evidencia(expediente, socio, "a.pdf", "a")
        client.post(
            _url(expediente),
            {"tipo": T03, "texto": "Escrito.", "evidencia_ids": [str(evidencia.id)]},
            format="json",
        )

        response = client.delete(_url(expediente))

        assert response.status_code == status.HTTP_200_OK
        descargo = DescargoExpediente.objects.get(expediente=expediente, socio=socio)
        assert descargo.es_vigente is False
        assert descargo.texto == "Escrito."
        ultima = descargo.versiones.last()
        assert (ultima.numero, ultima.operacion) == (2, OperacionDescargoEnum.RETIRADO)
        assert ultima.texto == "Escrito."
        assert EvidenciaDescargo.objects.filter(pk=evidencia.pk).exists()
        evidencia.refresh_from_db()
        assert evidencia.es_vigente is False

    def test_retiro_mantiene_el_contrato_externo_y_el_historial_de_estados(
        self, client, socio, expediente
    ) -> None:
        client.post(_url(expediente), {"tipo": T03, "texto": "Escrito."}, format="json")

        response = client.delete(_url(expediente))

        assert response.json() == {"detail": "Justificativo eliminado correctamente."}
        expediente.refresh_from_db()
        assert expediente.descargo_presentado is False
        assert expediente.descargo_texto == ""
        cambio = CambioEstadoExpediente.objects.filter(expediente=expediente).latest("id")
        assert cambio.motivo == "Eliminación de descargo dentro del plazo reglamentario."

    def test_retiro_fuera_de_plazo_no_cambia_nada(self, client, socio, expediente) -> None:
        client.post(_url(expediente), {"tipo": T03, "texto": "Escrito."}, format="json")
        expediente.plazo_limite_at = timezone.now() - timedelta(minutes=1)
        expediente.save(update_fields=["plazo_limite_at"])

        response = client.delete(_url(expediente))

        assert response.status_code == status.HTTP_409_CONFLICT
        descargo = DescargoExpediente.objects.get(expediente=expediente, socio=socio)
        assert descargo.es_vigente is True
        assert descargo.versiones.count() == 1

    def test_representar_tras_retiro_continua_la_numeracion(
        self, client, socio, expediente
    ) -> None:
        client.post(_url(expediente), {"tipo": T03, "texto": "Primero."}, format="json")
        client.delete(_url(expediente))

        response = client.post(_url(expediente), {"tipo": T03, "texto": "Segundo."}, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        descargo = DescargoExpediente.objects.get(expediente=expediente, socio=socio)
        assert descargo.es_vigente is True
        assert [(v.numero, v.operacion) for v in descargo.versiones.all()] == [
            (1, OperacionDescargoEnum.PRESENTADO),
            (2, OperacionDescargoEnum.RETIRADO),
            (3, OperacionDescargoEnum.PRESENTADO),
        ]
        expediente.refresh_from_db()
        assert expediente.descargo_presentado is True
        assert expediente.descargo_texto == "Segundo."

    def test_retiro_y_representacion_dejan_un_unico_descargo_por_socio(
        self, client, socio, expediente
    ) -> None:
        client.post(_url(expediente), {"tipo": T03, "texto": "Primero."}, format="json")
        client.delete(_url(expediente))
        client.post(_url(expediente), {"tipo": T02, "archivo": "c.pdf"}, format="json")

        assert DescargoExpediente.objects.filter(expediente=expediente, socio=socio).count() == 1


@pytest.mark.django_db(transaction=True)
class TestLectoresFiltranPorVigencia:
    """Un descargo retirado no cuenta como presentado para ningún lector (T7)."""

    def test_detalle_del_socio_no_muestra_el_descargo_retirado(self, client, expediente) -> None:
        client.post(_url(expediente), {"tipo": T03, "texto": "Escrito."}, format="json")
        client.delete(_url(expediente))

        data = client.get(f"/api/v1/expedientes/{expediente.id}/").json()

        assert data["descargo_presentado"] is False
        assert data["descargos"] == []
        assert not data["descargo_texto"]

    def test_td_no_ve_como_presentado_un_descargo_retirado(
        self, client, api_client, make_socio, expediente
    ) -> None:
        client.post(_url(expediente), {"tipo": T03, "texto": "Escrito."}, format="json")
        td = make_socio(legajo="80001", role=Role.TD)
        client.delete(_url(expediente))
        api_client.force_authenticate(user=td.user)

        data = api_client.get(f"/api/v1/expedientes/{expediente.id}/").json()

        assert data["descargo_presentado"] is False
        assert data["descargos"] == []

    def test_expediente_con_dos_socios_requiere_ambos_descargos_vigentes(
        self, client, api_client, make_socio, socio, expediente
    ) -> None:
        otro = make_socio(legajo="85194")
        expediente.socios.add(otro)
        client.post(_url(expediente), {"tipo": T03, "texto": "Del titular."}, format="json")
        api_client.force_authenticate(user=otro.user)
        api_client.post(_url(expediente), {"tipo": T03, "texto": "Del otro."}, format="json")
        expediente.refresh_from_db()
        assert expediente.descargo_presentado is True

        api_client.delete(_url(expediente))

        expediente.refresh_from_db()
        assert expediente.descargo_presentado is False
        assert DescargoExpediente.objects.filter(expediente=expediente).count() == 2

    def test_carga_de_evidencia_ignora_el_tipo_de_un_descargo_retirado(
        self, client, socio, expediente
    ) -> None:
        client.post(_url(expediente), {"tipo": T02, "archivo": "c.pdf"}, format="json")
        client.delete(_url(expediente))
        pdf = SimpleUploadedFile("a.pdf", b"%PDF-1.4 prueba", content_type="application/pdf")
        otros_pdf = [
            SimpleUploadedFile(f"{i}.pdf", b"%PDF-1.4 " + bytes([65 + i]) * 8) for i in range(4)
        ]

        response = client.post(
            f"/api/v1/expedientes/{expediente.id}/evidencia/",
            {"archivos": [pdf, *otros_pdf]},
            format="multipart",
        )

        # Sin descargo vigente no se aplica el cupo de 3 del T02 retirado.
        assert response.status_code == status.HTTP_201_CREATED
