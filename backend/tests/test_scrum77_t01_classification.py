"""T01: clasificación confirmada, identidades distintas y evidencia preservada."""

from copy import deepcopy
from datetime import date
from decimal import Decimal
from types import SimpleNamespace

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from rest_framework.test import APIClient

from expedientes.models import Expediente, ExpedienteNumberSequence, SolicitudT01
from padron.models import Socio as InstitutionalSocio
from padron.models import SocioEstudio
from socios.models import Role, SocialCategory, Socio, Subcomision

pytestmark = pytest.mark.django_db
UserModel = get_user_model()


def _dto(socio_id: int = 774101, **changes) -> SimpleNamespace:
    fields = {
        "socio_id": socio_id,
        "legajo": f"L{socio_id}",
        "dni": "38007741",
        "first_name": "Ficticio",
        "last_name": "Prueba T01",
        "email": f"socio{socio_id}@aveit.test",
        "subcomision": SimpleNamespace(id=7741, name="Subcomisión T01"),
        "social_year": None,
        "category": "EX_TRAVELER",
        "is_active": True,
        "membership_status": "ENABLED",
    }
    fields.update(changes)
    return SimpleNamespace(**fields)


@pytest.fixture
def t01_client(make_socio) -> tuple[APIClient, Socio]:
    authority = make_socio(legajo="774100", role=Role.CD)
    client = APIClient()
    client.force_authenticate(authority.user)
    return client, authority


def _repository(monkeypatch, *dtos: SimpleNamespace) -> None:
    records = {dto.socio_id: dto for dto in dtos}
    monkeypatch.setattr(
        "expedientes.serializers.get_padron_repository",
        lambda: SimpleNamespace(get_by_id=lambda sid: records.get(sid)),
    )


def _draft(client: APIClient, *ids: int) -> SolicitudT01:
    response = client.post(
        "/api/v1/expedientes/",
        {
            "tipo_accion": "SANCTION",
            "puntos": "-2.50",
            "motivo": "Hecho sintético para verificar clasificación e identidad",
            "destinatarios_socios_ids": list(ids),
        },
        format="json",
    )
    assert response.status_code == 201, response.data
    return SolicitudT01.objects.get(pk=response.data["id"])


def _emit(client: APIClient, draft: SolicitudT01):
    return client.post(f"/api/v1/expedientes/{draft.pk}/emitir/", {}, format="json")


def _rows() -> dict[str, list[dict]]:
    models = (
        UserModel,
        Socio,
        Subcomision,
        SolicitudT01,
        Expediente,
        ExpedienteNumberSequence,
        InstitutionalSocio,
        SocioEstudio,
    )
    return {model._meta.db_table: list(model.objects.order_by("pk").values()) for model in models}


def _institutional(sid: int, *, user_id: int | None, year: int = 4) -> InstitutionalSocio:
    record = InstitutionalSocio(
        nroSocio=sid,
        apellido="Prueba T01",
        nombre="Ficticio",
        fechaIngreso=date(2024, 1, 1),
        fechaNac=date(2000, 1, 1),
        codTipoDoc=1,
        nroDoc=38007741,
        codSexo=1,
        anoSocial=year,
        idTipoSocio=1,
        user_id=user_id,
    )
    record._allow_write = True
    record.save(force_insert=True)
    return record


