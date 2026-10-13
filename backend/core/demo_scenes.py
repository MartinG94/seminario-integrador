"""Escenas y antecedentes de SCRUM-77 dentro de la carga demo protegida.

El comando posee la transacción y el bloqueo. Los servicios vigentes asignan
números y plazos; el registro de propiedad permite repetir sin reconstruir
documentos, relaciones ni asientos. No se despachan notificaciones.
"""

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from django.core.exceptions import ValidationError
from django.core.management.base import CommandError
from django.utils import timezone

from expedientes.domain.calendar import compute_business_deadline
from expedientes.domain.holiday_provider import DbHolidayProvider
from expedientes.models import (
    CambioEstadoExpediente,
    EstadoExpedienteEnum,
    Expediente,
    ExpedienteNumberSequence,
    SolicitudT01,
)
from expedientes.serializers import EmitirT01Serializer, SolicitudT01Serializer
from expedientes.services.workflow_service import ExpedienteWorkflowService
from socios.demo_catalog import (
    AdvancedCauseFixture,
    DemoCatalog,
    HistoricalMovementFixture,
    T01Fixture,
    validate_catalog,
)
from socios.demo_presentation import legacy_scene_reason, scene_presentation

if TYPE_CHECKING:
    from core.demo_fixtures import DemoFixtureRegistry
    from core.demo_members import DemoMembersResult

_PRESENTATION_ACTOR = "DEMO_PRESENTATION_V1"
_PRESENTATION_AUDIT_REASON = (
    "Actualización autorizada del título y relato ficticios de demostración. "
    "Se conserva el estado, los plazos, los participantes y los actos del expediente."
)


@dataclass
class DemoScenesResult:
    causes: dict[str, Expediente] = field(default_factory=dict)
    t01s: dict[str, SolicitudT01] = field(default_factory=dict)
    issued_causes: dict[str, Expediente] = field(default_factory=dict)
    historical_expedientes: dict[str, dict[str, Any]] = field(default_factory=dict)
    historical_resolutions: dict[str, dict[str, Any]] = field(default_factory=dict)
    movements: dict[str, dict[str, Any]] = field(default_factory=dict)
    advanced_causes: dict[str, Expediente] = field(default_factory=dict)
    advanced_resolutions: dict[str, dict[str, Any]] = field(default_factory=dict)
    advanced_expedientes: dict[str, dict[str, Any]] = field(default_factory=dict)
    advanced_movements: dict[str, dict[str, Any]] = field(default_factory=dict)


def _scene_reason(key: str) -> str:
    return scene_presentation(key).case_text


def _check_presentation_collision(
    registry: "DemoFixtureRegistry",
    key: str,
    model: Any,
    field: str,
    legacy_value: str,
    approved_value: str,
) -> dict[str, str]:
    """No adoptar ni duplicar una plantilla anterior sin su propiedad acreditada."""
    record = registry.get(key)
    manager = model.objects.using(registry.connection.alias)
    if record is not None:
        if not record.owned or record.namespace != model._meta.db_table:
            raise ValidationError("La presentación demo requiere una referencia propia válida.")
        # Las etiquetas humanas no son únicas. La propiedad física acredita la
        # fila existente, aun si una causa o solicitud de UAT usa el mismo texto.
        matches = manager.filter(**{field: legacy_value}).exclude(pk=record.object_key)
        lookup = {"pk": record.object_key}
    else:
        matches = manager.filter(**{f"{field}__in": (legacy_value, approved_value)})
        lookup = {field: approved_value}
    if matches.exists():
        raise CommandError("Existe una presentación coincidente en una fila ajena al perfil.")
    return lookup


