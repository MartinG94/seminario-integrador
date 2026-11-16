"""Pruebas del adaptador de solo lectura para la condición de Miembro Titular o Suplente (S4-03)."""

from datetime import date

import pytest
from django.contrib.auth.models import User

from expedientes.domain.ports import TribunalConditionPort
from expedientes.domain.t03_valuation import TribunalCondition
from padron.adapters import DbTribunalConditionProvider
from padron.models import Socio
from tests.legacy_schema import create_legacy_record

pytestmark = pytest.mark.django_db


def _member(username: str, nro_socio: int, position: int, fecha_baja: date | None = None) -> User:
    user = User.objects.create_user(username=username, password="pass-12345")
    create_legacy_record(
        Socio,
        nroSocio=nro_socio,
        apellido="Miembro",
        nombre=username,
        idTipoSocio=position,
        user_id=user.id,
        fechaBaja=fecha_baja,
    )
    return user


def test_satisfies_domain_port() -> None:
    assert isinstance(DbTribunalConditionProvider(), TribunalConditionPort)


def test_titular_member() -> None:
    user = _member("titular", 953001, 10)
    assert DbTribunalConditionProvider().condition_for_user(user.id) == TribunalCondition.TITULAR


def test_suplente_member() -> None:
    user = _member("suplente", 953002, 11)
    assert DbTribunalConditionProvider().condition_for_user(user.id) == TribunalCondition.SUPLENTE


def test_other_position_is_not_informed() -> None:
    user = _member("socio-comun", 953003, 1)
    assert (
        DbTribunalConditionProvider().condition_for_user(user.id) == TribunalCondition.NO_INFORMADA
    )


def test_user_without_padron_row_is_not_informed() -> None:
    user = User.objects.create_user(username="ad-hoc", password="pass-12345")
    assert (
        DbTribunalConditionProvider().condition_for_user(user.id) == TribunalCondition.NO_INFORMADA
    )


def test_member_with_fecha_baja_is_not_informed() -> None:
    user = _member("dado-de-baja", 953004, 10, fecha_baja=date(2026, 1, 1))
    assert (
        DbTribunalConditionProvider().condition_for_user(user.id) == TribunalCondition.NO_INFORMADA
    )


def test_lookup_does_not_write_padron() -> None:
    user = _member("solo-lectura", 953005, 11)
    before = list(Socio.objects.order_by("nroSocio").values())

    DbTribunalConditionProvider().condition_for_user(user.id)

    assert list(Socio.objects.order_by("nroSocio").values()) == before
