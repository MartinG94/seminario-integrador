"""Pruebas del padrón: RF-06-WS (unicidad de legajo, categoría Pasivo/Activo)."""

import pytest
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError

from socios.models import Role, SocialCategory, Socio


@pytest.mark.parametrize(
    "social_year,expected",
    [
        (1, SocialCategory.PASSIVE),
        (2, SocialCategory.PASSIVE),
        (3, SocialCategory.PASSIVE),
        (4, SocialCategory.ACTIVE),
        (5, SocialCategory.ACTIVE),
        (6, SocialCategory.ACTIVE),
    ],
)
@pytest.mark.django_db
def test_category_is_derived_from_social_year(make_socio, social_year, expected):
    socio = make_socio(legajo=f"7000{social_year}", social_year=social_year)

    assert socio.category == expected


@pytest.mark.django_db
def test_category_is_independent_from_account_status(make_socio):
    """Constitución ppio. 8: la vigencia de la cuenta no surge de la categoría."""
    socio = make_socio(legajo="74907", social_year=5, is_enabled=False)

    assert socio.category == SocialCategory.ACTIVE
    assert socio.is_enabled is False


@pytest.mark.django_db
def test_legajo_is_unique(make_socio):
    make_socio(legajo="74907")

    with pytest.raises((IntegrityError, ValidationError)):
        make_socio(legajo="74907", email="otro@aveit.test")


@pytest.mark.django_db
def test_social_year_out_of_range_is_rejected(make_socio):
    with pytest.raises(ValidationError):
        make_socio(legajo="99999", social_year=7)


@pytest.mark.django_db
def test_default_role_is_socio(make_socio):
    socio = Socio.objects.get(pk=make_socio(legajo="74907").pk)

    assert socio.role == Role.SOCIO


@pytest.mark.django_db
def test_numero_socio_se_almacena_sin_reemplazar_legajo(make_socio):
    socio = make_socio(legajo="UTN-74907")
    socio.numero_socio = 74907
    socio.save()
    socio.refresh_from_db()

    assert socio.numero_socio == 74907
    assert socio.legajo == "UTN-74907"


@pytest.mark.django_db
def test_numero_socio_admite_null(make_socio):
    socio = make_socio(legajo="SIN-SOCIO")

    assert socio.numero_socio is None


@pytest.mark.django_db
def test_numero_socio_no_admite_duplicados(make_socio):
    primero = make_socio(legajo="74907", email="primero@example.test")
    primero.numero_socio = 74907
    primero.save()

    segundo = make_socio(legajo="85194", email="segundo@example.test")
    segundo.numero_socio = 74907
    with pytest.raises((IntegrityError, ValidationError)):
        segundo.save()


@pytest.mark.django_db
def test_numero_socio_no_modifica_la_pk_interna(make_socio):
    socio = make_socio(legajo="74907")
    pk = socio.pk
    socio.numero_socio = 74907
    socio.save()

    assert socio.pk == pk


@pytest.mark.django_db
def test_numero_socio_puede_coincidir_con_legajo_sin_ser_inferido(make_socio):
    socio = make_socio(legajo="74907")
    socio.numero_socio = 74907
    socio.save()

    assert socio.numero_socio == 74907
    assert socio.legajo == "74907"


@pytest.mark.django_db
def test_usuario_sin_numero_institucional_conserva_null(make_socio):
    socio = make_socio(legajo="LEGAJO-ACADEMICO")

    assert socio.numero_socio is None


@pytest.mark.django_db
def test_numero_socio_es_idempotente_en_ejecuciones_repetidas(make_socio):
    socio = make_socio(legajo="LEGAJO-IDEMPOTENTE")
    socio.numero_socio = 3003
    socio.save()
    socio.refresh_from_db()
    socio.save()
    socio.refresh_from_db()

    assert socio.numero_socio == 3003


@pytest.mark.django_db
def test_serializer_expone_numero_socio_y_legajo_como_solo_lectura(make_socio):
    from socios.serializers import SocioLegajoSerializer

    socio = make_socio(legajo="UTN-74907")
    socio.numero_socio = 74907
    socio.save()
    serializer = SocioLegajoSerializer(instance=socio)

    assert serializer.data["numero_socio"] == 74907
    assert serializer.data["legajo"] == "UTN-74907"
    assert serializer.fields["numero_socio"].read_only is True