def _upgrade_case_presentation(
    registry: "DemoFixtureRegistry", key: str, case: Expediente, *, scene_key: str | None = None
) -> None:
    """Actualizar sólo la plantilla heredada exacta, con auditoría atómica owned."""
    registry._check_write()
    record = registry.get(key)
    if (
        record is None
        or not record.owned
        or record.namespace != Expediente._meta.db_table
        or record.object_key != str(case.pk)
    ):
        raise ValidationError("La actualización de presentación requiere propiedad acreditada.")
    marker_key = f"{key}.presentation.v1"
    marker = registry.get(marker_key)
    if marker is not None:
        audit = (
            (
                CambioEstadoExpediente.objects.using(registry.connection.alias)
                .filter(pk=marker.object_key)
                .first()
            )
            if marker.namespace == CambioEstadoExpediente._meta.db_table
            else None
        )
        if (
            not marker.owned
            or marker.namespace != CambioEstadoExpediente._meta.db_table
            or audit is None
            or audit.expediente_id != case.pk
            or audit.actor != _PRESENTATION_ACTOR
            or audit.motivo != _PRESENTATION_AUDIT_REASON
            or audit.estado_anterior != audit.estado_nuevo
            or audit.estado_nuevo not in EstadoExpedienteEnum.values
        ):
            raise ValidationError("La actualización perdió su auditoría; no se reconstruye.")
        return
    locked = Expediente.objects.using(registry.connection.alias).select_for_update().get(pk=case.pk)
    base_key = scene_key or key
    if locked.motivo != legacy_scene_reason(base_key):
        return
    locked.motivo = scene_presentation(base_key).case_text
    locked.save(using=registry.connection.alias, update_fields=["motivo"])
    audit = CambioEstadoExpediente.objects.using(registry.connection.alias).create(
        expediente=locked,
        estado_anterior=locked.estado,
        estado_nuevo=locked.estado,
        actor=_PRESENTATION_ACTOR,
        motivo=_PRESENTATION_AUDIT_REASON,
    )
    registry.record(marker_key, CambioEstadoExpediente._meta.db_table, audit.pk)
    case.motivo = locked.motivo


def _record_case_components(registry: "DemoFixtureRegistry", key: str, case: Expediente) -> None:
    """Registrar sólo los componentes generados ahora por los servicios reales."""
    for index, change in enumerate(case.cambios_estado.order_by("pk")):
        registry.record(f"{key}.audit.{index}", CambioEstadoExpediente._meta.db_table, change.pk)
    through = Expediente.socios.through
    for link in through.objects.filter(expediente_id=case.pk).order_by("pk"):
        registry.record(f"{key}.link.{link.socio_id}", through._meta.db_table, link.pk)
    year = int(case.numero.rsplit("/", 1)[1])
    sequence = ExpedienteNumberSequence.objects.get(year=year)
    registry.record(
        f"reference.expediente-sequence.{year}",
        ExpedienteNumberSequence._meta.db_table,
        sequence.pk,
        owned=False,
    )


def _create_t01(fixture: T01Fixture, members: "DemoMembersResult") -> SolicitudT01:
    recipients = [members.institutional_members[key].pk for key in fixture.recipient_member_keys]
    presentation = scene_presentation(fixture.fixture_key)
    reason = presentation.reason
    payload = {
        "tipo_accion": SolicitudT01.TipoAccion.SANCTION,
        "destinatarios_socios_ids": recipients,
        "urgencia": fixture.urgency,
        "titulo": presentation.title,
        "motivo": reason,
        "razon": reason,
        "causal": presentation.causal,
        "puntos": fixture.requested_points if fixture.recipient_member_keys else None,
        "anexo_fecha": timezone.localdate(),
        "anexo_lugar": presentation.place,
        "anexo_relato": presentation.reason,
        "anexo_testigos": presentation.witnesses,
    }
    serializer = SolicitudT01Serializer(data=payload)
    serializer.is_valid(raise_exception=True)
    request = serializer.save(solicitante=members.accounts[fixture.creator_account_key])
    if fixture.status == SolicitudT01.Estado.ISSUED:
        emitter = EmitirT01Serializer(data={}, context={"solicitud": request})
        emitter.is_valid(raise_exception=True)
        request = emitter.save()
        case = request.expediente
        case.iniciar_plazo_descargo(
            fecha_hora_inicio=timezone.now(),
            actor=f"SOLICITANTE_{request.solicitante.legajo}",
        )
    return request