def test_ex_traveler_is_materialized_without_a_year_and_repeated_without_changes(
    monkeypatch, t01_client
) -> None:
    client, authority = t01_client
    dto = _dto()
    _repository(monkeypatch, dto)
    historical = SolicitudT01.objects.create(
        solicitante=authority,
        tipo_accion="SANCTION",
        puntos=Decimal("-1.00"),
        motivo="Evidencia histórica",
        destinatario_socio_id=77,
        estado="ISSUED",
        snapshot_destinatario={"socio_id": 77, "category": "ACTIVE", "social_year": 4},
        snapshot_emitido={"destinatario": {"category": "PASSIVE", "social_year": 3}},
    )
    history = SolicitudT01.objects.filter(pk=historical.pk).values().get()
    draft = _draft(client, dto.socio_id)
    response = _emit(client, draft)
    assert response.status_code == 200, response.data
    draft.refresh_from_db()
    local = Socio.objects.get(legajo=dto.legajo)
    assert local.pk != dto.socio_id
    assert local.social_year is None
    assert local.category == SocialCategory.EX_TRAVELER
    assert local.role == Role.SOCIO and local.is_enabled
    assert not local.user.has_usable_password()
    assert draft.expediente.socios.get() == local
    assert draft.expediente.socio_id == local.pk
    assert draft.snapshot_destinatario["category"] == "EX_TRAVELER"
    assert draft.snapshot_destinatario["social_year"] is None
    assert draft.snapshot_emitido["destinatarios"] == draft.snapshots_destinatarios
    before = _rows()
    repeated = _emit(client, draft)
    assert repeated.status_code == 200, repeated.data
    assert _rows() == before
    assert SolicitudT01.objects.filter(pk=historical.pk).values().get() == history


@pytest.mark.parametrize(
    "year, expected", [(1, "JUNIOR"), (2, "JUNIOR"), (3, "SENIOR"), (4, "SENIOR"), (6, "SENIOR")]
)
def test_new_snapshots_and_involved_members_use_the_confirmed_year(
    monkeypatch, t01_client, year: int, expected: str
) -> None:
    client, _ = t01_client
    dto = _dto(social_year=year, category=expected)
    _repository(monkeypatch, dto)
    draft = _draft(client, dto.socio_id)
    response = _emit(client, draft)
    assert response.status_code == 200, response.data
    draft.refresh_from_db()
    local = draft.expediente.socios.get()
    assert (local.category, local.social_year) == (expected, year)
    assert (
        draft.snapshot_destinatario["category"],
        draft.snapshot_destinatario["social_year"],
    ) == (expected, year)


@pytest.mark.parametrize(
    "category, year",
    [
        ("UNKNOWN", None),
        ("UNKNOWN", 4),
        ("JUNIOR", None),
        ("SENIOR", 0),
        ("SENIOR", 7),
        ("JUNIOR", True),
        ("SENIOR", "3"),
        ("EX_TRAVELER", 1),
        ("unconfirmed", None),
    ],
)
def test_anomalous_classification_aborts_without_materializing_or_issuing(
    monkeypatch, t01_client, category: str, year
) -> None:
    client, _ = t01_client
    dto = _dto(category=category, social_year=year)
    _repository(monkeypatch, dto)
    draft = _draft(client, dto.socio_id)
    before = _rows()
    response = _emit(client, draft)
    assert response.status_code == 400, response.data
    assert "destinatarios_socios_ids" in response.data
    assert _rows() == before


def test_a_local_pk_collision_does_not_reuse_an_unrelated_person(
    monkeypatch, make_socio, t01_client
) -> None:
    client, _ = t01_client
    foreign = make_socio(legajo="774199", role=Role.TD, is_enabled=False)
    dto = _dto(socio_id=foreign.pk)
    _repository(monkeypatch, dto)
    before = Socio.objects.filter(pk=foreign.pk).values().get()
    user_before = UserModel.objects.filter(pk=foreign.user_id).values().get()
    draft = _draft(client, dto.socio_id)
    response = _emit(client, draft)
    assert response.status_code == 200, response.data
    draft.refresh_from_db()
    local = Socio.objects.get(legajo=dto.legajo)
    assert local.pk != foreign.pk
    assert draft.expediente.socios.get() == local
    assert Socio.objects.filter(pk=foreign.pk).values().get() == before
    assert UserModel.objects.filter(pk=foreign.user_id).values().get() == user_before


