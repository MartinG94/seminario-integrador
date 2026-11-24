"""Servicio para restaurar la base de datos al snapshot SQL de la rama Regularidad."""

from __future__ import annotations

import os
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import connection, models, transaction
from django.utils import timezone

from expedientes.domain.calendar import compute_business_deadline
from expedientes.domain.holiday_provider import DbHolidayProvider
from expedientes.models import (
    AsistenciaEvento,
    AtencionFelicitacion,
    CambioEstadoExpediente,
    CategoriaEventoEnum,
    ConceptoExpedienteEnum,
    DecisionCausalDescargo,
    DecisionCausalEnum,
    DescargoExpediente,
    EstadoAsistenciaEventoEnum,
    EstadoEventoEnum,
    EstadoExpedienteEnum,
    EstadoResolucionEnum,
    EventoConvocado,
    EventoInstitucional,
    Expediente,
    ModalidadEventoEnum,
    ModoConvocatoriaEnum,
    Resolucion,
    SubtipoReunionEnum,
    TipoDescargoEnum,
    UrgenciaExpedienteEnum,
)
from expedientes.services.ledger_service import LedgerService
from expedientes.services.publication_service import calcular_hash_resolucion
from expedientes.services.resolution_service import registrar_firma_resolucion
from expedientes.services.tribunal_composition_service import TribunalCompositionService
from expedientes.services.workflow_service import ExpedienteWorkflowService
from ranking.domain.ledger import TipoAsiento
from socios.models import Role, Socio, Subcomision


def get_snapshot_path() -> Path:
    """Devuelve la ruta al archivo dump SQL de snapshot de Regularidad."""
    configured = getattr(settings, "REGULARIDAD_SNAPSHOT_PATH", None) or os.getenv(
        "REGULARIDAD_SNAPSHOT_PATH"
    )
    if configured:
        return Path(configured)
    return Path(settings.BASE_DIR).parent / "database" / "snapshot_regularidad.sql"


def split_sql_statements(raw_sql: bytes) -> list[bytes]:
    """Separa sentencias SQL en bytes preservando strings, escapes, binarios y comentarios."""
    statements: list[bytes] = []
    start = 0
    i = 0
    n = len(raw_sql)
    in_quote = 0
    in_line_comment = False
    in_block_comment = False

    while i < n:
        b = raw_sql[i]

        if in_line_comment:
            if b == 10:  # \n
                in_line_comment = False
            i += 1
            continue

        if in_block_comment:
            if b == 42 and i + 1 < n and raw_sql[i + 1] == 47:  # */
                in_block_comment = False
                i += 2
            else:
                i += 1
            continue

        if in_quote:
            if b == 92 and in_quote != 96:  # \ escape (no aplica dentro de backticks)
                i += 2
                continue
            if b == in_quote:
                if i + 1 < n and raw_sql[i + 1] == in_quote:
                    i += 2
                    continue
                in_quote = 0
            i += 1
            continue

        if b in (39, 34, 96):  # ', ", `
            in_quote = b
            i += 1
            continue

        if b == 45 and i + 2 < n and raw_sql[i + 1] == 45 and raw_sql[i + 2] in (32, 9, 10, 13):
            in_line_comment = True
            i += 3
            continue

        if b == 35:  # #
            in_line_comment = True
            i += 1
            continue

        if b == 47 and i + 1 < n and raw_sql[i + 1] == 42:  # /*
            in_block_comment = True
            i += 2
            continue

        if b == 59:  # ;
            stmt = raw_sql[start:i].strip()
            if stmt:
                statements.append(stmt)
            start = i + 1

        i += 1

    tail = raw_sql[start:].strip()
    if tail:
        statements.append(tail)

    return statements


def _strip_leading_line_comments(stmt: bytes) -> bytes:
    """Elimina comentarios de línea iniciales (`--` o `#`) para inspeccionar el verbo SQL."""
    lines = stmt.splitlines()
    idx = 0
    while idx < len(lines):
        stripped = lines[idx].strip()
        if not stripped or stripped.startswith((b"--", b"#")):
            idx += 1
            continue
        break
    return b"\n".join(lines[idx:]).strip()


