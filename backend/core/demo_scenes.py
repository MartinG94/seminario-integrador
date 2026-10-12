"""Escenas y antecedentes de SCRUM-77 dentro de la carga demo protegida.

El comando posee la transacción y el bloqueo. Los servicios vigentes asignan
números y plazos; el registro de propiedad permite repetir sin reconstruir
documentos, relaciones ni asientos. No se despachan notificaciones.
"""

from collections import defaultdict
from dataclasses import dataclass, field
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from django.core.exceptions import ValidationError
from django.utils import timezone

from expedientes.models import (
    CambioEstadoExpediente,
    Expediente,
    ExpedienteNumberSequence,
    SolicitudT01,
)
from expedientes.serializers import EmitirT01Serializer, SolicitudT01Serializer
from expedientes.services.workflow_service import ExpedienteWorkflowService
from socios.demo_catalog import DemoCatalog, HistoricalMovementFixture, T01Fixture, validate_catalog

if TYPE_CHECKING:
    from core.demo_fixtures import DemoFixtureRegistry
    from core.demo_members import DemoMembersResult


@dataclass
class DemoScenesResult:
    causes: dict[str, Expediente] = field(default_factory=dict)
    t01s: dict[str, SolicitudT01] = field(default_factory=dict)
    issued_causes: dict[str, Expediente] = field(default_factory=dict)
    historical_expedientes: dict[str, dict[str, Any]] = field(default_factory=dict)
    historical_resolutions: dict[str, dict[str, Any]] = field(default_factory=dict)
    movements: dict[str, dict[str, Any]] = field(default_factory=dict)


def _scene_reason(key: str) -> str:
    return f"SCRUM-77 [{key}]: causa ficticia para demostrar los recorridos institucionales."


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
    reason = _scene_reason(fixture.fixture_key)
    payload = {
        "tipo_accion": SolicitudT01.TipoAccion.SANCTION,
        "destinatarios_socios_ids": recipients,
        "urgencia": fixture.urgency,
        "titulo": f"SCRUM-77 [{fixture.fixture_key}]",
        "motivo": reason,
        "razon": reason,
        "causal": "Escena sintética de demostración",
        "puntos": fixture.requested_points if fixture.recipient_member_keys else None,
        "anexo_fecha": timezone.localdate(),
        "anexo_lugar": "Sede AVEIT — espacio ficticio de demostración",
        "anexo_relato": "Hecho sintético, sin efectos sobre personas ni actos institucionales.",
        "anexo_testigos": "No se presentan testigos reales en esta demostración.",
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
        actor = f"SOLICITANTE_{members.accounts[fixture.creator_account_key].legajo}"
        recipient_ids = [
            members.accounts[account_by_member[member_key]].pk
            for member_key in fixture.recipient_member_keys
        ]
        # fmt: off
        case = registry.ensure_model(
            key,
            Expediente,
            lookup={"motivo": reason},
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
    for fixture in catalog.t01_scenes:
        key = fixture.fixture_key
        is_new = registry.get(key) is None
        request = registry.ensure_model(
            key,
            SolicitudT01,
            lookup={"titulo": f"SCRUM-77 [{key}]"},
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


def load_demo_scenes(
    catalog: DemoCatalog, registry: "DemoFixtureRegistry", members: "DemoMembersResult"
) -> DemoScenesResult:
    """Cargar dentro de atomic; una repetición conserva íntegros los objetos propios."""
    validate_catalog(catalog)
    result = DemoScenesResult()
    _load_operational_scenes(catalog, registry, members, result)
    _load_history(catalog, registry, members, result)
    return result
