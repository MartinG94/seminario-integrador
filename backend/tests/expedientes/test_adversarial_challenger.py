"""Adversarial security, confidentiality, and data boundary test suite for SCRUM-75 / PB-04.

Author: Challenger 1 (Security Challenger Replacement)
Tests:
- Confidentiality (CA3): Zero leak of deliberations, internal notes, judge votes, drafts.
- Resolution lifecycle: None for all intermediate states, strictly emitted resolution for EMITIDO.
- Edge cases: Null/missing resolutions, non-emitted drafts, unlinked models.
- Multi-accused members: Preserving snapshots, subcomision variants (dict, str, None).
- Special characters: Unicode, emojis, XSS vectors, SQL injection strings in fields and
  query params.
- RBAC and data boundary isolation (CA1, CA4): Cross-authority access, anonymous, socio.
- Immutability of issued requests.
"""

from decimal import Decimal
from types import SimpleNamespace

import pytest
from django.core.exceptions import ValidationError
from rest_framework.test import APIClient

from expedientes.models import (
    CambioEstadoExpediente,
    EstadoExpedienteEnum,
    SolicitudT01,
)
from expedientes.serializers import MisSolicitudesT01Serializer
from socios.models import Role, Socio, Subcomision


@pytest.fixture
def mock_padron(monkeypatch):
    """Mockea get_padron_repository para validar socios por id en el serializer."""

    def _get_by_id(socio_id):
        socio = Socio.objects.filter(pk=socio_id).first()
        if not socio:
            return None
        return SimpleNamespace(
            socio_id=socio.id,
            legajo=socio.legajo,
            dni="30111222",
            first_name=socio.first_name,
            last_name=socio.last_name,
            email=socio.email,
            subcomision=socio.subcomision,
            social_year=socio.social_year,
            category=socio.category,
            is_active=socio.is_enabled,
            membership_status=SimpleNamespace(value="ENABLED"),
        )

    repo = SimpleNamespace(get_by_id=_get_by_id)
    monkeypatch.setattr("expedientes.serializers.get_padron_repository", lambda: repo)
    return repo


