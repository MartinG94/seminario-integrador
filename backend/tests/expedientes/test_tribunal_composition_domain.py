"""Dominio puro de composición del Tribunal de Disciplina (S4-04, Spec 007)."""

from expedientes.domain.tribunal_composition import (
    ACTIVE_SOCIAL_YEARS,
    Condition,
    Member,
    compose,
    roster_issues,
)

T4 = Member(socio_id=1, social_year=4, condition=Condition.TITULAR, label="Titular 4")
S4 = Member(socio_id=2, social_year=4, condition=Condition.SUPLENTE, label="Suplente 4")
T5 = Member(socio_id=3, social_year=5, condition=Condition.TITULAR, label="Titular 5")
S5 = Member(socio_id=4, social_year=5, condition=Condition.SUPLENTE, label="Suplente 5")
T6 = Member(socio_id=5, social_year=6, condition=Condition.TITULAR, label="Titular 6")
S6 = Member(socio_id=6, social_year=6, condition=Condition.SUPLENTE, label="Suplente 6")
ROSTER = (T4, S4, T5, S5, T6, S6)


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
        assert roster_issues((S4, T5, S5, T6, S6)) == ["Falta el titular del 4.º año."]

    def test_falta_suplente_de_un_anio(self):
        assert roster_issues((T4, S4, T5, T6, S6)) == ["Falta el suplente del 5.º año."]

    def test_dos_titulares_del_mismo_anio(self):
        otro = Member(socio_id=9, social_year=6, condition=Condition.TITULAR, label="Otro")
        assert "Hay más de un titular del 6.º año." in roster_issues((*ROSTER, otro))

    def test_integrante_que_no_es_activo(self):
        pasivo = Member(socio_id=9, social_year=3, condition=Condition.TITULAR, label="Pasivo")
        assert "Pasivo no es socio Activo (4.º a 6.º año)." in roster_issues((*ROSTER, pasivo))

    def test_incompatibilidad_de_cargos_en_la_nomina(self):
        cd = Member(
            socio_id=1,
            social_year=4,
            condition=Condition.TITULAR,
            label="Titular 4",
            other_position="Comisión Directiva",
        )
        assert roster_issues((cd, S4, T5, S5, T6, S6)) == [
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


class TestSuplenciaAutomatica:
    def test_sin_involucrados_integran_los_titulares(self):
        composition = compose(ROSTER, involved_ids=set())
        assert seat_ids(composition) == {4: 1, 5: 3, 6: 5}
        assert composition.separated == ()
        assert composition.requires_ad_hoc is False
        assert composition.issues == ()

    def test_titular_involucrado_lo_reemplaza_su_suplente(self):
        composition = compose(ROSTER, involved_ids={T5.socio_id})
        assert seat_ids(composition) == {4: 1, 5: 4, 6: 5}
        seat5 = composition.seats[1]
        assert seat5.member == S5
        assert seat5.replaces == T5
        assert composition.separated == (T5,)
        assert composition.requires_ad_hoc is False

    def test_suplente_involucrado_no_altera_el_cuerpo(self):
        composition = compose(ROSTER, involved_ids={S6.socio_id})
        assert seat_ids(composition) == {4: 1, 5: 3, 6: 5}
        assert composition.separated == (S6,)
        assert composition.requires_ad_hoc is False

    def test_involucrados_ajenos_a_la_nomina_no_apartan_a_nadie(self):
        composition = compose(ROSTER, involved_ids={99, 100})
        assert composition.separated == ()

    def test_dos_titulares_de_distintos_anios_no_es_ad_hoc(self):
        composition = compose(ROSTER, involved_ids={T4.socio_id, T6.socio_id})
        assert seat_ids(composition) == {4: 2, 5: 3, 6: 6}
        assert composition.requires_ad_hoc is False


class TestCasosAdHoc:
    def test_caso_a_titular_y_suplente_del_mismo_anio(self):
        composition = compose(ROSTER, involved_ids={T5.socio_id, S5.socio_id})
        assert composition.requires_ad_hoc is True
        assert seat_ids(composition)[5] is None
        assert composition.ad_hoc_reasons == (
            "El titular y el suplente del 5.º año están involucrados en la causa "
            "(Art. 95 del Estatuto).",
        )

    def test_caso_b_tres_o_mas_integrantes_involucrados(self):
        composition = compose(ROSTER, involved_ids={T4.socio_id, T5.socio_id, S6.socio_id})
        assert composition.requires_ad_hoc is True
        assert composition.ad_hoc_reasons == (
            "3 integrantes del Tribunal están involucrados en la causa (Art. 95 del Estatuto).",
        )

    def test_casos_a_y_b_simultaneos(self):
        composition = compose(ROSTER, involved_ids={T4.socio_id, S4.socio_id, T6.socio_id})
        assert len(composition.ad_hoc_reasons) == 2
