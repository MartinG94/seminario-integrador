"""Carga de datos de padrón institucional, cuentas operativas y expedientes de prueba.

Garantiza:
1. Padrón institucional completo (20 socios G57-G63 + 7 miembros de equipo).
2. Existencia y elegibilidad de todas las cuentas de login para expedientes y T01.
3. Consistencia matemática estricta entre expedientes emitidos y saldo de puntos.
4. Idempotencia total: puede ejecutarse múltiples veces sin duplicar registros.
5. Escenarios de revisión de S4-02 (decisión por causal T02): EXP-0901/2026 a EXP-0904/2026.
"""

import datetime
import hashlib
from decimal import Decimal
from pathlib import Path
from typing import Any

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import connection, transaction
from django.utils import timezone

from expedientes.domain.calendar import compute_business_deadline
from expedientes.domain.causal_resolution import CausalDecision
from expedientes.domain.holiday_provider import DbHolidayProvider
from expedientes.models import (
    AsistenciaEvento,
    AtencionFelicitacion,
    CambioEstadoExpediente,
    CategoriaEventoEnum,
    DescargoExpediente,
    EstadoAsistenciaEventoEnum,
    EstadoEventoEnum,
    EstadoExpedienteEnum,
    EventoInstitucional,
    EvidenciaDescargo,
    Expediente,
    ExpedienteNumberSequence,
    MetodoCapturaAsistenciaEnum,
    ModalidadEventoEnum,
    ModoConvocatoriaEnum,
    OperacionDescargoEnum,
    SubtipoActividadEnum,
    SubtipoReunionEnum,
    TipoDescargoEnum,
    UrgenciaExpedienteEnum,
)
from expedientes.services.causal_resolution_service import CausalResolutionService
from expedientes.services.descargo_version_service import DescargoVersionService
from socios.models import Role, Socio, Subcomision

UserModel = get_user_model()

DEMO_PASSWORD = "Aveit-Demo-2026!"

# PDF mínimo válido para que "Ver comprobante" abra un archivo real en la revisión manual.
DEMO_PDF = (
    b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
    b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
    b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 300 144]>>endobj\n"
    b"trailer<</Root 1 0 R>>\n%%EOF\n"
)
CAUSAL_GROUNDS = (
    "El certificado no acredita la fecha de la reunión plenaria convocada por la subcomisión."
)

# Escenarios de revisión de S4-02:
# (número, estado, motivo, [(legajo, tipo, causal, texto, con_comprobante)], decisiones T02)
CAUSAL_T02_SCENARIOS = [
    (
        "EXP-0901/2026",
        EstadoExpedienteEnum.REVISION_RESOLUCION,
        "Inasistencia a reunión plenaria de subcomisión.",
        [
            (
                "770001",
                TipoDescargoEnum.T02_CERTIFICADO,
                "Enfermedad certificada",
                "Adjunto certificado médico del día de la reunión.",
                True,
            )
        ],
        [],
    ),
    (
        "EXP-0902/2026",
        EstadoExpedienteEnum.REVISION_RESOLUCION,
        "Inasistencia a guardia programada de Cómputos.",
        [
            (
                "770002",
                TipoDescargoEnum.T02_CERTIFICADO,
                "Actividad laboral",
                "Tenía turno en el trabajo y no pude conseguir reemplazo.",
                False,
            )
        ],
        [],
    ),
    (
        "EXP-0903/2026",
        EstadoExpedienteEnum.ESPERA_RESOLUCION,
        "Inasistencia grupal a jornada de mantenimiento del laboratorio.",
        [
            (
                "770003",
                TipoDescargoEnum.T02_CERTIFICADO,
                "Examen universitario",
                "Rendí un parcial en UTN FRC en el mismo horario.",
                True,
            ),
            (
                "770004",
                TipoDescargoEnum.T03_EXTRAORDINARIO,
                "",
                "Tuve un problema familiar imprevisto que me impidió asistir.",
                False,
            ),
            ("770006", None, "", "", False),
        ],
        [(CausalDecision.ACCEPTED, ""), (CausalDecision.REJECTED, CAUSAL_GROUNDS)],
    ),
    (
        "EXP-0904/2026",
        EstadoExpedienteEnum.EMITIDO,
        "Inasistencia a asamblea ordinaria.",
        [
            (
                "770007",
                TipoDescargoEnum.T02_CERTIFICADO,
                "Enfermedad certificada",
                "Adjunto constancia de atención en guardia.",
                True,
            )
        ],
        [(CausalDecision.REJECTED, CAUSAL_GROUNDS)],
    ),
]

TEAM_MEMBERS = [
    ("74907", "Gastiaburu", "Lucas", Role.SOCIO, 2, "Cómputos"),
    ("85194", "Guillén", "Lucas Martín", Role.FISCALIZADORA, 4, "Recursos Humanos"),
    ("87414", "Sánchez", "Diego Gabriel", Role.CD, 5, "Comisión Directiva"),
    ("408917", "Rosales", "Nicolás", Role.TD, 6, "Tribunal de Disciplina"),
    ("403655", "Villegas", "Axel René", Role.ADMIN, 5, "Cómputos"),
    ("409953", "Urviola", "Luis", Role.SOCIO, 4, "Cómputos"),
    ("415327", "Quiroz", "Tomas Augusto", Role.SOCIO, 3, "Cómputos"),
]


