"""Pruebas de integración de la API de valoraciones T03 (S4-03)."""

import pytest
from django.contrib.auth import get_user_model
from django.db import OperationalError, connection
from django.test.utils import CaptureQueriesContext
from rest_framework import status
from rest_framework.test import APIClient

from expedientes.models import (
    DescargoExpediente,
    EstadoExpedienteEnum,
    Expediente,
    SolicitudT01,
    TipoDescargoEnum,
    ValoracionT03,
    ValoracionT03Antecedente,
)
from expedientes.services.t03_valuation_service import PADRON_UNAVAILABLE_MESSAGE
from padron.adapters import DbTribunalConditionProvider
from padron.models import Socio as PadronSocio
from socios.models import Role
from tests.legacy_schema import create_legacy_record

pytestmark = pytest.mark.django_db

GROUNDS = "El Tribunal considera acreditada la causa extraordinaria invocada."


def _url(descargo: DescargoExpediente) -> str:
    return f"/api/v1/expedientes/{descargo.expediente_id}/descargos/{descargo.id}/valoraciones-t03/"


def _client(user) -> APIClient:
    client = APIClient()
    client.force_authenticate(user=user)
    return client


def _post(user, descargo: DescargoExpediente, **payload):
    body = {"resultado": "ACCEPTED", "fundamento": GROUNDS, **payload}
    return _client(user).post(_url(descargo), body, format="json")


@pytest.fixture
def emitido(t03_descargo) -> Expediente:
    return Expediente.objects.create(
        numero="EXP-0702/2026",
        socio=t03_descargo.socio,
        motivo="Causa emitida anterior",
        estado=EstadoExpedienteEnum.EMITIDO,
    )