def _load_operational_scenes(
    catalog: DemoCatalog,
    registry: "DemoFixtureRegistry",
    members: "DemoMembersResult",
    result: DemoScenesResult,
) -> None:
    account_by_member = {fixture.member_key: fixture.fixture_key for fixture in catalog.accounts}
    for fixture in catalog.causes:
        key = fixture.fixture_key
        is_new = registry.get(key) is None
        reason = _scene_reason(key)
        lookup = _check_presentation_collision(
            registry, key, Expediente, "motivo", legacy_scene_reason(key), reason
        )
        actor = f"SOLICITANTE_{members.accounts[fixture.creator_account_key].legajo}"
        recipient_ids = [
            members.accounts[account_by_member[member_key]].pk
            for member_key in fixture.recipient_member_keys
        ]
        # fmt: off
        case = registry.ensure_model(
            key,
            Expediente,
            lookup=lookup,
            defaults={},
            create=lambda reason=reason, actor=actor,
                recipient_ids=recipient_ids, fixture=fixture: (
                ExpedienteWorkflowService.open_expediente(
                    motivo=reason,
                    socio_ids=recipient_ids,
                    actor=actor,
                    urgencia=fixture.urgency,
                    points=fixture.requested_points,
                )
            ),
        )
        # fmt: on
        result.causes[key] = case
        if is_new:
            _record_case_components(registry, key, case)
        else:
            _upgrade_case_presentation(registry, key, case)
    for fixture in catalog.t01_scenes:
        key = fixture.fixture_key
        is_new = registry.get(key) is None
        title = scene_presentation(key).title
        lookup = _check_presentation_collision(
            registry, key, SolicitudT01, "titulo", f"SCRUM-77 [{key}]", title
        )
        request = registry.ensure_model(
            key,
            SolicitudT01,
            lookup=lookup,
            defaults={},
            create=lambda fixture=fixture: _create_t01(fixture, members),
        )
        result.t01s[key] = request
        if fixture.status == SolicitudT01.Estado.ISSUED:
            case = request.expediente
            if case is None:
                raise ValidationError("La solicitud demo emitida perdió su expediente vinculado.")
            result.issued_causes[key] = case
            if is_new:
                case_key = f"{key}.expediente"
                registry.record(case_key, Expediente._meta.db_table, case.pk)
                _record_case_components(registry, case_key, case)
            else:
                _upgrade_case_presentation(registry, f"{key}.expediente", case, scene_key=key)


def _resolution_text(
    index: int, movements: list[HistoricalMovementFixture], catalog: DemoCatalog
) -> str:
    """El esquema legado conserva la identificación formal dentro de consideracion."""
    by_key = {member.fixture_key: member for member in catalog.members}
    individualized = " ".join(
        f"Art. {ordinal}: {by_key[move.member_key].first_name} "
        f"{by_key[move.member_key].last_name}, nroSocio "
        f"{by_key[move.member_key].institutional_number}, legajo "
        f"{by_key[move.member_key].academic_number}: {move.points:+.0f} puntos."
        for ordinal, move in enumerate(movements, start=1)
    )
    now = timezone.localtime()
    return (
        f"RESOLUCIÓN DEMO-77-{index:02d}/{now.year}. Córdoba, {now:%d/%m/%Y %H:%M hs}. "
        "Documento sintético de prueba; no constituye un acto institucional válido ni "
        "acredita firmas o facultades de integrantes del Tribunal. "
        "VISTO: regla de individualización de puntos, Notas del PO del 07/10/2026. "
        "CONSIDERANDO: se registra un antecedente ficticio respaldado para comprobar "
        "la integridad del libro mayor y sus referencias. "
        f"SE RESUELVE: {individualized} Registrar este antecedente sintético para "
        "demostración, sin remitir notificaciones externas ni afectar información real."
    )