def test_real_legajo_and_email_resolve_existing_member_without_changing_access(
    monkeypatch, make_socio, t01_client
) -> None:
    client, _ = t01_client
    local = make_socio(legajo="774144", role=Role.TD, is_enabled=False)
    dto = _dto(legajo=local.legajo, email=local.email)
    _repository(monkeypatch, dto)
    before = Socio.objects.filter(pk=local.pk).values().get()
    user_before = UserModel.objects.filter(pk=local.user_id).values().get()
    draft = _draft(client, dto.socio_id)
    response = _emit(client, draft)
    assert response.status_code == 200, response.data
    draft.refresh_from_db()
    local.refresh_from_db()
    assert (local.category, local.social_year) == (SocialCategory.EX_TRAVELER, None)
    assert draft.expediente.socios.get() == local
    expected = {**before, "category": "EX_TRAVELER", "social_year": None}
    assert Socio.objects.filter(pk=local.pk).values().get() == expected
    assert UserModel.objects.filter(pk=local.user_id).values().get() == user_before


def test_confirmed_institutional_user_link_handles_a_member_without_legajo(
    monkeypatch, make_socio, t01_client
) -> None:
    client, _ = t01_client
    local = make_socio(legajo="774155", role=Role.CD, social_year=4, is_enabled=False)
    _institutional(774155, user_id=local.user_id)
    dto = _dto(socio_id=774155, legajo=None, email=None, social_year=4, category="SENIOR")
    _repository(monkeypatch, dto)
    before = _rows()
    draft = _draft(client, dto.socio_id)
    response = _emit(client, draft)
    assert response.status_code == 200, response.data
    draft.refresh_from_db()
    assert draft.expediente.socios.get() == local
    assert list(UserModel.objects.order_by("pk").values()) == before[UserModel._meta.db_table]
    assert list(Socio.objects.order_by("pk").values()) == before[Socio._meta.db_table]


def test_conflicting_legajo_and_email_references_abort_without_changes(
    monkeypatch, make_socio, t01_client
) -> None:
    client, _ = t01_client
    local = make_socio(legajo="774166")
    unrelated = make_socio(legajo="774167")
    dto = _dto(legajo=local.legajo, email=unrelated.email)
    _repository(monkeypatch, dto)
    draft = _draft(client, dto.socio_id)
    before = _rows()
    response = _emit(client, draft)
    assert response.status_code == 400, response.data
    assert _rows() == before


def test_username_collision_does_not_attach_an_unrelated_account(monkeypatch, t01_client) -> None:
    client, _ = t01_client
    dto = _dto()
    UserModel.objects.create_user(
        username=dto.legajo, email="ajeno@aveit.test", password="Preserved!2026"
    )
    _repository(monkeypatch, dto)
    draft = _draft(client, dto.socio_id)
    before = _rows()
    response = _emit(client, draft)
    assert response.status_code == 400, response.data
    assert _rows() == before


def test_missing_real_identity_is_rejected_without_an_artificial_legajo(
    monkeypatch, t01_client
) -> None:
    client, _ = t01_client
    dto = _dto(legajo=None)
    _repository(monkeypatch, dto)
    draft = _draft(client, dto.socio_id)
    before = _rows()
    response = _emit(client, draft)
    assert response.status_code == 400, response.data
    assert _rows() == before


def test_unknown_late_recipient_preserves_all_previous_references_and_draft(
    monkeypatch, t01_client
) -> None:
    client, _ = t01_client
    confirmed = _dto()
    unknown = _dto(socio_id=774102, category="UNKNOWN")
    _repository(monkeypatch, confirmed, unknown)
    draft = _draft(client, confirmed.socio_id, unknown.socio_id)
    before = deepcopy(_rows())
    response = _emit(client, draft)
    assert response.status_code == 400, response.data
    assert _rows() == before


def test_canonical_snapshot_recalculates_an_old_third_year_label(monkeypatch, t01_client) -> None:
    client, _ = t01_client
    dto = _dto(social_year=3, category="PASSIVE")
    _repository(monkeypatch, dto)
    draft = _draft(client, dto.socio_id)
    response = _emit(client, draft)
    assert response.status_code == 200, response.data
    draft.refresh_from_db()
    assert draft.snapshot_destinatario["category"] == "SENIOR"
    assert draft.expediente.socios.get().category == "SENIOR"


