"""Pruebas para el Visor Autorizado de Expedientes y Evidencias (US S4-01 / SCRUM-51).

Verifica:
- CA1: Vista dedicada con cabecera TD, 3 jueces con grupo Gxx y timeline cronológico.
- CA2: Confidencialidad médica estricta (TD, CD, ADMIN y socio imputado titular).
- CA3: Auditoría inmutable de accesos en expedientes_auditoria_consulta.
- CA4: Integridad documental SHA-256 (flags sha256_valido, archivo_danado) y rotulado de "Plazo vencido sin descargo".
- Rechazo HTTP 403 a socios ordinarios no imputados.
"""

import hashlib
from datetime import timedelta
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from expedientes.models import (
    AuditoriaConsultaExpediente,
    DescargoExpediente,
    EstadoExpedienteEnum,
    EvidenciaDescargo,
    Expediente,
    SolicitudT01,
    TipoDescargoEnum,
    UrgenciaExpedienteEnum,
)
from socios.models import Role, Socio, Subcomision


@pytest.fixture
def subcomision_test(db) -> Subcomision:
    return Subcomision.objects.create(name="Subcomisión de Cómputos")


@pytest.fixture
def socio_imputado_1(db, subcomision_test, django_user_model) -> Socio:
    user = django_user_model.objects.create_user(
        username="75001",
        email="socio1@aveit.utn.edu.ar",
        password="Test-Password-2026!",
    )
    return Socio.objects.create(
        user=user,
        legajo="75001",
        first_name="Martín",
        last_name="Guillén",
        email="socio1@aveit.utn.edu.ar",
        subcomision=subcomision_test,
        social_year=3,
        role=Role.SOCIO,
        is_enabled=True,
    )


@pytest.fixture
def socio_imputado_2(db, subcomision_test, django_user_model) -> Socio:
    user = django_user_model.objects.create_user(
        username="75002",
        email="socio2@aveit.utn.edu.ar",
        password="Test-Password-2026!",
    )
    return Socio.objects.create(
        user=user,
        legajo="75002",
        first_name="Esteban",
        last_name="Quito",
        email="socio2@aveit.utn.edu.ar",
        subcomision=subcomision_test,
        social_year=2,
        role=Role.SOCIO,
        is_enabled=True,
    )


@pytest.fixture
def socio_ajeno(db, subcomision_test, django_user_model) -> Socio:
    user = django_user_model.objects.create_user(
        username="75003",
        email="ajeno@aveit.utn.edu.ar",
        password="Test-Password-2026!",
    )
    return Socio.objects.create(
        user=user,
        legajo="75003",
        first_name="Lucas",
        last_name="Alvarez",
        email="ajeno@aveit.utn.edu.ar",
        subcomision=subcomision_test,
        social_year=1,
        role=Role.SOCIO,
        is_enabled=True,
    )


@pytest.fixture
def vocal_td(db, subcomision_test, django_user_model) -> Socio:
    user = django_user_model.objects.create_user(
        username="11239",
        email="giuliano.toselli@aveit.utn.edu.ar",
        password="Test-Password-2026!",
    )
    return Socio.objects.create(
        user=user,
        legajo="11239",
        first_name="Giuliano",
        last_name="Toselli",
        email="giuliano.toselli@aveit.utn.edu.ar",
        subcomision=subcomision_test,
        social_year=5,
        role=Role.TD,
        is_enabled=True,
    )


@pytest.fixture
def directiva_cd(db, subcomision_test, django_user_model) -> Socio:
    user = django_user_model.objects.create_user(
        username="75004",
        email="cd.autoridad@aveit.utn.edu.ar",
        password="Test-Password-2026!",
    )
    return Socio.objects.create(
        user=user,
        legajo="75004",
        first_name="Diego",
        last_name="Directivo",
        email="cd.autoridad@aveit.utn.edu.ar",
        subcomision=subcomision_test,
        social_year=6,
        role=Role.CD,
        is_enabled=True,
    )


