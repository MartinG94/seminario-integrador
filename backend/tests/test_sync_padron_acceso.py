"""Pruebas para la fórmula dinámica de año social por grupo y sync_padron_acceso."""

from pathlib import Path

import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

from core.services.padron_access_sync_service import (
    default_csv_dir,
    load_authorized_padron,
    sync_padron_access,
)
from padron.domain import (
    SocioCategoryEnum,
    group_number_for_social_year,
    social_year_for_group,
)
from padron.services import classify_category, classify_group
from socios.models import Role, SocialCategory, Socio

UserModel = get_user_model()

HEADER = (
    "Socios\n\n"
    "Orden,Número Socio,Ingresante,Apellido,Nombre,DNI,SubComision,Email,"
    "Teléfono,Instagram,Especialidad,Legajo\n"
)


class TestGroupSocialYearFormula:
    def test_2026_cohort_mapping(self) -> None:
        assert social_year_for_group(63, 2026) == 1
        assert social_year_for_group(62, 2026) == 2
        assert social_year_for_group(61, 2026) == 3
        assert social_year_for_group(60, 2026) == 4
        assert social_year_for_group(59, 2026) == 5
        assert social_year_for_group(58, 2026) == 6
        assert social_year_for_group(57, 2026) == 7

    def test_2027_and_2028_progression_for_g59(self) -> None:
        assert social_year_for_group(59, 2027) == 6
        assert classify_group(59, 2027) == SocioCategoryEnum.ACTIVE
        assert social_year_for_group(59, 2028) == 7
        assert classify_group(59, 2028) == SocioCategoryEnum.UNKNOWN

    def test_inverse_group_number_for_social_year(self) -> None:
        for sy in range(1, 7):
            grp = group_number_for_social_year(sy, 2026)
            assert social_year_for_group(grp, 2026) == sy

    def test_classify_category_statutory_cut_at_year_3(self) -> None:
        assert classify_category(1) == SocioCategoryEnum.PASSIVE
        assert classify_category(2) == SocioCategoryEnum.PASSIVE
        assert classify_category(3) == SocioCategoryEnum.ACTIVE
        assert classify_category(6) == SocioCategoryEnum.ACTIVE
        assert classify_category(7) == SocioCategoryEnum.UNKNOWN


