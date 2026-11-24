"""Servicio para reiniciar la base de datos de demostración de la rama regularidad."""

from __future__ import annotations

from datetime import date, datetime, time, timedelta
from decimal import Decimal
from typing import Any

from django.contrib.auth import get_user_model
from django.db import connection, transaction
from django.utils import timezone

from expedientes.domain.calendar import compute_business_deadline
from expedientes.domain.holiday_provider import DbHolidayProvider
from expedientes.domain.ports import HolidayProviderPort
from expedientes.models import (
    AsistenciaEvento,
    AtencionFelicitacion,
    CambioEstadoExpediente,
    CategoriaEventoEnum,
    ConceptoExpedienteEnum,
    DecisionCausalDescargo,
    DecisionCausalEnum,
    DescargoExpediente,
    DescargoVersion,
    EstadoAsistenciaEventoEnum,
    EstadoEventoEnum,
    EstadoExpedienteEnum,
    EstadoResolucionEnum,
    EventoConvocado,
    EventoInstitucional,
    Expediente,
    ExpedienteNumberSequence,
    MetodoCapturaAsistenciaEnum,
    ModalidadEventoEnum,
    ModoConvocatoriaEnum,
    OperacionDescargoEnum,
    Resolucion,
    SubtipoReunionEnum,
    TipoDescargoEnum,
    UrgenciaExpedienteEnum,
)
from expedientes.services.meeting_compliance_service import MeetingComplianceService
from expedientes.services.tribunal_composition_service import TribunalCompositionService
from socios.models import Role, Socio, Subcomision

UserModel = get_user_model()

DEMO_PASSWORD = "Aveit-Demo-2026!"

DEMO_SOCIOS_SPECS: tuple[dict[str, Any], ...] = (
    {
        "legajo": "74907",
        "numero_socio": 74907,
        "first_name": "Lucas",
        "last_name": "Gastiaburu",
        "role": Role.SOCIO,
        "social_year": 2,
        "subcomision": "Cómputos",
    },
    {
        "legajo": "85194",
        "numero_socio": 85194,
        "first_name": "Lucas Martín",
        "last_name": "Guillén",
        "role": Role.FISCALIZADORA,
        "social_year": 4,
        "subcomision": "Recursos Humanos",
    },
    {
        "legajo": "87414",
        "numero_socio": 87414,
        "first_name": "Diego Gabriel",
        "last_name": "Sánchez",
        "role": Role.CD,
        "social_year": 5,
        "subcomision": "Comisión Directiva",
    },
    {
        "legajo": "408917",
        "numero_socio": 408917,
        "first_name": "Nicolás",
        "last_name": "Rosales",
        "role": Role.TD,
        "social_year": 6,
        "subcomision": "Tribunal de Disciplina",
    },
    {
        "legajo": "403655",
        "numero_socio": 403655,
        "first_name": "Axel René",
        "last_name": "Villegas",
        "role": Role.ADMIN,
        "social_year": 5,
        "subcomision": "Cómputos",
    },
    {
        "legajo": "85421",
        "numero_socio": 1001,
        "first_name": "Esteban",
        "last_name": "Pérez",
        "role": Role.TD,
        "social_year": 4,
        "subcomision": "Tribunal de Disciplina",
    },
    {
        "legajo": "770005",
        "numero_socio": 770005,
        "first_name": "Elena",
        "last_name": "Ensayo Demo",
        "role": Role.SOCIO,
        "social_year": 2,
        "subcomision": "Cómputos",
    },
    {
        "legajo": "770008",
        "numero_socio": 770008,
        "first_name": "Héctor",
        "last_name": "Horizonte Demo",
        "role": Role.SOCIO,
        "social_year": 2,
        "subcomision": "Cómputos",
    },
    {
        "legajo": "770013",
        "numero_socio": 770013,
        "first_name": "Malena",
        "last_name": "Marea Demo",
        "role": Role.SOCIO,
        "social_year": 3,
        "subcomision": "Cómputos",
    },
)

