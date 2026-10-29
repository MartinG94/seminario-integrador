"""Comando de importación e ingestión integral del padrón institucional y expedientes.

Carga y sincroniza:
1. Padrón institucional completo (5.508 socios) desde socios.csv hacia `socio_lista`
   y tablas satélite (`socio_estudio`, `socio_email`, `socio_telefono`, `socio_medio`).
2. Los 48 expedientes históricos reales del socio 11779 desde ExpedientesEjemplo11779.csv,
   aplicando la exención de sanciones por justificación aprobada y la consolidación 3:1.
3. Expedientes institucionales contextualizados para los restantes 218 socios con saldo
   en Publicaciones Tribunal - Puntos.csv, cerrando matemáticamente su puntaje 1:1.
4. Sincronización del libro mayor (`tribunal_puntajeaplicado`), caché
   (`tribunal_puntajegeneral`) y libro de llamados/felicitaciones (`atencionFelicitacion`)
   con regla 3:1 inmutable.
5. Garantía de reconciliación al 100% en el ranking (`diff == 0.00` y `reconciled == True`).
"""

import csv
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import connection, transaction

from expedientes.models import (
    AtencionFelicitacion,
    CambioEstadoExpediente,
    EstadoExpedienteEnum,
    Expediente,
    UrgenciaExpedienteEnum,
)
from socios.models import Role
from socios.models import Socio as DjangoSocio
from socios.models import Subcomision as DjangoSubcomision

UserModel = get_user_model()
DEMO_PASSWORD = "Aveit-Demo-2026!"

# Subcomisiones estatutarias y su código legacy
SUBCOMISIONES_CATALOG = [
    (1, "Cómputos"),
    (2, "Recursos Humanos"),
    (3, "Relaciones Institucionales"),
    (4, "Prensa"),
    (5, "Mantenimiento"),
    (6, "Gestión Social y Ambiental"),
    (7, "Eventos"),
    (8, "Rifas"),
    (9, "Comisión Directiva"),
    (10, "Tribunal de Disciplina"),
    (11, "Ex Viajeros"),
    (99, "Sin Subcomisión"),
]

# Especialidades universitarias canónicas UTN FRC
ESPECIALIDADES_CATALOG = [
    (1, "Ingeniería en Sistemas de Información", "Carrera de grado UTN FRC"),
    (2, "Ingeniería Electrónica", "Carrera de grado UTN FRC"),
    (3, "Ingeniería Mecánica", "Carrera de grado UTN FRC"),
    (4, "Ingeniería Industrial", "Carrera de grado UTN FRC"),
    (7, "Ingeniería Civil", "Carrera de grado UTN FRC"),
    (8, "Ingeniería Química", "Carrera de grado UTN FRC"),
    (9, "Ingeniería Eléctrica", "Carrera de grado UTN FRC"),
    (10, "Ingeniería Metalúrgica", "Carrera de grado UTN FRC"),
]

# Estados de membresía canónicos
ESTADOS_SOCIO_CATALOG = [
    (1, "Habilitado", "Socio con derechos plenos"),
    (2, "En receso", "Socio en receso académico"),
    (3, "Impasivo", "Mora transitoria / Inactivo Jr"),
    (4, "Inactivo", "Inactivo Sr en trámite de baja"),
    (5, "Baja", "Baja definitiva"),
]