@pytest.mark.django_db
class TestSyncPadronAcceso:
    def _write_csvs(self, tmp_path: Path) -> Path:
        def row(
            orden: int,
            nro: int,
            ing: str,
            ape: str,
            nom: str,
            dni: str,
            sub: str,
            email: str,
            leg: str,
        ) -> str:
            return f"{orden},{nro},{ing},{ape},{nom},{dni},{sub},{email},351,ig,Sistemas,{leg}"

        seniors = HEADER + "\n".join(
            [
                row(
                    1,
                    12604,
                    "si",
                    "Chiesa Gonzalez",
                    "Ramiro",
                    "46127547",
                    "Cómputos",
                    "ramichiesa@example.test",
                    "410766",
                ),
                row(
                    2,
                    11737,
                    "no",
                    "Cerda Gallego",
                    "Catalina",
                    "44000001",
                    "Tribunal de Disciplina",
                    "cata@example.test",
                    "86361",
                ),
                row(
                    3,
                    11779,
                    "no",
                    "Sanchez Turu Michel",
                    "Diego Gabriel",
                    "42642288",
                    "Gestión Social y Ambiental",
                    "diego@example.test",
                    '"87414, 420941"',
                ),
            ]
        )
        juniors = HEADER + "\n".join(
            [
                row(
                    1,
                    12795,
                    "si",
                    "fff",
                    "fff",
                    "123123123",
                    "Sin Subcomisión",
                    "franfigueroa1701@example.test",
                    "97189",
                ),
                row(
                    2,
                    8123,
                    "no",
                    "Acosta De La Fuente",
                    "Gabriela Soledad",
                    "11111111",
                    "Sin Subcomisión",
                    "old@example.test",
                    "",
                ),
                row(
                    3,
                    12574,
                    "si",
                    "Baudino",
                    "Santiago",
                    "45000001",
                    "Sin Subcomisión",
                    "santi@example.test",
                    "416500",
                ),
                row(
                    4,
                    12349,
                    "no",
                    "Camaño",
                    "Franco David",
                    "44000002",
                    "Sin Subcomisión",
                    "franco@example.test",
                    "410155",
                ),
            ]
        )
        (tmp_path / "SeniorsActivos.csv").write_text(seniors, encoding="utf-8")
        (tmp_path / "JuniorsPasivos.csv").write_text(juniors, encoding="utf-8")
        return tmp_path

    def test_sync_enforces_exclusive_access_and_preserves_roles(
        self, tmp_path: Path, make_socio
    ) -> None:
        csv_dir = self._write_csvs(tmp_path)

        # Socio existente sin numero_socio pero con legajo coincidente y rol TD
        cata = make_socio(
            legajo="86361",
            email="cata.old@example.test",
            role=Role.TD,
            social_year=5,
            is_enabled=True,
        )
        # Cuenta demo o externa que no figura en los CSV
        outsider = make_socio(
            legajo="408917",
            numero_socio=408917,
            email="408917@aveit.test",
            role=Role.TD,
            social_year=6,
            is_enabled=True,
        )

        summary = sync_padron_access(csv_dir=csv_dir, reference_year=2026)

        assert summary["authorized_total"] == 5
        assert summary["excluded_test"] == 1
        assert summary["excluded_historical"] == 1
        assert summary["disabled"] == 1

        cata.refresh_from_db()
        assert cata.numero_socio == 11737
        assert cata.role == Role.TD
        assert cata.social_year == 6
        assert cata.category == SocialCategory.ACTIVE
        assert cata.is_enabled is True

        ramiro = Socio.objects.get(numero_socio=12604)
        assert ramiro.social_year == 3
        assert ramiro.category == SocialCategory.ACTIVE
        assert ramiro.is_enabled is True

        santiago = Socio.objects.get(numero_socio=12574)
        assert santiago.social_year == 1
        assert santiago.category == SocialCategory.PASSIVE

        franco = Socio.objects.get(numero_socio=12349)
        assert franco.social_year == 2
        assert franco.category == SocialCategory.PASSIVE

        assert not Socio.objects.filter(numero_socio=12795).exists()
        assert not Socio.objects.filter(numero_socio=8123).exists()

        outsider.refresh_from_db()
        assert outsider.is_enabled is False

        client = APIClient()
        denied = client.post("/api/v1/auth/login/", {"identifier": "408917"}, format="json")
        assert denied.status_code == status.HTTP_401_UNAUTHORIZED

        allowed = client.post("/api/v1/auth/login/", {"identifier": "12604"}, format="json")
        assert allowed.status_code == status.HTTP_200_OK
        assert allowed.data["user"]["category"] == SocialCategory.ACTIVE

    def test_real_groups_map_overrides_nro_socio_heuristic(self, tmp_path: Path) -> None:
        seniors = HEADER + "\n".join(
            [
                "1,12310,no,Paste Kvapil,Ignacio,1,Relaciones Institucionales,"
                "p@example.test,351,ig,Sistemas,95802",
                "2,11988,no,Ejemplo,G61,2,Cómputos,e@example.test,351,ig,Sistemas,400001",
            ]
        )
        juniors = HEADER + "\n".join(
            [
                "1,12789,si,Podversich,Uriel,3,Sin Subcomisión,"
                "u@example.test,351,ig,Sistemas,401056",
            ]
        )
        (tmp_path / "SeniorsActivos.csv").write_text(seniors, encoding="utf-8")
        (tmp_path / "JuniorsPasivos.csv").write_text(juniors, encoding="utf-8")
        (tmp_path / "grupos_reales_panel.csv").write_text(
            "Número Socio,Grupo,Estado\n12310,59,Activo\n11988,61,Activo\n12789,62,Pasivo\n",
            encoding="utf-8",
        )

        records, stats = load_authorized_padron(csv_dir=tmp_path, reference_year=2026)
        by_nro = {r.numero_socio: r for r in records}

        assert stats["resolved_from_real_groups"] == 3
        assert (by_nro[12310].group_number, by_nro[12310].social_year) == (59, 5)
        assert (by_nro[11988].group_number, by_nro[11988].social_year) == (61, 3)
        assert (by_nro[12789].group_number, by_nro[12789].social_year) == (62, 2)

    @pytest.mark.skipif(
        not (default_csv_dir() / "SeniorsActivos.csv").exists(),
        reason="CSVs reales locales no versionados por privacidad de datos personales",
    )
    def test_real_csvs_load_exact_450_authorized_socios(self) -> None:
        from collections import Counter

        records, stats = load_authorized_padron(reference_year=2026)
        assert len(records) == 450
        assert sum(1 for r in records if r.is_senior) == 219
        assert sum(1 for r in records if not r.is_senior) == 231
        assert stats["excluded_test"] == 1
        assert stats["excluded_historical"] == 31
        if (default_csv_dir() / "grupos_reales_panel.csv").exists():
            assert stats["resolved_from_real_groups"] == 450
            by_group = Counter(r.group_number for r in records)
            assert dict(sorted(by_group.items())) == {
                58: 41,
                59: 46,
                60: 47,
                61: 86,
                62: 78,
                63: 152,
            }
