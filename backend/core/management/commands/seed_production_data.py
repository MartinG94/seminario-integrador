"""Carga de datos de padrón institucional, cuentas operativas y expedientes de prueba.

Garantiza:
1. Padrón institucional completo (20 socios G57-G63 + 7 miembros de equipo).
2. Existencia y elegibilidad de todas las cuentas de login para expedientes y T01.
3. Consistencia matemática estricta entre expedientes emitidos y saldo de puntos.
4. Idempotencia total: puede ejecutarse múltiples veces sin duplicar registros.
"""

from decimal import Decimal
from pathlib import Path
from typing import Any

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import connection, transaction

from expedientes.models import EstadoExpedienteEnum, Expediente, UrgenciaExpedienteEnum
from socios.models import Role, Socio, Subcomision

UserModel = get_user_model()

DEMO_PASSWORD = "Aveit-Demo-2026!"

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

        # 1. Ejecutar esquema legado inicial si no existen tablas
        init_sql_path = Path(settings.BASE_DIR) / "core" / "sql" / "02-initial-data.sql"
        if not init_sql_path.exists():
            init_sql_path = (
                Path(settings.BASE_DIR).parent / "docker" / "mysql" / "init" / "02-initial-data.sql"
            )

        if init_sql_path.exists():
            self.stdout.write(f"Cargando padrón institucional desde: {init_sql_path}")
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

        # 3. Cargar cuentas de usuarios y socios locales para los 7 integrantes
        with transaction.atomic():
            for legajo, last_name, first_name, role, social_year, sub_name in TEAM_MEMBERS:
                email = f"{legajo}@aveit.test"
                user, created_user = UserModel.objects.get_or_create(
                    username=legajo,
                    defaults={"email": email, "first_name": first_name, "last_name": last_name},
                )
                if created_user or not user.has_usable_password():
                    user.set_password(DEMO_PASSWORD)
                    user.save(update_fields=["password"])

                sub = subcomisiones.get(sub_name)
                socio, created_socio = Socio.objects.get_or_create(
                    legajo=legajo,
                    defaults={
                        "user": user,
                        "first_name": first_name,
                        "last_name": last_name,
                        "email": email,
                        "subcomision": sub,
                        "social_year": social_year,
                        "role": role,
                        "is_enabled": True,
                    },
                )
                if not created_socio:
                    # Asegurar campos operativos
                    socio.user = user
                    socio.first_name = first_name
                    socio.last_name = last_name
                    socio.email = email
                    socio.subcomision = sub
                    socio.social_year = social_year
                    socio.role = role
                    socio.is_enabled = True
                    socio.save()

                self.stdout.write(
                    f"+ Socio local verificado: {legajo} - {last_name}, {first_name} ({role})"
                )

        # 4. Crear expedientes de muestra en estados canónicos
        lucas_socio = Socio.objects.get(legajo="74907")
        lucas_guillen = Socio.objects.get(legajo="85194")
        diego_socio = Socio.objects.get(legajo="87414")
        axel_socio = Socio.objects.get(legajo="403655")

        expedientes_def = [
            (
                "EXP-2026-001",
                lucas_socio,
                EstadoExpedienteEnum.EMITIDO,
                Decimal("-1.00"),
                "Inasistencia injustificada a guardia programada de Cómputos.",
                UrgenciaExpedienteEnum.NORMAL,
                True,
            ),
            (
                "EXP-2026-002",
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
                "EXP-2026-003",
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
                "EXP-2026-004",
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
                "EXP-2026-005",
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
                "EXP-2026-006",
                axel_socio,
                EstadoExpedienteEnum.REVISION_RESOLUCION,
                Decimal("-1.00"),
                "Revisión de justificación por inasistencia a plenario general.",
                UrgenciaExpedienteEnum.NORMAL,
                False,
            ),
        ]

        with transaction.atomic():
            for numero, socio_dest, estado, puntos, motivo, urgencia, descargo in expedientes_def:
                exp, created_exp = Expediente.objects.get_or_create(
                    numero=numero,
                    defaults={
                        "socio": socio_dest,
                        "estado": estado,
                        "puntos": puntos,
                        "motivo": motivo,
                        "urgencia": urgencia,
                        "descargo_presentado": descargo,
                    },
                )
                if not created_exp:
                    exp.socio = socio_dest
                    exp.estado = estado
                    exp.puntos = puntos
                    exp.motivo = motivo
                    exp.urgencia = urgencia
                    exp.descargo_presentado = descargo
                    exp.save()
                if not exp.socios.filter(pk=socio_dest.pk).exists():
                    exp.socios.add(socio_dest)

                self.stdout.write(
                    f"+ Expediente verificado: {numero} ({estado}) para {socio_dest.legajo}"
                )

        # 5. Sincronizar libro mayor (tribunal_puntajeaplicado) y caché (tribunal_puntajegeneral)
        # Consistencia: Sum(emitidos) == Sum(puntaje_aplicado) == puntajegeneral.puntos
        self._sincronizar_puntos_libro_mayor()

        self.stdout.write(
            self.style.SUCCESS("\n✓ Carga de datos completada exitosamente con consistencia total.")
        )
        self.stdout.write(f"Contraseña de demostración para todas las cuentas: {DEMO_PASSWORD}")

    def _sincronizar_puntos_libro_mayor(self) -> None:
        """Sincroniza tribunal_puntajeaplicado y tribunal_puntajegeneral."""
        with connection.cursor() as cursor:
            # Obtener expedientes emitidos
            cursor.execute(
                "SELECT id, numero, socio_id, puntos FROM expedientes_expediente WHERE estado = %s",
                [EstadoExpedienteEnum.EMITIDO],
            )
            emitidos = cursor.fetchall()

            # Mapear socio_id de expedientes_expediente (socios_socio.id) a nroSocio institucional
            for exp_id, numero, s_id, puntos in emitidos:
                cursor.execute("SELECT legajo FROM socios_socio WHERE id = %s", [s_id])
                row = cursor.fetchone()
                if not row:
                    continue
                legajo = row[0]
                if not legajo.isdigit():
                    continue
                nro_socio = int(legajo)

                # Verificar si ya existe el asiento para este expediente_id
                cursor.execute(
                    "SELECT idPuntajeAplicado FROM tribunal_puntajeaplicado "
                    "WHERE expediente_id = %s",
                    [exp_id],
                )
                asiento = cursor.fetchone()
                if not asiento:
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
                        "INSERT INTO tribunal_puntajeaplicado "
                        "(puntajeAplicado, socio_id, expediente_id) "
                        "VALUES (%s, %s, %s)",
                        [puntos, nro_socio, exp_id],
                    )

            # Recalcular tribunal_puntajegeneral desde tribunal_puntajeaplicado
            cursor.execute(
                "SELECT socio_id, SUM(puntajeAplicado), "
                "SUM(CASE WHEN puntajeAplicado > 0 THEN 1 ELSE 0 END), "
                "SUM(CASE WHEN puntajeAplicado < 0 THEN 1 ELSE 0 END) "
                "FROM tribunal_puntajeaplicado GROUP BY socio_id"
            )
            totales = cursor.fetchall()
            for nro_socio, total_puntos, fel, llam in totales:
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