def _should_skip_statement(stmt: bytes) -> bool:
    """Omite comentarios vacíos, CREATE DATABASE y USE para restaurar en la BD activa."""
    effective = _strip_leading_line_comments(stmt)
    if not effective:
        return True
    upper = effective.upper()
    return upper.startswith((b"CREATE DATABASE", b"USE "))


def _drop_legacy_asistente_fk_if_exists(cursor: Any) -> bool:
    """Elimina la FK heredada `fk_asistente_socio` si aún existe en MySQL."""
    cursor.execute(
        """
        SELECT CONSTRAINT_NAME
        FROM information_schema.TABLE_CONSTRAINTS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = %s
          AND CONSTRAINT_NAME = %s
          AND CONSTRAINT_TYPE = 'FOREIGN KEY'
        """,
        ["tribunal_asistente", "fk_asistente_socio"],
    )
    if cursor.fetchone() is None:
        return False
    cursor.execute("ALTER TABLE tribunal_asistente DROP FOREIGN KEY fk_asistente_socio;")
    return True


def _previous_business_day(target_date: date, holiday_provider: DbHolidayProvider) -> date:
    """Devuelve el día hábil inmediatamente anterior a `target_date`."""
    candidate = target_date - timedelta(days=1)
    while candidate.weekday() >= 5 or holiday_provider.is_holiday(candidate):
        candidate -= timedelta(days=1)
    return candidate


def _compute_event_dates(now: datetime | None = None) -> tuple[datetime, datetime, datetime]:
    """Calcula fechas hábiles para evento Flujo 1: (publicación, inicio, fin)."""
    provider = DbHolidayProvider()
    local_now = timezone.localtime(now or timezone.now())
    tz = local_now.tzinfo or timezone.get_current_timezone()

    event_date = _previous_business_day(local_now.date(), provider)
    fecha_programada = datetime.combine(event_date, time(19, 0), tzinfo=tz)
    fecha_fin = fecha_programada + timedelta(hours=1)

    pub_date = event_date
    for _ in range(3):
        pub_date = _previous_business_day(pub_date, provider)
    fecha_publicacion = datetime.combine(pub_date, time(10, 0), tzinfo=tz)
    while compute_business_deadline(fecha_publicacion, 2, provider) > fecha_programada:
        pub_date = _previous_business_day(pub_date, provider)
        fecha_publicacion = datetime.combine(pub_date, time(10, 0), tzinfo=tz)

    return fecha_publicacion, fecha_programada, fecha_fin


def _get_or_create_demo_socio(
    *,
    legajo: str,
    first_name: str,
    last_name: str,
    email: str,
    social_year: int,
    role: str,
    numero_socio: int | None = None,
) -> Socio:
    """Busca un socio por legajo sin alterarlo; si no existe (DB de test vacía), lo crea."""
    existing = Socio.objects.select_related("user", "subcomision").filter(legajo=legajo).first()
    if existing is not None:
        return existing

    user_model = get_user_model()
    user, created = user_model.objects.get_or_create(
        username=legajo,
        defaults={
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
            "is_active": True,
        },
    )
    if created:
        user.set_password("aveit2026")
        user.save(update_fields=["password"])

    subcomision, _ = Subcomision.objects.get_or_create(
        name="Cómputos",
        defaults={"description": "Subcomisión de Cómputos"},
    )
    return Socio.objects.create(
        user=user,
        legajo=legajo,
        numero_socio=numero_socio,
        first_name=first_name,
        last_name=last_name,
        email=email,
        subcomision=subcomision,
        social_year=social_year,
        role=role,
        is_enabled=True,
    )


def _ensure_numero_socio(socio: Socio, expected_numero: int) -> Socio:
    if socio.numero_socio is None:
        socio.numero_socio = expected_numero
        socio.save(update_fields=["numero_socio"])
    return socio