# Tablas transaccionales ordenadas de hijas a padres para respetar FKs e inmutabilidad
# (incluye tablas InsertOnlyQuerySet / ReadOnlyModel que bloquean ORM `.delete()`).
TRANSACTIONAL_TABLES_DELETE_ORDER: tuple[str, ...] = (
    "expedientes_asiento_libro_mayor",
    "tribunal_puntajeaplicado",
    "expedientes_enmienda_resolucion",
    "expedientes_valoracion_t03_antecedente",
    "expedientes_valoracion_t03",
    "expedientes_decision_causal",
    "expedientes_descargo_version_evidencias",
    "expedientes_descargo_version",
    "expedientes_auditoria_descarga",
    "expedientes_evidencia_descargo",
    "expedientes_descargo",
    "expedientes_apelacion_t01",
    "expedientes_periodo_apelacion",
    "expedientes_adecuacion_t01",
    "expedientes_solicitudt01",
    "expedientes_integrante_composicion",
    "expedientes_composicion_tribunal",
    "expedientes_resolucion",
    "expedientes_cambio_estado",
    "expedientes_auditoria_consulta",
    "notifications_email_attachment",
    "notifications_email_outbox",
    "atencionFelicitacion",
    "tribunal_asistente",
    "tribunal_evento_convocado",
    "tribunal_evento",
    "expedientes_expediente_socios",
    "expedientes_expediente",
    "expedientes_numero_secuencia",
)


def _ensure_demo_socios() -> dict[str, Socio]:
    """Asegura la existencia y habilitación de los socios requeridos para la demo."""
    socios_by_legajo: dict[str, Socio] = {}

    for spec in DEMO_SOCIOS_SPECS:
        legajo = spec["legajo"]
        socio = Socio.objects.select_related("user").filter(legajo=legajo).first()
        if socio is None:
            socio = (
                Socio.objects.select_related("user")
                .filter(numero_socio=spec["numero_socio"])
                .first()
            )

        subcomision, _ = Subcomision.objects.get_or_create(name=spec["subcomision"])

        if socio is None:
            email = f"socio.{legajo}@aveit.test"
            username = str(spec["numero_socio"])
            user, created_user = UserModel.objects.get_or_create(
                username=username,
                defaults={
                    "email": email,
                    "first_name": spec["first_name"],
                    "last_name": spec["last_name"],
                    "is_active": True,
                },
            )
            if created_user or not user.has_usable_password():
                user.set_password(DEMO_PASSWORD)
                user.save(update_fields=["password"])

            socio = Socio.objects.create(
                user=user,
                legajo=legajo,
                numero_socio=spec["numero_socio"],
                first_name=spec["first_name"],
                last_name=spec["last_name"],
                email=email,
                subcomision=subcomision,
                social_year=spec["social_year"],
                role=spec["role"],
                is_enabled=True,
            )
        else:
            changed_fields: list[str] = []
            if not socio.is_enabled:
                socio.is_enabled = True
                changed_fields.append("is_enabled")
            if legajo == "408917":
                if socio.role != Role.TD:
                    socio.role = Role.TD
                    changed_fields.append("role")
                if socio.social_year != 6:
                    socio.social_year = 6
                    changed_fields.append("social_year")
            if changed_fields:
                socio.save(update_fields=changed_fields)

            if not socio.user.is_active:
                socio.user.is_active = True
                socio.user.save(update_fields=["is_active"])

        socios_by_legajo[legajo] = socio

    return socios_by_legajo


def _clear_transactional_tables() -> None:
    """Limpia las tablas transaccionales respetando el orden de claves foráneas."""
    existing_tables = set(connection.introspection.table_names())
    with connection.cursor() as cursor:
        for table_name in TRANSACTIONAL_TABLES_DELETE_ORDER:
            if table_name in existing_tables:
                quoted = connection.ops.quote_name(table_name)
                cursor.execute(f"DELETE FROM {quoted}")

        if "tribunal_puntajegeneral" in existing_tables:
            quoted_pg = connection.ops.quote_name("tribunal_puntajegeneral")
            cursor.execute(
                f"UPDATE {quoted_pg} "
                "SET puntos = 0.00, felicitaciones = 0, llamadosAtencion = 0"
            )


def _grupo_para_anio_social(social_year: int) -> str:
    current_year = timezone.localdate().year
    return f"G{(current_year - 1962) - social_year}"


def _build_firma_dict(
    *,
    social_year: int,
    full_name: str,
    legajo: str,
    numero_socio: int,
    user_id: int | None,
    signed_at_iso: str,
) -> dict[str, Any]:
    grupo = _grupo_para_anio_social(social_year)
    etiqueta = f"{numero_socio} - {full_name} - {grupo}"
    return {
        "user_id": user_id,
        "numero_socio": numero_socio,
        "legajo": legajo,
        "full_name": full_name,
        "social_year": social_year,
        "anio_social": social_year,
        "grupo": grupo,
        "condicion": "TITULAR",
        "es_suplente": False,
        "etiqueta": etiqueta,
        "firma": etiqueta,
        "signed_at": signed_at_iso,
        "firmado_at": signed_at_iso,
    }


