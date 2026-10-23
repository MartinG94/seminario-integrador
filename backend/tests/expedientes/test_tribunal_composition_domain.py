"""Dominio puro de composición del Tribunal de Disciplina (S4-04, Spec 007)."""

import pytest

from expedientes.domain.tribunal_composition import (
    ACTIVE_SOCIAL_YEARS,
    CompositionError,
    Condition,
    Member,
    SeparationCause,
    compose,
    roster_issues,
    validate_conflict_grounds,
    validate_designation,
)

T4 = Member(socio_id=1, social_year=4, condition=Condition.TITULAR, label="Titular 4")
S4 = Member(socio_id=2, social_year=4, condition=Condition.SUPLENTE, label="Suplente 4")
T5 = Member(socio_id=3, social_year=5, condition=Condition.TITULAR, label="Titular 5")
S5 = Member(socio_id=4, social_year=5, condition=Condition.SUPLENTE, label="Suplente 5")
T6 = Member(socio_id=5, social_year=6, condition=Condition.TITULAR, label="Titular 6")
S6 = Member(socio_id=6, social_year=6, condition=Condition.SUPLENTE, label="Suplente 6")
ROSTER = (T4, S4, T5, S5, T6, S6)


def ad_hoc(socio_id: int, social_year: int, **kwargs) -> Member:
    return Member(
        socio_id=socio_id,
        social_year=social_year,
        condition=Condition.AD_HOC,
        label=f"Ad hoc {socio_id}",
        **kwargs,
    )


def seat_ids(composition) -> dict[int, int | None]:
    return {
        seat.social_year: seat.member.socio_id if seat.member else None
        for seat in composition.seats
    }


class TestNomina:
    def test_nomina_completa_no_tiene_observaciones(self):
        assert roster_issues(ROSTER) == []
        assert ACTIVE_SOCIAL_YEARS == (4, 5, 6)

    def test_falta_titular_de_un_anio(self):
        issues = roster_issues((S4, T5, S5, T6, S6))
        assert issues == ["Falta el titular del 4.º año."]

    def test_falta_suplente_de_un_anio(self):
        assert roster_issues((T4, S4, T5, T6, S6)) == ["Falta el suplente del 5.º año."]

    def test_dos_titulares_del_mismo_anio(self):
        otro = Member(socio_id=9, social_year=6, condition=Condition.TITULAR, label="Otro")
        assert "Hay más de un titular del 6.º año." in roster_issues((*ROSTER, otro))

    def test_integrante_que_no_es_activo(self):
        pasivo = Member(socio_id=9, social_year=3, condition=Condition.TITULAR, label="Pasivo")
        issues = roster_issues((*ROSTER, pasivo))
        assert "Pasivo no es socio Activo (4.º a 6.º año)." in issues

    def test_incompatibilidad_de_cargos_en_la_nomina(self):
        cd = Member(
            socio_id=1,
            social_year=4,
            condition=Condition.TITULAR,
            label="Titular 4",
            other_position="Comisión Directiva",
        )
        issues = roster_issues((cd, S4, T5, S5, T6, S6))
        assert issues == [
            "Titular 4 ocupa otro cargo (Comisión Directiva), "
            "incompatible con el Tribunal (Art. 92)."
        ]

    def test_integrante_sin_cuenta_habilitada(self):
        baja = Member(
            socio_id=2,
            social_year=4,
            condition=Condition.SUPLENTE,
            label="Suplente 4",
            enabled=False,
        )
        assert roster_issues((T4, baja, T5, S5, T6, S6)) == [
            "Suplente 4 no tiene la cuenta habilitada."
        ]


class TestSuplencia:
    def test_sin_involucrados_integran_los_tres_titulares(self):
        composition = compose(ROSTER, involved_ids=set(), conflict_ids=set(), replacements={})
        assert seat_ids(composition) == {4: 1, 5: 3, 6: 5}
        assert composition.ad_hoc is False
        assert composition.separations == {}
        assert composition.can_be_constituted

    def test_titular_involucrado_lo_reemplaza_su_suplente(self):
        composition = compose(ROSTER, involved_ids={3}, conflict_ids=set(), replacements={})
        assert seat_ids(composition) == {4: 1, 5: 4, 6: 5}
        assert composition.separations == {3: SeparationCause.INVOLVED}
        seat5 = next(s for s in composition.seats if s.social_year == 5)
        assert seat5.replaces == T5
        assert composition.ad_hoc is False
        assert composition.can_be_constituted

    def test_conflicto_declarado_tambien_activa_la_suplencia(self):
        composition = compose(ROSTER, involved_ids=set(), conflict_ids={5}, replacements={})
        assert seat_ids(composition) == {4: 1, 5: 3, 6: 6}
        assert composition.separations == {5: SeparationCause.CONFLICT}

    def test_involucramiento_prevalece_sobre_el_conflicto(self):
        composition = compose(ROSTER, involved_ids={1}, conflict_ids={1}, replacements={})
        assert composition.separations == {1: SeparationCause.INVOLVED}

    def test_suplente_involucrado_no_altera_el_cuerpo(self):
        composition = compose(ROSTER, involved_ids={2}, conflict_ids=set(), replacements={})
        assert seat_ids(composition) == {4: 1, 5: 3, 6: 5}
        assert composition.ad_hoc is False

    def test_socios_ajenos_a_la_nomina_no_se_apartan(self):
        composition = compose(ROSTER, involved_ids={99}, conflict_ids=set(), replacements={})
        assert composition.separations == {}


