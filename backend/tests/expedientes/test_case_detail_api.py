"""Pruebas de integración para el endpoint seguro de detalle de expediente (CA4).

Valida:
- GET /api/v1/expedientes/{id}/
- 401 Unauthorized para usuarios anónimos (sin JWT).
- 403 Forbidden para socios ordinarios ajenos a la causa.
- 200 OK para el socio imputado titular de la causa.
- 200 OK para autoridades del Tribunal de Disciplina (TD), Directiva (CD) o Administrador.
- 404 Not Found para expedientes inexistentes.
"""

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from expedientes.models import EstadoExpedienteEnum, Expediente
from socios.models import Role, Socio, Subcomision


@pytest.fixture
def subcomision_test(db) -> Subcomision:
    return Subcomision.objects.create(name="Subcomisión de Cómputos")


@pytest.fixture
def socio_imputado(db, subcomision_test, django_user_model) -> Socio:
    user = django_user_model.objects.create_user(
        username="74301",
        email="socio.imputado@aveit.utn.edu.ar",
        password="Test-Password-2026!",
    )
    return Socio.objects.create(
        user=user,
        legajo="74301",
        first_name="Martín",
        last_name="Guillén",
        email="socio.imputado@aveit.utn.edu.ar",
        subcomision=subcomision_test,
        social_year=3,
        role=Role.SOCIO,
        is_enabled=True,
    )


@pytest.fixture
def socio_ajeno(db, subcomision_test, django_user_model) -> Socio:
    user = django_user_model.objects.create_user(
        username="74302",
        email="ajeno@aveit.utn.edu.ar",
        password="Test-Password-2026!",
    )
    return Socio.objects.create(
        user=user,
        legajo="74302",
        first_name="Lucas",
        last_name="Alvarez",
        email="ajeno@aveit.utn.edu.ar",
        subcomision=subcomision_test,
        social_year=2,
        role=Role.SOCIO,
        is_enabled=True,
    )


@pytest.fixture
def vocal_td(db, subcomision_test, django_user_model) -> Socio:
    user = django_user_model.objects.create_user(
        username="74303",
        email="vocal.td@aveit.utn.edu.ar",
        password="Test-Password-2026!",
    )
    return Socio.objects.create(
        user=user,
        legajo="74303",
        first_name="Valeria",
        last_name="Gómez",
        email="vocal.td@aveit.utn.edu.ar",
        subcomision=subcomision_test,
        social_year=4,
        role=Role.TD,
        is_enabled=True,
    )


@pytest.fixture
def directiva_cd(db, subcomision_test, django_user_model) -> Socio:
    user = django_user_model.objects.create_user(
        username="74304",
        email="cd@aveit.utn.edu.ar",
        password="Test-Password-2026!",
    )
    return Socio.objects.create(
        user=user,
        legajo="74304",
        first_name="Diego",
        last_name="Pérez",
        email="cd@aveit.utn.edu.ar",
        subcomision=subcomision_test,
        social_year=5,
        role=Role.CD,
        is_enabled=True,
    )


@pytest.fixture
def expediente_caso(db, socio_imputado) -> Expediente:
    return Expediente.objects.create(
        numero="EXP-2026-0888",
        socio=socio_imputado,
        motivo="Inasistencia injustificada a reuniones plenarias",
        puntos=-1.0,
        estado=EstadoExpedienteEnum.JUSTIFICANDO,
    )


