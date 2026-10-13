"""Proyección de lectura de expedientes, sin reconstruir ni modificar actos."""

from collections import defaultdict
from typing import Any, TypedDict

from django.db import DatabaseError
from django.db.models import Q
from rest_framework.exceptions import APIException

from core.models import DemoFixtureOwnership
from expedientes.models import Expediente, SolicitudT01
from padron.models import Socio as InstitutionalSocio
from padron.models import SocioEstudio
from socios.demo_catalog import CATALOG
from socios.demo_presentation import SCENE_PRESENTATIONS, legacy_scene_reason
from socios.identity import _positive_number
from socios.models import Socio
from socios.points import has_institutional_points_source


class CaseMember(TypedDict):
    local_socio_id: int
    full_name: str
    login_identifier: str
    institutional_number: int | None
    academic_number: str | None


class CaseReadMetadata(TypedDict):
    title: str
    motivo: str
    creator: CaseMember | None
    involved_members: list[CaseMember]


class CasePresentationUnavailable(APIException):
    status_code = 503
    default_detail = "No se pudo consultar la información del expediente. Intente nuevamente."


def case_members(case: Expediente) -> list[Socio]:
    """El socio principal forma parte del caso aun sin M2M en registros anteriores."""
    members = {case.socio_id: case.socio}
    members.update((member.pk, member) for member in case.socios.all())
    return list(members.values())


def _request_overrides(request: SolicitudT01, key: str) -> dict[str, str]:
    presentation = SCENE_PRESENTATIONS[key]
    old_reason = legacy_scene_reason(key)
    known = {
        "titulo": (f"SCRUM-77 [{key}]", presentation.title),
        "motivo": (old_reason, presentation.reason),
        "razon": (old_reason, presentation.reason),
        "causal": ("Escena sintética de demostración", presentation.causal),
        "anexo_lugar": ("Sede AVEIT — espacio ficticio de demostración", presentation.place),
        "anexo_relato": (
            "Hecho sintético, sin efectos sobre personas ni actos institucionales.",
            presentation.reason,
        ),
        "anexo_testigos": (
            "No se presentan testigos reales en esta demostración.",
            presentation.witnesses,
        ),
    }
    overrides = {
        field: approved
        for field, (old, approved) in known.items()
        if getattr(request, field) == old
    }
    return overrides


def request_presentation_overrides(requests: list[SolicitudT01]) -> dict[Any, dict[str, str]]:
    """Sólo plantillas exactas de solicitudes cuya propiedad está persistida."""
    by_id = {str(request.pk): request for request in requests}
    if not by_id:
        return {}
    refs = DemoFixtureOwnership.objects.filter(
        profile=CATALOG.profile,
        owned=True,
        namespace=SolicitudT01._meta.db_table,
        object_key__in=by_id,
    )
    result = {}
    for ref in refs:
        if ref.fixture_key in SCENE_PRESENTATIONS and ref.fixture_key.startswith("t01."):
            request = by_id[ref.object_key]
            result[request.pk] = _request_overrides(request, ref.fixture_key)
    return result


def _institutional_identities(profiles: list[Socio]) -> dict[int, tuple[int, str | None]]:
    """Resolver en lote los mismos vínculos únicos y legajos reales del legajo.

    No se usa la PK operativa como nroSocio. Un adaptador mock deliberado no
    acredita una identidad institucional; un fallo real de base no se oculta.
    """
    if not has_institutional_points_source():
        return {}
    user_ids = {profile.user_id for profile in profiles} | {-1}
    academic = {
        number for profile in profiles if (number := _positive_number(profile.legajo)) is not None
    } | {-1}
    candidates = list(
        InstitutionalSocio.objects.filter(
            Q(user_id__in=user_ids)
            | Q(pk__in=SocioEstudio.objects.filter(nroLegajo__in=academic).values("socio_id"))
        ).values("nroSocio", "user_id")
    )
    candidate_ids = {row["nroSocio"] for row in candidates} | {-1}
    studies = list(
        SocioEstudio.objects.filter(socio_id__in=candidate_ids).values(
            "socio_id", "nroLegajo", "compositeKey"
        )
    )
    numbers = {row["nroLegajo"] for row in studies if row["nroLegajo"] > 0} | {-1}
    study_owners: dict[int, set[int]] = defaultdict(set)
    for row in SocioEstudio.objects.filter(nroLegajo__in=numbers).values("nroLegajo", "socio_id"):
        study_owners[row["nroLegajo"]].add(row["socio_id"])
    local_owners: dict[str, set[int]] = defaultdict(set)
    for pk, legajo in Socio.objects.filter(
        legajo__in=[str(number) for number in numbers]
    ).values_list("pk", "legajo"):
        local_owners[legajo].add(pk)
    by_user: dict[int, list[int]] = defaultdict(list)
    candidate_users = {}
    for row in candidates:
        candidate_users[row["nroSocio"]] = row["user_id"]
        if row["user_id"] is not None:
            by_user[row["user_id"]].append(row["nroSocio"])
    studies_by_id: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in sorted(studies, key=lambda row: row["compositeKey"], reverse=True):
        studies_by_id[row["socio_id"]].append(row)
    result = {}
    for profile in profiles:
        direct = by_user[profile.user_id]
        if len(direct) > 1:
            continue
        if direct:
            member_id = direct[0]
        else:
            number = _positive_number(profile.legajo)
            owners = study_owners.get(number, set())
            if len(owners) != 1:
                continue
            member_id = next(iter(owners))
            if candidate_users.get(member_id) is not None:
                continue
            linked_locals = set()
            for study in studies_by_id[member_id]:
                real_number = study["nroLegajo"]
                if real_number > 0 and study_owners[real_number] == {member_id}:
                    linked_locals.update(local_owners[str(real_number)])
            if linked_locals != {profile.pk}:
                continue
        if _positive_number(str(member_id)) is None:
            continue
        own_studies = studies_by_id[member_id]
        academic_number = (
            str(own_studies[0]["nroLegajo"])
            if own_studies and own_studies[0]["nroLegajo"] > 0
            else None
        )
        result[profile.pk] = (member_id, academic_number)
    return result