def _reset_malena_history(malena: Socio) -> None:
    """Limpia únicamente el historial previo de Malena (770013) sin tocar otros socios."""
    malena_exp_ids = list(
        Expediente.objects.filter(models.Q(socio=malena) | models.Q(socios=malena))
        .values_list("id", flat=True)
        .distinct()
    )
    with connection.cursor() as cursor:
        cursor.execute(
            "DELETE FROM expedientes_asiento_libro_mayor WHERE socio_id = %s",
            [malena.id],
        )
        cursor.execute(
            "DELETE FROM tribunal_puntajeaplicado WHERE socio_id = %s",
            [770013],
        )
        cursor.execute(
            "UPDATE tribunal_puntajegeneral "
            "SET puntos = 0.00, llamadosAtencion = 0, felicitaciones = 0 "
            "WHERE socio_id = %s",
            [770013],
        )
        if not malena_exp_ids:
            return
        placeholders = ", ".join(["%s"] * len(malena_exp_ids))
        cursor.execute(
            f"DELETE FROM expedientes_asiento_libro_mayor WHERE expediente_id IN ({placeholders})",
            malena_exp_ids,
        )
        cursor.execute(
            f"DELETE FROM expedientes_enmienda_resolucion "
            f"WHERE resolucion_anterior_id IN ("
            f"SELECT id FROM expedientes_resolucion WHERE expediente_id IN ({placeholders})"
            f") OR resolucion_nueva_id IN ("
            f"SELECT id FROM expedientes_resolucion WHERE expediente_id IN ({placeholders})"
            f")",
            malena_exp_ids + malena_exp_ids,
        )
        cursor.execute(
            f"DELETE FROM expedientes_resolucion WHERE expediente_id IN ({placeholders})",
            malena_exp_ids,
        )
        cursor.execute(
            f"DELETE FROM expedientes_integrante_composicion WHERE composicion_id IN ("
            f"SELECT id FROM expedientes_composicion_tribunal "
            f"WHERE expediente_id IN ({placeholders})"
            f")",
            malena_exp_ids,
        )
        cursor.execute(
            f"DELETE FROM expedientes_composicion_tribunal WHERE expediente_id IN ({placeholders})",
            malena_exp_ids,
        )
        cursor.execute(
            f"DELETE FROM expedientes_auditoria_consulta WHERE expediente_id IN ({placeholders})",
            malena_exp_ids,
        )
        cursor.execute(
            f"DELETE FROM expedientes_decision_causal WHERE expediente_id IN ({placeholders})",
            malena_exp_ids,
        )
        cursor.execute(
            f"DELETE FROM expedientes_valoracion_t03_antecedente "
            f"WHERE expediente_antecedente_id IN ({placeholders}) OR valoracion_id IN ("
            f"SELECT id FROM expedientes_valoracion_t03 WHERE expediente_id IN ({placeholders})"
            f")",
            malena_exp_ids + malena_exp_ids,
        )
        cursor.execute(
            f"DELETE FROM expedientes_valoracion_t03 WHERE expediente_id IN ({placeholders})",
            malena_exp_ids,
        )
        cursor.execute(
            f"DELETE FROM expedientes_descargo_version_evidencias WHERE descargoversion_id IN ("
            f"SELECT dv.id FROM expedientes_descargo_version dv "
            f"INNER JOIN expedientes_descargo d ON d.id = dv.descargo_id "
            f"WHERE d.expediente_id IN ({placeholders})"
            f")",
            malena_exp_ids,
        )
        cursor.execute(
            f"DELETE FROM expedientes_descargo_version WHERE descargo_id IN ("
            f"SELECT id FROM expedientes_descargo WHERE expediente_id IN ({placeholders})"
            f")",
            malena_exp_ids,
        )
        cursor.execute(
            f"DELETE FROM expedientes_auditoria_descarga WHERE evidencia_id IN ("
            f"SELECT id FROM expedientes_evidencia_descargo WHERE expediente_id IN ({placeholders})"
            f")",
            malena_exp_ids,
        )
        cursor.execute(
            f"DELETE FROM expedientes_evidencia_descargo WHERE expediente_id IN ({placeholders})",
            malena_exp_ids,
        )
        cursor.execute(
            f"DELETE FROM expedientes_descargo WHERE expediente_id IN ({placeholders})",
            malena_exp_ids,
        )
        cursor.execute(
            f"DELETE FROM expedientes_apelacion_t01 WHERE expediente_id IN ({placeholders})",
            malena_exp_ids,
        )
        cursor.execute(
            f"DELETE FROM expedientes_periodo_apelacion WHERE expediente_id IN ({placeholders})",
            malena_exp_ids,
        )
        cursor.execute(
            f"DELETE FROM expedientes_adecuacion_t01 WHERE expediente_id IN ({placeholders})",
            malena_exp_ids,
        )
        cursor.execute(
            f"UPDATE expedientes_solicitudt01 SET expediente_id = NULL "
            f"WHERE expediente_id IN ({placeholders})",
            malena_exp_ids,
        )
        cursor.execute(
            f"UPDATE tribunal_asistente SET expediente_generado_id = NULL "
            f"WHERE expediente_generado_id IN ({placeholders})",
            malena_exp_ids,
        )
        cursor.execute(
            f"DELETE FROM expedientes_cambio_estado WHERE expediente_id IN ({placeholders})",
            malena_exp_ids,
        )
        cursor.execute(
            f"DELETE FROM expedientes_expediente_socios WHERE expediente_id IN ({placeholders})",
            malena_exp_ids,
        )
        cursor.execute(
            f"DELETE FROM expedientes_expediente WHERE id IN ({placeholders})",
            malena_exp_ids,
        )