class TestTribunalAdHoc:
    def test_dos_involucrados_del_mismo_anio_exigen_ad_hoc(self):
        composition = compose(ROSTER, involved_ids={1, 2}, conflict_ids=set(), replacements={})
        assert composition.ad_hoc is True
        assert seat_ids(composition)[4] is None
        assert {m.socio_id for m in composition.pending_replacements} == {1, 2}
        assert not composition.can_be_constituted
        assert (
            "Falta designar por Asamblea el reemplazo ad hoc de Titular 4 (4.º año)."
            in composition.issues
        )

    def test_tres_involucrados_de_distintos_anios_exigen_ad_hoc(self):
        composition = compose(ROSTER, involved_ids={1, 3, 6}, conflict_ids=set(), replacements={})
        assert composition.ad_hoc is True
        assert {m.socio_id for m in composition.pending_replacements} == {1, 3, 6}

    def test_designados_del_mismo_anio_integran_el_tribunal_ad_hoc(self):
        replacements = {1: ad_hoc(41, 4), 2: ad_hoc(42, 4)}
        composition = compose(
            ROSTER, involved_ids={1, 2}, conflict_ids=set(), replacements=replacements
        )
        assert seat_ids(composition) == {4: 41, 5: 3, 6: 5}
        seat4 = next(s for s in composition.seats if s.social_year == 4)
        assert seat4.replaces == T4
        assert composition.pending_replacements == ()
        assert composition.can_be_constituted

    def test_en_ad_hoc_el_reemplazo_del_titular_precede_al_suplente(self):
        replacements = {1: ad_hoc(41, 4), 3: ad_hoc(43, 5), 6: ad_hoc(46, 6)}
        composition = compose(
            ROSTER, involved_ids={1, 3, 6}, conflict_ids=set(), replacements=replacements
        )
        assert seat_ids(composition) == {4: 41, 5: 43, 6: 5}

    def test_anio_sin_titular_ni_suplente_por_conflicto_exige_ad_hoc(self):
        composition = compose(ROSTER, involved_ids=set(), conflict_ids={5, 6}, replacements={})
        assert composition.ad_hoc is True
        assert {m.socio_id for m in composition.pending_replacements} == {5, 6}

    def test_reemplazos_se_ignoran_fuera_del_caso_ad_hoc(self):
        composition = compose(
            ROSTER, involved_ids={3}, conflict_ids=set(), replacements={3: ad_hoc(43, 5)}
        )
        assert seat_ids(composition)[5] == 4


class TestFundamentoConflicto:
    def test_fundamento_breve_se_rechaza(self):
        with pytest.raises(CompositionError, match="20 caracteres"):
            validate_conflict_grounds("Soy amigo")

    def test_fundamento_suficiente_se_acepta(self):
        validate_conflict_grounds("Comparto vivienda con el socio imputado.")


class TestDesignacionAdHoc:
    @pytest.fixture
    def composicion_ad_hoc(self):
        return compose(ROSTER, involved_ids={1, 2}, conflict_ids=set(), replacements={})

    def validar(self, composition, replaced, designee, involved=frozenset({1, 2})):
        validate_designation(
            composition=composition,
            replaced=replaced,
            designee=designee,
            roster=ROSTER,
            involved_ids=set(involved),
        )

    def test_designado_valido(self, composicion_ad_hoc):
        self.validar(composicion_ad_hoc, T4, ad_hoc(41, 4))

    def test_fuera_del_caso_ad_hoc_se_rechaza(self):
        composition = compose(ROSTER, involved_ids={1}, conflict_ids=set(), replacements={})
        with pytest.raises(CompositionError, match="Art. 95"):
            self.validar(composition, T4, ad_hoc(41, 4), involved={1})

    def test_integrante_que_no_requiere_reemplazo(self, composicion_ad_hoc):
        with pytest.raises(CompositionError, match="no requiere reemplazo"):
            self.validar(composicion_ad_hoc, T5, ad_hoc(45, 5))

    def test_designado_de_otro_anio_social(self, composicion_ad_hoc):
        with pytest.raises(CompositionError, match="mismo año social"):
            self.validar(composicion_ad_hoc, T4, ad_hoc(45, 5))

    def test_designado_involucrado_en_la_causa(self, composicion_ad_hoc):
        with pytest.raises(CompositionError, match="involucrado"):
            self.validar(composicion_ad_hoc, T4, ad_hoc(77, 4), involved={1, 2, 77})

    def test_designado_que_ya_integra_el_tribunal(self, composicion_ad_hoc):
        with pytest.raises(CompositionError, match="ya integra"):
            self.validar(composicion_ad_hoc, T4, ad_hoc(3, 4))

    def test_designado_con_cargo_incompatible(self, composicion_ad_hoc):
        designee = ad_hoc(41, 4, other_position="Tesorero")
        with pytest.raises(CompositionError, match="Art. 92"):
            self.validar(composicion_ad_hoc, T4, designee)

    def test_designado_sin_cuenta_habilitada(self, composicion_ad_hoc):
        with pytest.raises(CompositionError, match="habilitada"):
            self.validar(composicion_ad_hoc, T4, ad_hoc(41, 4, enabled=False))

    def test_designado_ya_designado_para_otro_integrante(self):
        composition = compose(
            ROSTER, involved_ids={1, 2}, conflict_ids=set(), replacements={1: ad_hoc(41, 4)}
        )
        with pytest.raises(CompositionError, match="ya integra"):
            self.validar(composition, S4, ad_hoc(41, 4))

    def test_no_existe_causa_de_recusacion(self):
        assert {cause.value for cause in SeparationCause} == {
            "INVOLUCRADO",
            "CONFLICTO_INTERES",
        }
