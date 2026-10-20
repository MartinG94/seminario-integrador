"""Pruebas de integración de la API de decisiones por causal T02 (S4-02)."""

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from rest_framework import status
from rest_framework.test import APIClient

from expedientes.models import (
    DecisionCausalDescargo,
    DescargoExpediente,
    EstadoExpedienteEnum,
    Expediente,
    TipoDescargoEnum,
)
from expedientes.services.causal_resolution_service import current_evidence_for
from socios.models import Role

GROUNDS = "El certificado presentado no acredita la fecha de la inasistencia."


def _url(descargo) -> str:
    return f"/api/v1/expedientes/{descargo.expediente_id}/descargos/{descargo.id}/decisiones/"


def _client(socio) -> APIClient:
    client = APIClient()
    client.force_authenticate(user=socio.user)
    return client


@pytest.mark.django_db
class TestRegistrarDecisionCausal:
    def test_vocal_registers_decision_201(
        self, causal_descargo, causal_evidencia, causal_vocal
    ) -> None:
        response = _client(causal_vocal).post(
            _url(causal_descargo),
            {"decision": "ACCEPTED", "evidencia_ids": [str(causal_evidencia.id)]},
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED, response.data
        assert response.data["version"] == 1
        assert response.data["decision_display"] == "Aceptada"
        assert response.data["autor"] == causal_vocal.legajo
        assert response.data["evidencias_valoradas"][0]["sha256_hash"] == (
            causal_evidencia.sha256_hash
        )

    def test_rejection_without_grounds_400(
        self, causal_descargo, causal_evidencia, causal_vocal
    ) -> None:
        response = _client(causal_vocal).post(
            _url(causal_descargo), {"decision": "REJECTED"}, format="json"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "fundamento" in response.data["detail"]
        assert not DecisionCausalDescargo.objects.exists()

    def test_invalid_decision_value_400(self, causal_descargo, causal_vocal) -> None:
        response = _client(causal_vocal).post(
            _url(causal_descargo), {"decision": "MAYBE", "fundamento": GROUNDS}, format="json"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_outside_review_stage_409(
        self, causal_descargo, causal_evidencia, causal_vocal
    ) -> None:
        expediente = causal_descargo.expediente
        expediente.estado = EstadoExpedienteEnum.JUSTIFICANDO
        expediente.save(update_fields=["estado"])

        response = _client(causal_vocal).post(
            _url(causal_descargo), {"decision": "ACCEPTED"}, format="json"
        )

        assert response.status_code == status.HTTP_409_CONFLICT

    def test_unknown_descargo_404(self, causal_descargo, causal_vocal) -> None:
        url = f"/api/v1/expedientes/{causal_descargo.expediente_id}/descargos/999999/decisiones/"

        response = _client(causal_vocal).post(url, {"decision": "ACCEPTED"}, format="json")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_t03_descargo_400(self, causal_descargo, causal_vocal) -> None:
        DescargoExpediente.objects.filter(pk=causal_descargo.pk).update(
            tipo=TipoDescargoEnum.T03_EXTRAORDINARIO
        )

        response = _client(causal_vocal).post(
            _url(causal_descargo), {"decision": "ACCEPTED", "fundamento": GROUNDS}, format="json"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert not DecisionCausalDescargo.objects.exists()

    def test_evidence_of_another_socio_400(self, multiactor, causal_vocal) -> None:
        response = _client(causal_vocal).post(
            _url(multiactor["descargo"]),
            {"decision": "ACCEPTED", "evidencia_ids": [str(multiactor["ajena_vinculada"].id)]},
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert not DecisionCausalDescargo.objects.exists()

    def test_descargo_from_another_expediente_404(
        self, causal_descargo, causal_vocal, make_socio
    ) -> None:
        otro_imputado = make_socio(legajo="76098")
        otro_expediente = Expediente.objects.create(
            numero="EXP-9998/2026",
            socio=otro_imputado,
            motivo="Otro motivo",
            estado=EstadoExpedienteEnum.REVISION_RESOLUCION,
        )
        otro_descargo = DescargoExpediente.objects.create(
            expediente=otro_expediente,
            socio=otro_imputado,
            tipo=TipoDescargoEnum.T02_CERTIFICADO,
            causal="Enfermedad",
        )
        url = (
            f"/api/v1/expedientes/{causal_descargo.expediente_id}"
            f"/descargos/{otro_descargo.id}/decisiones/"
        )

        response = _client(causal_vocal).post(
            url, {"decision": "ACCEPTED", "fundamento": GROUNDS}, format="json"
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert not DecisionCausalDescargo.objects.exists()

    def test_anonymous_401(self, causal_descargo) -> None:
        response = APIClient().post(_url(causal_descargo), {"decision": "ACCEPTED"}, format="json")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.parametrize("role", [Role.SOCIO, Role.CD, Role.ADMIN, Role.FISCALIZADORA])
    def test_only_tribunal_can_decide_403(self, role, causal_descargo, make_socio) -> None:
        otro = make_socio(legajo="76009", role=role)

        response = _client(otro).post(
            _url(causal_descargo), {"decision": "ACCEPTED", "fundamento": GROUNDS}, format="json"
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_disabled_vocal_403(self, causal_descargo, make_socio) -> None:
        inhabilitado = make_socio(legajo="76010", role=Role.TD, is_enabled=False)

        response = _client(inhabilitado).post(
            _url(causal_descargo), {"decision": "ACCEPTED", "fundamento": GROUNDS}, format="json"
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestConsultarDecisionesCausal:
    def _registrar_dos_versiones(self, descargo, vocal) -> None:
        client = _client(vocal)
        client.post(_url(descargo), {"decision": "ACCEPTED"}, format="json")
        client.post(_url(descargo), {"decision": "REJECTED", "fundamento": GROUNDS}, format="json")

    def test_history_lists_versions_newest_first(
        self, causal_descargo, causal_evidencia, causal_vocal, make_socio
    ) -> None:
        self._registrar_dos_versiones(causal_descargo, causal_vocal)
        directiva = make_socio(legajo="76011", role=Role.CD)

        response = _client(directiva).get(_url(causal_descargo))

        assert response.status_code == status.HTTP_200_OK
        assert [d["version"] for d in response.data] == [2, 1]
        assert response.data[0]["fundamento"] == GROUNDS

    def test_admin_reads_history_200(
        self, causal_descargo, causal_evidencia, causal_vocal, make_socio
    ) -> None:
        self._registrar_dos_versiones(causal_descargo, causal_vocal)
        admin = make_socio(legajo="76012", role=Role.ADMIN)

        response = _client(admin).get(_url(causal_descargo))

        assert response.status_code == status.HTTP_200_OK
        assert [d["version"] for d in response.data] == [2, 1]

    def test_anonymous_history_401(self, causal_descargo) -> None:
        response = APIClient().get(_url(causal_descargo))

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_imputado_cannot_read_history_403(
        self, causal_descargo, causal_evidencia, causal_vocal, causal_imputado
    ) -> None:
        self._registrar_dos_versiones(causal_descargo, causal_vocal)

        response = _client(causal_imputado).get(_url(causal_descargo))

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_detail_shows_decisions_to_tribunal_only(
        self, causal_descargo, causal_evidencia, causal_vocal, causal_imputado
    ) -> None:
        self._registrar_dos_versiones(causal_descargo, causal_vocal)
        url = f"/api/v1/expedientes/{causal_descargo.expediente_id}/"

        vocal_data = _client(causal_vocal).get(url).data["descargos"][0]
        imputado_data = _client(causal_imputado).get(url).data["descargos"][0]

        assert vocal_data["regla_sugerida"] == "ACCEPTED"
        assert [d["version"] for d in vocal_data["decisiones_causal"]] == [2, 1]
        assert "decisiones_causal" not in imputado_data
        assert "regla_sugerida" not in imputado_data

    def test_history_stays_readable_after_emission(
        self, causal_descargo, causal_evidencia, causal_vocal, make_socio
    ) -> None:
        self._registrar_dos_versiones(causal_descargo, causal_vocal)
        expediente = causal_descargo.expediente
        expediente.estado = EstadoExpedienteEnum.EMITIDO
        expediente.save(update_fields=["estado"])
        directiva = make_socio(legajo="76013", role=Role.CD)
        url = f"/api/v1/expedientes/{expediente.id}/"

        data = _client(directiva).get(url).data["descargos"][0]

        assert [d["version"] for d in data["decisiones_causal"]] == [2, 1]


@pytest.mark.django_db
class TestDetalleInvolucradosYEvidencia:
    def test_listed_evidence_matches_the_suggested_rule(self, multiactor, causal_vocal) -> None:
        url = f"/api/v1/expedientes/{multiactor['descargo'].expediente_id}/"

        descargos = {d["id"]: d for d in _client(causal_vocal).get(url).data["descargos"]}

        for key in ("descargo", "otro_descargo"):
            descargo = multiactor[key]
            listed = {ev["id"] for ev in descargos[descargo.id]["evidencias"]}
            assert listed == {str(ev.id) for ev in current_evidence_for(descargo)}
            assert descargos[descargo.id]["regla_sugerida"] == "ACCEPTED"

    def test_descargo_without_evidence_suggests_rejection(
        self, causal_descargo, causal_vocal
    ) -> None:
        url = f"/api/v1/expedientes/{causal_descargo.expediente_id}/"

        descargo = _client(causal_vocal).get(url).data["descargos"][0]

        assert descargo["evidencias"] == []
        assert descargo["regla_sugerida"] == "REJECTED"

    def test_involucrados_expose_first_and_last_name(
        self, causal_descargo, causal_vocal, causal_imputado
    ) -> None:
        url = f"/api/v1/expedientes/{causal_descargo.expediente_id}/"

        data = _client(causal_vocal).get(url).data

        assert data["socios"][0]["first_name"] == causal_imputado.first_name
        assert data["socios"][0]["last_name"] == causal_imputado.last_name
        assert data["descargos"][0]["socio_first_name"] == causal_imputado.first_name
        assert data["descargos"][0]["socio_last_name"] == causal_imputado.last_name


def _expediente_con_causal_decidida(numero: int, make_socio, make_evidencia, vocal) -> None:
    imputado = make_socio(legajo=f"77{numero:03d}")
    expediente = Expediente.objects.create(
        numero=f"EXP-{numero:04d}/2026",
        socio=imputado,
        motivo="Inasistencia",
        estado=EstadoExpedienteEnum.REVISION_RESOLUCION,
    )
    expediente.socios.add(imputado)
    descargo = DescargoExpediente.objects.create(
        expediente=expediente,
        socio=imputado,
        tipo=TipoDescargoEnum.T02_CERTIFICADO,
        causal="Enfermedad",
    )
    make_evidencia(expediente, imputado, descargo=descargo)
    _client(vocal).post(_url(descargo), {"decision": "ACCEPTED"}, format="json")


@pytest.mark.django_db
class TestRendimientoListado:
    URL = "/api/v1/expedientes/gestion/"

    def _count_queries(self, client: APIClient) -> int:
        with CaptureQueriesContext(connection) as ctx:
            response = client.get(self.URL)
        assert response.status_code == status.HTTP_200_OK
        return len(ctx.captured_queries)

    def test_t02_causales_do_not_add_queries_per_descargo(
        self, causal_vocal, make_socio, make_evidencia, django_assert_num_queries
    ) -> None:
        client = _client(causal_vocal)
        _expediente_con_causal_decidida(1, make_socio, make_evidencia, causal_vocal)
        baseline = self._count_queries(client)

        for numero in range(2, 7):
            _expediente_con_causal_decidida(numero, make_socio, make_evidencia, causal_vocal)

        with django_assert_num_queries(baseline):
            response = client.get(self.URL)
        assert len(response.data) == 6
        assert all(e["descargos"][0]["decisiones_causal"] for e in response.data)