def _load_history(
    catalog: DemoCatalog,
    registry: "DemoFixtureRegistry",
    members: "DemoMembersResult",
    result: DemoScenesResult,
) -> None:
    groups: dict[str, list[HistoricalMovementFixture]] = defaultdict(list)
    for movement in catalog.historical_movements:
        groups[movement.resolution_key].append(movement)
    state = registry.ensure_legacy(
        "reference.history.emitted-state",
        "tribunal_estadoexpediente",
        "idEstadoExpediente",
        lookup={"idEstadoExpediente": 6},
        values={
            "idEstadoExpediente": 6,
            "nombre": "Emitido",
            "descripcion": "Disposición notificada y puntos aplicados",
        },
        reference=True,
    )
    for index, (resolution_key, movements) in enumerate(groups.items(), start=1):
        title = f"SCRUM77 respaldo {index:02d}"
        total = sum((movement.points for movement in movements), Decimal("0"))
        value = registry.ensure_legacy(
            f"{resolution_key}.value",
            "tribunal_valorsancion",
            "idSancion",
            lookup={"nombre": title},
            values={"nombre": title, "valor": float(total)},
        )
        reference = f"Documento sintético SCRUM-77, respaldo {index:02d}; individualización del PO."
        resolution = registry.ensure_legacy(
            resolution_key,
            "tribunal_datosresolucion",
            "idDatosResolucion",
            lookup={"reglamento1": reference},
            values={
                "reglamento1": reference,
                "consideracion": _resolution_text(index, movements, catalog),
            },
        )
        result.historical_resolutions[resolution_key] = resolution
        case_key = movements[0].legacy_expediente_key
        number = f"D77{index:02d}{catalog.recorded_on.year % 100:02d}"
        case = registry.ensure_legacy(
            case_key,
            "tribunal_expediente",
            "idExpediente",
            lookup={"nroExpediente": number},
            values={
                "nroExpediente": number,
                "estadoExpediente_id": state["idEstadoExpediente"],
                "puntos_id": value["idSancion"],
                "dataRes_id": resolution["idDatosResolucion"],
            },
        )
        if case["dataRes_id"] != resolution["idDatosResolucion"]:
            raise ValidationError("El antecedente demo perdió su respaldo resolutivo.")
        result.historical_expedientes[case_key] = case
    # Mantener el orden original del catálogo; cada asiento recibe sólo sus puntos.
    for fixture in catalog.historical_movements:
        member_id = members.institutional_members[fixture.member_key].pk
        case_id = result.historical_expedientes[fixture.legacy_expediente_key]["idExpediente"]
        invariant = {
            "socio_id": member_id,
            "expediente_id": case_id,
            "puntajeAplicado": fixture.points,
        }
        movement = registry.ensure_legacy(
            fixture.fixture_key,
            "tribunal_puntajeaplicado",
            "idPuntajeAplicado",
            lookup={"socio_id": member_id, "expediente_id": case_id},
            values=invariant,
        )
        if any(movement[column] != value for column, value in invariant.items()):
            raise ValidationError("El asiento demo no conserva su atribución individual inmutable.")
        result.movements[fixture.fixture_key] = movement


def _advanced_history(fixture: AdvancedCauseFixture) -> list[tuple[str, datetime]]:
    """Fechas y etapas declaradas del relato, sin recomputar un plazo congelado."""
    timeline = [
        (EstadoExpedienteEnum.CREADO, fixture.opened_at),
        (EstadoExpedienteEnum.JUSTIFICANDO, fixture.justification_started_at),
        (EstadoExpedienteEnum.REVISION_RESOLUCION, fixture.reviewed_at),
    ]
    for state, timestamp in (
        (EstadoExpedienteEnum.ESPERA_RESOLUCION, fixture.signature_pending_at),
        (EstadoExpedienteEnum.PENDIENTE_CORREOS, fixture.dispatch_pending_at),
        (EstadoExpedienteEnum.EMITIDO, fixture.emitted_at),
    ):
        if timestamp is not None:
            timeline.append((state, timestamp))
    return timeline