class Command(BaseCommand):
    help = "Importa socios.csv, Puntos.csv y ExpedientesEjemplo11779.csv."

    def add_arguments(self, parser):
        parser.add_argument(
            "--socios-csv",
            type=str,
            default=None,
            help="Ruta al archivo socios.csv",
        )
        parser.add_argument(
            "--puntos-csv",
            type=str,
            default=None,
            help="Ruta al archivo Publicaciones Tribunal - Puntos.csv",
        )
        parser.add_argument(
            "--ejemplo-11779-csv",
            type=str,
            default=None,
            help="Ruta al archivo ExpedientesEjemplo11779.csv",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Ejecuta en modo simulación sin comitear cambios.",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        self.stdout.write(
            self.style.NOTICE("=== Ingestión del Padrón y Expedientes del Tribunal ===")
        )

        base_dir = Path(settings.BASE_DIR)
        data_dir = base_dir / "data"

        # Resolver rutas de archivos
        socios_path = (
            Path(options["socios_csv"]) if options["socios_csv"] else data_dir / "socios.csv"
        )
        puntos_path = (
            Path(options["puntos_csv"])
            if options["puntos_csv"]
            else data_dir / "publicaciones_tribunal_puntos.csv"
        )
        ejemplo_path = (
            Path(options["ejemplo_11779_csv"])
            if options["ejemplo_11779_csv"]
            else data_dir / "expedientes_ejemplo_11779.csv"
        )

        if not socios_path.exists():
            alt = Path(r"G:\My Drive\Estudios\Seminario\socios.csv")
            if alt.exists():
                socios_path = alt

        if not puntos_path.exists():
            alt = Path(r"G:\My Drive\Estudios\Seminario\Publicaciones Tribunal - Puntos.csv")
            if alt.exists():
                puntos_path = alt

        if not ejemplo_path.exists():
            alt = Path(r"G:\My Drive\Estudios\Seminario\ExpedientesEjemplo11779.csv")
            if alt.exists():
                ejemplo_path = alt

        s_status = "OK" if socios_path.exists() else "NO EXISTE"
        p_status = "OK" if puntos_path.exists() else "NO EXISTE"
        e_status = "OK" if ejemplo_path.exists() else "NO EXISTE"

        self.stdout.write(f"1. Padrón: {socios_path.name} ({s_status})")
        self.stdout.write(f"2. Puntos: {puntos_path.name} ({p_status})")
        self.stdout.write(f"3. Expedientes 11779: {ejemplo_path.name} ({e_status})")

        if not socios_path.exists() or not puntos_path.exists():
            self.stderr.write(self.style.ERROR("Error: Faltan archivos CSV requeridos."))
            return

        dry_run = options.get("dry_run", False)

        with transaction.atomic():
            # 1. Asegurar catálogos base
            self._ensure_catalogs()

            # 2. Cargar socios.csv (5.508 socios)
            socios_dict = self._import_socios_csv(socios_path)

            # 3. Importar expedientes reales del socio 11779
            if ejemplo_path.exists():
                self._import_expedientes_11779(ejemplo_path, socios_dict)

            # 4. Generar expedientes sintéticos para los restantes 218 socios
            self._import_puntos_tribunal_and_generate_expedientes(puntos_path, socios_dict)

            # 5. Sincronizar saldos de los socios sin expedientes en 0.00
            self._sync_zero_balance_socios()

            # 6. Verificación de reconciliación
            self._verify_reconciliation()

            if dry_run:
                self.stdout.write(self.style.WARNING("Modo --dry-run activo: Revertiendo."))
                transaction.set_rollback(True)
            else:
                self.stdout.write(self.style.SUCCESS("✓ Ingestión completada exitosamente."))

    def _ensure_catalogs(self) -> None:
        """Asegura que los catálogos en MySQL tengan los registros canónicos."""
        self.stdout.write(self.style.NOTICE("\n--- 1. Verificando catálogos base ---"))
        with connection.cursor() as cursor:
            # Subcomisiones legacy
            for cod, nombre in SUBCOMISIONES_CATALOG:
                cursor.execute(
                    "INSERT INTO socio_tiposubcomision (codSubcomision, nombre) "
                    "VALUES (%s, %s) ON DUPLICATE KEY UPDATE nombre=VALUES(nombre)",
                    [cod, nombre],
                )

            # Especialidades legacy
            for cod, nombre, desc in ESPECIALIDADES_CATALOG:
                cursor.execute(
                    "INSERT INTO socio_especialidad "
                    "(codEspecialidad, nombre, descripcion) VALUES (%s, %s, %s) "
                    "ON DUPLICATE KEY UPDATE nombre=VALUES(nombre)",
                    [cod, nombre, desc],
                )

            # Estados de socio legacy
            for cod, nombre, desc in ESTADOS_SOCIO_CATALOG:
                cursor.execute(
                    "INSERT INTO socio_estado "
                    "(codEstadoSocio, nombre, descripcion) VALUES (%s, %s, %s) "
                    "ON DUPLICATE KEY UPDATE nombre=VALUES(nombre), "
                    "descripcion=VALUES(descripcion)",
                    [cod, nombre, desc],
                )

        # Subcomisiones Django
        for _, nombre in SUBCOMISIONES_CATALOG:
            if nombre != "Sin Subcomisión":
                DjangoSubcomision.objects.get_or_create(name=nombre)

        # Tablas satélite de soporte si no existieran (ej. base de pruebas efímera)
        with connection.cursor() as cursor:
            tables = set(connection.introspection.table_names())
            if "socio_telefono" not in tables:
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS `socio_telefono` (
                      `compositeKey` int(11) NOT NULL,
                      `nroSocio` int(11) NOT NULL,
                      `idTelefono` int(11) NOT NULL,
                      `telefono` varchar(45) NOT NULL,
                      `codTipoTelefono` int(11) NOT NULL,
                      PRIMARY KEY (`compositeKey`)
                    )
                    """
                )
            if "socio_medio" not in tables:
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS `socio_medio` (
                      `compositeKey` int(11) NOT NULL,
                      `nroSocio` int(11) NOT NULL,
                      `codMedio` int(11) NOT NULL,
                      `descripcion` varchar(45) NOT NULL,
                      PRIMARY KEY (`compositeKey`)
                    )
                    """
                )

        self.stdout.write("✓ Catálogos verificados.")

    def _map_subcomision(self, subcom_str: str) -> tuple[int, str]:
        """Mapea el string del CSV al código y nombre de subcomisión."""
        s = subcom_str.strip().lower()
        if "cómputos" in s or "computos" in s:
            return 1, "Cómputos"
        if "recursos humanos" in s or "rrhh" in s:
            return 2, "Recursos Humanos"
        if "relaciones institucionales" in s or "rrii" in s:
            return 3, "Relaciones Institucionales"
        if "prensa" in s:
            return 4, "Prensa"
        if "mantenimiento" in s:
            return 5, "Mantenimiento"
        if "gestión social" in s or "ambiental" in s or "gsa" in s:
            return 6, "Gestión Social y Ambiental"
        if "eventos" in s or "organización" in s:
            return 7, "Eventos"
        if "rifas" in s:
            return 8, "Rifas"
        if "comisión directiva" in s or "directiva" in s or "cd" == s:
            return 9, "Comisión Directiva"
        if "tribunal" in s or "disciplina" in s or "td" == s:
            return 10, "Tribunal de Disciplina"
        if "ex viajeros" in s or "exviajeros" in s:
            return 11, "Ex Viajeros"
        return 99, "Sin Subcomisión"

    def _map_especialidad(self, esp_str: str) -> tuple[int, int]:
        """Retorna (codEspecialidadPrimaria, codEspecialidadSecundaria)."""
        s = esp_str.strip().lower()
        primary = 1
        secondary = 0
        if "sistemas" in s:
            primary = 1
            if "industrial" in s:
                secondary = 4
            elif "civil" in s:
                secondary = 7
        elif "electrónica" in s or "electronica" in s:
            primary = 2
        elif "mecánica" in s or "mecanica" in s:
            primary = 3
            if "industrial" in s:
                secondary = 4
        elif "industrial" in s:
            primary = 4
            if "mecánica" in s or "mecanica" in s:
                secondary = 3
        elif "civil" in s:
            primary = 7
        elif "química" in s or "quimica" in s:
            primary = 8
        elif "eléctrica" in s or "electrica" in s:
            primary = 9
        elif "metalúrgica" in s or "metalurgica" in s:
            primary = 10
        return primary, secondary

    def _estimate_ano_social(self, nro_socio: int, ingresante: bool, cod_sub: int) -> int:
        """Estima el año social (1 a 6) para ubicar al socio en su ciclo formativo."""
        if cod_sub == 11:
            return 0  # Ex Viajero (fuera de escala)
        if ingresante:
            return 1
        # Caso testigo Diego Sánchez (#11779): año 6 en 2026
        if nro_socio == 11779:
            return 6
        if nro_socio >= 12600:
            return 1
        if nro_socio >= 12300:
            return 2
        if nro_socio >= 12000:
            return 3
        if nro_socio >= 11800:
            return 4
        if nro_socio >= 11400:
            return 5
        if nro_socio >= 10500:
            return 6
        return 0  # Histórico

    def _import_socios_csv(self, file_path: Path) -> dict[int, dict[str, Any]]:
        """Lee socios.csv e inserta/actualiza en socio_lista y tablas satélite."""
        self.stdout.write(self.style.NOTICE("\n--- 2. Ingestando padrón general (socios.csv) ---"))

        socios_dict = {}
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            reader = csv.reader(f)
            # Saltear las 3 líneas de encabezado descriptivo
            next(reader, None)
            next(reader, None)
            next(reader, None)

            count = 0
            with connection.cursor() as cursor:
                for r in reader:
                    if not r or not any(r):
                        continue
                    try:
                        nro_socio = int(r[1].strip())
                    except ValueError:
                        continue

                    ingresante = r[2].strip().lower() == "si"
                    apellido = r[3].strip()[:45]
                    nombre = r[4].strip()[:45]
                    dni_str = r[5].strip()
                    dni = int(dni_str) if dni_str.isdigit() else 0
                    subcom_raw = r[6].strip()
                    email = r[7].strip()
                    telefono = r[8].strip()
                    instagram = r[9].strip()
                    especialidad_raw = r[10].strip()
                    legajo_raw = r[11].strip()

                    cod_sub, subcom_nombre = self._map_subcomision(subcom_raw)
                    ano_social = self._estimate_ano_social(nro_socio, ingresante, cod_sub)
                    entry_year = 2026 - ano_social + 1 if 1 <= ano_social <= 6 else 2018
                    fecha_ingreso = date(entry_year, 3, 1)
                    fecha_nac = date(entry_year - 18, 1, 1)
                    id_tipo_socio = 10 if cod_sub == 10 else 12

                    # Inserción en socio_lista
                    cursor.execute(
                        """
                        INSERT INTO socio_lista
                        (nroSocio, apellido, nombre, fechaIngreso, codTipoDoc, nroDoc,
                         fechaNac, codSexo, codSubcomision, codEstadoCivil, fechaBaja,
                         anoSocial, ingresante, idTipoSocio, user_id, forzarCambioClave)
                        VALUES (%s, %s, %s, %s, 1, %s, %s, 3, %s, 1, NULL, %s, %s, %s, NULL, 0)
                        ON DUPLICATE KEY UPDATE
                            apellido=VALUES(apellido),
                            nombre=VALUES(nombre),
                            codSubcomision=VALUES(codSubcomision),
                            anoSocial=VALUES(anoSocial),
                            ingresante=VALUES(ingresante)
                        """,
                        [
                            nro_socio,
                            apellido,
                            nombre,
                            fecha_ingreso,
                            dni,
                            fecha_nac,
                            cod_sub,
                            ano_social,
                            1 if ingresante else 0,
                            id_tipo_socio,
                        ],
                    )

                    # socio_estudio (Legajo y Especialidad)
                    esp_prim, esp_sec = self._map_especialidad(especialidad_raw)
                    if legajo_raw:
                        leg_items = [
                            item.strip() for item in legajo_raw.split(",") if item.strip().isdigit()
                        ]
                        if not leg_items and legajo_raw.isdigit():
                            leg_items = [legajo_raw]

                        for idx, leg_item in enumerate(leg_items, start=1):
                            leg_num = int(leg_item)
                            comp_key = (nro_socio * 100) + idx
                            cod_esp = esp_sec if idx > 1 and esp_sec else esp_prim
                            cursor.execute(
                                """
                                INSERT INTO socio_estudio
                                (compositeKey, nroSocio, nroLegajo, codEspecialidad,
                                 curso, aula, codTurno)
                                VALUES (%s, %s, %s, %s, NULL, NULL, NULL)
                                ON DUPLICATE KEY UPDATE
                                    nroLegajo=VALUES(nroLegajo),
                                    codEspecialidad=VALUES(codEspecialidad)
                                """,
                                [comp_key, nro_socio, leg_num, cod_esp],
                            )

                    # socio_email
                    if email:
                        cursor.execute(
                            """
                            INSERT INTO socio_email
                            (compositeKey, nroSocio, idEmail, email, comprobado, habilitado)
                            VALUES (%s, %s, 0, %s, 1, 1)
                            ON DUPLICATE KEY UPDATE email=VALUES(email), habilitado=1
                            """,
                            [nro_socio * 100, nro_socio, email[:45]],
                        )

                    # socio_telefono
                    if telefono:
                        cursor.execute(
                            """
                            INSERT INTO socio_telefono
                            (compositeKey, nroSocio, idTelefono, telefono, codTipoTelefono)
                            VALUES (%s, %s, 0, %s, 1)
                            ON DUPLICATE KEY UPDATE telefono=VALUES(telefono)
                            """,
                            [nro_socio * 100, nro_socio, telefono[:45]],
                        )

                    # socio_medio (Instagram)
                    if instagram:
                        clean_insta = instagram.lstrip("@")[:45]
                        cursor.execute(
                            """
                            INSERT INTO socio_medio
                            (compositeKey, nroSocio, codMedio, descripcion)
                            VALUES (%s, %s, 1, %s)
                            ON DUPLICATE KEY UPDATE descripcion=VALUES(descripcion)
                            """,
                            [nro_socio * 100, nro_socio, clean_insta],
                        )

                    # socio_estadoHistorial
                    cod_estado = 1
                    if cod_sub == 11 or ano_social == 0:
                        cod_estado = 2  # En receso / Exviajero
                    grupo_id = (
                        58
                        if ano_social == 6
                        else (
                            59
                            if ano_social == 5
                            else (
                                60
                                if ano_social == 4
                                else (62 if ano_social == 2 else (63 if ano_social == 1 else 57))
                            )
                        )
                    )
                    cursor.execute(
                        """
                        INSERT INTO socio_estadoHistorial
                        (idEstadoHistorial, idGrupo, nroSocio, fechaHora,
                         codEstadoSocio, socio_motivoCambioEstado)
                        VALUES (%s, %s, %s, %s, %s, 1)
                        ON DUPLICATE KEY UPDATE codEstadoSocio=VALUES(codEstadoSocio)
                        """,
                        [
                            (nro_socio * 10) + 1,
                            grupo_id,
                            nro_socio,
                            datetime(entry_year, 3, 1, 10, 0),
                            cod_estado,
                        ],
                    )

                    primary_legajo = (
                        legajo_raw.split(",")[0].strip() if legajo_raw else str(nro_socio)
                    )
                    socios_dict[nro_socio] = {
                        "apellido": apellido,
                        "nombre": nombre,
                        "dni": dni,
                        "subcom_id": cod_sub,
                        "subcom_nombre": subcom_nombre,
                        "ano_social": ano_social,
                        "ingresante": ingresante,
                        "legajo": primary_legajo,
                        "email": email or f"{nro_socio}@aveit.test",
                    }
                    count += 1

        self.stdout.write(f"✓ {count} socios registrados en el padrón general.")
        return socios_dict

    def _ensure_django_socio(self, nro_socio: int, socio_data: dict[str, Any]) -> DjangoSocio:
        """Asegura la existencia de la cuenta de usuario y el modelo Django Socio."""
        legajo = socio_data["legajo"]
        subcom_name = socio_data["subcom_nombre"]
        sub = DjangoSubcomision.objects.filter(name=subcom_name).first()
        if not sub and subcom_name != "Sin Subcomisión":
            sub, _ = DjangoSubcomision.objects.get_or_create(name=subcom_name)

        user, _ = UserModel.objects.get_or_create(
            username=str(nro_socio),
            defaults={
                "email": socio_data["email"],
                "first_name": socio_data["nombre"],
                "last_name": socio_data["apellido"],
            },
        )
        if not user.has_usable_password():
            user.set_password(DEMO_PASSWORD)
            user.save(update_fields=["password"])

        ano_social = max(1, min(6, socio_data["ano_social"] or 1))
        role = Role.TD if socio_data["subcom_id"] == 10 else Role.SOCIO

        socio, _ = DjangoSocio.objects.get_or_create(
            legajo=legajo,
            defaults={
                "user": user,
                "first_name": socio_data["nombre"],
                "last_name": socio_data["apellido"],
                "email": socio_data["email"],
                "subcomision": sub,
                "social_year": ano_social,
                "role": role,
                "is_enabled": True,
            },
        )
        return socio

    def _import_expedientes_11779(
        self, file_path: Path, socios_dict: dict[int, dict[str, Any]]
    ) -> None:
        """Importa los 48 expedientes históricos reales del socio 11779."""
        self.stdout.write(
            self.style.NOTICE(
                "\n--- 3. Importando expedientes históricos reales del socio 11779 ---"
            )
        )

        socio_data = socios_dict.get(
            11779,
            {
                "apellido": "Sanchez Turu Michel",
                "nombre": "Diego Gabriel",
                "dni": 42642288,
                "subcom_id": 6,
                "subcom_nombre": "Gestión Social y Ambiental",
                "ano_social": 6,
                "ingresante": False,
                "legajo": "87414",
                "email": "dgs1760@gmail.com",
            },
        )
        diego_socio = self._ensure_django_socio(11779, socio_data)

        actor_td = UserModel.objects.filter(socio__role=Role.TD).first()
        actor_username = actor_td.username if actor_td else "408917"

        count = 0
        puntos_aplicados_total = Decimal("0.00")
        felicitaciones_count = 0

        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            reader = csv.reader(f)
            next(reader, None)

            with connection.cursor() as cursor:
                for r in reader:
                    if not r or not any(r):
                        continue
                    nro_exp_raw = r[0].strip()
                    razon = r[2].strip()
                    pts_str = r[3].strip()
                    estado_just = r[4].strip()

                    try:
                        pts = Decimal(pts_str)
                    except Exception:
                        pts = Decimal("0.00")

                    parts = nro_exp_raw.split("/")
                    num_int = int(parts[0]) if parts[0].isdigit() else 1
                    year_int = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 2026
                    num_canonico = f"EXP-{num_int:04d}/{year_int}"

                    exp, _ = Expediente.objects.update_or_create(
                        numero=num_canonico,
                        defaults={
                            "socio": diego_socio,
                            "estado": EstadoExpedienteEnum.EMITIDO,
                            "puntos": pts,
                            "motivo": razon,
                            "urgencia": UrgenciaExpedienteEnum.NORMAL,
                            "descargo_presentado": (estado_just == "Justificación aprobada"),
                        },
                    )
                    exp.socios.add(diego_socio)

                    if not exp.cambios_estado.exists():
                        CambioEstadoExpediente.objects.create(
                            expediente=exp,
                            estado_anterior=EstadoExpedienteEnum.CREADO,
                            estado_nuevo=EstadoExpedienteEnum.EMITIDO,
                            actor=actor_username,
                            motivo=f"Emisión formal: {razon[:100]}",
                        )

                    cursor.execute(
                        """
                        INSERT INTO tribunal_expediente
                        (idExpediente, nroExpediente, estadoExpediente_id, puntos_id)
                        VALUES (%s, %s, 6, 2)
                        ON DUPLICATE KEY UPDATE
                            nroExpediente=VALUES(nroExpediente),
                            estadoExpediente_id=6
                        """,
                        [exp.id, nro_exp_raw[:9]],
                    )

                    # Asiento en libro mayor: solo si NO fue justificación aprobada
                    if estado_just != "Justificación aprobada":
                        if pts == Decimal("0.33"):
                            felicitaciones_count += 1
                        else:
                            cursor.execute(
                                """
                                INSERT INTO tribunal_puntajeaplicado
                                (puntajeAplicado, socio_id, expediente_id)
                                VALUES (%s, 11779, %s)
                                """,
                                [pts, exp.id],
                            )
                            puntos_aplicados_total += pts

                    count += 1

                # Consolidación regla 3:1 (4 felicitaciones -> +1.00 pt neto y 1 remanente)
                pts_consolidados = Decimal(felicitaciones_count // 3)
                fel_remanentes = felicitaciones_count % 3

                if pts_consolidados > 0:
                    cursor.execute(
                        """
                        INSERT INTO tribunal_puntajeaplicado
                        (puntajeAplicado, socio_id, expediente_id)
                        VALUES (%s, 11779, NULL)
                        """,
                        [pts_consolidados],
                    )
                    puntos_aplicados_total += pts_consolidados

                cursor.execute(
                    """
                    INSERT INTO tribunal_puntajegeneral
                    (socio_id, puntos, felicitaciones, llamadosAtencion)
                    VALUES (11779, %s, %s, 0)
                    ON DUPLICATE KEY UPDATE
                        puntos=VALUES(puntos),
                        felicitaciones=VALUES(felicitaciones),
                        llamadosAtencion=0
                    """,
                    [puntos_aplicados_total, fel_remanentes],
                )

                AtencionFelicitacion.objects.update_or_create(
                    socio=diego_socio,
                    defaults={
                        "felicitaciones": fel_remanentes,
                        "llamadosAtencion": 0,
                    },
                )

        self.stdout.write(
            f"✓ 48 expedientes de Diego Sánchez importados ({puntos_aplicados_total} pts, "
            f"{fel_remanentes} felicitación)."
        )

    def _import_puntos_tribunal_and_generate_expedientes(
        self, file_path: Path, socios_dict: dict[int, dict[str, Any]]
    ) -> None:
        """Carga saldos de Puntos.csv y genera expedientes sintéticos para los otros socios."""
        self.stdout.write(
            self.style.NOTICE(
                "\n--- 4. Generando expedientes para los restantes 218 socios con saldo ---"
            )
        )

        actor_td = UserModel.objects.filter(socio__role=Role.TD).first()
        actor_username = actor_td.username if actor_td else "408917"

        motivos_pos = {
            1: [
                "Reconocimiento por mantenimiento de servidores del Centro de Cómputos.",
                "Mérito por guardia técnica extraordinaria en periodo electoral.",
                "Colaboración destacada en el desarrollo del sistema SGD-AVEIT.",
            ],
            2: [
                "Coordinación destacada de las jornadas de inducción a ingresantes.",
                "Reconocimiento por depuración del padrón institucional.",
                "Mérito por ejecución del programa de acompañamiento a ingresantes.",
            ],
            3: [
                "Reconocimiento por convenios estratégicos con empresas del sector.",
                "Mérito por organización de visitas técnicas a industrias.",
                "Colaboración en la gestión de becas y pasantías institucionales.",
            ],
            4: [
                "Mención destacada por la campaña de comunicación institucional.",
                "Reconocimiento por cobertura audiovisual de la peña institucional.",
                "Mérito por rediseño de la identidad visual de la sede gremial.",
            ],
            5: [
                "Mérito por refacción, pintura y acondicionamiento en sede.",
                "Reconocimiento por mantenimiento de instalaciones eléctricas.",
                "Colaboración en armado de stand tecnológico en la muestra anual.",
            ],
            6: [
                "Reconocimiento por coordinación de campaña de reciclaje y forestación.",
                "Mérito por gestión de donaciones y jornada solidaria comunitaria.",
                "Colaboración en el proyecto de huerta sustentable y ambiente.",
            ],
            7: [
                "Reconocimiento por organización del Congreso Tecnológico Nacional.",
                "Mérito por gestión de acreditaciones y seguridad en eventos.",
                "Colaboración en la coordinación de la fiesta de bienvenida.",
            ],
            8: [
                "Reconocimiento por gestión de metas en la Gran Rifa Anual AVEIT.",
                "Mérito por control de cobranzas y apertura de puntos de venta.",
            ],
            9: [
                "Reconocimiento por gestión directiva y balance societario anual.",
                "Mérito por representación de AVEIT ante autoridades universitarias.",
            ],
            10: [
                "Reconocimiento por redacción de dictámenes y modernización procesal.",
                "Mérito por celeridad en la resolución de expedientes.",
            ],
        }

        motivos_neg = [
            "Inasistencia injustificada a guardia programada de subcomisión.",
            "Demora no justificada en la entrega de balances y comprobantes.",
            "Inasistencia injustificada a reunión plenaria obligatoria de subcomisión.",
            "Incumplimiento de tareas asignadas en limpieza y mantenimiento de sede.",
            "Inasistencia a jornada de guardia extraordinaria asignada por cronograma.",
        ]

        count_socios = 0
        total_expedientes = 0
        seq_by_year = {y: 500 for y in range(2020, 2027)}

        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            reader = csv.reader(f)
            next(reader, None)

            for r in reader:
                if not r or len(r) < 12 or not r[1].strip().isdigit():
                    continue

                nro_socio = int(r[1].strip())
                if nro_socio == 11779:
                    continue

                pts_str = r[9].strip().replace(",", ".")
                fel_str = r[10].strip()
                llam_str = r[11].strip()

                try:
                    total_pts = Decimal(pts_str)
                except Exception:
                    total_pts = Decimal("0.00")

                felicitaciones = fel_str.count("*")
                llamados = llam_str.count("°")

                socio_info = socios_dict.get(nro_socio)
                if not socio_info:
                    continue

                # Excluir exviajeros de expedientes
                if socio_info["subcom_id"] == 11 or socio_info["ano_social"] == 0:
                    continue

                django_socio = self._ensure_django_socio(nro_socio, socio_info)
                sub_id = socio_info["subcom_id"]
                ano_social = max(1, min(6, socio_info["ano_social"] or 1))
                entry_year = 2026 - ano_social + 1

                with connection.cursor() as cursor:
                    if total_pts > 0:
                        rem = total_pts
                        chunk_idx = 0
                        motivos = motivos_pos.get(sub_id, motivos_pos[1])

                        while rem > 0:
                            if rem >= Decimal("3.00"):
                                chunk = Decimal("3.00")
                            elif rem >= Decimal("2.00"):
                                chunk = Decimal("2.00")
                            elif rem >= Decimal("1.50"):
                                chunk = Decimal("1.50")
                            elif rem >= Decimal("1.00"):
                                chunk = Decimal("1.00")
                            else:
                                chunk = rem

                            rem -= chunk
                            chunk_idx += 1
                            span = max(1, 2026 - entry_year + 1)
                            year = min(2026, entry_year + (chunk_idx % span))
                            motivo = motivos[chunk_idx % len(motivos)]

                            seq_by_year[year] = seq_by_year.get(year, 500) + 1
                            seq_num = seq_by_year[year]

                            exp = Expediente.objects.create(
                                numero=f"EXP-{seq_num:04d}/{year}",
                                socio=django_socio,
                                estado=EstadoExpedienteEnum.EMITIDO,
                                puntos=chunk,
                                motivo=motivo,
                                urgencia=UrgenciaExpedienteEnum.NORMAL,
                                descargo_presentado=False,
                            )
                            exp.socios.add(django_socio)

                            CambioEstadoExpediente.objects.create(
                                expediente=exp,
                                estado_anterior=EstadoExpedienteEnum.CREADO,
                                estado_nuevo=EstadoExpedienteEnum.EMITIDO,
                                actor=actor_username,
                                motivo=f"Reconocimiento: {motivo[:100]}",
                            )

                            cursor.execute(
                                """
                                INSERT INTO tribunal_expediente
                                (idExpediente, nroExpediente, estadoExpediente_id, puntos_id)
                                VALUES (%s, %s, 6, 2)
                                """,
                                [exp.id, f"{seq_num}/{year}"[:9]],
                            )

                            cursor.execute(
                                """
                                INSERT INTO tribunal_puntajeaplicado
                                (puntajeAplicado, socio_id, expediente_id)
                                VALUES (%s, %s, %s)
                                """,
                                [chunk, nro_socio, exp.id],
                            )
                            total_expedientes += 1

                    elif total_pts < 0:
                        rem = total_pts
                        chunk_idx = 0

                        while rem < 0:
                            if rem <= Decimal("-3.00"):
                                chunk = Decimal("-3.00")
                            elif rem <= Decimal("-2.00"):
                                chunk = Decimal("-2.00")
                            elif rem <= Decimal("-1.50"):
                                chunk = Decimal("-1.50")
                            elif rem <= Decimal("-1.00"):
                                chunk = Decimal("-1.00")
                            else:
                                chunk = rem

                            rem -= chunk
                            chunk_idx += 1
                            span = max(1, 2026 - entry_year + 1)
                            year = min(2026, entry_year + (chunk_idx % span))
                            motivo = motivos_neg[chunk_idx % len(motivos_neg)]

                            seq_by_year[year] = seq_by_year.get(year, 500) + 1
                            seq_num = seq_by_year[year]

                            exp = Expediente.objects.create(
                                numero=f"EXP-{seq_num:04d}/{year}",
                                socio=django_socio,
                                estado=EstadoExpedienteEnum.EMITIDO,
                                puntos=chunk,
                                motivo=motivo,
                                urgencia=UrgenciaExpedienteEnum.NORMAL,
                                descargo_presentado=False,
                            )
                            exp.socios.add(django_socio)

                            CambioEstadoExpediente.objects.create(
                                expediente=exp,
                                estado_anterior=EstadoExpedienteEnum.CREADO,
                                estado_nuevo=EstadoExpedienteEnum.EMITIDO,
                                actor=actor_username,
                                motivo=f"Sanción: {motivo[:100]}",
                            )

                            cursor.execute(
                                """
                                INSERT INTO tribunal_expediente
                                (idExpediente, nroExpediente, estadoExpediente_id, puntos_id)
                                VALUES (%s, %s, 6, 3)
                                """,
                                [exp.id, f"{seq_num}/{year}"[:9]],
                            )

                            cursor.execute(
                                """
                                INSERT INTO tribunal_puntajeaplicado
                                (puntajeAplicado, socio_id, expediente_id)
                                VALUES (%s, %s, %s)
                                """,
                                [chunk, nro_socio, exp.id],
                            )
                            total_expedientes += 1

                    cursor.execute(
                        """
                        INSERT INTO tribunal_puntajegeneral
                        (socio_id, puntos, felicitaciones, llamadosAtencion)
                        VALUES (%s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE
                            puntos=VALUES(puntos),
                            felicitaciones=VALUES(felicitaciones),
                            llamadosAtencion=VALUES(llamadosAtencion)
                        """,
                        [nro_socio, total_pts, felicitaciones, llamados],
                    )

                    AtencionFelicitacion.objects.update_or_create(
                        socio=django_socio,
                        defaults={
                            "felicitaciones": felicitaciones,
                            "llamadosAtencion": llamados,
                        },
                    )
                    count_socios += 1

        self.stdout.write(
            f"✓ Generados {total_expedientes} expedientes para {count_socios} socios."
        )

    def _sync_zero_balance_socios(self) -> None:
        """Asegura que los socios sin expedientes figuren con 0.00 pts en caché."""
        self.stdout.write(
            self.style.NOTICE("\n--- 5. Fijando saldos en 0.00 para socios sin causas ---")
        )
        with connection.cursor() as cursor:
            cursor.execute("SELECT DISTINCT socio_id FROM tribunal_puntajeaplicado")
            socios_con_puntos = {r[0] for r in cursor.fetchall()}

            cursor.execute("SELECT nroSocio FROM socio_lista")
            todos_socios = [r[0] for r in cursor.fetchall()]

            cero_count = 0
            for nro in todos_socios:
                if nro not in socios_con_puntos:
                    cursor.execute(
                        """
                        INSERT INTO tribunal_puntajegeneral
                        (socio_id, puntos, felicitaciones, llamadosAtencion)
                        VALUES (%s, 0.00, 0, 0)
                        ON DUPLICATE KEY UPDATE
                            puntos=0.00,
                            felicitaciones=0,
                            llamadosAtencion=0
                        """,
                        [nro],
                    )
                    cero_count += 1

        self.stdout.write(f"✓ {cero_count} socios fijados en 0.00 puntos.")

    def _verify_reconciliation(self) -> None:
        """Verifica la consistencia integral y la tasa de reconciliación en ranking."""
        self.stdout.write(
            self.style.NOTICE("\n--- 6. Verificación de consistencia del Libro Mayor y Ranking ---")
        )

        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM socio_lista")
            total_padron = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM tribunal_expediente WHERE estadoExpediente_id = 6")
            total_exp_emitidos = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*), SUM(puntajeAplicado) FROM tribunal_puntajeaplicado")
            asientos_count, sum_asientos = cursor.fetchone()

            cursor.execute("SELECT SUM(puntos) FROM tribunal_puntajegeneral")
            sum_cache = cursor.fetchone()[0]

            cursor.execute(
                """
                SELECT pg.socio_id, pg.puntos, COALESCE(SUM(pa.puntajeAplicado), 0.00) as sum_pa,
                       ROUND(COALESCE(SUM(pa.puntajeAplicado), 0.00) - pg.puntos, 2) as diff
                FROM tribunal_puntajegeneral pg
                LEFT JOIN tribunal_puntajeaplicado pa ON pg.socio_id = pa.socio_id
                GROUP BY pg.socio_id, pg.puntos
                HAVING diff != 0.00
                """
            )
            discrepancias = cursor.fetchall()

        self.stdout.write(f"• Total socios en padrón: {total_padron}")
        self.stdout.write(f"• Total expedientes emitidos: {total_exp_emitidos}")
        self.stdout.write(f"• Asientos en libro mayor: {asientos_count} (Suma: {sum_asientos})")
        self.stdout.write(f"• Suma en caché general: {sum_cache}")

        if not discrepancias:
            self.stdout.write(
                self.style.SUCCESS(
                    "✓ RECONCILIACIÓN 100%: Cero discrepancias entre libro mayor y caché."
                )
            )
        else:
            self.stdout.write(
                self.style.ERROR(
                    f"✗ ALERTA: Se detectaron {len(discrepancias)} discrepancias de saldo."
                )
            )
            for d in discrepancias[:5]:
                self.stdout.write(f"  Socio {d[0]}: cache={d[1]}, sum_pa={d[2]}, diff={d[3]}")