@pytest.fixture
def expediente_causa(db, socio_imputado_1, socio_imputado_2) -> Expediente:
    exp = Expediente.objects.create(
        numero="EXP-0888/2026",
        socio=socio_imputado_1,
        motivo="Inasistencia injustificada y desorden en sede",
        estado=EstadoExpedienteEnum.JUSTIFICANDO,
        urgencia=UrgenciaExpedienteEnum.URGENTE,
        plazo_inicio_at=timezone.now() - timedelta(days=2),
        plazo_limite_at=timezone.now() + timedelta(days=3),
    )
    exp.socios.add(socio_imputado_1, socio_imputado_2)

    # Crear Solicitud T01 vinculada con Anexo
    SolicitudT01.objects.create(
        expediente=exp,
        solicitante=socio_imputado_1,
        destinatarios_socios_ids=[socio_imputado_1.id, socio_imputado_2.id],
        titulo="Inasistencia y desorden en laboratorio",
        motivo="Relato formal de los hechos ocurridos en la sede.",
        razon="Apertura formal de causa disciplinaria.",
        causal="Art. 21 y 24 Reglamento Procesal",
        reglamentos_respaldantes=["Art. 21", "Art. 24"],
        anexo_lugar="Sede Central AVEIT, Lab de Cómputos",
        anexo_fecha=timezone.localdate(),
        anexo_relato="Se constató la ausencia injustificada y alteración de equipos.",
        anexo_testigos="Juan Pérez (11200) - Testigo presencial",
        estado=SolicitudT01.Estado.ISSUED,
        tipo_accion=SolicitudT01.TipoAccion.SANCTION,
        puntos=Decimal("-1.00"),
    )
    return exp


