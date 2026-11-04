"""Nómina del Tribunal leída del padrón legado `socio_lista` (S4-04, CA1/CA5)."""

import pytest

from expedientes.domain.tribunal_composition import Condition
from expedientes.services.tribunal_roster import LegacyTribunalRosterAdapter
from socios.models import Role
from tests.expedientes.conftest import CARGO_TITULAR_TD

pytestmark = pytest.mark.django_db


def test_nomina_titulares_y_suplentes_por_anio(tribunal_nomina):
    roster = LegacyTribunalRosterAdapter().load(current_year=2026)

    assert roster.issues == []
    by_socio = {entry.socio.id: entry for entry in roster.entries}
    assert len(by_socio) == 6
    t5 = by_socio[tribunal_nomina["t5"].id]
    assert t5.member.condition == Condition.TITULAR
    assert t5.member.social_year == 5
    assert t5.nro_socio == 81005
    assert t5.grupo == "G59"
    assert by_socio[tribunal_nomina["s4"].id].member.condition == Condition.SUPLENTE


def test_socios_ordinarios_no_integran_la_nomina(tribunal_nomina, make_legacy_socio):
    make_legacy_socio(90001, 5)
    assert len(LegacyTribunalRosterAdapter().load().entries) == 6


def test_integrante_con_baja_no_integra_la_nomina(tribunal_nomina):
    from datetime import date

    from padron.models import Socio as LegacySocio
    from tests.legacy_schema import create_legacy_record

    create_legacy_record(
        LegacySocio,
        nroSocio=81099,
        apellido="Baja",
        nombre="Socio",
        anoSocial=4,
        idTipoSocio=CARGO_TITULAR_TD,
        fechaBaja=date(2026, 1, 1),
    )
    assert len(LegacyTribunalRosterAdapter().load().entries) == 6


def test_integrante_sin_cuenta_local_se_informa(make_legacy_socio):
    make_legacy_socio(81004, 4, CARGO_TITULAR_TD, Role.TD, linked=False)
    roster = LegacyTribunalRosterAdapter().load()
    assert roster.entries == []
    assert roster.issues == [
        "El integrante N° 81004 del padrón no tiene cuenta habilitada en el sistema."
    ]


def test_integrante_con_rol_de_comision_directiva_es_incompatible(make_legacy_socio):
    make_legacy_socio(81004, 4, CARGO_TITULAR_TD, Role.CD)
    (entry,) = LegacyTribunalRosterAdapter().load().entries
    assert entry.member.other_position == "Comisión Directiva"


def test_anio_social_se_deriva_del_grupo_y_no_del_campo_estatico(make_legacy_socio):
    # El legado informa anoSocial=3 desactualizado, pero G58 es 6.º año en 2026.
    make_legacy_socio(81006, 3, CARGO_TITULAR_TD, Role.TD, grupo=58)
    (entry,) = LegacyTribunalRosterAdapter().load(current_year=2026).entries
    assert entry.member.social_year == 6
    assert entry.grupo == "G58"


def test_sin_grupo_registrado_se_usa_el_anio_social_del_padron(make_legacy_socio):
    make_legacy_socio(81004, 4, CARGO_TITULAR_TD, Role.TD)
    (entry,) = LegacyTribunalRosterAdapter().load(current_year=2026).entries
    assert entry.member.social_year == 4
    assert entry.grupo == ""