def test_linked_institutional_account_can_be_materialized_without_replacing_credentials(
    monkeypatch, t01_client
) -> None:
    client, _ = t01_client
    dto = _dto()
    user = UserModel.objects.create_user(
        username="cuenta-institucional-t01", email="original@aveit.test", password="Preserved!2026"
    )
    _institutional(dto.socio_id, user_id=user.pk)
    _repository(monkeypatch, dto)
    before = UserModel.objects.filter(pk=user.pk).values().get()
    draft = _draft(client, dto.socio_id)
    response = _emit(client, draft)
    assert response.status_code == 200, response.data
    draft.refresh_from_db()
    assert draft.expediente.socios.get().user_id == user.pk
    assert UserModel.objects.filter(pk=user.pk).values().get() == before


def test_email_without_real_legajo_does_not_establish_identity(
    monkeypatch, make_socio, t01_client
) -> None:
    client, _ = t01_client
    local = make_socio(legajo="774188")
    dto = _dto(legajo=None, email=local.email)
    _repository(monkeypatch, dto)
    draft = _draft(client, dto.socio_id)
    before = _rows()
    response = _emit(client, draft)
    assert response.status_code == 400, response.data
    assert _rows() == before


def test_institutional_account_and_real_legajo_cannot_point_to_different_people(
    monkeypatch, make_socio, t01_client
) -> None:
    client, _ = t01_client
    confirmed = make_socio(legajo="774177")
    unrelated = make_socio(legajo="774178")
    dto = _dto(legajo=unrelated.legajo, email=unrelated.email)
    _institutional(dto.socio_id, user_id=confirmed.user_id)
    _repository(monkeypatch, dto)
    draft = _draft(client, dto.socio_id)
    before = _rows()
    response = _emit(client, draft)
    assert response.status_code == 400, response.data
    assert _rows() == before


def test_late_account_collision_rolls_back_prior_materialization(monkeypatch, t01_client) -> None:
    client, _ = t01_client
    first = _dto()
    conflicting = _dto(socio_id=774102)
    UserModel.objects.create_user(username=conflicting.legajo, email="ajeno@aveit.test")
    _repository(monkeypatch, first, conflicting)
    draft = _draft(client, first.socio_id, conflicting.socio_id)
    before = _rows()
    response = _emit(client, draft)
    assert response.status_code == 400, response.data
    assert _rows() == before


def test_failed_workflow_does_not_leave_a_materialized_member_or_issued_request(
    monkeypatch, t01_client
) -> None:
    client, _ = t01_client
    dto = _dto()
    _repository(monkeypatch, dto)
    draft = _draft(client, dto.socio_id)
    before = _rows()

    def fail_workflow(**kwargs) -> None:
        raise ValidationError({"socios": "Apertura de prueba rechazada."})

    monkeypatch.setattr(
        "expedientes.services.workflow_service.ExpedienteWorkflowService.open_expediente",
        fail_workflow,
    )
    response = _emit(client, draft)
    assert response.status_code == 400, response.data
    assert _rows() == before


def test_a_shared_institutional_account_does_not_establish_a_unique_person(
    monkeypatch, make_socio, t01_client
) -> None:
    client, _ = t01_client
    local = make_socio(legajo="774190")
    dto = _dto(legajo=local.legajo, email=local.email)
    _institutional(dto.socio_id, user_id=local.user_id)
    _institutional(dto.socio_id + 1, user_id=local.user_id)
    _repository(monkeypatch, dto)
    draft = _draft(client, dto.socio_id)
    before = _rows()
    response = _emit(client, draft)
    assert response.status_code == 400, response.data
    assert _rows() == before