class Command(BaseCommand):
    help = "Carga datos del padrón, socios de login, expedientes y saldos consistentes."

    def handle(self, *args: Any, **options: Any) -> None:
        self.stdout.write(
            self.style.NOTICE("=== Iniciando carga de datos para producción y desarrollo ===")
        )

        # 1. Ejecutar esquema legado inicial si no existen datos en socio_lista
        has_data = False
        with connection.cursor() as cursor:
            if "socio_lista" in connection.introspection.table_names():
                cursor.execute("SELECT 1 FROM socio_lista LIMIT 1")
                has_data = cursor.fetchone() is not None

        if not has_data:
            init_sql_path = Path(settings.BASE_DIR) / "core" / "sql" / "02-initial-data.sql"
            if not init_sql_path.exists():
                init_sql_path = (
                    Path(settings.BASE_DIR).parent
                    / "docker"
                    / "mysql"
                    / "init"
                    / "02-initial-data.sql"
                )

            if init_sql_path.exists():
                self.stdout.write(f"Cargando padrón institucional desde: {init_sql_path}")
                if "socio_lista" in connection.introspection.table_names():
                    from ranking.management.commands.load_legacy_schema import (
                        Command as LoadCommand,
                    )

                    cmd = LoadCommand()
                    with open(init_sql_path, encoding="utf-8") as f:
                        raw_sql = f.read()
                    raw_stmts = cmd._split_sql_statements(raw_sql)
                    with connection.cursor() as cursor:
                        for stmt in raw_stmts:
                            s = stmt.strip()
                            if s.upper().startswith("INSERT"):
                                cursor.execute(s)
                else:
                    call_command("load_legacy_schema", path=str(init_sql_path))
            else:
                self.stdout.write(
                    self.style.WARNING(
                        "No se encontró 02-initial-data.sql, omitiendo paso SQL directo."
                    )
                )

        # 2. Cargar subcomisiones en modelo local
        subcomisiones = {}
        for name in [
            "Cómputos",
            "Recursos Humanos",
            "Relaciones Institucionales",
            "Prensa",
            "Mantenimiento",
            "Gestión Social y Ambiental",
            "Eventos",
            "Rifas",
            "Comisión Directiva",
            "Tribunal de Disciplina",
        ]:
            sub, _ = Subcomision.objects.get_or_create(name=name)
            subcomisiones[name] = sub

        # 3. Cargar cuentas de usuarios y socios locales para TODOS los socios de socio_lista
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT sl.nroSocio, sl.apellido, sl.nombre, sl.codSubcomision,
                       sl.anoSocial, sl.idTipoSocio
                FROM socio_lista sl
                ORDER BY sl.nroSocio
            """)
            socios_rows = cursor.fetchall()

        team_dict = {
            legajo: (last_name, first_name, role, social_year, sub_name)
            for legajo, last_name, first_name, role, social_year, sub_name in TEAM_MEMBERS
        }

        subcomisiones_map = {
            1: "Cómputos",
            2: "Recursos Humanos",
            3: "Relaciones Institucionales",
            4: "Prensa",
            5: "Mantenimiento",
            6: "Gestión Social y Ambiental",
            7: "Eventos",
            8: "Rifas",
            9: "Comisión Directiva",
            10: "Tribunal de Disciplina",
            11: "Ex Viajeros",
            99: "Sin Subcomisión",
        }

        with transaction.atomic():
            for nro_socio, apellido, nombre, cod_sub, ano_soc, id_tipo in socios_rows:
                str_nro = str(nro_socio)

                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT nroLegajo FROM socio_estudio "
                        "WHERE nroSocio = %s ORDER BY compositeKey DESC",
                        [nro_socio],
                    )
                    est_row = cursor.fetchone()
                    legajo = str(est_row[0]) if est_row and est_row[0] else str_nro

                    cursor.execute(
                        "SELECT email FROM socio_email "
                        "WHERE nroSocio = %s AND habilitado = 1 ORDER BY compositeKey ASC",
                        [nro_socio],
                    )
                    email_row = cursor.fetchone()
                    email = email_row[0] if email_row and email_row[0] else f"{legajo}@aveit.test"

                if str_nro in team_dict:
                    t_last, t_first, role, social_year, sub_name = team_dict[str_nro]
                    sub = subcomisiones.get(sub_name)
                elif legajo in team_dict:
                    t_last, t_first, role, social_year, sub_name = team_dict[legajo]
                    sub = subcomisiones.get(sub_name)
                else:
                    role = Role.TD if id_tipo == 10 or cod_sub == 10 else Role.SOCIO
                    sub_name = subcomisiones_map.get(cod_sub, "Cómputos")
                    sub = subcomisiones.get(sub_name)
                    social_year = max(1, min(6, ano_soc or 1))

                user, created_user = UserModel.objects.get_or_create(
                    username=str_nro,
                    defaults={"email": email, "first_name": nombre, "last_name": apellido},
                )
                if created_user or not user.has_usable_password():
                    user.set_password(DEMO_PASSWORD)
                    user.save(update_fields=["password"])

                socio, created_socio = Socio.objects.get_or_create(
                    legajo=legajo,
                    defaults={
                        "user": user,
                        "first_name": nombre,
                        "last_name": apellido,
                        "email": email,
                        "subcomision": sub,
                        "social_year": social_year,
                        "role": role,
                        "is_enabled": True,
                    },
                )
                if not created_socio:
                    socio.user = user
                    socio.first_name = nombre
                    socio.last_name = apellido
                    socio.email = email
                    socio.subcomision = sub
                    socio.social_year = social_year
                    socio.role = role
                    socio.is_enabled = True
                    socio.save()

                with connection.cursor() as cursor:
                    cursor.execute(
                        "UPDATE socio_lista SET user_id = %s, forzarCambioClave = 0 "
                        "WHERE nroSocio = %s",
                        [user.id, nro_socio],
                    )

                self.stdout.write(
                    f"+ Socio local verificado: {legajo} - {apellido}, {nombre} ({role})"
                )

        # 4. Crear expedientes de muestra en estados canónicos
        lucas_socio = Socio.objects.get(legajo="74907")
        lucas_guillen = Socio.objects.get(legajo="85194")
        diego_socio = Socio.objects.get(legajo="87414")
        nicolas_socio = Socio.objects.get(legajo="408917")
        axel_socio = Socio.objects.get(legajo="403655")
        elena_socio = Socio.objects.get(legajo="770005")
        malena_socio = Socio.objects.get(legajo="770013")

        # Limpiar identificadores legacy si existieran (ej. EXP-2026-001..009)
        Expediente.objects.filter(numero__regex=r"^EXP-2026-\d+").delete()

        expedientes_def = [
            (
                "EXP-0001/2026",
                lucas_socio,
                EstadoExpedienteEnum.EMITIDO,
                Decimal("-1.00"),
                "Inasistencia injustificada a guardia programada de Cómputos.",
                UrgenciaExpedienteEnum.NORMAL,
                False,
            ),
            (
                "EXP-0002/2026",
                lucas_socio,
                EstadoExpedienteEnum.EMITIDO,
                Decimal("2.00"),
                (
                    "Reconocimiento destacado por mantenimiento y migración de infraestructura "
                    "del servidor de Cómputos."
                ),
                UrgenciaExpedienteEnum.BAJA,
                False,
            ),
            (
                "EXP-0003/2026",
                lucas_socio,
                EstadoExpedienteEnum.JUSTIFICANDO,
                Decimal("-1.50"),
                (
                    "Apertura de sumario administrativo por reporte de demora en entrega de "
                    "inventario."
                ),
                UrgenciaExpedienteEnum.NORMAL,
                False,
            ),
            (
                "EXP-0004/2026",
                lucas_guillen,
                EstadoExpedienteEnum.CREADO,
                Decimal("1.00"),
                (
                    "Propuesta de mención de honor por organización de jornadas de inducción a "
                    "ingresantes."
                ),
                UrgenciaExpedienteEnum.NORMAL,
                False,
            ),
            (
                "EXP-0005/2026",
                diego_socio,
                EstadoExpedienteEnum.EMITIDO,
                Decimal("1.00"),
                (
                    "Reconocimiento por gestión y presentación del balance general de Comisión "
                    "Directiva."
                ),
                UrgenciaExpedienteEnum.NORMAL,
                False,
            ),
            (
                "EXP-0006/2026",
                axel_socio,
                EstadoExpedienteEnum.REVISION_RESOLUCION,
                Decimal("-1.00"),
                "Revisión de justificación por inasistencia a plenario general.",
                UrgenciaExpedienteEnum.NORMAL,
                False,
            ),
            (
                "EXP-0007/2026",
                nicolas_socio,
                EstadoExpedienteEnum.ESPERA_RESOLUCION,
                Decimal("-1.00"),
                "Retraso reiterado en entrega de actas de subcomisión.",
                UrgenciaExpedienteEnum.NORMAL,
                False,
            ),
            (
                "EXP-0008/2026",
                elena_socio,
                EstadoExpedienteEnum.EMITIDO,
                Decimal("3.00"),
                "Mérito destacado por coordinación de actividades académicas de extensión.",
                UrgenciaExpedienteEnum.BAJA,
                False,
            ),
            (
                "EXP-0009/2026",
                malena_socio,
                EstadoExpedienteEnum.EMITIDO,
                Decimal("-2.00"),
                "Sanción disciplinaria por incumplimiento de guardia de laboratorio.",
                UrgenciaExpedienteEnum.NORMAL,
                True,
            ),
        ]

        holiday_provider = DbHolidayProvider()

        with transaction.atomic():
            for numero, socio_dest, estado, puntos, motivo, urgencia, descargo in expedientes_def:
                plazo_inicio = None
                plazo_limite = None
                if estado == EstadoExpedienteEnum.JUSTIFICANDO:
                    plazo_inicio = timezone.now()
                    plazo_limite = compute_business_deadline(
                        start_at=plazo_inicio,
                        business_days=5,
                        holiday_provider=holiday_provider,
                    )

                exp, created_exp = Expediente.objects.get_or_create(
                    numero=numero,
                    defaults={
                        "socio": socio_dest,
                        "estado": estado,
                        "puntos": puntos,
                        "motivo": motivo,
                        "urgencia": urgencia,
                        "descargo_presentado": descargo,
                        "plazo_inicio_at": plazo_inicio,
                        "plazo_limite_at": plazo_limite,
                    },
                )
                if not created_exp:
                    exp.socio = socio_dest
                    exp.estado = estado
                    exp.puntos = puntos
                    exp.motivo = motivo
                    exp.urgencia = urgencia
                    exp.descargo_presentado = descargo
                    if estado == EstadoExpedienteEnum.JUSTIFICANDO and (
                        not exp.plazo_limite_at or exp.plazo_limite_at < timezone.now()
                    ):
                        exp.plazo_inicio_at = plazo_inicio
                        exp.plazo_limite_at = plazo_limite
                    exp.save()
                if numero == "EXP-0003/2026":
                    exp.socios.set([socio_dest, diego_socio])
                else:
                    exp.socios.set([socio_dest])

                actor_creador = (
                    diego_socio.legajo
                    if numero in ("EXP-0002/2026", "EXP-0004/2026", "EXP-0008/2026")
                    else nicolas_socio.legajo
                )
                if not exp.cambios_estado.exists():
                    CambioEstadoExpediente.objects.create(
                        expediente=exp,
                        estado_anterior=EstadoExpedienteEnum.CREADO,
                        estado_nuevo=estado,
                        actor=actor_creador,
                        motivo=motivo,
                    )

                self.stdout.write(
                    f"+ Expediente verificado: {numero} ({estado}) para {socio_dest.legajo}"
                )

        # Actualizar secuencia correlativa anual para que nuevas aperturas sigan desde EXP-0010/2026
        seq, _ = ExpedienteNumberSequence.objects.get_or_create(year=2026)
        if seq.last_value < len(expedientes_def):
            seq.last_value = len(expedientes_def)
            seq.save(update_fields=["last_value"])

        # Escenarios S4-02 antes de sincronizar: el emitido impacta en el libro mayor.
        self._sembrar_escenarios_causal_t02(actor_td=nicolas_socio)

        # 5. Sincronizar libro mayor (tribunal_puntajeaplicado) y caché (tribunal_puntajegeneral)
        # Consistencia: Sum(emitidos) == Sum(puntaje_aplicado) == puntajegeneral.puntos
        self._sincronizar_puntos_libro_mayor()

        # 6. Sembrar reuniones, actividades, asistencias y apercibimientos (Spec 005)
        self._sembrar_eventos_y_asistencias(subcomisiones)

        self.stdout.write(
            self.style.SUCCESS("\n✓ Carga de datos completada exitosamente con consistencia total.")
        )
        self.stdout.write(f"Contraseña de demostración para todas las cuentas: {DEMO_PASSWORD}")

    @transaction.atomic
    def _sembrar_escenarios_causal_t02(self, actor_td: Socio) -> None:
        """Siembra los escenarios de revisión de S4-02 (idempotente)."""
        legajos = {legajo for _, _, _, invs, _ in CAUSAL_T02_SCENARIOS for legajo, *_ in invs}
        socios = {s.legajo: s for s in Socio.objects.filter(legajo__in=legajos)}

        for numero, estado, motivo, involucrados, decisiones in CAUSAL_T02_SCENARIOS:
            exp, _ = Expediente.objects.update_or_create(
                numero=numero,
                defaults={
                    "socio": socios[involucrados[0][0]],
                    "estado": estado,
                    "puntos": Decimal("-1.00"),
                    "motivo": motivo,
                    "urgencia": UrgenciaExpedienteEnum.NORMAL,
                    "descargo_presentado": True,
                },
            )
            exp.socios.set([socios[legajo] for legajo, *_ in involucrados])
            if not exp.cambios_estado.exists():
                CambioEstadoExpediente.objects.create(
                    expediente=exp,
                    estado_anterior=EstadoExpedienteEnum.CREADO,
                    estado_nuevo=estado,
                    actor=actor_td.legajo,
                    motivo=motivo,
                )

            t02 = None
            for legajo, tipo, causal, texto, con_comprobante in involucrados:
                if tipo is None:
                    continue  # Involucrado sin justificación presentada.
                socio = socios[legajo]
                descargo, creado = DescargoExpediente.objects.get_or_create(
                    expediente=exp,
                    socio=socio,
                    defaults={"tipo": tipo, "causal": causal, "texto": texto},
                )
                if con_comprobante and not descargo.evidencias.exists():
                    EvidenciaDescargo.objects.create(
                        expediente=exp,
                        descargo=descargo,
                        socio=socio,
                        contenido_blob=DEMO_PDF,
                        nombre_original=f"comprobante-{legajo}.pdf",
                        extension=".pdf",
                        mime_type="application/pdf",
                        tamanio_bytes=len(DEMO_PDF),
                        sha256_hash=hashlib.sha256(DEMO_PDF).hexdigest(),
                    )
                if creado:
                    DescargoVersionService.registrar_version(
                        descargo, OperacionDescargoEnum.PRESENTADO, socio
                    )
                if tipo == TipoDescargoEnum.T02_CERTIFICADO:
                    t02 = descargo

            if t02 is not None and decisiones and not t02.decisiones_causal.exists():
                # Las decisiones se registran en la etapa de resolución mediante el servicio
                # (autoría, snapshot y versión reales); luego se fija el estado del escenario.
                exp.estado = EstadoExpedienteEnum.ESPERA_RESOLUCION
                exp.save(update_fields=["estado"])
                for decision, fundamento in decisiones:
                    CausalResolutionService.decide(
                        expediente_id=exp.id,
                        descargo_id=t02.id,
                        decision=decision,
                        fundamento=fundamento,
                        evidencia_ids=None,
                        user=actor_td.user,
                    )
                exp.estado = estado
                exp.save(update_fields=["estado"])

            self.stdout.write(f"+ Escenario S4-02 verificado: {numero} ({estado})")

    def _sincronizar_puntos_libro_mayor(self) -> None:
        """Sincroniza tribunal_puntajeaplicado y tribunal_puntajegeneral."""
        with connection.cursor() as cursor:
            # 1. Obtener expedientes emitidos
            cursor.execute(
                "SELECT id, numero, socio_id, puntos FROM expedientes_expediente WHERE estado = %s",
                [EstadoExpedienteEnum.EMITIDO],
            )
            emitidos = cursor.fetchall()
            emitidos_ids = set()

            # Mapear socio_id de expedientes_expediente (socios_socio.id) a nroSocio institucional
            for exp_id, numero, s_id, puntos in emitidos:
                emitidos_ids.add(exp_id)
                cursor.execute("SELECT legajo FROM socios_socio WHERE id = %s", [s_id])
                row = cursor.fetchone()
                if not row:
                    continue
                legajo = row[0]
                if not legajo.isdigit():
                    continue
                nro_socio = int(legajo)

                # Asegurar existencia en tribunal_expediente para respetar la FK
                cursor.execute(
                    "SELECT idExpediente FROM tribunal_expediente WHERE idExpediente = %s",
                    [exp_id],
                )
                if not cursor.fetchone():
                    cursor.execute(
                        "INSERT INTO tribunal_expediente "
                        "(idExpediente, nroExpediente, estadoExpediente_id, puntos_id) "
                        "VALUES (%s, %s, 6, 2)",
                        [exp_id, f"{exp_id:02d}/2026"],
                    )

                cursor.execute(
                    "SELECT idPuntajeAplicado FROM tribunal_puntajeaplicado "
                    "WHERE expediente_id = %s",
                    [exp_id],
                )
                asiento = cursor.fetchone()
                if asiento:
                    cursor.execute(
                        "UPDATE tribunal_puntajeaplicado SET puntajeAplicado = %s, socio_id = %s "
                        "WHERE expediente_id = %s",
                        [puntos, nro_socio, exp_id],
                    )
                else:
                    cursor.execute(
                        "INSERT INTO tribunal_puntajeaplicado "
                        "(puntajeAplicado, socio_id, expediente_id) "
                        "VALUES (%s, %s, %s)",
                        [puntos, nro_socio, exp_id],
                    )

            # Limpiar asientos que apunten a expedientes no emitidos o eliminados
            if emitidos_ids:
                placeholders = ", ".join(["%s"] * len(emitidos_ids))
                delete_query = (
                    "DELETE FROM tribunal_puntajeaplicado "
                    f"WHERE expediente_id IS NOT NULL AND expediente_id NOT IN ({placeholders})"
                )
                cursor.execute(delete_query, list(emitidos_ids))
            else:
                cursor.execute(
                    "DELETE FROM tribunal_puntajeaplicado WHERE expediente_id IS NOT NULL"
                )

            # 2. Recalcular tribunal_puntajegeneral desde tribunal_puntajeaplicado
            cursor.execute(
                "SELECT socio_id, SUM(puntajeAplicado), "
                "SUM(CASE WHEN puntajeAplicado > 0 THEN 1 ELSE 0 END), "
                "SUM(CASE WHEN puntajeAplicado < 0 THEN 1 ELSE 0 END) "
                "FROM tribunal_puntajeaplicado GROUP BY socio_id"
            )
            totales = cursor.fetchall()
            socios_con_puntos = set()

            for nro_socio, total_puntos, fel, llam in totales:
                socios_con_puntos.add(nro_socio)
                cursor.execute(
                    "SELECT idPuntajeGeneral FROM tribunal_puntajegeneral WHERE socio_id = %s",
                    [nro_socio],
                )
                pg = cursor.fetchone()
                if pg:
                    cursor.execute(
                        "UPDATE tribunal_puntajegeneral SET puntos = %s, "
                        "felicitaciones = %s, llamadosAtencion = %s "
                        "WHERE socio_id = %s",
                        [total_puntos, fel, llam, nro_socio],
                    )
                else:
                    cursor.execute(
                        "INSERT INTO tribunal_puntajegeneral "
                        "(puntos, felicitaciones, llamadosAtencion, socio_id) "
                        "VALUES (%s, %s, %s, %s)",
                        [total_puntos, fel, llam, nro_socio],
                    )

            # 3. Para todos los socios del padrón que NO tienen expedientes emitidos,
            # fijar su saldo estrictamente en 0.00
            cursor.execute("SELECT nroSocio FROM socio_lista")
            todos_socios = [r[0] for r in cursor.fetchall()]
            for nro_socio in todos_socios:
                if nro_socio not in socios_con_puntos:
                    cursor.execute(
                        "SELECT idPuntajeGeneral FROM tribunal_puntajegeneral WHERE socio_id = %s",
                        [nro_socio],
                    )
                    pg = cursor.fetchone()
                    if pg:
                        cursor.execute(
                            "UPDATE tribunal_puntajegeneral SET puntos = 0.00, "
                            "felicitaciones = 0, llamadosAtencion = 0 "
                            "WHERE socio_id = %s",
                            [nro_socio],
                        )
                    else:
                        cursor.execute(
                            "INSERT INTO tribunal_puntajegeneral "
                            "(puntos, felicitaciones, llamadosAtencion, socio_id) "
                            "VALUES (0.00, 0, 0, %s)",
                            [nro_socio],
                        )

    def _sembrar_eventos_y_asistencias(self, subcomisiones: dict[str, Subcomision]) -> None:
        """Siembra eventos institucionales, asistencias y libro mayor de apercibimientos."""
        self.stdout.write(self.style.NOTICE("\n--- Sembrando eventos y asistencias (Spec 005) ---"))

        diego_socio = Socio.objects.get(legajo="87414")
        axel_socio = Socio.objects.get(legajo="403655")
        lucas_socio = Socio.objects.get(legajo="74907")
        elena_socio = Socio.objects.get(legajo="770005")
        felix_socio = Socio.objects.get(legajo="770006")
        galatea_socio = Socio.objects.get(legajo="770007")
        hector_socio = Socio.objects.get(legajo="770008")
        irina_socio = Socio.objects.get(legajo="770009")
        malena_socio = Socio.objects.get(legajo="770013")
        quimey_socio = Socio.objects.get(legajo="770017")

        cd_sub = subcomisiones.get("Comisión Directiva")
        computos_sub = subcomisiones.get("Cómputos")
        mantenimiento_sub = subcomisiones.get("Mantenimiento")

        # 1. Reunión Ordinaria en Sede (convocatoria por Grupo G58)
        ev1, _ = EventoInstitucional.objects.update_or_create(
            titulo="Reunión Ordinaria Mensual de Grupo G58",
            defaults={
                "descripcion": (
                    "Reunión ordinaria institucional mensual obligatoria para todos los socios "
                    "activos de Grupo G58."
                ),
                "categoria": CategoriaEventoEnum.REUNION,
                "tipo": SubtipoReunionEnum.ORDINARIA,
                "modalidad": ModalidadEventoEnum.PRESENCIAL_SEDE,
                "lugar": "Sede Central AVEIT - Aula Magna",
                "ubicacion": None,
                "fecha_publicacion": timezone.make_aware(datetime.datetime(2026, 10, 1, 10, 0)),
                "fecha_programada": timezone.make_aware(datetime.datetime(2026, 10, 6, 18, 0)),
                "fecha_fin": timezone.make_aware(datetime.datetime(2026, 10, 6, 20, 0)),
                "fecha_hora_cierre_efectivo": timezone.make_aware(
                    datetime.datetime(2026, 10, 6, 20, 15)
                ),
                "fecha_reporte": timezone.make_aware(datetime.datetime(2026, 10, 7, 11, 0)),
                "tolerancia_tardanza_minutos": 15,
                "tolerancia_retiro_minutos": 15,
                "estado": EstadoEventoEnum.CERRADA,
                "modo_convocatoria": ModoConvocatoriaEnum.GRUPO,
                "grupo_convocado": "G58",
                "es_obligatoria": True,
                "es_sancionable": True,
                "convocante": diego_socio,
                "reportado_por": diego_socio,
                "subcomision": cd_sub,
            },
        )
        self.stdout.write(f"+ Evento 1 verificado: {ev1.titulo} ({ev1.estado})")

        # Asistencias Evento 1
        asist_ev1_data = [
            (
                elena_socio,
                EstadoAsistenciaEventoEnum.PRESENTE,
                timezone.make_aware(datetime.datetime(2026, 10, 6, 18, 5)),
                timezone.make_aware(datetime.datetime(2026, 10, 6, 20, 15)),
                0,
                0,
                MetodoCapturaAsistenciaEnum.MANUAL,
                None,
                "Presente a horario con acreditación institucional.",
                "Puntualidad conforme a reglamento.",
                False,
            ),
            (
                felix_socio,
                EstadoAsistenciaEventoEnum.TARDE_LEVE,
                timezone.make_aware(datetime.datetime(2026, 10, 6, 18, 22)),
                timezone.make_aware(datetime.datetime(2026, 10, 6, 20, 15)),
                22,
                0,
                MetodoCapturaAsistenciaEnum.MANUAL,
                None,
                "Llegada con demora de 22 minutos por congestión vehicular justificada.",
                "Superó tolerancia de 15 min. Corresponde apercibimiento Art. 100.a.",
                True,
            ),
            (
                galatea_socio,
                EstadoAsistenciaEventoEnum.AUSENTE,
                None,
                None,
                0,
                0,
                MetodoCapturaAsistenciaEnum.MANUAL,
                None,
                "Inasistencia sin previo aviso ni justificación administrativa.",
                "Ausente injustificado en reunión obligatoria de grupo.",
                False,
            ),
            (
                hector_socio,
                EstadoAsistenciaEventoEnum.PRESENTE,
                timezone.make_aware(datetime.datetime(2026, 10, 6, 17, 55)),
                timezone.make_aware(datetime.datetime(2026, 10, 6, 20, 15)),
                0,
                0,
                MetodoCapturaAsistenciaEnum.BIOMETRICO,
                "BIO-SEDE-01",
                "Presente registrado biométricamente en ingreso principal.",
                "Registro biométrico validado.",
                False,
            ),
        ]

        asistencias_ev1 = {}
        for (
            s,
            est,
            h_in,
            h_out,
            m_tarde,
            m_ret,
            metodo,
            disp,
            motivo,
            obs,
            proc,
        ) in asist_ev1_data:
            asist, _ = AsistenciaEvento.objects.update_or_create(
                evento=ev1,
                socio=s,
                defaults={
                    "estado_asistencia": est,
                    "hora_registro": h_in,
                    "hora_salida": h_out,
                    "minutos_tardanza": m_tarde,
                    "minutos_retiro_anticipado": m_ret,
                    "metodo_captura": metodo,
                    "dispositivo_id": disp,
                    "motivo": motivo,
                    "observaciones": obs,
                    "procesado_disciplinario": proc,
                },
            )
            asistencias_ev1[s.legajo] = asist
            self.stdout.write(f"  - Asistencia G58: {s.legajo} -> {est}")

        # 2. Reunión Extraordinaria Virtual con Meet (convocatoria por Subcomisión Cómputos)
        ev2, _ = EventoInstitucional.objects.update_or_create(
            titulo="Reunión Extraordinaria de Coordinación Técnica de Cómputos",
            defaults={
                "descripcion": (
                    "Planificación extraordinaria de migración de servidores y servicios de "
                    "cómputos."
                ),
                "categoria": CategoriaEventoEnum.REUNION,
                "tipo": SubtipoReunionEnum.EXTRAORDINARIA,
                "modalidad": ModalidadEventoEnum.VIRTUAL,
                "lugar": "Plataforma Virtual Google Meet",
                "ubicacion": "https://meet.google.com/aveit-computos-coord",
                "fecha_publicacion": timezone.make_aware(datetime.datetime(2026, 10, 12, 9, 0)),
                "fecha_programada": timezone.make_aware(datetime.datetime(2026, 10, 20, 19, 0)),
                "fecha_fin": timezone.make_aware(datetime.datetime(2026, 10, 20, 20, 30)),
                "tolerancia_tardanza_minutos": 15,
                "tolerancia_retiro_minutos": 15,
                "estado": EstadoEventoEnum.PROGRAMADA,
                "modo_convocatoria": ModoConvocatoriaEnum.SUBCOMISION,
                "subcomision": computos_sub,
                "es_obligatoria": True,
                "es_sancionable": True,
                "convocante": axel_socio,
                "reportado_por": None,
            },
        )
        self.stdout.write(f"+ Evento 2 verificado: {ev2.titulo} ({ev2.estado})")

        # 3. Jornada de Mantenimiento Externa (convocatoria personalizada ad-hoc)
        ev3, _ = EventoInstitucional.objects.update_or_create(
            titulo="Jornada Operativa de Mantenimiento en Predio Deportivo",
            defaults={
                "descripcion": (
                    "Actividad institucional en exteriores: tareas de pintura, reparación y "
                    "acondicionamiento de instalaciones."
                ),
                "categoria": CategoriaEventoEnum.ACTIVIDAD,
                "tipo": SubtipoActividadEnum.MANTENIMIENTO,
                "modalidad": ModalidadEventoEnum.PRESENCIAL_EXTERNA,
                "lugar": "Predio Deportivo UTN",
                "ubicacion": "Predio Deportivo UTN - Cancha 2, Los Nogales 1200",
                "fecha_publicacion": timezone.make_aware(datetime.datetime(2026, 10, 5, 8, 0)),
                "fecha_programada": timezone.make_aware(datetime.datetime(2026, 10, 10, 9, 0)),
                "fecha_fin": None,  # Estrictamente opcional según CA8
                "fecha_hora_cierre_efectivo": timezone.make_aware(
                    datetime.datetime(2026, 10, 10, 13, 30)
                ),
                "fecha_reporte": timezone.make_aware(datetime.datetime(2026, 10, 11, 10, 0)),
                "tolerancia_tardanza_minutos": 15,
                "tolerancia_retiro_minutos": 15,
                "estado": EstadoEventoEnum.CERRADA,
                "modo_convocatoria": ModoConvocatoriaEnum.PERSONALIZADA,
                "es_obligatoria": True,
                "es_sancionable": True,
                "convocante": diego_socio,
                "reportado_por": diego_socio,
                "subcomision": mantenimiento_sub,
            },
        )
        self.stdout.write(f"+ Evento 3 verificado: {ev3.titulo} ({ev3.estado})")

        # Asistencias Evento 3 (Ad-hoc)
        asist_ev3_data = [
            (
                irina_socio,
                EstadoAsistenciaEventoEnum.PRESENTE,
                timezone.make_aware(datetime.datetime(2026, 10, 10, 8, 50)),
                timezone.make_aware(datetime.datetime(2026, 10, 10, 13, 30)),
                0,
                0,
                MetodoCapturaAsistenciaEnum.MANUAL,
                None,
                "Presente cumpliendo tareas asignadas de acondicionamiento edilicio.",
                "Participación activa durante toda la jornada.",
                False,
            ),
            (
                malena_socio,
                EstadoAsistenciaEventoEnum.RETIRO_ANTICIPADO_LEVE,
                timezone.make_aware(datetime.datetime(2026, 10, 10, 9, 0)),
                timezone.make_aware(datetime.datetime(2026, 10, 10, 13, 5)),
                0,
                25,
                MetodoCapturaAsistenciaEnum.MANUAL,
                None,
                "Retiro anticipado de 25 minutos por compromiso laboral impostergable.",
                "Notificó al coordinador antes de retirarse.",
                False,
            ),
            (
                quimey_socio,
                EstadoAsistenciaEventoEnum.AUSENTE,
                None,
                None,
                0,
                0,
                MetodoCapturaAsistenciaEnum.MANUAL,
                None,
                "Inasistencia sin justificación documental a la jornada operativa.",
                "Convocado personalizado que no asistió.",
                False,
            ),
            (
                lucas_socio,
                EstadoAsistenciaEventoEnum.PRESENTE,
                timezone.make_aware(datetime.datetime(2026, 10, 10, 9, 5)),
                timezone.make_aware(datetime.datetime(2026, 10, 10, 13, 30)),
                5,
                0,
                MetodoCapturaAsistenciaEnum.MANUAL,
                None,
                "Presente supervisando tareas de cableado e infraestructura.",
                "Dentro del período de tolerancia de 15 minutos.",
                False,
            ),
        ]

        for (
            s,
            est,
            h_in,
            h_out,
            m_tarde,
            m_ret,
            metodo,
            disp,
            motivo,
            obs,
            proc,
        ) in asist_ev3_data:
            AsistenciaEvento.objects.update_or_create(
                evento=ev3,
                socio=s,
                defaults={
                    "estado_asistencia": est,
                    "hora_registro": h_in,
                    "hora_salida": h_out,
                    "minutos_tardanza": m_tarde,
                    "minutos_retiro_anticipado": m_ret,
                    "metodo_captura": metodo,
                    "dispositivo_id": disp,
                    "motivo": motivo,
                    "observaciones": obs,
                    "procesado_disciplinario": proc,
                },
            )
            self.stdout.write(f"  - Asistencia Ad-hoc: {s.legajo} -> {est}")

        # 4. Libro de Llamados y Felicitaciones (atencionFelicitacion)
        # 4.1 Llamado de atención derivado de la tardanza leve de Félix Fábula (770006)
        asist_felix = asistencias_ev1.get("770006")
        if asist_felix:
            asist_felix.notificado = True
            asist_felix.fechaNotificacion = datetime.date(2026, 10, 6)
            asist_felix.save(update_fields=["notificado", "fechaNotificacion"])

        AtencionFelicitacion.objects.update_or_create(
            socio=felix_socio,
            defaults={"llamadosAtencion": 1, "felicitaciones": 0},
        )
        self.stdout.write(
            f"+ AtencionFelicitacion verificado para Félix Fábula ({felix_socio.legajo}): 1 llamado"
        )

        # 4.2 Dos llamados de atención para Malena Marea (770013) (2 pendientes para regla 3:1)
        AtencionFelicitacion.objects.update_or_create(
            socio=malena_socio,
            defaults={"llamadosAtencion": 2, "felicitaciones": 0},
        )
        self.stdout.write(
            f"+ AtencionFelicitacion verificado para {malena_socio.legajo} "
            "(2 pendientes para regla 3:1)"
        )

        # 4.3 Lucas Gastiaburu (74907) con 0 llamados (consolidado previamente en EXP-2026-001)
        AtencionFelicitacion.objects.update_or_create(
            socio=lucas_socio,
            defaults={"llamadosAtencion": 0, "felicitaciones": 0},
        )
        self.stdout.write(
            f"+ AtencionFelicitacion verificado para {lucas_socio.legajo} "
            "(0 llamados tras consolidar EXP-2026-001)"
        )

        self.stdout.write(
            self.style.SUCCESS(
                "✓ Seed de eventos institucionales y asistencias completado exitosamente."
            )
        )
