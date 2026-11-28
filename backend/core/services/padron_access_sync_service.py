"""Sincronización del padrón oficial y control de acceso exclusivo (Seniors + Juniors).

Aplica las reglas estatutarias vigentes (2026+):
- Fórmula de cohorte: `social_year = (year - 1962) - group_number`.
- Categoría Pasivo (Junior): años 1–2 (en 2026: G63 y G62).
- Categoría Activo (Senior): años 3–6 (en 2026: G61, G60, G59 y G58).
- Acceso habilitado (`is_enabled=True`) únicamente para los socios vigentes presentes
  en `SeniorsActivos.csv` y `JuniorsPasivos.csv`, excluyendo registros de prueba/históricos.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import connection, transaction
from django.db.models import Q

from padron.domain import group_number_for_social_year, social_year_for_group
from socios.models import Role, Socio, Subcomision

UserModel = get_user_model()

EXCLUDED_TEST_SOCIO_NUMBERS: frozenset[int] = frozenset({12795})
MIN_VALID_JUNIOR_SOCIO_NUMBER: int = 12000

# Cohortes fijas documentadas en notasPO.md donde el N° de Socio no coincide con la banda base.
SENIOR_GROUP_OVERRIDES: dict[int, int] = {
    11779: 58,  # Diego Gabriel Sanchez Turu Michel (G58)
    11737: 58,  # Catalina Cerda Gallego (G58)
    11928: 58,  # Abril Gusella (G58)
    11735: 59,  # Candela Moreno Migliore (G59)
    12123: 60,  # Abril Sofia Moya (G60)
}

SUBCOMISION_ALIASES: dict[str, tuple[int, str]] = {
    "cómputos": (1, "Cómputos"),
    "computos": (1, "Cómputos"),
    "recursos humanos": (2, "Recursos Humanos"),
    "relaciones institucionales": (3, "Relaciones Institucionales"),
    "prensa": (4, "Prensa"),
    "prensa y difusión": (4, "Prensa"),
    "mantenimiento": (5, "Mantenimiento"),
    "gestión social y ambiental": (6, "Gestión Social y Ambiental"),
    "organización y eventos": (7, "Eventos"),
    "eventos": (7, "Eventos"),
    "rifas": (8, "Rifas"),
    "comisión directiva": (9, "Comisión Directiva"),
    "tribunal de disciplina": (10, "Tribunal de Disciplina"),
}


@dataclass(frozen=True)
class AuthorizedSocioRecord:
    """Registro normalizado de un socio autorizado a ingresar al sistema."""

    numero_socio: int
    first_name: str
    last_name: str
    email: str
    legajo: str
    subcomision_code: int
    subcomision_name: str
    ingresante: bool
    group_number: int
    social_year: int
    is_senior: bool


def default_csv_dir() -> Path:
    """Resuelve la carpeta que contiene SeniorsActivos.csv y JuniorsPasivos.csv."""
    candidates = [
        Path(settings.BASE_DIR).parent / "docs" / "analisis-proceso-actual" / "sistema-actual",
        Path("/docs/analisis-proceso-actual/sistema-actual"),
    ]
    for path in candidates:
        if path.exists():
            return path
    return candidates[0]


def resolve_subcomision(raw: str) -> tuple[int, str]:
    """Normaliza el nombre de subcomisión de los CSV hacia el catálogo institucional."""
    cleaned = (raw or "").strip()
    key = cleaned.lower()
    if key in SUBCOMISION_ALIASES:
        return SUBCOMISION_ALIASES[key]
    if key == "sin subcomisión" or not cleaned:
        return 99, "Sin Subcomisión"
    return 99, cleaned


def infer_group_number(
    *,
    nro_socio: int,
    ingresante: bool,
    is_senior: bool,
    reference_year: int,
) -> int:
    """Determina el número de grupo (cohorte) de un socio según categoría, ingresante y N°."""
    if not is_senior:
        return group_number_for_social_year(1 if ingresante else 2, reference_year)

    if ingresante:
        return group_number_for_social_year(3, reference_year)
    if nro_socio in SENIOR_GROUP_OVERRIDES:
        return SENIOR_GROUP_OVERRIDES[nro_socio]
    if nro_socio >= 12300:
        return group_number_for_social_year(3, reference_year)
    if nro_socio >= 12000:
        return group_number_for_social_year(4, reference_year)
    if nro_socio >= 11700:
        return group_number_for_social_year(5, reference_year)
    return group_number_for_social_year(6, reference_year)


def _read_csv_rows(csv_path: Path) -> list[dict[str, str]]:
    with csv_path.open("r", encoding="utf-8-sig", newline="") as fh:
        lines = fh.readlines()
    if len(lines) <= 2:
        return []
    return [row for row in csv.DictReader(lines[2:]) if (row.get("Número Socio") or "").strip()]


def load_authorized_padron(
    *,
    csv_dir: Path | None = None,
    reference_year: int | None = None,
) -> tuple[list[AuthorizedSocioRecord], dict[str, int]]:
    """Carga y depura el padrón autorizado desde SeniorsActivos.csv y JuniorsPasivos.csv."""
    base_dir = csv_dir or default_csv_dir()
    seniors_path = base_dir / "SeniorsActivos.csv"
    juniors_path = base_dir / "JuniorsPasivos.csv"
    if not seniors_path.exists():
        raise FileNotFoundError(f"No se encontró {seniors_path}")
    if not juniors_path.exists():
        raise FileNotFoundError(f"No se encontró {juniors_path}")

    year = reference_year if reference_year is not None else date.today().year
    records: list[AuthorizedSocioRecord] = []
    seen_nros: set[int] = set()
    stats = {
        "excluded_test": 0,
        "excluded_historical": 0,
        "excluded_out_of_cycle": 0,
    }

    for is_senior, path in ((True, seniors_path), (False, juniors_path)):
        for row in _read_csv_rows(path):
            raw_nro = (row.get("Número Socio") or "").strip()
            if not raw_nro.isdigit():
                continue
            nro_socio = int(raw_nro)

            if nro_socio in EXCLUDED_TEST_SOCIO_NUMBERS:
                stats["excluded_test"] += 1
                continue
            if not is_senior and nro_socio < MIN_VALID_JUNIOR_SOCIO_NUMBER:
                stats["excluded_historical"] += 1
                continue
            if nro_socio in seen_nros:
                continue

            ingresante = (row.get("Ingresante") or "").strip().lower() == "si"
            group_number = infer_group_number(
                nro_socio=nro_socio,
                ingresante=ingresante,
                is_senior=is_senior,
                reference_year=year,
            )
            social_year = social_year_for_group(group_number, year)
            if not (1 <= social_year <= 6):
                stats["excluded_out_of_cycle"] += 1
                continue

            legajo_raw = (row.get("Legajo") or "").strip()
            primary_legajo = legajo_raw.split(",")[0].strip() if legajo_raw else str(nro_socio)
            if not primary_legajo:
                primary_legajo = str(nro_socio)

            email = (row.get("Email") or "").strip() or f"{nro_socio}@aveit.test"
            sub_code, sub_name = resolve_subcomision(row.get("SubComision") or "")

            seen_nros.add(nro_socio)
            records.append(
                AuthorizedSocioRecord(
                    numero_socio=nro_socio,
                    first_name=(row.get("Nombre") or "").strip()[:100],
                    last_name=(row.get("Apellido") or "").strip()[:100],
                    email=email[:150],
                    legajo=primary_legajo[:20],
                    subcomision_code=sub_code,
                    subcomision_name=sub_name,
                    ingresante=ingresante,
                    group_number=group_number,
                    social_year=social_year,
                    is_senior=is_senior,
                )
            )

    return records, stats


def _reconcile_socio(record: AuthorizedSocioRecord) -> Socio | None:
    """Localiza el Socio existente por numero_socio, o por legajo/email si no tiene número."""
    socio = Socio.objects.filter(numero_socio=record.numero_socio).first()
    if socio is not None:
        return socio

    socio = Socio.objects.filter(legajo=record.legajo, numero_socio__isnull=True).first()
    if socio is not None:
        return socio

    return Socio.objects.filter(email__iexact=record.email, numero_socio__isnull=True).first()


def _release_conflicting_non_authorized(
    record: AuthorizedSocioRecord,
    authorized_nros: set[int],
    current_socio_id: int | None,
) -> None:
    """Libera legajo/email si pertenecen a una cuenta no autorizada que será deshabilitada."""
    conflict_filter = Q(legajo=record.legajo) | Q(email__iexact=record.email)
    qs = Socio.objects.filter(conflict_filter)
    if current_socio_id is not None:
        qs = qs.exclude(pk=current_socio_id)

    for conflict in qs:
        if conflict.numero_socio in authorized_nros:
            continue
        updates: list[str] = []
        if conflict.legajo == record.legajo:
            conflict.legajo = f"OLD-{conflict.pk}-{conflict.legajo}"[:20]
            updates.append("legajo")
        if conflict.email.lower() == record.email.lower():
            conflict.email = f"disabled+{conflict.pk}@invalid.aveit.local"[:150]
            updates.append("email")
        if conflict.is_enabled:
            conflict.is_enabled = False
            updates.append("is_enabled")
        if updates:
            conflict.save(update_fields=updates)


def _sync_legacy_tables(records: list[AuthorizedSocioRecord]) -> int:
    """Actualiza anoSocial e idGrupo en socio_lista / socio_estadoHistorial si existen."""
    tables = set(connection.introspection.table_names())
    if "socio_lista" not in tables:
        return 0

    updated_legacy = 0
    has_estado_hist = "socio_estadoHistorial" in tables
    has_grupo_lista = "grupo_lista" in tables
    with connection.cursor() as cursor:
        if has_grupo_lista:
            group_labels = {(rec.group_number, rec.social_year) for rec in records}
            for grp, sy in sorted(group_labels):
                cat_label = "Senior" if sy >= 3 else "Junior"
                desc = f"Grupo {grp} - {cat_label} {sy}ro"[:45]
                cursor.execute(
                    """
                    INSERT IGNORE INTO grupo_lista (nroGrupo, nombre, descripcion)
                    VALUES (%s, %s, %s)
                    """,
                    [grp, f"G{grp}"[:45], desc],
                )
        for rec in records:
            cursor.execute(
                """
                UPDATE socio_lista
                SET anoSocial = %s,
                    ingresante = %s
                WHERE nroSocio = %s
                """,
                [rec.social_year, 1 if rec.ingresante else 0, rec.numero_socio],
            )
            if cursor.rowcount:
                updated_legacy += 1

            if has_estado_hist:
                cursor.execute(
                    """
                    UPDATE socio_estadoHistorial
                    SET idGrupo = %s,
                        codEstadoSocio = 1
                    WHERE nroSocio = %s
                    ORDER BY fechaHora DESC, idEstadoHistorial DESC
                    LIMIT 1
                    """,
                    [rec.group_number, rec.numero_socio],
                )
    return updated_legacy


@transaction.atomic
def sync_padron_access(
    *,
    csv_dir: Path | None = None,
    reference_year: int | None = None,
) -> dict[str, Any]:
    """Sincroniza socios_socio y acceso exclusivo según SeniorsActivos + JuniorsPasivos."""
    records, filter_stats = load_authorized_padron(csv_dir=csv_dir, reference_year=reference_year)
    authorized_nros = {rec.numero_socio for rec in records}

    subcomisiones: dict[str, Subcomision] = {}
    for rec in records:
        if rec.subcomision_code != 99 and rec.subcomision_name not in subcomisiones:
            sub, _ = Subcomision.objects.get_or_create(name=rec.subcomision_name)
            subcomisiones[rec.subcomision_name] = sub

    created_count = 0
    updated_count = 0

    for rec in records:
        sub = subcomisiones.get(rec.subcomision_name)
        socio = _reconcile_socio(rec)
        _release_conflicting_non_authorized(
            rec, authorized_nros, socio.pk if socio is not None else None
        )

        if socio is None:
            user, _ = UserModel.objects.get_or_create(
                username=str(rec.numero_socio),
                defaults={
                    "email": rec.email,
                    "first_name": rec.first_name,
                    "last_name": rec.last_name,
                },
            )
            socio = Socio.objects.filter(user=user).first()

        if socio is None:
            role = Role.TD if rec.subcomision_code == 10 else Role.SOCIO
            Socio.objects.create(
                user=user,
                legajo=rec.legajo,
                numero_socio=rec.numero_socio,
                first_name=rec.first_name,
                last_name=rec.last_name,
                email=rec.email,
                subcomision=sub,
                social_year=rec.social_year,
                role=role,
                is_enabled=True,
            )
            created_count += 1
        else:
            socio.numero_socio = rec.numero_socio
            socio.legajo = rec.legajo
            socio.first_name = rec.first_name
            socio.last_name = rec.last_name
            socio.email = rec.email
            socio.subcomision = sub
            socio.social_year = rec.social_year
            socio.is_enabled = True
            socio.save()
            updated_count += 1

    disabled_count = (
        Socio.objects.filter(Q(numero_socio__isnull=True) | ~Q(numero_socio__in=authorized_nros))
        .filter(is_enabled=True)
        .update(is_enabled=False)
    )
    legacy_updated = _sync_legacy_tables(records)

    return {
        "authorized_total": len(records),
        "seniors_count": sum(1 for r in records if r.is_senior),
        "juniors_count": sum(1 for r in records if not r.is_senior),
        "created": created_count,
        "updated": updated_count,
        "disabled": disabled_count,
        "legacy_updated": legacy_updated,
        **filter_stats,
    }