@transaction.atomic
def seed_presentation_mocks() -> dict[str, Any]:
    """Siembra únicamente los mocks de presentación sobre el snapshot sin alterar datos previos."""
    lucas = _get_or_create_demo_socio(
        legajo="74907",
        numero_socio=74907,
        first_name="Lucas",
        last_name="Gastiaburu",
        email="lucas.gastiaburu@aveit.test",
        social_year=2,
        role=Role.SOCIO,
    )
    diego_cd = _get_or_create_demo_socio(
        legajo="87414",
        numero_socio=11779,
        first_name="Diego Gabriel",
        last_name="Sanchez Turu Michel",
        email="diego.cd@aveit.test",
        social_year=6,
        role=Role.CD,
    )
    _nicolas_td = _get_or_create_demo_socio(
        legajo="408917",
        numero_socio=408917,
        first_name="Nicolás",
        last_name="Rosales",
        email="nicolas.td@aveit.test",
        social_year=6,
        role=Role.TD,
    )
    esteban_td = _get_or_create_demo_socio(
        legajo="85421",
        numero_socio=1001,
        first_name="Esteban",
        last_name="Pérez",
        email="esteban.td@aveit.test",
        social_year=4,
        role=Role.TD,
    )
    axel_g5 = (
        Socio.objects.select_related("user").filter(legajo="403655").first()
        or Socio.objects.select_related("user").filter(social_year=5).first()
        or _get_or_create_demo_socio(
            legajo="403655",
            numero_socio=403655,
            first_name="Axel René",
            last_name="Villegas",
            email="axel.admin@aveit.test",
            social_year=5,
            role=Role.ADMIN,
        )
    )
    if axel_g5.legajo == "403655":
        _ensure_numero_socio(axel_g5, 403655)
    catalina_td = Socio.objects.select_related("user").filter(legajo="86361").first()
    if catalina_td is not None:
        _ensure_numero_socio(catalina_td, 11737)
    firmante_g5 = catalina_td or axel_g5
    malena = _ensure_numero_socio(
        _get_or_create_demo_socio(
            legajo="770013",
            numero_socio=770013,
            first_name="Malena",
            last_name="Marea Demo",
            email="malena.demo@aveit.test",
            social_year=4,
            role=Role.SOCIO,
        ),
        770013,
    )
    _ensure_numero_socio(
        _get_or_create_demo_socio(
            legajo="770005",
            numero_socio=770005,
            first_name="Elena",
            last_name="Ensayo Demo",
            email="elena.demo@aveit.test",
            social_year=6,
            role=Role.SOCIO,
        ),
        770005,
    )
    _ensure_numero_socio(
        _get_or_create_demo_socio(
            legajo="770008",
            numero_socio=770008,
            first_name="Héctor",
            last_name="Horizonte Demo",
            email="hector.demo@aveit.test",
            social_year=6,
            role=Role.SOCIO,
        ),
        770008,
    )

    _reset_malena_history(malena)

    elena = Socio.objects.select_related("user").get(legajo="770005")
    hector = Socio.objects.select_related("user").get(legajo="770008")

    AtencionFelicitacion.objects.update_or_create(
        socio=malena,
        defaults={"llamadosAtencion": 2, "felicitaciones": 0},
    )
    AtencionFelicitacion.objects.update_or_create(
        socio=lucas,
        defaults={"llamadosAtencion": 0, "felicitaciones": 0},
    )

    fecha_publicacion, fecha_programada, fecha_fin = _compute_event_dates()
    evento = EventoInstitucional.objects.create(
        titulo="Reunión Ordinaria de Seguimiento - Cómputos y CD",
        categoria=CategoriaEventoEnum.REUNION,
        tipo=SubtipoReunionEnum.ORDINARIA,
        modalidad=ModalidadEventoEnum.PRESENCIAL_SEDE,
        lugar="Sede Central AVEIT",
        modo_convocatoria=ModoConvocatoriaEnum.PERSONALIZADA,
        convocante=diego_cd,
        subcomision=diego_cd.subcomision,
        estado=EstadoEventoEnum.NOTIFICADO,
        es_obligatoria=True,
        es_sancionable=True,
        fecha_publicacion=fecha_publicacion,
        fecha_programada=fecha_programada,
        fecha_fin=fecha_fin,
        tieneHoraFin=True,
    )

    for socio_convocado in (lucas, malena, elena, hector):
        EventoConvocado.objects.create(evento=evento, socio=socio_convocado)

    AsistenciaEvento.objects.create(
        evento=evento,
        socio=lucas,
        estado_asistencia=EstadoAsistenciaEventoEnum.AUSENTE,
        motivo="Inasistencia registrada en reunión.",
        procesado_disciplinario=False,
        expediente_generado=None,
    )
    AsistenciaEvento.objects.create(
        evento=evento,
        socio=malena,
        estado_asistencia=EstadoAsistenciaEventoEnum.TARDE_LEVE,
        hora_registro=fecha_programada + timedelta(minutes=22),
        minutos_tardanza=22,
        motivo="Llegada 22 minutos tarde.",
        procesado_disciplinario=False,
        expediente_generado=None,
    )
    AsistenciaEvento.objects.create(
        evento=evento,
        socio=elena,
        estado_asistencia=EstadoAsistenciaEventoEnum.PRESENTE,
        hora_registro=fecha_programada,
        procesado_disciplinario=False,
        expediente_generado=None,
    )
    AsistenciaEvento.objects.create(
        evento=evento,
        socio=hector,
        estado_asistencia=EstadoAsistenciaEventoEnum.PRESENTE,
        hora_registro=fecha_programada,
        procesado_disciplinario=False,
        expediente_generado=None,
    )

    provider = DbHolidayProvider()
    plazo_inicio = fecha_publicacion
    plazo_limite = compute_business_deadline(plazo_inicio, 5, provider)
    if plazo_limite > timezone.now():
        plazo_inicio = timezone.now() - timedelta(days=14)
        plazo_limite = compute_business_deadline(plazo_inicio, 5, provider)

    # Mock 1: Expediente en revision_resolucion con descargo T02 leído y rechazado.
    numero_revision = ExpedienteWorkflowService.reserve_numero(2026)
    motivo_revision = "Inasistencia injustificada a reunión ordinaria de Cómputos."
    exp_revision = Expediente.objects.create(
        numero=numero_revision,
        socio=lucas,
        titulo="Inasistencia a Reunión de Cómputos",
        motivo=motivo_revision,
        puntos=Decimal("-1.00"),
        estado=EstadoExpedienteEnum.REVISION_RESOLUCION,
        concepto=ConceptoExpedienteEnum.GSA,
        urgencia=UrgenciaExpedienteEnum.NORMAL,
        plazo_inicio_at=plazo_inicio,
        plazo_limite_at=plazo_limite,
        descargo_presentado=True,
        descargo_tipo=TipoDescargoEnum.T02_CERTIFICADO,
        descargo_causal="Enfermedad / Reposo médico",
        descargo_texto="Adjunto certificado médico emitido fuera del horario institucional.",
        descargo_presentado_at=plazo_inicio + timedelta(days=1),
    )
    exp_revision.socios.set([lucas])
    CambioEstadoExpediente.objects.create(
        expediente=exp_revision,
        estado_anterior=EstadoExpedienteEnum.CREADO,
        estado_nuevo=EstadoExpedienteEnum.CREADO,
        actor=diego_cd.legajo,
        motivo=motivo_revision,
    )
    CambioEstadoExpediente.objects.create(
        expediente=exp_revision,
        estado_anterior=EstadoExpedienteEnum.CREADO,
        estado_nuevo=EstadoExpedienteEnum.JUSTIFICANDO,
        actor="SISTEMA",
        motivo="Apertura de período de justificaciones (demo).",
    )
    CambioEstadoExpediente.objects.create(
        expediente=exp_revision,
        estado_anterior=EstadoExpedienteEnum.JUSTIFICANDO,
        estado_nuevo=EstadoExpedienteEnum.REVISION_RESOLUCION,
        actor="SISTEMA",
        motivo="Cierre de período de justificaciones y pase a revisión (demo).",
    )
    descargo_rev = DescargoExpediente.objects.create(
        expediente=exp_revision,
        socio=lucas,
        tipo=TipoDescargoEnum.T02_CERTIFICADO,
        causal="Enfermedad / Reposo médico",
        texto="Adjunto certificado médico emitido fuera del horario institucional.",
        es_vigente=True,
        puntaje_ratificado="-1.00",
    )
    fundamento_decision = (
        "El certificado presentado no acredita imposibilidad horaria durante la convocatoria."
    )
    DecisionCausalDescargo.objects.create(
        expediente=exp_revision,
        descargo=descargo_rev,
        version=1,
        decision=DecisionCausalEnum.REJECTED,
        regla_sugerida=DecisionCausalEnum.REJECTED,
        se_aparta_de_regla=False,
        fundamento=fundamento_decision,
        evidencias_valoradas=[],
        descargo_snapshot={
            "socio_id": lucas.id,
            "socio_legajo": lucas.legajo,
            "tipo": descargo_rev.tipo,
            "causal": descargo_rev.causal,
            "texto": descargo_rev.texto,
            "archivo": descargo_rev.archivo,
            "presentado_at": (
                descargo_rev.presentado_at.isoformat() if descargo_rev.presentado_at else None
            ),
            "puntaje_final": -1.0,
            "fundamento_cambio_puntaje": fundamento_decision,
        },
        autor=esteban_td.user,
        autor_legajo=esteban_td.legajo,
        autor_rol=esteban_td.role,
    )

    # Mock 2: Expediente en pendiente_correos con 2 firmas (año 4 y 5), listo para firma de 408917.
    numero_firma = ExpedienteWorkflowService.reserve_numero(2026)
    motivo_firma = "Incumplimiento de guardia programada en sede central."
    exp_firma = Expediente.objects.create(
        numero=numero_firma,
        socio=lucas,
        titulo="Guardia programada en sede",
        motivo=motivo_firma,
        puntos=Decimal("-1.00"),
        estado=EstadoExpedienteEnum.PENDIENTE_CORREOS,
        concepto=ConceptoExpedienteEnum.GSA,
        urgencia=UrgenciaExpedienteEnum.NORMAL,
        plazo_inicio_at=plazo_inicio,
        plazo_limite_at=plazo_limite,
    )
    exp_firma.socios.set([lucas])
    for estado_ant, estado_nvo, actor_trans, motivo_trans in (
        (
            EstadoExpedienteEnum.CREADO,
            EstadoExpedienteEnum.CREADO,
            diego_cd.legajo,
            motivo_firma,
        ),
        (
            EstadoExpedienteEnum.CREADO,
            EstadoExpedienteEnum.JUSTIFICANDO,
            "SISTEMA",
            "Apertura de período de justificaciones (demo).",
        ),
        (
            EstadoExpedienteEnum.JUSTIFICANDO,
            EstadoExpedienteEnum.REVISION_RESOLUCION,
            "SISTEMA",
            "Pase a revisión del Tribunal de Disciplina (demo).",
        ),
        (
            EstadoExpedienteEnum.REVISION_RESOLUCION,
            EstadoExpedienteEnum.ESPERA_RESOLUCION,
            esteban_td.legajo,
            "Cierre de evaluación y pase a espera de resolución (demo).",
        ),
        (
            EstadoExpedienteEnum.ESPERA_RESOLUCION,
            EstadoExpedienteEnum.PENDIENTE_CORREOS,
            esteban_td.legajo,
            "Adopción de resolución en borrador pendiente de firma colegiada (demo).",
        ),
    ):
        CambioEstadoExpediente.objects.create(
            expediente=exp_firma,
            estado_anterior=estado_ant,
            estado_nuevo=estado_nvo,
            actor=actor_trans,
            motivo=motivo_trans,
        )

    TribunalCompositionService.stamp_for_resolution(exp_firma)
    resolucion = Resolucion.objects.create(
        expediente=exp_firma,
        version=1,
        estado=EstadoResolucionEnum.DRAFT,
        numero_expediente_snapshot=exp_firma.numero,
        vistos=(
            f"Visto el expediente N° {exp_firma.numero} iniciado contra el socio "
            f"{lucas.first_name} {lucas.last_name} (Legajo {lucas.legajo})."
        ),
        considerandos=(
            "Considerando la acreditación del incumplimiento de la guardia programada en sede "
            "central y la ausencia de descargo justificatorio."
        ),
        articulos_resolutivos=(
            "ARTÍCULO 1°: Aplicar la sanción reglamentaria de -1.00 punto al socio imputado "
            "conforme al Art. 85 del Reglamento Interno."
        ),
        puntos_finales=Decimal("-1.00"),
        medidas=[],
        firmantes=[],
        created_by=esteban_td.user,
    )
    registrar_firma_resolucion(resolucion, esteban_td.user, es_suplente=False, anio_social=4)
    registrar_firma_resolucion(resolucion, firmante_g5.user, es_suplente=False, anio_social=5)

    # Mock 3 y 4: Dos expedientes de llamado de atención ya EMITIDOS y confirmados para Malena.
    malena_llamados: list[str] = []
    current_year = timezone.localdate().year
    grupo_g6 = f"G{(current_year - 1962) - 6}"
    nicolas_id = str(_nicolas_td.numero_socio or _nicolas_td.legajo)
    nicolas_name = f"{_nicolas_td.first_name} {_nicolas_td.last_name}".strip()
    nicolas_etiqueta = f"{nicolas_id} - {nicolas_name} - {grupo_g6}"

    for idx in (1, 2):
        numero_llamado = ExpedienteWorkflowService.reserve_numero(2026)
        titulo_llamado = "Llamado de atención: Impuntualidad leve en reunión previa"
        motivo_llamado = (
            "Llamado de atención (Art. 100.a): Impuntualidad leve en reunión previa."
        )
        exp_llamado = Expediente.objects.create(
            numero=numero_llamado,
            socio=malena,
            titulo=titulo_llamado,
            motivo=motivo_llamado,
            puntos=Decimal("0.00"),
            estado=EstadoExpedienteEnum.EMITIDO,
            concepto=ConceptoExpedienteEnum.GSA,
            urgencia=UrgenciaExpedienteEnum.NORMAL,
            plazo_inicio_at=plazo_inicio,
            plazo_limite_at=plazo_limite,
        )
        exp_llamado.socios.set([malena])
        for estado_ant, estado_nvo, actor_trans, motivo_trans in (
            (
                EstadoExpedienteEnum.CREADO,
                EstadoExpedienteEnum.CREADO,
                diego_cd.legajo,
                motivo_llamado,
            ),
            (
                EstadoExpedienteEnum.CREADO,
                EstadoExpedienteEnum.JUSTIFICANDO,
                "SISTEMA",
                "Apertura de período de justificaciones (demo).",
            ),
            (
                EstadoExpedienteEnum.JUSTIFICANDO,
                EstadoExpedienteEnum.REVISION_RESOLUCION,
                "SISTEMA",
                "Pase a revisión del Tribunal de Disciplina (demo).",
            ),
            (
                EstadoExpedienteEnum.REVISION_RESOLUCION,
                EstadoExpedienteEnum.ESPERA_RESOLUCION,
                esteban_td.legajo,
                "Cierre de evaluación y pase a espera de resolución (demo).",
            ),
            (
                EstadoExpedienteEnum.ESPERA_RESOLUCION,
                EstadoExpedienteEnum.PENDIENTE_CORREOS,
                esteban_td.legajo,
                "Adopción de resolución de llamado de atención (demo).",
            ),
            (
                EstadoExpedienteEnum.PENDIENTE_CORREOS,
                EstadoExpedienteEnum.EMITIDO,
                _nicolas_td.legajo,
                "Resolución emitida con la totalidad de firmas requeridas (demo).",
            ),
        ):
            CambioEstadoExpediente.objects.create(
                expediente=exp_llamado,
                estado_anterior=estado_ant,
                estado_nuevo=estado_nvo,
                actor=actor_trans,
                motivo=motivo_trans,
            )

        TribunalCompositionService.stamp_for_resolution(exp_llamado)
        res_llamado = Resolucion.objects.create(
            expediente=exp_llamado,
            version=1,
            estado=EstadoResolucionEnum.DRAFT,
            numero_expediente_snapshot=exp_llamado.numero,
            vistos=(
                f"Visto el expediente N° {exp_llamado.numero} iniciado contra la socia "
                f"{malena.first_name} {malena.last_name} (Legajo {malena.legajo})."
            ),
            considerandos=(
                "Considerando la impuntualidad leve acreditada en reunión previa "
                "sin presentación de descargo eximente."
            ),
            articulos_resolutivos=(
                "ARTÍCULO 1°: Imponer un Llamado de Atención a la socia imputada "
                "conforme al Art. 100 Inc. a del Reglamento Interno."
            ),
            puntos_finales=Decimal("0.00"),
            medidas=["Llamado de atención"],
            firmantes=[],
            created_by=esteban_td.user,
        )
        registrar_firma_resolucion(res_llamado, esteban_td.user, es_suplente=False, anio_social=4)
        registrar_firma_resolucion(res_llamado, axel_g5.user, es_suplente=False, anio_social=5)
        res_llamado.refresh_from_db()
        ahora_iso = timezone.now().isoformat()
        firmantes = list(res_llamado.firmantes or [])
        firmantes.append(
            {
                "user_id": _nicolas_td.user.id,
                "numero_socio": _nicolas_td.numero_socio,
                "legajo": _nicolas_td.legajo,
                "full_name": nicolas_name,
                "social_year": 6,
                "anio_social": 6,
                "grupo": grupo_g6,
                "condicion": "TITULAR",
                "es_suplente": False,
                "etiqueta": nicolas_etiqueta,
                "firma": nicolas_etiqueta,
                "signed_at": ahora_iso,
                "firmado_at": ahora_iso,
            }
        )
        res_llamado.firmantes = firmantes
        res_llamado.estado = EstadoResolucionEnum.ISSUED
        res_llamado.issued_by = _nicolas_td.user
        res_llamado.issued_at = plazo_limite
        res_llamado.contenido_hash = calcular_hash_resolucion(res_llamado)
        res_llamado.save()

        LedgerService._crear_asiento(
            resolucion=res_llamado,
            socio=malena,
            nro_socio=770013,
            tipo=TipoAsiento.LLAMADO_ATENCION,
            puntos=Decimal("0.00"),
            contador_resultante=idx,
            puntaje_aplicado_id=None,
            autor=_nicolas_td.user,
        )
        malena_llamados.append(exp_llamado.numero)

    return {
        "mock_expedientes": [exp_revision.numero, exp_firma.numero],
        "malena_llamados": malena_llamados,
        "evento_id": evento.id,
        "evento_titulo": evento.titulo,
    }


def reset_regularidad_database(snapshot_path: Path | None = None) -> dict[str, Any]:
    """Restaura la base de datos MySQL activa desde el snapshot SQL de Regularidad."""
    path = snapshot_path or get_snapshot_path()
    if not path.is_file():
        raise FileNotFoundError(f"No se encontró el archivo snapshot SQL en: {path}")

    if connection.vendor != "mysql":
        raise RuntimeError(
            "La restauración desde snapshot SQL requiere conexión a MySQL "
            f"(motor actual: {connection.vendor})."
        )

    raw_sql = path.read_bytes()
    statements = split_sql_statements(raw_sql)

    executed = 0
    with connection.cursor() as cursor:
        try:
            for stmt in statements:
                if _should_skip_statement(stmt):
                    continue
                cursor.execute(stmt)
                executed += 1
        finally:
            cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")
        _drop_legacy_asistente_fk_if_exists(cursor)

    mocks = seed_presentation_mocks()
    expedientes = list(Expediente.objects.order_by("numero").values_list("numero", flat=True))
    return {
        "snapshot": str(path),
        "statements_executed": executed,
        "expedientes": expedientes,
        **mocks,
    }