def _advanced_timeline(
    fixture: AdvancedCauseFixture,
) -> tuple[list[tuple[str, datetime]], datetime]:
    """Validar una importación histórica; nunca mover un expediente existente."""
    timeline = _advanced_history(fixture)
    now = timezone.now()
    if any(timestamp > now for _, timestamp in timeline):
        raise ValidationError(
            "La historia sintética no admite fechas posteriores a la importación."
        )
    if timeline[-1][0] != fixture.stage or any(
        ExpedienteWorkflowService.NEXT_STATE.get(before[0]) != after[0] or before[1] >= after[1]
        for before, after in zip(timeline, timeline[1:], strict=False)
    ):
        raise ValidationError("La historia sintética no conserva la secuencia canónica de estados.")
    deadline = compute_business_deadline(
        start_at=fixture.justification_started_at,
        business_days=5,
        holiday_provider=DbHolidayProvider(),
    )
    if deadline >= fixture.reviewed_at:
        raise ValidationError("El plazo hábil histórico no venció antes de la revisión sintética.")
    return timeline, deadline


def _insert_historical_instance(
    instance: Expediente | CambioEstadoExpediente, *, database_alias: str
) -> None:
    """Insertar una fixture nueva con fechas explícitas, sin UPDATE ni reloj global.

    raw=True es el mecanismo de carga de fixtures de Django: conserva auto_now.
    Sólo se usa dentro del callback protegido por registry.ensure_model; toda
    instancia se valida y debe ser nueva. No se importa una firma productiva.
    """
    if instance.pk is not None or not instance._state.adding:
        raise ValidationError("La importación histórica sólo admite instancias nuevas.")
    instance.full_clean()
    instance.save_base(raw=True, force_insert=True, using=database_alias)


def _create_advanced_case(
    fixture: AdvancedCauseFixture,
    members: "DemoMembersResult",
    *,
    database_alias: str,
) -> Expediente:
    timeline, deadline = _advanced_timeline(fixture)
    # Los perfiles operativos se resuelven por la cuenta declarada del catálogo;
    # nunca se usa nroSocio institucional como una PK managed.
    recipient_ids = [
        members.local_socios[f"local_socio.{key.removeprefix('member.')}"].pk
        for key in fixture.recipient_member_keys
    ]
    year = fixture.opened_at.year
    case = Expediente(
        numero=ExpedienteWorkflowService.format_numero(
            ExpedienteNumberSequence.next_value(year), year
        ),
        socio_id=recipient_ids[0],
        motivo=_scene_reason(fixture.fixture_key),
        estado=fixture.stage,
        urgencia=fixture.urgency,
        puntos=fixture.requested_points,
        plazo_inicio_at=fixture.justification_started_at,
        plazo_limite_at=deadline,
        created_at=fixture.opened_at,
        updated_at=fixture.updated_at,
    )
    _insert_historical_instance(case, database_alias=database_alias)
    case.socios.set(recipient_ids)
    actor = f"IMPORTACION_DEMO_{members.accounts[fixture.creator_account_key].legajo}"
    previous_state = EstadoExpedienteEnum.CREADO
    for state, timestamp in timeline:
        change = CambioEstadoExpediente(
            expediente=case,
            estado_anterior=previous_state,
            estado_nuevo=state,
            fecha_hora=timestamp,
            actor=actor,
            motivo=(
                f"Historia sintética [{fixture.fixture_key}]: {fixture.source_reference}. "
                f"Registro ficticio de la etapa {state}; sin envío de notificaciones."
            ),
        )
        _insert_historical_instance(change, database_alias=database_alias)
        previous_state = state
    return case