class TestRegisterValuationApi:
    def test_tribunal_member_registers_valuation_201(
        self, t03_descargo, tribunal_member, emitido
    ) -> None:
        create_legacy_record(
            PadronSocio,
            nroSocio=953101,
            apellido="Miembro",
            nombre="Titular",
            idTipoSocio=10,
            user_id=tribunal_member.user_id,
        )

        response = _post(
            tribunal_member.user,
            t03_descargo,
            resultado="REJECTED",
            antecedente_ids=[emitido.id],
        )

        assert response.status_code == status.HTTP_201_CREATED, response.data
        assert response.data["version"] == 1
        assert response.data["resultado"] == "REJECTED"
        assert response.data["resultado_display"] == "Desaprobada"
        assert response.data["fundamento"] == GROUNDS
        assert response.data["autor_legajo"] == "77002"
        assert response.data["autor_rol"] == Role.TD
        assert response.data["autor_condicion"] == "TITULAR"
        assert response.data["autor_condicion_display"] == "Miembro Titular"
        assert response.data["antecedentes"] == [
            {"expediente_id": emitido.id, "numero": "EXP-0702/2026"}
        ]
        assert response.data["created_at"]
        stored = ValoracionT03.objects.get(pk=response.data["id"])
        assert stored.resultado == "REJECTED"
        assert stored.autor_condicion == "TITULAR"
        assert stored.antecedentes.get().expediente_antecedente_id == emitido.id

    def test_member_missing_from_padron_is_recorded_as_not_informed(
        self, t03_descargo, tribunal_member
    ) -> None:
        response = _post(tribunal_member.user, t03_descargo)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["autor_condicion"] == "NO_INFORMADA"
        assert response.data["autor_condicion_display"] == "No informada en el padrón"
        assert response.data["antecedentes"] == []

    def test_padron_read_failure_503_records_nothing(
        self, t03_descargo, tribunal_member, emitido, monkeypatch
    ) -> None:
        def failing_read(_provider, _user_id: int) -> None:
            raise OperationalError("padron unavailable")

        monkeypatch.setattr(DbTribunalConditionProvider, "condition_for_user", failing_read)

        response = _post(tribunal_member.user, t03_descargo, antecedente_ids=[emitido.id])

        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        assert response.data["detail"] == PADRON_UNAVAILABLE_MESSAGE
        assert not ValoracionT03.objects.exists()
        assert not ValoracionT03Antecedente.objects.exists()

    @pytest.mark.parametrize("fundamento", ["", "   ", "Muy corto", "x" * 5001])
    def test_invalid_grounds_400(self, t03_descargo, tribunal_member, fundamento) -> None:
        response = _post(tribunal_member.user, t03_descargo, fundamento=fundamento)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "fundamento" in response.data["detail"]
        assert not ValoracionT03.objects.exists()

    def test_missing_grounds_400(self, t03_descargo, tribunal_member) -> None:
        response = _client(tribunal_member.user).post(
            _url(t03_descargo), {"resultado": "ACCEPTED"}, format="json"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "fundamento" in response.data["detail"]
        assert not ValoracionT03.objects.exists()

    def test_invalid_result_400(self, t03_descargo, tribunal_member) -> None:
        response = _post(tribunal_member.user, t03_descargo, resultado="PARTIAL")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "resultado" in response.data["detail"]
        assert not ValoracionT03.objects.exists()

    def test_t02_descargo_400(self, causal_descargo, tribunal_member) -> None:
        response = _post(tribunal_member.user, causal_descargo)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "T03" in response.data["detail"]
        assert not ValoracionT03.objects.exists()

    def test_withdrawn_descargo_400(self, t03_descargo, tribunal_member) -> None:
        DescargoExpediente.objects.filter(pk=t03_descargo.pk).update(es_vigente=False)

        response = _post(tribunal_member.user, t03_descargo)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "vigente" in response.data["detail"]
        assert not ValoracionT03.objects.exists()

    def test_antecedent_not_emitted_400(self, t03_descargo, tribunal_member, emitido) -> None:
        Expediente.objects.filter(pk=emitido.pk).update(
            estado=EstadoExpedienteEnum.PENDIENTE_CORREOS
        )

        response = _post(tribunal_member.user, t03_descargo, antecedente_ids=[emitido.id])

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "emitido" in response.data["detail"]
        assert not ValoracionT03.objects.exists()
        assert not ValoracionT03Antecedente.objects.exists()

    def test_unknown_antecedent_400(self, t03_descargo, tribunal_member) -> None:
        response = _post(tribunal_member.user, t03_descargo, antecedente_ids=[999999])

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert not ValoracionT03.objects.exists()

    def test_repeated_antecedent_400(self, t03_descargo, tribunal_member, emitido) -> None:
        response = _post(
            tribunal_member.user, t03_descargo, antecedente_ids=[emitido.id, emitido.id]
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "repetido" in response.data["detail"]
        assert not ValoracionT03.objects.exists()

    def test_own_expediente_as_antecedent_400(self, t03_descargo, tribunal_member) -> None:
        response = _post(
            tribunal_member.user, t03_descargo, antecedente_ids=[t03_descargo.expediente_id]
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "mismo expediente" in response.data["detail"]
        assert not ValoracionT03.objects.exists()

    def test_outside_valuation_stage_409(self, t03_descargo, tribunal_member) -> None:
        Expediente.objects.filter(pk=t03_descargo.expediente_id).update(
            estado=EstadoExpedienteEnum.JUSTIFICANDO
        )

        response = _post(tribunal_member.user, t03_descargo)

        assert response.status_code == status.HTTP_409_CONFLICT
        assert "no admite valoraciones" in response.data["detail"]
        assert not ValoracionT03.objects.exists()

    def test_unknown_descargo_404(self, t03_descargo, tribunal_member) -> None:
        url = f"/api/v1/expedientes/{t03_descargo.expediente_id}/descargos/999999/valoraciones-t03/"

        response = _client(tribunal_member.user).post(
            url, {"resultado": "ACCEPTED", "fundamento": GROUNDS}, format="json"
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_unknown_expediente_404(self, t03_descargo, tribunal_member) -> None:
        url = f"/api/v1/expedientes/999999/descargos/{t03_descargo.id}/valoraciones-t03/"

        response = _client(tribunal_member.user).post(
            url, {"resultado": "ACCEPTED", "fundamento": GROUNDS}, format="json"
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_anonymous_401(self, t03_descargo) -> None:
        response = APIClient().post(
            _url(t03_descargo), {"resultado": "ACCEPTED", "fundamento": GROUNDS}, format="json"
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert not ValoracionT03.objects.exists()

    @pytest.mark.parametrize("role", [Role.SOCIO, Role.CD, Role.ADMIN, Role.FISCALIZADORA])
    def test_non_tribunal_role_403(self, t03_descargo, make_socio, role) -> None:
        other = make_socio(legajo="77030", role=role)

        response = _post(other.user, t03_descargo)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert not ValoracionT03.objects.exists()

    def test_user_without_socio_403(self, t03_descargo) -> None:
        user = get_user_model().objects.create_user(username="sin-socio", password="pass-12345")

        response = _post(user, t03_descargo)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert not ValoracionT03.objects.exists()

    def test_interested_party_member_403(self, t03_descargo, make_socio) -> None:
        member = make_socio(legajo="77031", role=Role.TD)
        t03_descargo.expediente.socios.add(member)

        response = _post(member.user, t03_descargo)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "parte interesada" in response.data["detail"]
        assert not ValoracionT03.objects.exists()

    def test_interested_party_gets_403_even_outside_stage(self, t03_descargo, make_socio) -> None:
        member = make_socio(legajo="77032", role=Role.TD)
        t03_descargo.expediente.socios.add(member)
        Expediente.objects.filter(pk=t03_descargo.expediente_id).update(
            estado=EstadoExpedienteEnum.EMITIDO
        )

        response = _post(member.user, t03_descargo)

        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestListValuationsApi:
    @pytest.fixture
    def two_versions(self, t03_descargo, tribunal_member, emitido) -> None:
        assert _post(tribunal_member.user, t03_descargo).status_code == 201
        second = _post(
            tribunal_member.user,
            t03_descargo,
            resultado="REJECTED",
            fundamento="Nuevo criterio: la causa no quedó acreditada con suficiencia.",
            antecedente_ids=[emitido.id],
        )
        assert second.status_code == 201

    @pytest.mark.parametrize("role", [Role.TD, Role.CD, Role.ADMIN])
    def test_authorities_list_newest_first(
        self, t03_descargo, two_versions, make_socio, emitido, role
    ) -> None:
        reader = make_socio(legajo="77040", role=role)

        response = _client(reader.user).get(_url(t03_descargo))

        assert response.status_code == status.HTTP_200_OK
        assert [item["version"] for item in response.data] == [2, 1]
        newest = response.data[0]
        assert newest["resultado"] == "REJECTED"
        assert newest["fundamento"].startswith("Nuevo criterio")
        assert newest["antecedentes"] == [{"expediente_id": emitido.id, "numero": "EXP-0702/2026"}]
        assert newest["autor_legajo"] == "77002"
        assert newest["autor_condicion"] == "NO_INFORMADA"
        assert newest["created_at"]

    def test_empty_history_200(self, t03_descargo, tribunal_member) -> None:
        response = _client(tribunal_member.user).get(_url(t03_descargo))

        assert response.status_code == status.HTTP_200_OK
        assert response.data == []

    def test_imputado_cannot_list_403(self, t03_descargo, two_versions) -> None:
        response = _client(t03_descargo.socio.user).get(_url(t03_descargo))

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_anonymous_cannot_list_401(self, t03_descargo) -> None:
        response = APIClient().get(_url(t03_descargo))

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_unknown_descargo_404(self, t03_descargo, tribunal_member) -> None:
        url = f"/api/v1/expedientes/{t03_descargo.expediente_id}/descargos/999999/valoraciones-t03/"

        response = _client(tribunal_member.user).get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestCaseDetailValuations:
    """RF-21, RF-23 y RF-24: las valoraciones son reservadas a TD, CD y Administrador."""

    @pytest.fixture
    def valued(self, t03_descargo, tribunal_member, emitido) -> None:
        assert _post(tribunal_member.user, t03_descargo).status_code == 201
        second = _post(
            tribunal_member.user,
            t03_descargo,
            resultado="REJECTED",
            antecedente_ids=[emitido.id],
        )
        assert second.status_code == 201

    @staticmethod
    def _detail_descargos(user, expediente_id: int) -> dict[int, dict]:
        response = _client(user).get(f"/api/v1/expedientes/{expediente_id}/")
        assert response.status_code == status.HTTP_200_OK
        return {d["id"]: d for d in response.data["descargos"]}

    @pytest.mark.parametrize("role", [Role.TD, Role.CD, Role.ADMIN])
    def test_authorities_see_valuations_newest_first(
        self, t03_descargo, valued, make_socio, emitido, role
    ) -> None:
        reader = make_socio(legajo="77060", role=role)

        item = self._detail_descargos(reader.user, t03_descargo.expediente_id)[t03_descargo.id]

        assert [v["version"] for v in item["valoraciones_t03"]] == [2, 1]
        assert item["valoraciones_t03"][0]["antecedentes"] == [
            {"expediente_id": emitido.id, "numero": "EXP-0702/2026"}
        ]
        assert item["valoraciones_t03"][0]["fundamento"] == GROUNDS

    def test_t03_without_valuations_shows_empty_list(self, t03_descargo, tribunal_member) -> None:
        item = self._detail_descargos(tribunal_member.user, t03_descargo.expediente_id)[
            t03_descargo.id
        ]

        assert item["valoraciones_t03"] == []

    def test_imputado_does_not_see_valuations(self, t03_descargo, valued) -> None:
        item = self._detail_descargos(t03_descargo.socio.user, t03_descargo.expediente_id)[
            t03_descargo.id
        ]

        assert "valoraciones_t03" not in item
        assert GROUNDS not in repr(item)

    def test_t02_descargo_keeps_its_contract(
        self, causal_descargo, tribunal_member, causal_evidencia
    ) -> None:
        item = self._detail_descargos(tribunal_member.user, causal_descargo.expediente_id)[
            causal_descargo.id
        ]

        assert "valoraciones_t03" not in item
        assert item["decisiones_causal"] == []
        assert item["regla_sugerida"] == "ACCEPTED"

    def test_listing_does_not_add_queries_per_t03_valuation(
        self, t03_descargo, tribunal_member, make_socio, django_assert_num_queries
    ) -> None:
        client = _client(tribunal_member.user)
        assert _post(tribunal_member.user, t03_descargo).status_code == 201

        def _count() -> int:
            with CaptureQueriesContext(connection) as ctx:
                assert client.get("/api/v1/expedientes/gestion/").status_code == 200
            return len(ctx.captured_queries)

        baseline = _count()
        for numero in range(2, 6):
            imputado = make_socio(legajo=f"7708{numero}")
            expediente = Expediente.objects.create(
                numero=f"EXP-08{numero:02d}/2026",
                socio=imputado,
                motivo="Otra ausencia",
                estado=EstadoExpedienteEnum.REVISION_RESOLUCION,
            )
            expediente.socios.add(imputado)
            descargo = DescargoExpediente.objects.create(
                expediente=expediente,
                socio=imputado,
                tipo=TipoDescargoEnum.T03_EXTRAORDINARIO,
                texto="Motivo extraordinario.",
            )
            assert _post(tribunal_member.user, descargo).status_code == 201

        with django_assert_num_queries(baseline):
            response = client.get("/api/v1/expedientes/gestion/")
        assert all(e["descargos"][0]["valoraciones_t03"] for e in response.data)


class TestValuationsHiddenFromImputados:
    """RF-24: un imputado de la causa no ve la valoración, tenga el rol que tenga."""

    @pytest.fixture
    def valued(self, t03_descargo, tribunal_member) -> None:
        assert _post(tribunal_member.user, t03_descargo).status_code == 201

    @staticmethod
    def _co_imputado(t03_descargo, make_socio, role: str, legajo: str):
        member = make_socio(legajo=legajo, role=role)
        t03_descargo.expediente.socios.add(member)
        return member

    @pytest.mark.parametrize("role", [Role.TD, Role.CD, Role.ADMIN])
    def test_co_imputado_authority_does_not_see_valuations_in_detail(
        self, t03_descargo, valued, make_socio, role
    ) -> None:
        member = self._co_imputado(t03_descargo, make_socio, role, "77070")

        response = _client(member.user).get(f"/api/v1/expedientes/{t03_descargo.expediente_id}/")

        assert response.status_code == status.HTTP_200_OK
        item = {d["id"]: d for d in response.data["descargos"]}[t03_descargo.id]
        assert "valoraciones_t03" not in item
        assert GROUNDS not in repr(response.data)

    def test_main_imputado_authority_does_not_see_valuations(self, t03_descargo, valued) -> None:
        imputado = t03_descargo.socio
        imputado.role = Role.TD
        imputado.save(update_fields=["role"])

        detail = _client(imputado.user).get(f"/api/v1/expedientes/{t03_descargo.expediente_id}/")
        listed = _client(imputado.user).get(_url(t03_descargo))

        assert GROUNDS not in repr(detail.data)
        assert listed.status_code == status.HTTP_403_FORBIDDEN

    def test_co_imputado_member_does_not_see_valuations_in_listing(
        self, t03_descargo, valued, make_socio
    ) -> None:
        member = self._co_imputado(t03_descargo, make_socio, Role.TD, "77071")

        response = _client(member.user).get("/api/v1/expedientes/gestion/")

        assert response.status_code == status.HTTP_200_OK
        case = next(e for e in response.data if e["id"] == t03_descargo.expediente_id)
        assert all("valoraciones_t03" not in d for d in case["descargos"])
        assert GROUNDS not in repr(response.data)

    @pytest.mark.parametrize("role", [Role.TD, Role.CD, Role.ADMIN])
    def test_co_imputado_authority_gets_403_on_history(
        self, t03_descargo, valued, make_socio, role
    ) -> None:
        member = self._co_imputado(t03_descargo, make_socio, role, "77072")

        response = _client(member.user).get(_url(t03_descargo))

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "imputado" in response.data["detail"]

    def test_t01_requester_member_still_sees_valuations(
        self, t03_descargo, valued, make_socio
    ) -> None:
        requester = make_socio(legajo="77073", role=Role.TD)
        SolicitudT01.objects.create(
            solicitante=requester,
            tipo_accion=SolicitudT01.TipoAccion.SANCTION,
            puntos=-1,
            destinatarios_socios_ids=[t03_descargo.socio_id],
            estado=SolicitudT01.Estado.ISSUED,
            expediente=t03_descargo.expediente,
        )

        history = _client(requester.user).get(_url(t03_descargo))
        detail = _client(requester.user).get(f"/api/v1/expedientes/{t03_descargo.expediente_id}/")

        assert history.status_code == status.HTTP_200_OK
        assert [v["version"] for v in history.data] == [1]
        item = {d["id"]: d for d in detail.data["descargos"]}[t03_descargo.id]
        assert [v["version"] for v in item["valoraciones_t03"]] == [1]