def _previous_business_day(
    reference_date: date,
    provider: HolidayProviderPort,
    steps: int = 1,
) -> date:
    """Retrocede `steps` días hábiles (lunes a viernes, excluyendo feriados)."""
    current = reference_date
    remaining = steps
    while remaining > 0:
        current -= timedelta(days=1)
        if current.weekday() < 5 and not provider.is_holiday(current):
            remaining -= 1
    return current


def _compute_event_dates(
    now: datetime | None = None,
    holiday_provider: HolidayProviderPort | None = None,
) -> tuple[datetime, datetime, datetime]:
    """Calcula dinámicamente `(fecha_publicacion, fecha_programada, fecha_fin)`.

    Garantiza:
    - `fecha_fin < now` y dentro de la ventana de 72 horas hábiles
      (`compute_business_deadline(fecha_fin, 3, provider) > now`).
    - Preaviso mínimo de 2 días hábiles cumplido
      (`compute_business_deadline(fecha_publicacion, 2, provider) <= fecha_programada`).
    """
    reference_now = now or timezone.now()
    local_now = timezone.localtime(reference_now)
    provider = holiday_provider or DbHolidayProvider()

    candidate_date = _previous_business_day(local_now.date(), provider, steps=1)
    fecha_programada = datetime.combine(candidate_date, time(19, 0), tzinfo=local_now.tzinfo)
    fecha_fin = fecha_programada + timedelta(hours=1)

    if not (
        fecha_fin < local_now and compute_business_deadline(fecha_fin, 3, provider) > local_now
    ):
        today = local_now.date()
        if today.weekday() < 5 and not provider.is_holiday(today) and local_now.hour >= 2:
            alt_end = (local_now - timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
            alt_start = alt_end - timedelta(hours=1)
            if compute_business_deadline(alt_end, 3, provider) > local_now:
                candidate_date = today
                fecha_programada = alt_start
                fecha_fin = alt_end

    pub_date = _previous_business_day(candidate_date, provider, steps=3)
    fecha_publicacion = datetime.combine(pub_date, time(10, 0), tzinfo=local_now.tzinfo)
    while compute_business_deadline(fecha_publicacion, 2, provider) > fecha_programada:
        pub_date = _previous_business_day(pub_date, provider, steps=1)
        fecha_publicacion = datetime.combine(pub_date, time(10, 0), tzinfo=local_now.tzinfo)

    return fecha_publicacion, fecha_programada, fecha_fin


@transaction.atomic
def reset_regularidad_database() -> dict[str, Any]:
    """Reinicia la base de datos transaccional dejando expedientes y evento demo."""
    socios = _ensure_demo_socios()
    lucas = socios["74907"]
    elena = socios["770005"]
    hector = socios["770008"]
    malena = socios["770013"]
    diego_cd = socios["87414"]
    td_nicolas = socios["408917"]
    td_esteban = socios["85421"]

    _clear_transactional_tables()

    ahora = timezone.now()
    ExpedienteNumberSequence.objects.update_or_create(
        year=timezone.localdate().year,
        defaults={"last_value": 2},
    )

    # 1. EXP-0001/2026: En revisión de resolución, con descargo leído (Generar Resolución)
    descargo_texto = (
        "Solicito se contemple la justificación por cuadro febril que impidió mi "
        "asistencia a la jornada ambiental."
    )
    exp1 = Expediente.objects.create(
        numero="EXP-0001/2026",
        titulo="Inasistencia a jornada de concientización ambiental",
        socio=lucas,
        motivo=(
            "Inasistencia injustificada a jornada programada de "
            "Gestión Social y Ambiental (GSA)."
        ),
        puntos=Decimal("-1.00"),
        estado=EstadoExpedienteEnum.REVISION_RESOLUCION,
        concepto=ConceptoExpedienteEnum.GSA,
        urgencia=UrgenciaExpedienteEnum.NORMAL,
        descargo_presentado=True,
        descargo_tipo=TipoDescargoEnum.T02_CERTIFICADO,
        descargo_causal="Enfermedad certificada",
        descargo_texto=descargo_texto,
        descargo_presentado_at=ahora - timedelta(days=2),
    )
    exp1.socios.add(lucas)

    CambioEstadoExpediente.objects.create(
        expediente=exp1,
        estado_anterior=EstadoExpedienteEnum.CREADO,
        estado_nuevo=EstadoExpedienteEnum.JUSTIFICANDO,
        actor=td_nicolas.user.username,
        motivo="Apertura de período de justificaciones.",
    )
    CambioEstadoExpediente.objects.create(
        expediente=exp1,
        estado_anterior=EstadoExpedienteEnum.JUSTIFICANDO,
        estado_nuevo=EstadoExpedienteEnum.REVISION_RESOLUCION,
        actor="SISTEMA",
        motivo="Cierre de plazo y pase a revisión del Tribunal de Disciplina.",
    )

    descargo1 = DescargoExpediente.objects.create(
        expediente=exp1,
        socio=lucas,
        tipo=TipoDescargoEnum.T02_CERTIFICADO,
        causal="Enfermedad certificada",
        texto=descargo_texto,
        es_vigente=True,
        puntaje_ratificado="-1.00",
    )
    DescargoVersion.objects.create(
        descargo=descargo1,
        numero=1,
        operacion=OperacionDescargoEnum.PRESENTADO,
        tipo=TipoDescargoEnum.T02_CERTIFICADO,
        causal=descargo1.causal,
        texto=descargo1.texto,
        actor=lucas.legajo,
    )
    DecisionCausalDescargo.objects.create(
        expediente=exp1,
        descargo=descargo1,
        version=1,
        decision=DecisionCausalEnum.REJECTED,
        regla_sugerida=DecisionCausalEnum.REJECTED,
        se_aparta_de_regla=False,
        fundamento="El descargo no adjunta constancia médica que acredite reposo en la fecha.",
        evidencias_valoradas=[],
        descargo_snapshot={
            "socio_id": lucas.id,
            "socio_legajo": lucas.legajo,
            "tipo": TipoDescargoEnum.T02_CERTIFICADO,
            "causal": descargo1.causal,
            "texto": descargo1.texto,
            "puntaje_final": -1.0,
        },
        autor=td_nicolas.user,
        autor_legajo=td_nicolas.legajo,
        autor_rol=Role.TD,
    )

    # 2. EXP-0002/2026: Pendiente de firma y envío con 2 firmas (4.º y 5.º año), falta 408917 (6.º)
    exp2 = Expediente.objects.create(
        numero="EXP-0002/2026",
        titulo="Inasistencia a actividad solidaria de GSA",
        socio=lucas,
        motivo="Inasistencia a actividad institucional coordinada por la subcomisión GSA.",
        puntos=Decimal("-1.00"),
        estado=EstadoExpedienteEnum.PENDIENTE_CORREOS,
        concepto=ConceptoExpedienteEnum.GSA,
        urgencia=UrgenciaExpedienteEnum.NORMAL,
        descargo_presentado=False,
    )
    exp2.socios.add(lucas)

    CambioEstadoExpediente.objects.create(
        expediente=exp2,
        estado_anterior=EstadoExpedienteEnum.CREADO,
        estado_nuevo=EstadoExpedienteEnum.JUSTIFICANDO,
        actor=td_nicolas.user.username,
        motivo="Apertura de período de justificaciones.",
    )
    CambioEstadoExpediente.objects.create(
        expediente=exp2,
        estado_anterior=EstadoExpedienteEnum.JUSTIFICANDO,
        estado_nuevo=EstadoExpedienteEnum.REVISION_RESOLUCION,
        actor="SISTEMA",
        motivo="Cierre de plazo sin presentación de descargo.",
    )
    CambioEstadoExpediente.objects.create(
        expediente=exp2,
        estado_anterior=EstadoExpedienteEnum.REVISION_RESOLUCION,
        estado_nuevo=EstadoExpedienteEnum.PENDIENTE_CORREOS,
        actor=td_esteban.user.username,
        motivo="Resolución oficial generada y enviada a pendiente de firma.",
    )

    TribunalCompositionService.stamp_for_resolution(exp2)

    firma_4 = _build_firma_dict(
        social_year=4,
        full_name=f"{td_esteban.first_name} {td_esteban.last_name}".strip(),
        legajo=td_esteban.legajo,
        numero_socio=int(td_esteban.numero_socio or td_esteban.legajo),
        user_id=td_esteban.user_id,
        signed_at_iso=(ahora - timedelta(hours=3)).isoformat(),
    )
    firma_5 = _build_firma_dict(
        social_year=5,
        full_name="Sofía Martínez",
        legajo="85422",
        numero_socio=85422,
        user_id=None,
        signed_at_iso=(ahora - timedelta(hours=2)).isoformat(),
    )

    Resolucion.objects.create(
        expediente=exp2,
        version=1,
        plantilla_version="v1",
        estado=EstadoResolucionEnum.DRAFT,
        numero_expediente_snapshot=exp2.numero,
        vistos=(
            "VISTO: Las actuaciones obrantes en el Expediente EXP-0002/2026 y lo normado en "
            "las disposiciones institucionales de A.V.E.I.T.: Reglamento Interno - Art. 12."
        ),
        considerandos=(
            "CONSIDERANDO: Que el socio involucrado no presentó descargo dentro del plazo "
            "reglamentario vigente, correspondiendo ratificar la sanción de -1.00 punto."
        ),
        articulos_resolutivos=(
            "ARTÍCULO 1°.- Aplicar la sanción de -1.00 puntos al socio N° 74907 - "
            "Lucas Gastiaburu.\n\n"
            "ARTÍCULO 2°.- Notifíquese a la Comisión Directiva y al socio involucrado, "
            "regístrese, publíquese y archívese."
        ),
        reglamentos_respaldantes=["Reglamento Interno - Art. 12"],
        firmantes=[firma_4, firma_5],
        created_by=td_esteban.user,
    )

    # 3. Flujo 1 (Apertura): Evento institucional sancionable listo para procesar y cerrar
    holiday_provider = DbHolidayProvider()
    fecha_publicacion, fecha_programada, fecha_fin = _compute_event_dates(
        now=ahora,
        holiday_provider=holiday_provider,
    )
    es_sancionable, motivo_no_sancionable = MeetingComplianceService.validate_notice_period(
        fecha_publicacion=fecha_publicacion,
        fecha_programada=fecha_programada,
        holiday_provider=holiday_provider,
    )
    subcomision_cd = (
        diego_cd.subcomision or Subcomision.objects.get_or_create(name="Comisión Directiva")[0]
    )

    evento = EventoInstitucional.objects.create(
        titulo="Reunión Ordinaria de Seguimiento - Cómputos y CD",
        categoria=CategoriaEventoEnum.REUNION,
        tipo=SubtipoReunionEnum.ORDINARIA,
        modalidad=ModalidadEventoEnum.PRESENCIAL_SEDE,
        lugar="Sede Central AVEIT",
        ubicacion="Sede Central AVEIT",
        modo_convocatoria=ModoConvocatoriaEnum.PERSONALIZADA,
        convocante=diego_cd,
        subcomision=subcomision_cd,
        estado=EstadoEventoEnum.NOTIFICADO,
        es_obligatoria=True,
        es_sancionable=es_sancionable,
        motivo_no_sancionable=motivo_no_sancionable or "",
        fecha_publicacion=fecha_publicacion,
        fecha_programada=fecha_programada,
        fecha_fin=fecha_fin,
        tieneHoraFin=True,
    )

    convocados = (lucas, malena, elena, hector)
    EventoConvocado.objects.bulk_create(
        [EventoConvocado(evento=evento, socio=socio) for socio in convocados]
    )

    AsistenciaEvento.objects.bulk_create(
        [
            AsistenciaEvento(
                evento=evento,
                socio=lucas,
                estado_asistencia=EstadoAsistenciaEventoEnum.AUSENTE,
                metodo_captura=MetodoCapturaAsistenciaEnum.MANUAL,
                motivo="Inasistencia registrada en reunión.",
                procesado_disciplinario=False,
                expediente_generado=None,
            ),
            AsistenciaEvento(
                evento=evento,
                socio=malena,
                estado_asistencia=EstadoAsistenciaEventoEnum.TARDE_LEVE,
                hora_registro=fecha_programada + timedelta(minutes=10),
                minutos_tardanza=10,
                metodo_captura=MetodoCapturaAsistenciaEnum.MANUAL,
                motivo="Llegada 10 minutos tarde.",
                procesado_disciplinario=False,
                expediente_generado=None,
            ),
            AsistenciaEvento(
                evento=evento,
                socio=elena,
                estado_asistencia=EstadoAsistenciaEventoEnum.PRESENTE,
                hora_registro=fecha_programada,
                metodo_captura=MetodoCapturaAsistenciaEnum.MANUAL,
                motivo="Asistencia registrada en horario.",
                procesado_disciplinario=False,
                expediente_generado=None,
            ),
            AsistenciaEvento(
                evento=evento,
                socio=hector,
                estado_asistencia=EstadoAsistenciaEventoEnum.PRESENTE,
                hora_registro=fecha_programada,
                metodo_captura=MetodoCapturaAsistenciaEnum.MANUAL,
                motivo="Asistencia registrada en horario.",
                procesado_disciplinario=False,
                expediente_generado=None,
            ),
        ]
    )

    AtencionFelicitacion.objects.bulk_create(
        [
            AtencionFelicitacion(
                socio=malena,
                llamadosAtencion=2,
                felicitaciones=0,
            ),
            AtencionFelicitacion(
                socio=lucas,
                llamadosAtencion=0,
                felicitaciones=0,
            ),
        ]
    )

    return {
        "expedientes": [exp1.numero, exp2.numero],
        "evento_id": evento.id,
        "evento_titulo": evento.titulo,
    }