def _load_advanced_cases(
    catalog: DemoCatalog,
    registry: "DemoFixtureRegistry",
    members: "DemoMembersResult",
    result: DemoScenesResult,
) -> None:
    for fixture in catalog.advanced_causes:
        key = fixture.fixture_key
        is_new = registry.get(key) is None
        lookup = _check_presentation_collision(
            registry, key, Expediente, "motivo", legacy_scene_reason(key), _scene_reason(key)
        )
        case = registry.ensure_model(
            key,
            Expediente,
            lookup=lookup,
            defaults={},
            create=lambda fixture=fixture: _create_advanced_case(
                fixture, members, database_alias=registry.connection.alias
            ),
        )
        result.advanced_causes[key] = case
        if is_new:
            _record_case_components(registry, key, case)
        else:
            _upgrade_case_presentation(registry, key, case)
        _validate_advanced_components(fixture, registry, members, case)


def _validate_advanced_components(
    fixture: AdvancedCauseFixture,
    registry: "DemoFixtureRegistry",
    members: "DemoMembersResult",
    case: Expediente,
) -> None:
    """Rechazar referencias existentes movidas; no reparar auditoría o vínculos."""
    previous_state = EstadoExpedienteEnum.CREADO
    for index, (state, timestamp) in enumerate(_advanced_history(fixture)):
        record = registry.get(f"{fixture.fixture_key}.audit.{index}")
        if record is None or record.namespace != CambioEstadoExpediente._meta.db_table:
            raise ValidationError("La historia sintética perdió su registro de auditoría.")
        change = (
            CambioEstadoExpediente.objects.using(registry.connection.alias)
            .filter(pk=record.object_key)
            .first()
        )
        if change is None:
            raise ValidationError("La auditoría histórica registrada no existe; no se reconstruye.")
        if (
            change.expediente_id != case.pk
            or change.estado_anterior != previous_state
            or change.estado_nuevo != state
            or change.fecha_hora != timestamp
            or not change.actor
            or fixture.source_reference not in change.motivo
        ):
            raise ValidationError("La auditoría sintética no conserva la causa y su historia.")
        previous_state = state
    through = Expediente.socios.through
    for key in fixture.recipient_member_keys:
        local_id = members.local_socios[f"local_socio.{key.removeprefix('member.')}"].pk
        record = registry.get(f"{fixture.fixture_key}.link.{local_id}")
        if (
            record is None
            or record.namespace != through._meta.db_table
            or not (
                through.objects.using(registry.connection.alias)
                .filter(pk=record.object_key, expediente_id=case.pk, socio_id=local_id)
                .exists()
            )
        ):
            raise ValidationError("La historia sintética perdió su vínculo individual registrado.")