@pytest.mark.django_db
class TestExpedienteDetailAPI:
    """Pruebas del endpoint GET /api/v1/expedientes/<id>/ con protección RBAC."""

    def test_api_detail_anonymous_unauthorized_401(self, expediente_caso) -> None:
        client = APIClient()
        url = f"/api/v1/expedientes/{expediente_caso.id}/"
        response = client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_api_detail_imputado_authorized_200(self, socio_imputado, expediente_caso) -> None:
        client = APIClient()
        client.force_authenticate(user=socio_imputado.user)

        url = f"/api/v1/expedientes/{expediente_caso.id}/"
        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == expediente_caso.id
        assert data["numero"] == "EXP-2026-0888"
        assert data["estado"] == "justificando"
        assert data["socio_legajo"] == "74301"

    def test_api_detail_other_socio_forbidden_403(self, socio_ajeno, expediente_caso) -> None:
        client = APIClient()
        client.force_authenticate(user=socio_ajeno.user)

        url = f"/api/v1/expedientes/{expediente_caso.id}/"
        response = client.get(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_api_detail_td_authorized_200(self, vocal_td, expediente_caso) -> None:
        client = APIClient()
        client.force_authenticate(user=vocal_td.user)

        url = f"/api/v1/expedientes/{expediente_caso.id}/"
        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["numero"] == "EXP-2026-0888"

    def test_api_detail_cd_authorized_200(self, directiva_cd, expediente_caso) -> None:
        client = APIClient()
        client.force_authenticate(user=directiva_cd.user)

        url = f"/api/v1/expedientes/{expediente_caso.id}/"
        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["numero"] == "EXP-2026-0888"

    def test_api_detail_not_found_404(self, vocal_td) -> None:
        client = APIClient()
        client.force_authenticate(user=vocal_td.user)

        url = "/api/v1/expedientes/99999/"
        response = client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_api_detail_coimputado_authorized_200(self, socio_ajeno, expediente_caso) -> None:
        """Co-imputados incluidos en expediente.socios.all() tienen acceso 200 OK (SCRUM-79)."""
        expediente_caso.socios.add(socio_ajeno)

        client = APIClient()
        client.force_authenticate(user=socio_ajeno.user)

        url = f"/api/v1/expedientes/{expediente_caso.id}/"
        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == expediente_caso.id

    def test_api_detail_includes_evidencias_and_socio_atribucion(
        self, vocal_td, socio_imputado, expediente_caso
    ) -> None:
        """El detalle expone evidencias con socio_id y socio_nombre para auditoría del TD."""
        from expedientes.models import EvidenciaDescargo

        EvidenciaDescargo.objects.create(
            expediente=expediente_caso,
            socio=socio_imputado,
            contenido_blob=b"%PDF-1.4 dummy",
            nombre_original="certificado_medico.pdf",
            extension=".pdf",
            mime_type="application/pdf",
            tamanio_bytes=1024,
            sha256_hash="dummyhash123",
            es_vigente=True,
        )

        client = APIClient()
        client.force_authenticate(user=vocal_td.user)

        url = f"/api/v1/expedientes/{expediente_caso.id}/"
        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["evidencias"]) == 1
        ev = data["evidencias"][0]
        assert ev["nombre_original"] == "certificado_medico.pdf"
        assert ev["socio_id"] == socio_imputado.id
        assert ev["socio_nombre"] == "Martín Guillén"

    def test_api_detail_td_sees_descargos_list(
        self, vocal_td, socio_imputado, expediente_caso
    ) -> None:
        """El TD puede auditar la colección completa de descargos por socio (SCRUM-79)."""
        from expedientes.models import DescargoExpediente

        DescargoExpediente.objects.create(
            expediente=expediente_caso,
            socio=socio_imputado,
            tipo="T02_CERTIFICADO",
            causal="Examen Académico Universitario en UTN FRC",
            archivo="constancia.pdf",
            texto="Rendí examen",
        )

        client = APIClient()
        client.force_authenticate(user=vocal_td.user)

        url = f"/api/v1/expedientes/{expediente_caso.id}/"
        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "descargos" in data
        assert len(data["descargos"]) == 1
        d = data["descargos"][0]
        assert d["socio_id"] == socio_imputado.id
        assert d["socio_legajo"] == "74301"
        assert d["socio_nombre"] == "Martín Guillén"
        assert d["tipo"] == "T02_CERTIFICADO"

    def test_api_detail_includes_reglamentos_respaldantes(
        self, vocal_td, socio_imputado, expediente_caso
    ) -> None:
        """El detalle expone reglamentos_respaldantes del expediente y de la solicitud T01."""
        client = APIClient()
        client.force_authenticate(user=vocal_td.user)

        # Caso 1: Sin solicitud T01 (fallback)
        response = client.get(f"/api/v1/expedientes/{expediente_caso.id}/")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "reglamentos_respaldantes" in data
        assert data["reglamentos_respaldantes"] == ["Reglamento Procesal Disciplinario 2026"]

        # Caso 2: Con solicitud T01 y reglamentos respaldantes explícitos
        from expedientes.models import SolicitudT01

        solicitud = SolicitudT01.objects.create(
            solicitante=socio_imputado,
            destinatario_socio_id=socio_imputado.id,
            tipo_accion=SolicitudT01.TipoAccion.SANCTION,
            puntos=-5,
            motivo="Incumplimiento de tareas",
            causal="Falta a guardia",
            reglamentos_respaldantes=[
                "Estatuto Social Art. 14 Inc. b",
                "Reglamento Interno Art. 22",
            ],
            expediente=expediente_caso,
        )

        response = client.get(f"/api/v1/expedientes/{expediente_caso.id}/")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["reglamentos_respaldantes"] == [
            "Estatuto Social Art. 14 Inc. b",
            "Reglamento Interno Art. 22",
        ]

        # Caso 3: Con causal pero sin reglamentos_respaldantes
        solicitud.reglamentos_respaldantes = []
        solicitud.save()
        response = client.get(f"/api/v1/expedientes/{expediente_caso.id}/")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["reglamentos_respaldantes"] == ["Falta a guardia"]

    def test_api_detail_descargo_leido_and_puntaje_ratificado(
        self, vocal_td, socio_imputado, expediente_caso
    ) -> None:
        """Verifica leido, puntaje_ratificado y decisiones_causal para descargos T02 y T03."""
        from expedientes.models import (
            DecisionCausalDescargo,
            DecisionCausalEnum,
            DescargoExpediente,
            TipoDescargoEnum,
        )

        expediente_caso.puntos = -10
        expediente_caso.save()

        # 1. Descargo T02 sin decisiones: leido False, puntaje_ratificado None
        descargo_t02 = DescargoExpediente.objects.create(
            expediente=expediente_caso,
            socio=socio_imputado,
            tipo=TipoDescargoEnum.T02_CERTIFICADO,
            causal="Examen Universitario",
            archivo="constancia.pdf",
        )

        client = APIClient()
        client.force_authenticate(user=vocal_td.user)

        response = client.get(f"/api/v1/expedientes/{expediente_caso.id}/")
        assert response.status_code == status.HTTP_200_OK
        d = response.json()["descargos"][0]
        assert d["leido"] is False
        assert d["puntaje_ratificado"] is None
        assert d["decisiones_causal"] == []

        # 2. Registrar decisión ACCEPTED: leido True, puntaje_ratificado 0
        DecisionCausalDescargo.objects.create(
            expediente=expediente_caso,
            descargo=descargo_t02,
            version=1,
            decision=DecisionCausalEnum.ACCEPTED,
            regla_sugerida=DecisionCausalEnum.ACCEPTED,
            autor=vocal_td.user,
            autor_legajo=vocal_td.legajo,
            autor_rol=vocal_td.role,
        )

        response = client.get(f"/api/v1/expedientes/{expediente_caso.id}/")
        d = response.json()["descargos"][0]
        assert d["leido"] is True
        assert d["puntaje_ratificado"] == 0
        assert len(d["decisiones_causal"]) == 1

        # 3. Nueva versión REJECTED: leido True, puntaje_ratificado -10
        DecisionCausalDescargo.objects.create(
            expediente=expediente_caso,
            descargo=descargo_t02,
            version=2,
            decision=DecisionCausalEnum.REJECTED,
            regla_sugerida=DecisionCausalEnum.ACCEPTED,
            fundamento="El certificado no tiene sello institucional.",
            autor=vocal_td.user,
            autor_legajo=vocal_td.legajo,
            autor_rol=vocal_td.role,
        )

        response = client.get(f"/api/v1/expedientes/{expediente_caso.id}/")
        d = response.json()["descargos"][0]
        assert d["leido"] is True
        assert d["puntaje_ratificado"] == -10.0
        assert len(d["decisiones_causal"]) == 2

        # 4. Descargo T03: autoridad también ve decisiones_causal
        expediente_t03 = Expediente.objects.create(
            socio=socio_imputado,
            numero="EXP-2026-TEST-T03",
            motivo="Causa T03",
            puntos=-5,
            estado=EstadoExpedienteEnum.JUSTIFICANDO,
        )
        DescargoExpediente.objects.create(
            expediente=expediente_t03,
            socio=socio_imputado,
            tipo=TipoDescargoEnum.T03_EXTRAORDINARIO,
            texto="Hechos de fuerza mayor...",
        )
        response = client.get(f"/api/v1/expedientes/{expediente_t03.id}/")
        d = response.json()["descargos"][0]
        assert "decisiones_causal" in d
        assert d["decisiones_causal"] == []
        assert d["leido"] is False
        assert d["puntaje_ratificado"] is None

    def test_decision_causal_puntaje_final_regla_negocio(
        self, vocal_td, socio_imputado, expediente_caso
    ) -> None:
        """Verifica la regla de negocio: si puntaje_final < pedido, fundamento obligatorio."""
        from expedientes.models import DescargoExpediente, TipoDescargoEnum

        expediente_caso.estado = EstadoExpedienteEnum.REVISION_RESOLUCION
        expediente_caso.save()

        descargo = DescargoExpediente.objects.create(
            expediente=expediente_caso,
            socio=socio_imputado,
            tipo=TipoDescargoEnum.T02_CERTIFICADO,
            causal="Enfermedad",
            texto="Descargo médico de prueba.",
        )

        client = APIClient()
        client.force_authenticate(user=vocal_td.user)
        url = f"/api/v1/expedientes/{expediente_caso.id}/descargos/{descargo.id}/decisiones/"

        # 1. Sanción Agravada (pedido: -1.0, final: -3.0): menor a pedido -> obligatorio
        res_sin_fundamento = client.post(
            url,
            {"decision": "REJECTED", "puntaje_final": -3.0, "fundamento": ""},
            format="json",
        )
        assert res_sin_fundamento.status_code == status.HTTP_400_BAD_REQUEST
        assert "fundamentación" in res_sin_fundamento.json()["detail"].lower()

        # 2. Con fundamento >= 10 chars: éxito
        res_con_fundamento = client.post(
            url,
            {
                "decision": "REJECTED",
                "puntaje_final": -3.0,
                "fundamento": "Se agrava la sanción por reincidencia acreditada.",
            },
            format="json",
        )
        assert res_con_fundamento.status_code == status.HTTP_201_CREATED

        # 3. A favor del socio (pedido: -1.0, final: 0.0): mayor a pedido -> opcional
        expediente2 = Expediente.objects.create(
            socio=socio_imputado,
            numero="EXP-2026-TEST-FAVOR",
            motivo="Causa test a favor",
            puntos=-1.0,
            estado=EstadoExpedienteEnum.REVISION_RESOLUCION,
        )
        descargo2 = DescargoExpediente.objects.create(
            expediente=expediente2,
            socio=socio_imputado,
            tipo=TipoDescargoEnum.T02_CERTIFICADO,
            causal="Enfermedad",
            texto="Descargo médico.",
        )
        # Crear evidencia para sugerir ACCEPTED
        from expedientes.models import EvidenciaDescargo

        EvidenciaDescargo.objects.create(
            expediente=expediente2,
            socio=socio_imputado,
            descargo=descargo2,
            nombre_original="certificado.pdf",
            contenido_blob=b"pdf content",
            sha256_hash="hash",
            tamanio_bytes=100,
            mime_type="application/pdf",
        )
        url2 = f"/api/v1/expedientes/{expediente2.id}/descargos/{descargo2.id}/decisiones/"
        res_a_favor = client.post(
            url2,
            {"decision": "ACCEPTED", "puntaje_final": 0.0, "fundamento": ""},
            format="json",
        )
        assert res_a_favor.status_code == status.HTTP_201_CREATED
