"""TS77.34: filtros y clasificación comprobados en SQL antes de paginar."""

from datetime import date

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from rest_framework.test import APIClient

from padron.adapters import DatabasePadronAdapter
from padron.domain import SocioCategoryEnum
from padron.models import Socio, SocioEmail, SocioEstadoHistorial, SocioEstudio, Subcomision
from ranking.serializers import RankingSocioSerializer
from ranking.services import get_reconciled_ranking_queryset
from tests.legacy_schema import create_legacy_record


@pytest.fixture(scope="session", autouse=True)
def classification_satellite_tables(django_db_setup, django_db_blocker):
    """Completa tablas propias de tests si otro módulo no las creó previamente."""
    created = []
    with django_db_blocker.unblock():
        existing = set(connection.introspection.table_names())
        with connection.schema_editor() as editor:
            for model in (SocioEmail, SocioEstadoHistorial):
                if model._meta.db_table not in existing:
                    editor.create_model(model)
                    created.append(model)
                    existing.add(model._meta.db_table)
    yield
    with django_db_blocker.unblock():
        with connection.schema_editor() as editor:
            for model in reversed(created):
                if model._meta.db_table in connection.introspection.table_names():
                    editor.delete_model(model)


@pytest.fixture
def classification_records(db) -> dict[int, tuple[str, int | None]]:
    """NULL desconocido y subcomisión/cargo no sustituyen un marcador confirmado."""
    from socios.models import InstitutionalMembershipCondition

    regular_sub = create_legacy_record(Subcomision, codSubcomision=1, nombre="Cómputos")
    ex_sub = create_legacy_record(Subcomision, codSubcomision=11, nombre="Ex Viajeros")
    cases = [
        (1, "JUNIOR", 1),
        (2, "JUNIOR", 2),
        (3, "SENIOR", 3),
        (4, "SENIOR", 4),
        (5, "SENIOR", 5),
        (6, "SENIOR", 6),
        (None, "EX_TRAVELER", None),
        (None, "UNKNOWN", None),
        (0, "UNKNOWN", None),
        (7, "UNKNOWN", None),
        (None, "UNKNOWN", None),
    ]
    expected = {}
    for offset, (stored_year, category, projected_year) in enumerate(cases, start=1):
        number = 8034000 + offset
        # El helper anterior completa None con año 1: este fixture conserva NULL explícito.
        socio = Socio(
            nroSocio=number,
            nombre=f"Socio {offset}",
            apellido=f"Clasificación {offset:02d}",
            fechaIngreso=date(2024, 1, 1),
            codTipoDoc=1,
            nroDoc=40000000 + offset,
            fechaNac=date(2000, 1, 1),
            codSexo=1,
            subcomision=ex_sub if offset == 11 else regular_sub,
            anoSocial=stored_year,
            idTipoSocio=12,
        )
        socio._allow_write = True
        socio.save(force_insert=True)
        create_legacy_record(
            SocioEstudio,
            compositeKey=number,
            socio=socio,
            nroLegajo=9034000 + offset,
            codEspecialidad=1,
        )
        if category == "EX_TRAVELER":
            marker = InstitutionalMembershipCondition(
                institutional_number=number,
                condition="EX_TRAVELER",
                source_reference="test:SCRUM-77:RN77-01",
                social_cycle="TEST-2026",
            )
            marker.full_clean()
            marker.save()
        expected[number] = category, projected_year
    return expected


@pytest.mark.django_db
def test_real_adapter_ranking_and_detail_share_classification(classification_records) -> None:
    repo = DatabasePadronAdapter()
    result = repo.list_socios(page_size=100)
    actual = {dto.socio_id: (dto.category.value, dto.social_year) for dto in result.results}
    assert result.count == len(classification_records)
    assert actual == classification_records
    ranking = RankingSocioSerializer(get_reconciled_ranking_queryset(), many=True).data
    assert {int(row["id"]): row["categoria"] for row in ranking} == {
        number: category for number, (category, _) in classification_records.items()
    }
    for number, (category, year) in classification_records.items():
        dto = repo.get_by_id(number)
        assert dto is not None
        assert (dto.category.value, dto.social_year) == (category, year)
        by_legajo = repo.get_by_legajo(str(9034000 + number - 8034000))
        assert by_legajo == dto
        assert dto.is_active is True


@pytest.mark.django_db
@pytest.mark.parametrize("category", ["JUNIOR", "SENIOR", "EX_TRAVELER", "UNKNOWN"])
def test_category_sql_count_and_pages_are_consistent(
    classification_records, category: str, django_assert_num_queries
) -> None:
    expected_ids = [
        number
        for number, (expected_category, _) in classification_records.items()
        if expected_category == category
    ]
    repo = DatabasePadronAdapter()
    with CaptureQueriesContext(connection) as captured:
        first = repo.list_socios(category=SocioCategoryEnum(category), page_size=1)
    assert len(captured) == 4
    assert first.count == len(expected_ids)
    assert [dto.socio_id for dto in first.results] == expected_ids[:1]
    assert "LIMIT 1" in captured[1]["sql"]
    assert "WHERE" in captured[0]["sql"]
    with django_assert_num_queries(4):
        last = repo.list_socios(
            category=SocioCategoryEnum(category), page=len(expected_ids), page_size=1
        )
    assert last.count == len(expected_ids)
    assert [dto.socio_id for dto in last.results] == expected_ids[-1:]
    with django_assert_num_queries(2):
        empty = repo.list_socios(
            category=SocioCategoryEnum(category), page=len(expected_ids) + 1, page_size=1
        )
    assert empty.count == len(expected_ids)
    assert empty.results == []


@pytest.mark.django_db
@pytest.mark.parametrize(
    "supplied,canonical",
    [
        ("JUNIOR", "JUNIOR"),
        ("PASSIVE", "JUNIOR"),
        ("PASIVO", "JUNIOR"),
        ("SENIOR", "SENIOR"),
        ("ACTIVE", "SENIOR"),
        ("ACTIVO", "SENIOR"),
        ("EX_TRAVELER", "EX_TRAVELER"),
        ("UNKNOWN", "UNKNOWN"),
    ],
)
def test_ranking_http_filters_use_canonical_sql_semantics(
    classification_records, supplied: str, canonical: str
) -> None:
    expected_ids = {
        number for number, (category, _) in classification_records.items() if category == canonical
    }
    with CaptureQueriesContext(connection) as captured:
        response = APIClient().get("/api/v1/ranking/", {"categoria": supplied})
    assert response.status_code == 200, response.data
    assert len(captured) == 1
    assert {int(row["id"]) for row in response.data} == expected_ids
    assert {row["categoria"] for row in response.data} == {canonical}