@pytest.mark.django_db
class TestVisorExpedienteAPI:
    """Suite de pruebas para ExpedienteVisorView."""

    def test_visor_acceso_denegado_a_terceros_socio_no_imputado(
        self, expediente_causa, socio_ajeno
    ) -> None:
        """CA2: Socios ordinarios ajenos a la causa reciben HTTP 403 Forbidden."""
        client = APIClient()
        client.force_authenticate(user=socio_ajeno.user)

        response = client.get(f"/api/v1/expedientes/{expediente_causa.id}/visor/")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_visor_miembro_td_y_cd_obtienen_payload_completo(
        self, expediente_causa, vocal_td, directiva_cd
    ) -> None:
        """CA1: Integrantes de TD y CD acceden al visor con cabecera TD, jueces Gxx y timeline."""
        for user_auth in (vocal_td.user, directiva_cd.user):
            client = APIClient()
            client.force_authenticate(user=user_auth)

            response = client.get(f"/api/v1/expedientes/{expediente_causa.id}/visor/")
            assert response.status_code == status.HTTP_200_OK
            data = response.data

            # Cabecera oficial
            assert data["numero"] == "EXP-0888/2026"
            assert data["anio"] == 2026
            assert data["urgencia"] == "urgente"
            assert data["urgencia_display"] == "Urgente"
            assert data["estado"] == "justificando"

            # 3 Responsables del TD con grupo
            assert len(data["responsables_td"]) == 3
            assert data["responsables_td"][0]["display"] == "11239 - Giuliano Toselli - G59"

            # T01 y Anexo
            assert data["titulo"] == "Inasistencia y desorden en laboratorio"
            assert data["anexo"]["anexo_lugar"] == "Sede Central AVEIT, Lab de Cómputos"
            assert "Juan Pérez" in data["anexo"]["anexo_testigos"]

            # Timeline
            assert isinstance(data["timeline"], list)
            assert len(data["timeline"]) >= 2  # Creación + Plazo

    def test_visor_auditoria_inmutable_registrada_al_consultar(
        self, expediente_causa, vocal_td
    ) -> None:
        """CA3: Cada consulta al visor asienta una fila inmutable en AuditoriaConsultaExpediente."""
        conteo_inicial = AuditoriaConsultaExpediente.objects.filter(
            expediente=expediente_causa
        ).count()

        client = APIClient()
        client.force_authenticate(user=vocal_td.user)
        response = client.get(
            f"/api/v1/expedientes/{expediente_causa.id}/visor/",
            HTTP_USER_AGENT="PytestClient/1.0",
        )

        assert response.status_code == status.HTTP_200_OK
        conteo_final = AuditoriaConsultaExpediente.objects.filter(
            expediente=expediente_causa
        ).count()
        assert conteo_final == conteo_inicial + 1

        registro = AuditoriaConsultaExpediente.objects.filter(
            expediente=expediente_causa
        ).latest("fecha_hora")
        assert registro.usuario == "11239"
        assert registro.legajo == "11239"
        assert registro.rol == "TD"
        assert registro.user_agent == "PytestClient/1.0"

        # Inmutabilidad
        with pytest.raises(ValidationError):
            registro.usuario = "otro"
            registro.save()

        with pytest.raises(ValidationError):
            registro.delete()

    def test_visor_datos_medicos_ocultos_para_roles_no_autorizados(
        self, expediente_causa, socio_imputado_1, socio_imputado_2, vocal_td
    ) -> None:
        """CA2: Causal médica es reservada para co-imputados y visible para TD, CD y el titular."""
        # Crear descargo T02 con causa médica para socio_imputado_1
        raw_pdf = b"%PDF-1.4 Mock medical certificate content"
        pdf_hash = hashlib.sha256(raw_pdf).hexdigest()

        descargo_medico = DescargoExpediente.objects.create(
            expediente=expediente_causa,
            socio=socio_imputado_1,
            tipo=TipoDescargoEnum.T02_CERTIFICADO,
            causal="Enfermedad certificada de salud",
            texto="Diagnóstico médico de reposo por 48 horas.",
            es_vigente=True,
            presentado_at=timezone.now(),
        )

        EvidenciaDescargo.objects.create(
            expediente=expediente_causa,
            descargo=descargo_medico,
            socio=socio_imputado_1,
            nombre_original="certificado_medico.pdf",
            extension=".pdf",
            mime_type="application/pdf",
            tamanio_bytes=len(raw_pdf),
            sha256_hash=pdf_hash,
            contenido_blob=raw_pdf,
            es_vigente=True,
        )

        # 1. Socio 2 (co-imputado) consulta el visor: puede entrar pero datos médicos de socio 1 están enmascarados
        client_coimputado = APIClient()
        client_coimputado.force_authenticate(user=socio_imputado_2.user)
        resp_coimputado = client_coimputado.get(
            f"/api/v1/expedientes/{expediente_causa.id}/visor/"
        )
        assert resp_coimputado.status_code == status.HTTP_200_OK

        involucrado_1_data = next(
            inv for inv in resp_coimputado.data["involucrados"] if inv["id"] == socio_imputado_1.id
        )
        assert involucrado_1_data["descargo"]["causal"] == "[Información médica reservada]"
        assert involucrado_1_data["descargo"]["texto"] == "[Información médica reservada]"
        assert involucrado_1_data["descargo"]["evidencias"] == []
        assert involucrado_1_data["descargo"]["datos_medicos_restringidos"] is True

        # 2. Socio 1 (titular) consulta el visor: ve su propia justificación médica completa
        client_titular = APIClient()
        client_titular.force_authenticate(user=socio_imputado_1.user)
        resp_titular = client_titular.get(f"/api/v1/expedientes/{expediente_causa.id}/visor/")
        assert resp_titular.status_code == status.HTTP_200_OK

        involucrado_1_titular = next(
            inv for inv in resp_titular.data["involucrados"] if inv["id"] == socio_imputado_1.id
        )
        assert "Enfermedad" in involucrado_1_titular["descargo"]["causal"]
        assert len(involucrado_1_titular["descargo"]["evidencias"]) == 1
        assert involucrado_1_titular["descargo"]["datos_medicos_restringidos"] is False

        # 3. Vocal TD consulta el visor: ve datos médicos completos
        client_td = APIClient()
        client_td.force_authenticate(user=vocal_td.user)
        resp_td = client_td.get(f"/api/v1/expedientes/{expediente_causa.id}/visor/")
        assert resp_td.status_code == status.HTTP_200_OK
        inv_td = next(
            inv for inv in resp_td.data["involucrados"] if inv["id"] == socio_imputado_1.id
        )
        assert "Enfermedad" in inv_td["descargo"]["causal"]
        assert len(inv_td["descargo"]["evidencias"]) == 1

    def test_visor_detecta_archivo_danado_o_inconsistencia_sha256(
        self, expediente_causa, vocal_td, socio_imputado_1
    ) -> None:
        """CA4: Marca flag sha256_valido=False y archivo_danado=True ante discordancia de hash."""
        raw_valid = b"%PDF-1.4 Valid file content"
        hash_valid = hashlib.sha256(raw_valid).hexdigest()

        raw_corrupted = b"%PDF-1.4 Altered file bytes"
        hash_fake = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

        descargo = DescargoExpediente.objects.create(
            expediente=expediente_causa,
            socio=socio_imputado_1,
            tipo=TipoDescargoEnum.T02_CERTIFICADO,
            causal="Actividad laboral",
            es_vigente=True,
        )

        ev_valida = EvidenciaDescargo.objects.create(
            expediente=expediente_causa,
            descargo=descargo,
            socio=socio_imputado_1,
            nombre_original="valido.pdf",
            extension=".pdf",
            mime_type="application/pdf",
            tamanio_bytes=len(raw_valid),
            sha256_hash=hash_valid,
            contenido_blob=raw_valid,
            es_vigente=True,
        )

        ev_danada = EvidenciaDescargo.objects.create(
            expediente=expediente_causa,
            descargo=descargo,
            socio=socio_imputado_1,
            nombre_original="danado.pdf",
            extension=".pdf",
            mime_type="application/pdf",
            tamanio_bytes=len(raw_corrupted),
            sha256_hash=hash_fake,  # Hash no coincide con raw_corrupted
            contenido_blob=raw_corrupted,
            es_vigente=True,
        )

        client = APIClient()
        client.force_authenticate(user=vocal_td.user)
        response = client.get(f"/api/v1/expedientes/{expediente_causa.id}/visor/")
        assert response.status_code == status.HTTP_200_OK

        involucrado = next(
            inv for inv in response.data["involucrados"] if inv["id"] == socio_imputado_1.id
        )
        evs = involucrado["descargo"]["evidencias"]
        dto_valida = next(e for e in evs if e["id"] == str(ev_valida.id))
        dto_danada = next(e for e in evs if e["id"] == str(ev_danada.id))

        assert dto_valida["sha256_valido"] is True
        assert dto_valida["archivo_danado"] is False

        assert dto_danada["sha256_valido"] is False
        assert dto_danada["archivo_danado"] is True

    def test_visor_rotula_plazo_vencido_sin_descargo(
        self, expediente_causa, vocal_td, socio_imputado_2
    ) -> None:
        """CA4: Rotula 'Plazo vencido sin descargo' cuando expiró el plazo y el imputado no justificó."""
        # Configurar expediente con plazo expirado
        expediente_causa.plazo_limite_at = timezone.now() - timedelta(hours=1)
        expediente_causa.estado = EstadoExpedienteEnum.REVISION_RESOLUCION
        expediente_causa.save()

        client = APIClient()
        client.force_authenticate(user=vocal_td.user)
        response = client.get(f"/api/v1/expedientes/{expediente_causa.id}/visor/")
        assert response.status_code == status.HTTP_200_OK

        involucrado_2 = next(
            inv for inv in response.data["involucrados"] if inv["id"] == socio_imputado_2.id
        )
        assert involucrado_2["tiene_descargo"] is False
        assert involucrado_2["estado_descargo"] == "PLAZO_VENCIDO_SIN_DESCARGO"
        assert involucrado_2["estado_descargo_display"] == "Plazo vencido sin descargo"

    def test_visor_diferencia_consulta_de_descarga_en_timeline(
        self, expediente_causa, vocal_td, socio_imputado_1
    ) -> None:
        """Distingue entre visualización en pantalla y descarga formal a disco en la auditoría."""
        raw_doc = b"%PDF-1.4 test preview vs download"
        hash_doc = hashlib.sha256(raw_doc).hexdigest()

        descargo = DescargoExpediente.objects.create(
            expediente=expediente_causa,
            socio=socio_imputado_1,
            tipo=TipoDescargoEnum.T02_CERTIFICADO,
            causal="Certificado de estudio",
            es_vigente=True,
        )

        evidencia = EvidenciaDescargo.objects.create(
            expediente=expediente_causa,
            descargo=descargo,
            socio=socio_imputado_1,
            nombre_original="constancia.pdf",
            extension=".pdf",
            mime_type="application/pdf",
            tamanio_bytes=len(raw_doc),
            sha256_hash=hash_doc,
            contenido_blob=raw_doc,
            es_vigente=True,
        )

        client = APIClient()
        client.force_authenticate(user=vocal_td.user)

        # 1. El vocal consulta el documento en el visor (sin descargar a disco)
        res_ver = client.get(
            f"/api/v1/expedientes/{expediente_causa.id}/evidencia/{evidencia.id}/?accion=ver"
        )
        assert res_ver.status_code == status.HTTP_200_OK

        # 2. El vocal luego presiona 'Descargar'
        res_desc = client.get(
            f"/api/v1/expedientes/{expediente_causa.id}/evidencia/{evidencia.id}/?accion=descarga"
        )
        assert res_desc.status_code == status.HTTP_200_OK

        # 3. Comprobar que en el visor se reflejan ambos hitos adecuadamente rotulados
        res_visor = client.get(f"/api/v1/expedientes/{expediente_causa.id}/visor/")
        assert res_visor.status_code == status.HTTP_200_OK

        timeline = res_visor.data["timeline"]
        tipos_timeline = [h["tipo"] for h in timeline]

        assert "CONSULTA_DOCUMENTO" in tipos_timeline
        assert "DESCARGA_DOCUMENTO" in tipos_timeline

        hito_consulta = next(h for h in timeline if h["tipo"] == "CONSULTA_DOCUMENTO")
        assert "Consulta: constancia.pdf" in hito_consulta["titulo"]
        assert hito_consulta["icono"] == "visibility"

        hito_descarga = next(h for h in timeline if h["tipo"] == "DESCARGA_DOCUMENTO")
        assert "Descarga: constancia.pdf" in hito_descarga["titulo"]
        assert hito_descarga["icono"] == "file_download"
