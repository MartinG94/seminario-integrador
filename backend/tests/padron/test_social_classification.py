"""TS77.34: clasificación institucional canónica y contratos de lectura."""

from dataclasses import replace
from types import SimpleNamespace

import pytest
from rest_framework.test import APIClient

from padron.adapters import MockPadronAdapter
from padron.domain import MembershipStatusEnum, SocioCategoryEnum
from padron.serializers import SocioFilterParamsSerializer, SocioInstitucionalSerializer
from padron.services import classify_category
from socios.serializers import SocioLegajoSerializer
from socios.views import InstitutionalSocioAdapter


@pytest.mark.parametrize(
    "year,expected",
    [(1, "JUNIOR"), (2, "JUNIOR"), (3, "SENIOR"), (4, "SENIOR"), (5, "SENIOR"), (6, "SENIOR")],
)
def test_institutional_classifier_uses_the_confirmed_scale(year: int, expected: str) -> None:
    assert classify_category(year).value == expected


@pytest.mark.parametrize("year", [None, -1, 0, 7, True, False, 1.0, "2"])
def test_unconfirmed_anomalies_remain_unknown(year: object) -> None:
    assert classify_category(year).value == "UNKNOWN"


@pytest.mark.parametrize("year", [None, 0, 3, 7])
def test_explicit_ex_traveler_condition_has_priority(year: int | None) -> None:
    assert classify_category(year, is_ex_traveler=True).value == "EX_TRAVELER"


@pytest.mark.parametrize(
    "supplied,expected",
    [
        ("JUNIOR", "JUNIOR"),
        ("SENIOR", "SENIOR"),
        ("EX_TRAVELER", "EX_TRAVELER"),
        ("UNKNOWN", "UNKNOWN"),
        ("PASSIVE", "JUNIOR"),
        ("PASIVO", "JUNIOR"),
        ("ACTIVE", "SENIOR"),
        ("ACTIVO", "SENIOR"),
    ],
)
def test_category_filters_accept_only_explicit_input_aliases(supplied: str, expected: str) -> None:
    params = SocioFilterParamsSerializer(data={"category": supplied})
    assert params.is_valid(), params.errors
    assert params.validated_data["category"] == expected


@pytest.mark.parametrize("supplied", ["HONORARIO", "EXVIAJERO", "PASSIVES"])
def test_category_filters_reject_unknown_input(supplied: str) -> None:
    params = SocioFilterParamsSerializer(data={"category": supplied})
    assert not params.is_valid()
    assert "category" in params.errors


def test_default_mock_is_recalculated_by_year() -> None:
    repo = MockPadronAdapter()
    assert [(s.socio_id, s.social_year, s.category.value) for s in repo.list_socios().results] == [
        (1001, 4, "SENIOR"),
        (1002, 3, "SENIOR"),
        (1003, 2, "JUNIOR"),
    ]


@pytest.mark.parametrize(
    "code,label", [("EX_TRAVELER", "Exviajero"), ("UNKNOWN", "Sin clasificación")]
)
def test_dto_mock_and_legajo_preserve_null_with_a_distinct_label(code: str, label: str) -> None:
    repo = MockPadronAdapter()
    source = repo.get_by_id(1001)
    assert source is not None
    dto = replace(
        source,
        social_year=None,
        category=SocioCategoryEnum(code),
        is_active=True,
        membership_status=MembershipStatusEnum.ENABLED,
    )
    repo._socios = [dto]
    result = repo.list_socios(category=SocioCategoryEnum(code), page_size=1)
    assert result.count == 1
    assert result.results == [dto]
    assert repo.list_socios(category=SocioCategoryEnum("JUNIOR")).count == 0
    assert repo.list_socios(category=SocioCategoryEnum("SENIOR")).count == 0
    payload = SocioInstitucionalSerializer(dto).data
    assert payload["category"] == code
    assert payload["social_year"] is None
    assert payload["is_active"] is True
    validated = SocioInstitucionalSerializer(data=payload)
    assert validated.is_valid(), validated.errors
    legajo = SocioLegajoSerializer(InstitutionalSocioAdapter(dto)).data
    assert (legajo["category"], legajo["category_display"], legajo["social_year"]) == (
        code,
        label,
        None,
    )
    assert legajo["is_enabled"] is True


@pytest.mark.parametrize(
    "supplied,expected_count,expected_category",
    [
        ("JUNIOR", 1, "JUNIOR"),
        ("PASSIVE", 1, "JUNIOR"),
        ("PASIVO", 1, "JUNIOR"),
        ("SENIOR", 2, "SENIOR"),
        ("ACTIVE", 2, "SENIOR"),
        ("ACTIVO", 2, "SENIOR"),
    ],
)
def test_padron_http_aliases_use_the_new_boundary(
    monkeypatch: pytest.MonkeyPatch,
    supplied: str,
    expected_count: int,
    expected_category: str,
) -> None:
    monkeypatch.setattr("padron.views.get_padron_repository", lambda: MockPadronAdapter())
    client = APIClient()
    client.force_authenticate(user=SimpleNamespace(is_authenticated=True))
    response = client.get("/api/v1/padron/socios/", {"category": supplied, "page_size": 1})
    assert response.status_code == 200, response.data
    assert response.data["count"] == expected_count
    assert len(response.data["results"]) == 1
    assert response.data["results"][0]["category"] == expected_category


@pytest.mark.parametrize(
    "url,param",
    [("/api/v1/padron/socios/", "category"), ("/api/v1/ranking/", "categoria")],
)
def test_unknown_category_query_returns_http_400(url: str, param: str) -> None:
    client = APIClient()
    client.force_authenticate(user=SimpleNamespace(is_authenticated=True))
    response = client.get(url, {param: "HONORARIO"})
    assert response.status_code == 400