@pytest.mark.parametrize("requested_id, returned_id", [(774101, 774102), (1, True), (True, 1)])
def test_institutional_reference_must_match_the_selected_integer_identity(
    monkeypatch, t01_client, requested_id, returned_id
) -> None:
    client, _ = t01_client
    dto = _dto(socio_id=returned_id)
    monkeypatch.setattr(
        "expedientes.serializers.get_padron_repository",
        lambda: SimpleNamespace(get_by_id=lambda sid: dto),
    )
    draft = _draft(client, requested_id)
    before = _rows()
    response = _emit(client, draft)
    assert response.status_code == 400, response.data
    assert "destinatarios_socios_ids" in response.data
    assert _rows() == before


def test_different_institutional_ids_cannot_reuse_one_member_and_keep_the_changes(
    monkeypatch, make_socio, t01_client
) -> None:
    client, _ = t01_client
    local = make_socio(legajo="774191", role=Role.TD, is_enabled=False)
    first = _dto(legajo=local.legajo, email=local.email)
    second = _dto(
        socio_id=774102, legajo=local.legajo, email=local.email, social_year=3, category="SENIOR"
    )
    _repository(monkeypatch, first, second)
    draft = _draft(client, first.socio_id, second.socio_id)
    before = _rows()
    response = _emit(client, draft)
    assert response.status_code == 400, response.data
    assert _rows() == before


def _enrollment(sid: int, key: int, legajo: str, specialty: int = 1) -> None:
    enrollment = SocioEstudio(
        compositeKey=key, socio_id=sid, nroLegajo=int(legajo), codEspecialidad=specialty
    )
    enrollment._allow_write = True
    enrollment.save(force_insert=True)


@pytest.mark.parametrize("existing_local", [True, False], ids=["reuse", "creation"])
def test_a_shared_institutional_legajo_does_not_establish_a_unique_person(
    monkeypatch, make_socio, t01_client, existing_local: bool
) -> None:
    client, _ = t01_client
    legajo = "774192"
    email = f"socio{legajo}@aveit.test"
    if existing_local:
        make_socio(legajo=legajo, role=Role.TD, is_enabled=False, email=email)
    _institutional(774201, user_id=None)
    _institutional(774202, user_id=None)
    _enrollment(774201, 774201, legajo)
    _enrollment(774202, 774202, legajo)
    dto = _dto(socio_id=774201, legajo=legajo, email=email, category="SENIOR", social_year=4)
    _repository(monkeypatch, dto)
    draft = _draft(client, dto.socio_id)
    before = _rows()
    response = _emit(client, draft)
    assert response.status_code == 400, response.data
    assert _rows() == before


def test_multiple_courses_of_one_member_preserve_an_unambiguous_institutional_legajo(
    monkeypatch, make_socio, t01_client
) -> None:
    client, _ = t01_client
    local = make_socio(legajo="774193", role=Role.TD, is_enabled=False)
    _institutional(774203, user_id=None)
    _enrollment(774203, 774203, local.legajo)
    _enrollment(774203, 774204, local.legajo, specialty=2)
    dto = _dto(
        socio_id=774203, legajo=local.legajo, email=local.email, category="SENIOR", social_year=4
    )
    _repository(monkeypatch, dto)
    before_local = Socio.objects.filter(pk=local.pk).values().get()
    before_user = UserModel.objects.filter(pk=local.user_id).values().get()
    before_institutional = list(InstitutionalSocio.objects.order_by("pk").values())
    before_courses = list(SocioEstudio.objects.order_by("pk").values())
    draft = _draft(client, dto.socio_id)
    response = _emit(client, draft)
    assert response.status_code == 200, response.data
    draft.refresh_from_db()
    assert draft.expediente.socios.get() == local
    assert Socio.objects.filter(pk=local.pk).values().get() == {
        **before_local,
        "category": "SENIOR",
        "social_year": 4,
    }
    assert UserModel.objects.filter(pk=local.user_id).values().get() == before_user
    assert list(InstitutionalSocio.objects.order_by("pk").values()) == before_institutional
    assert list(SocioEstudio.objects.order_by("pk").values()) == before_courses