def build_case_read_metadata(cases: list[Expediente]) -> dict[int, CaseReadMetadata]:
    """Batch para evitar consultas adicionales por cada expediente o participante."""
    if not cases:
        return {}
    try:
        case_ids = [case.pk for case in cases]
        requests = list(SolicitudT01.objects.filter(expediente_id__in=case_ids))
        requests_by_case = {request.expediente_id: request for request in requests}
        request_overrides = request_presentation_overrides(requests)
        case_keys = {
            int(ref.object_key): ref.fixture_key.removesuffix(".expediente")
            for ref in DemoFixtureOwnership.objects.filter(
                profile=CATALOG.profile,
                owned=True,
                namespace=Expediente._meta.db_table,
                object_key__in=[str(pk) for pk in case_ids],
            )
            if ref.fixture_key.removesuffix(".expediente") in SCENE_PRESENTATIONS
        }
        members_by_case = {case.pk: case_members(case) for case in cases}
        actors = {}
        for case in cases:
            changes = sorted(
                case.cambios_estado.all(), key=lambda change: (change.fecha_hora, change.pk)
            )
            actors[case.pk] = changes[0].actor if changes else None
        actor_names = {actor for actor in actors.values() if actor}
        actor_legajos = {
            actor.removeprefix(prefix)
            for actor in actor_names
            for prefix in ("SOLICITANTE_", "IMPORTACION_DEMO_")
            if actor.startswith(prefix)
        }
        profile_ids = {member.pk for members in members_by_case.values() for member in members}
        profile_ids.update(request.solicitante_id for request in requests)
        profiles = list(
            Socio.objects.filter(
                Q(pk__in=profile_ids)
                | Q(user__username__in=actor_names)
                | Q(legajo__in=actor_legajos)
            ).select_related("user")
        )
        profiles_by_id = {profile.pk: profile for profile in profiles}
        identities = _institutional_identities(profiles)

        def member_dto(profile: Socio) -> CaseMember:
            number, academic = identities.get(profile.pk, (None, None))
            return {
                "local_socio_id": profile.pk,
                "full_name": profile.user.get_full_name().strip()
                or f"{profile.first_name} {profile.last_name}".strip(),
                "login_identifier": profile.user.get_username(),
                "institutional_number": number,
                "academic_number": academic,
            }

        result = {}
        for case in cases:
            request = requests_by_case.get(case.pk)
            creator = None
            if request:
                creator = profiles_by_id.get(request.solicitante_id)
            else:
                actor = actors[case.pk]
                candidates = [
                    profile for profile in profiles if profile.user.get_username() == actor
                ]
                if not candidates and actor:
                    for prefix in ("SOLICITANTE_", "IMPORTACION_DEMO_"):
                        if actor.startswith(prefix):
                            candidates = [
                                profile
                                for profile in profiles
                                if profile.legajo == actor.removeprefix(prefix)
                            ]
                            break
                if len(candidates) == 1:
                    creator = candidates[0]
            key = case_keys.get(case.pk)
            if key and case.motivo == legacy_scene_reason(key):
                title, reason = SCENE_PRESENTATIONS[key].title, SCENE_PRESENTATIONS[key].reason
            elif key and case.motivo == SCENE_PRESENTATIONS[key].case_text:
                title, reason = SCENE_PRESENTATIONS[key].title, SCENE_PRESENTATIONS[key].reason
            else:
                title, reason = (
                    case.motivo.splitlines()[0] if case.motivo else case.numero,
                    case.motivo,
                )
            if request:
                title = request_overrides.get(request.pk, {}).get("titulo", request.titulo)
            result[case.pk] = {
                "title": title,
                "motivo": reason,
                "creator": member_dto(creator) if creator else None,
                "involved_members": [
                    member_dto(profiles_by_id[member.pk]) for member in members_by_case[case.pk]
                ],
            }
        return result
    except DatabaseError as exc:
        raise CasePresentationUnavailable from exc