def _load_advanced_emissions(
    catalog: DemoCatalog,
    registry: "DemoFixtureRegistry",
    members: "DemoMembersResult",
    result: DemoScenesResult,
) -> None:
    """Cuatro INSERT individuales respaldados; no invocar emisión productiva."""
    by_key = {member.fixture_key: member for member in catalog.members}
    emitted = [
        fixture
        for fixture in catalog.advanced_causes
        if fixture.stage == EstadoExpedienteEnum.EMITIDO
    ]
    for index, fixture in enumerate(emitted, start=1):
        key = fixture.fixture_key
        case = result.advanced_causes[key]
        member = by_key[fixture.recipient_member_keys[0]]
        member_id = members.institutional_members[member.fixture_key].pk
        value = registry.ensure_legacy(
            f"{key}.value",
            "tribunal_valorsancion",
            "idSancion",
            lookup={"nombre": f"SCRUM77 avanzado {index:02d}"},
            values={
                "nombre": f"SCRUM77 avanzado {index:02d}",
                "valor": float(fixture.requested_points),
            },
        )
        reference = f"RF77-16 respaldo sintético [{key}]"
        if fixture.emitted_at is None:
            raise ValidationError("El emitido sintético requiere su fecha histórica de emisión.")
        emission = timezone.localtime(fixture.emitted_at)
        text = (
            f"RESOLUCIÓN DEMO-A77-{index:02d}/{emission.year}. "
            f"Córdoba, {emission:%d/%m/%Y %H:%M hs}. "
            f"Ref: {case.numero}, fixture [{key}]. Documento histórico sintético; "
            "sin firma productiva ni acreditación de facultades del Tribunal. "
            "VISTO: individualización de puntos de las Notas del PO del 07/10/2026. "
            "CONSIDERANDO: antecedente ficticio de la historia sintética importada, "
            "sin efectos sobre personas o actos institucionales reales. "
            f"SE RESUELVE: Art. 1: {member.first_name} {member.last_name}, "
            f"nroSocio {member_id}, legajo {member.academic_number}: "
            f"{fixture.requested_points:+.0f} puntos individuales en {case.numero}. "
            "Art. 2: registrar para demostración, sin notificaciones externas."
        )
        resolution = registry.ensure_legacy(
            f"{key}.resolution",
            "tribunal_datosresolucion",
            "idDatosResolucion",
            lookup={"reglamento1": reference},
            values={"reglamento1": reference, "consideracion": text},
        )
        required_references = (
            case.numero,
            f"[{key}]",
            f"nroSocio {member_id}, legajo {member.academic_number}",
            f"{fixture.requested_points:+.0f} puntos individuales",
        )
        if (
            value["valor"] != fixture.requested_points
            or resolution["reglamento1"] != reference
            or any(item not in resolution["consideracion"] for item in required_references)
        ):
            raise ValidationError("El emitido sintético no conserva su resolución individual.")
        legacy_case = registry.ensure_legacy(
            f"{key}.history",
            "tribunal_expediente",
            "idExpediente",
            lookup={"nroExpediente": f"A77{index:02d}{fixture.opened_at.year % 100:02d}"},
            values={
                "nroExpediente": f"A77{index:02d}{fixture.opened_at.year % 100:02d}",
                "estadoExpediente_id": 6,
                "puntos_id": value["idSancion"],
                "dataRes_id": resolution["idDatosResolucion"],
            },
        )
        if (
            legacy_case["dataRes_id"] != resolution["idDatosResolucion"]
            or legacy_case["puntos_id"] != value["idSancion"]
            or legacy_case["estadoExpediente_id"] != 6
        ):
            raise ValidationError("El emitido sintético perdió su respaldo histórico.")
        invariant = {
            "socio_id": member_id,
            "expediente_id": legacy_case["idExpediente"],
            "puntajeAplicado": fixture.requested_points,
        }
        movement = registry.ensure_legacy(
            f"{key}.movement",
            "tribunal_puntajeaplicado",
            "idPuntajeAplicado",
            lookup={"socio_id": member_id, "expediente_id": legacy_case["idExpediente"]},
            values=invariant,
        )
        if any(movement[column] != value for column, value in invariant.items()):
            raise ValidationError("El emitido sintético perdió su atribución individual inmutable.")
        result.advanced_resolutions[key] = resolution
        result.advanced_expedientes[key] = legacy_case
        result.advanced_movements[key] = movement


def load_demo_scenes(
    catalog: DemoCatalog, registry: "DemoFixtureRegistry", members: "DemoMembersResult"
) -> DemoScenesResult:
    """Cargar dentro de atomic; una repetición conserva íntegros los objetos propios."""
    validate_catalog(catalog)
    result = DemoScenesResult()
    _load_operational_scenes(catalog, registry, members, result)
    _load_history(catalog, registry, members, result)
    _load_advanced_cases(catalog, registry, members, result)
    _load_advanced_emissions(catalog, registry, members, result)
    return result