@pytest.mark.django_db
class TestAdversarialConfidentialityAndBoundaries:
    """Stress tests on confidentiality, authorization, and data boundary rules (CA1-CA4)."""

    def test_adv_confidentiality_no_td_deliberation_leak_across_all_states(
        self, make_socio, authenticate, mock_padron
    ):
        """CA3: In all procedural states, no internal deliberation, note,
        vote, or draft judgment leaks.
        """
        autoridad = make_socio(legajo="71001", role=Role.CD)
        imputado = make_socio(legajo="71002", role=Role.SOCIO)
        client = authenticate(autoridad)

        # 1. Crear y emitir solicitud
        resp_draft = client.post(
            "/api/v1/expedientes/",
            {
                "tipo_accion": "SANCTION",
                "puntos": "-1.50",
                "titulo": "Causa bajo examen confidencial",
                "motivo": "Motivo público de apertura",
                "destinatarios_socios_ids": [imputado.id],
            },
            format="json",
        )
        sol_id = resp_draft.data["id"]
        client.post(f"/api/v1/expedientes/{sol_id}/emitir/", {}, format="json")

        solicitud = SolicitudT01.objects.get(pk=sol_id)
        expediente = solicitud.expediente
        assert expediente is not None

        # Lista de estados intermedios del Art. 12
        intermediate_states = [
            EstadoExpedienteEnum.CREADO,
            EstadoExpedienteEnum.JUSTIFICANDO,
            EstadoExpedienteEnum.REVISION_RESOLUCION,
            EstadoExpedienteEnum.ESPERA_RESOLUCION,
            EstadoExpedienteEnum.PENDIENTE_CORREOS,
        ]

        forbidden_leak_keys = {
            "deliberacion",
            "deliberaciones",
            "voto",
            "votos",
            "votos_nominales",
            "votos_en_curso",
            "notas_internas",
            "nota_interna",
            "notas_secretas",
            "borradores_resolucion",
            "dictamen_borrador",
            "proyecto_resolucion",
            "observaciones_tribunal",
            "acta_deliberacion",
            "internal_notes",
            "judge_votes",
        }

        # Simular auditoría de cambios de estado internos
        CambioEstadoExpediente.objects.create(
            expediente=expediente,
            estado_anterior=EstadoExpedienteEnum.CREADO,
            estado_nuevo=EstadoExpedienteEnum.REVISION_RESOLUCION,
            actor="TRIBUNAL_SECRETARIO",
            motivo="Nota interna confidencial del Tribunal: deliberación preliminar privada.",
        )

        # Verificar cada estado intermedio
        for st in intermediate_states:
            expediente.estado = st
            expediente.save(update_fields=["estado"])

            resp = client.get("/api/v1/expedientes/mis-solicitudes/")
            assert resp.status_code == 200
            item = resp.data[0]

            # Verificar que resolucion_final es estrictamente None
            assert item["resolucion_final"] is None, (
                f"resolucion_final debe ser None en estado intermedio {st}"
            )

            # Verificar ausencia total de campos prohibidos
            for fk in forbidden_leak_keys:
                assert fk not in item, f"Campo reservado {fk} no debe exponerse"

            # Verificar que no se filtran textos internos en ninguno de los campos serializados
            serialized_dump = str(item).lower()
            assert "deliberación preliminar privada" not in serialized_dump
            assert "nota interna confidencial" not in serialized_dump

        # Ahora transicionar a EMITIDO (firme)
        expediente.estado = EstadoExpedienteEnum.EMITIDO
        expediente.save(update_fields=["estado"])

        resp_final = client.get("/api/v1/expedientes/mis-solicitudes/")
        assert resp_final.status_code == 200
        item_final = resp_final.data[0]

        assert item_final["resolucion_final"] is not None
        assert item_final["resolucion_final"]["emitido"] is True
        assert "dictamen" in item_final["resolucion_final"]
        assert f"causa {expediente.numero}" in item_final["resolucion_final"]["dictamen"]

        # Incluso en emitido, verificar que ningún voto o nota interna se fuga
        for fk in forbidden_leak_keys:
            assert fk not in item_final
            assert fk not in item_final["resolucion_final"]

    def test_adv_null_and_missing_resolutions_edge_cases(self, make_socio, mock_padron):
        """Edge case: Solicitudes sin expediente, borradores o campos vacíos."""
        autoridad = make_socio(legajo="72001", role=Role.TD)

        # 1. Borrador sin destinatarios ni expediente
        sol_vacia = SolicitudT01.objects.create(
            solicitante=autoridad,
            tipo_accion=SolicitudT01.TipoAccion.SANCTION,
            titulo="",
            motivo="",
            causal="",
            razon="",
            destinatarios_socios_ids=[],
        )

        serializer = MisSolicitudesT01Serializer(sol_vacia)
        data = serializer.data

        assert data["numero"] == "Borrador sin número"
        assert data["estado_procesal"] == "borrador"
        assert data["estado_procesal_display"] == "Borrador"
        assert data["involucrados"] == []
        assert data["resolucion_final"] is None
        assert data["puntos"] is None

        # 2. Solicitud emitida con expediente=None (simulando caso de desconexión o fallo previo)
        sol_sin_exp = SolicitudT01.objects.create(
            solicitante=autoridad,
            estado=SolicitudT01.Estado.ISSUED,
            tipo_accion=SolicitudT01.TipoAccion.MERIT,
            puntos=Decimal("2.00"),
            titulo="Mérito huérfano",
            motivo="Motivo",
            numero_expediente="T01-2026-TESTHUERFANO",
            destinatarios_socios_ids=[autoridad.id],
            expediente=None,
        )

        serializer2 = MisSolicitudesT01Serializer(sol_sin_exp)
        data2 = serializer2.data

        assert data2["numero"] == "T01-2026-TESTHUERFANO"
        assert data2["estado_procesal"] == "creado"
        assert data2["estado_procesal_display"] == "Expediente Creado"
        assert data2["resolucion_final"] is None

    def test_adv_multiple_accused_members_and_subcomision_variations(self, make_socio, mock_padron):
        """Edge case: Múltiples acusados, subcomisión None, subcomisión dict y subcomisión str."""
        autoridad = make_socio(legajo="73001", role=Role.FISCALIZADORA)
        sub_deportes = Subcomision.objects.create(name="Deportes y Recreación")

        # Crear 5 socios con diferentes configuraciones
        socios = []
        for i in range(5):
            sub = sub_deportes if i % 2 == 0 else None
            s = make_socio(legajo=f"7301{i}", role=Role.SOCIO)
            s.subcomision = sub
            s.save()
            socios.append(s)

        # Crear solicitud con múltiples snapshots que tienen variaciones en subcomision
        snapshots_dest = [
            # Caso 1: subcomision como dict completo
            {
                "socio_id": socios[0].id,
                "legajo": socios[0].legajo,
                "first_name": socios[0].first_name,
                "last_name": socios[0].last_name,
                "subcomision": {"id": sub_deportes.id, "name": sub_deportes.name},
            },
            # Caso 2: subcomision como None explícito
            {
                "socio_id": socios[1].id,
                "legajo": socios[1].legajo,
                "first_name": socios[1].first_name,
                "last_name": socios[1].last_name,
                "subcomision": None,
            },
            # Caso 3: subcomision como string plano
            {
                "socio_id": socios[2].id,
                "legajo": socios[2].legajo,
                "first_name": socios[2].first_name,
                "last_name": socios[2].last_name,
                "subcomision": "Subcomisión Cultural",
            },
            # Caso 4: socio sin nombres ni legajo completo
            {
                "socio_id": socios[3].id,
                "subcomision": None,
            },
            # Caso 5: subcomision dict vacío o dict con name=None
            {
                "socio_id": socios[4].id,
                "legajo": socios[4].legajo,
                "first_name": socios[4].first_name,
                "last_name": socios[4].last_name,
                "subcomision": {"name": None},
            },
        ]

        solicitud = SolicitudT01.objects.create(
            solicitante=autoridad,
            tipo_accion=SolicitudT01.TipoAccion.SANCTION,
            puntos=Decimal("-3.00"),
            titulo="Sanción colectiva",
            motivo="Falta colectiva",
            destinatarios_socios_ids=[s.id for s in socios],
            snapshots_destinatarios=snapshots_dest,
        )

        serializer = MisSolicitudesT01Serializer(solicitud)
        inv = serializer.data["involucrados"]

        assert len(inv) == 5
        assert inv[0]["subcomision"] == "Deportes y Recreación"
        assert inv[1]["subcomision"] == "Sin subcomisión"
        assert inv[2]["subcomision"] == "Subcomisión Cultural"
        assert inv[3]["legajo"] == "S/D"
        assert inv[3]["subcomision"] == "Sin subcomisión"
        assert inv[4]["subcomision"] is None or inv[4]["subcomision"] == "Sin subcomisión"

    def test_adv_special_characters_emojis_xss_and_injection(
        self, make_socio, authenticate, mock_padron
    ):
        """Edge case: Caracteres especiales, emojis, XSS payloads y SQL injection
        en campos y búsquedas.
        """
        autoridad = make_socio(legajo="74001", role=Role.CD)
        imputado = make_socio(legajo="74002", role=Role.SOCIO)
        client = authenticate(autoridad)

        payload_xss_sql = {
            "tipo_accion": "SANCTION",
            "puntos": "-2.00",
            "titulo": "🚨 <script>alert('XSS')</script> -- ¡Falta Grave! 🔥",
            "motivo": 'Causa con SQL: \'; DROP TABLE expedientes_expediente; -- y comillas "test"',
            "causal": "Infracción Estatutaria Art. 45º (ñoño & árabe: العربية)",
            "razon": "Fundamentos con saltos\nde\nlínea y tab\t y backslash \\.",
            "anexo_lugar": "Sede Central 'Norte' <div style='display:none;'>x</div>",
            "anexo_relato": "Relato con emojis: ⚖️🏛️📜 y comillas simples ''",
            "destinatarios_socios_ids": [imputado.id],
        }

        # 1. Crear borrador con caracteres especiales
        resp = client.post("/api/v1/expedientes/", payload_xss_sql, format="json")
        assert resp.status_code == 201

        # 2. Consultar mis-solicitudes y verificar integridad de serialización
        resp_list = client.get("/api/v1/expedientes/mis-solicitudes/")
        assert resp_list.status_code == 200
        assert len(resp_list.data) == 1
        item = resp_list.data[0]

        assert item["titulo"] == payload_xss_sql["titulo"]
        assert item["motivo"] == payload_xss_sql["motivo"]
        assert item["causal"] == payload_xss_sql["causal"]
        assert item["razon"] == payload_xss_sql["razon"]

        # 3. Test de ataques por query parameter `search`
        adversarial_search_queries = [
            "<script>",
            "'; DROP TABLE",
            "--",
            "/*",
            "ñoño",
            "العربية",
            "🚨",
            "🔥",
            ".*",  # Regex meta
            "[a-z]",  # Regex bracket
            "(",  # Regex paren abierta
            "%",  # SQL wildcard
            "_",  # SQL wildcard
            "'",  # SQL single quote
            '"',  # SQL double quote
            "\\",  # Backslash
        ]

        for query in adversarial_search_queries:
            resp_search = client.get(f"/api/v1/expedientes/mis-solicitudes/?search={query}")
            assert resp_search.status_code == 200, (
                f"La búsqueda con '{query}' no debe causar error 500"
            )

        # 4. Búsqueda exacta de contenido especial debe devolver la solicitud
        resp_found_xss = client.get("/api/v1/expedientes/mis-solicitudes/?search=script")
        assert resp_found_xss.status_code == 200
        assert len(resp_found_xss.data) == 1

        resp_found_emoji = client.get("/api/v1/expedientes/mis-solicitudes/?search=🚨")
        assert resp_found_emoji.status_code == 200
        assert len(resp_found_emoji.data) == 1

    def test_adv_cross_authority_boundary_isolation_ca1_ca4(
        self, make_socio, authenticate, mock_padron
    ):
        """CA1 & CA4: Aislamiento estricto de creador y rechazo de acciones cruzadas."""
        autoridad_cd = make_socio(legajo="75001", role=Role.CD)
        autoridad_td = make_socio(legajo="75002", role=Role.TD)
        socio_ordinario = make_socio(legajo="75003", role=Role.SOCIO)

        client_cd = authenticate(autoridad_cd)

        # CD crea un borrador
        resp_draft_cd = client_cd.post(
            "/api/v1/expedientes/",
            {
                "tipo_accion": "SANCTION",
                "puntos": "-1.00",
                "titulo": "Causa Privada de CD",
                "motivo": "Motivo",
                "destinatarios_socios_ids": [socio_ordinario.id],
            },
            format="json",
        )
        assert resp_draft_cd.status_code == 201
        draft_cd_id = resp_draft_cd.data["id"]

        # TD se autentica
        client_td = APIClient()
        login_td = client_td.post(
            "/api/v1/auth/login/",
            {"identifier": autoridad_td.legajo, "password": "Aveit-Test-2026!"},
            format="json",
        )
        client_td.credentials(HTTP_AUTHORIZATION=f"Bearer {login_td.data['access']}")

        # TD consulta mis-solicitudes: NO debe ver la causa de CD
        resp_td_list = client_td.get("/api/v1/expedientes/mis-solicitudes/")
        assert resp_td_list.status_code == 200
        assert len(resp_td_list.data) == 0

        # TD intenta LEER el borrador de CD directamente via GET: debe ser 404
        resp_td_read = client_td.get(f"/api/v1/expedientes/{draft_cd_id}/")
        assert resp_td_read.status_code == 404

        # TD intenta MODIFICAR el borrador de CD: debe ser 404
        resp_td_patch = client_td.patch(
            f"/api/v1/expedientes/{draft_cd_id}/",
            {"titulo": "Ataque de Modificación Cruzada"},
            format="json",
        )
        assert resp_td_patch.status_code == 404

        # TD intenta ELIMINAR el borrador de CD: debe ser 404
        resp_td_del = client_td.delete(f"/api/v1/expedientes/{draft_cd_id}/")
        assert resp_td_del.status_code == 404

        # TD intenta EMITIR el borrador de CD: debe ser 404
        resp_td_emit = client_td.post(
            f"/api/v1/expedientes/{draft_cd_id}/emitir/", {}, format="json"
        )
        assert resp_td_emit.status_code == 404

        # Verificar que el borrador sigue intacto en posesión de CD
        resp_cd_check = client_cd.get(f"/api/v1/expedientes/{draft_cd_id}/")
        assert resp_cd_check.status_code == 200
        assert resp_cd_check.data["titulo"] == "Causa Privada de CD"

    def test_adv_immutability_and_deletion_protection_of_issued_requests(
        self, make_socio, authenticate, mock_padron
    ):
        """Una solicitud emitida es estrictamente inmutable y no puede eliminarse."""
        autoridad = make_socio(legajo="76001", role=Role.CD)
        imputado = make_socio(legajo="76002", role=Role.SOCIO)
        client = authenticate(autoridad)

        # 1. Crear y emitir
        resp_draft = client.post(
            "/api/v1/expedientes/",
            {
                "tipo_accion": "SANCTION",
                "puntos": "-1.00",
                "titulo": "Causa para Test de Inmutabilidad",
                "motivo": "Motivo",
                "destinatarios_socios_ids": [imputado.id],
            },
            format="json",
        )
        sol_id = resp_draft.data["id"]
        client.post(f"/api/v1/expedientes/{sol_id}/emitir/", {}, format="json")

        solicitud = SolicitudT01.objects.get(pk=sol_id)
        assert solicitud.estado == SolicitudT01.Estado.ISSUED

        # 2. Intento de eliminación vía API DELETE: debe responder 409 Conflict
        resp_del = client.delete(f"/api/v1/expedientes/{sol_id}/")
        assert resp_del.status_code == 409
        assert "no puede eliminarse" in resp_del.data["detail"]

        # 3. Intento de modificación vía API PATCH: debe responder 400 Bad Request
        resp_patch = client.patch(
            f"/api/v1/expedientes/{sol_id}/",
            {"titulo": "Intento de alteración de solicitud emitida"},
            format="json",
        )
        assert resp_patch.status_code == 400

        # 4. Intento de eliminación a nivel de modelo ORM: debe lanzar ValidationError
        with pytest.raises(ValidationError, match="inmutable y no puede eliminarse"):
            solicitud.delete()

        # 5. Intento de re-guardar o alterar campos en ORM: debe lanzar ValidationError
        solicitud.titulo = "Alteración fraudulenta"
        with pytest.raises(ValidationError, match="inmutable"):
            solicitud.save()
