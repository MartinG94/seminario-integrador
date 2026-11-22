"""API de parámetros del sistema (Spec 011, T2 a T4): RBAC, validación y auditoría."""

from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from django.test import override_settings

from core.models import SystemParameterChange
from core.services.system_parameters import SystemParameterService
from expedientes.models import ParametroPlazoApelacion
from socios.models import Role

LIST_URL = "/api/v1/admin/parametros/"
ATTACHMENTS_URL = "/api/v1/parametros/adjuntos/"
APPEAL_URL = "/api/v1/expedientes/parametros/plazo-apelacion/"


def detail_url(clave: str) -> str:
    return f"{LIST_URL}{clave}/"


def history_url(clave: str) -> str:
    return f"{LIST_URL}{clave}/historial/"


@pytest.fixture
def admin_client(make_socio, authenticate):
    return authenticate(make_socio(legajo="403655", role=Role.ADMIN))


def by_key(response) -> dict:
    return {item["clave"]: item for item in response.data}


# --- RF-01: acceso exclusivo del ADMIN ---


@pytest.mark.django_db
def test_anonymous_request_is_rejected(api_client) -> None:
    assert api_client.get(LIST_URL).status_code == 401


@pytest.mark.parametrize("role", [Role.SOCIO, Role.FISCALIZADORA, Role.CD, Role.TD])
@pytest.mark.django_db
def test_non_admin_roles_get_403_on_every_admin_endpoint(make_socio, authenticate, role) -> None:
    client = authenticate(make_socio(legajo=f"30{role}", role=role))

    assert client.get(LIST_URL).status_code == 403
    assert client.get(history_url("plazo_descargo_dias_habiles")).status_code == 403
    response = client.put(detail_url("plazo_descargo_dias_habiles"), {"valor": 9}, format="json")
    assert response.status_code == 403
    assert not SystemParameterChange.objects.exists()


# --- RF-02: consulta ---


@pytest.mark.django_db
@override_settings(CD_EMAIL="cd@aveit.test", TRIBUNAL_EMAIL="tribunal@aveit.test")
def test_admin_lists_every_parameter_with_initial_values(admin_client) -> None:
    response = admin_client.get(LIST_URL)

    assert response.status_code == 200
    items = by_key(response)
    assert len(items) == 9
    plazo = items["plazo_descargo_dias_habiles"]
    assert plazo["valor"] == 5
    assert plazo["valor_inicial"] == 5
    assert (plazo["minimo"], plazo["maximo"]) == ("1", "30")
    assert plazo["categoria"] == "PLAZOS"
    assert plazo["editable"] is True
    assert plazo["actualizado_at"] is None
    assert plazo["actualizado_por"] == ""
    assert items["umbral_critico"]["valor"] == "-10.0"
    assert items["umbral_critico"]["editable"] is False
    assert items["umbral_preventivo"]["valor"] == "-7.0"
    assert items["umbral_preventivo_activo"]["valor"] is False
    assert items["email_comision_directiva"]["valor"] == "cd@aveit.test"
    assert items["email_tribunal_disciplina"]["valor"] == "tribunal@aveit.test"


# --- RF-03 / RF-04: modificación validada y auditada ---


@pytest.mark.django_db
def test_admin_updates_a_parameter_and_the_change_is_audited(admin_client) -> None:
    response = admin_client.put(
        detail_url("plazo_descargo_dias_habiles"), {"valor": 7}, format="json"
    )

    assert response.status_code == 200
    assert response.data["valor"] == 7
    assert response.data["valor_inicial"] == 5
    assert response.data["actualizado_por"] == "Apellido403655, Nombre (N° de socio s/n)"
    assert response.data["actualizado_at"] is not None
    registro = SystemParameterChange.objects.get()
    assert (registro.key, registro.value, registro.previous_value) == (
        "plazo_descargo_dias_habiles",
        7,
        5,
    )
    assert registro.author.get_username() == "403655"
    assert SystemParameterService.descargo_business_days() == 7


@pytest.mark.django_db
def test_each_change_inserts_a_new_record_and_history_lists_them(admin_client) -> None:
    for valor in (7, 10):
        admin_client.put(detail_url("plazo_descargo_dias_habiles"), {"valor": valor}, format="json")

    response = admin_client.get(history_url("plazo_descargo_dias_habiles"))

    assert response.status_code == 200
    assert [(c["valor"], c["valor_anterior"]) for c in response.data] == [(10, 7), (7, 5)]
    assert response.data[0]["autor"] == "Apellido403655, Nombre (N° de socio s/n)"
    assert SystemParameterChange.objects.count() == 2


@pytest.mark.parametrize(
    ("clave", "valor"),
    [
        ("plazo_descargo_dias_habiles", 0),
        ("plazo_descargo_dias_habiles", 31),
        ("plazo_descargo_dias_habiles", "cinco"),
        ("umbral_preventivo", "-10"),
        ("umbral_preventivo", "1"),
        ("umbral_preventivo_activo", "si"),
        ("email_tribunal_disciplina", "no-es-un-correo"),
        ("adjuntos_tamano_maximo_mb", 21),
        ("adjuntos_cantidad_maxima", 0),
        ("adjuntos_cantidad_maxima", None),
    ],
)
@pytest.mark.django_db
def test_invalid_values_are_rejected_without_recording(admin_client, clave, valor) -> None:
    response = admin_client.put(detail_url(clave), {"valor": valor}, format="json")

    assert response.status_code == 400
    assert isinstance(response.data["valor"][0], str)
    assert not SystemParameterChange.objects.exists()


@pytest.mark.django_db
def test_missing_value_and_unknown_key_are_rejected(admin_client) -> None:
    assert admin_client.put(detail_url("umbral_preventivo"), {}, format="json").status_code == 400
    assert (
        admin_client.put(detail_url("inexistente"), {"valor": 1}, format="json").status_code == 404
    )
    assert admin_client.get(history_url("inexistente")).status_code == 404


@pytest.mark.django_db
def test_audit_records_cannot_be_edited_or_deleted(admin_client) -> None:
    admin_client.put(detail_url("adjuntos_tamano_maximo_mb"), {"valor": 8}, format="json")
    registro = SystemParameterChange.objects.get()

    registro.value = 20
    with pytest.raises(ValidationError):
        registro.save()
    with pytest.raises(ValidationError):
        registro.delete()
    assert SystemParameterChange.objects.get().value == 8


# --- RF-05: umbral crítico reglamentario ---


@pytest.mark.django_db
def test_critical_threshold_cannot_be_modified(admin_client) -> None:
    response = admin_client.put(detail_url("umbral_critico"), {"valor": "-12"}, format="json")

    assert response.status_code == 400
    assert "reglamentario" in response.data["valor"][0]
    assert not SystemParameterChange.objects.exists()


@pytest.mark.django_db
def test_preventive_threshold_and_its_switch_are_configurable(admin_client) -> None:
    admin_client.put(detail_url("umbral_preventivo"), {"valor": "-8.5"}, format="json")
    response = admin_client.put(
        detail_url("umbral_preventivo_activo"), {"valor": True}, format="json"
    )

    assert response.status_code == 200
    assert SystemParameterService.preventive_threshold() == (Decimal("-8.5"), True)
    assert by_key(admin_client.get(LIST_URL))["umbral_preventivo"]["valor"] == "-8.5"


# --- Correos ---


@pytest.mark.django_db
@override_settings(TRIBUNAL_EMAIL="tribunal@aveit.test", COMISION_DIRECTIVA_EMAIL="cd2@aveit.test")
def test_configured_email_overrides_the_environment_value(admin_client) -> None:
    assert SystemParameterService.email("email_tribunal_disciplina") == "tribunal@aveit.test"
    assert (
        SystemParameterService.email("email_comision_directiva", fallback="cd2@aveit.test")
        == "cd2@aveit.test"
    )

    response = admin_client.put(
        detail_url("email_tribunal_disciplina"), {"valor": " TD@Aveit.test "}, format="json"
    )

    assert response.status_code == 200
    assert response.data["valor"] == "td@aveit.test"
    assert response.data["valor_inicial"] == "tribunal@aveit.test"
    assert SystemParameterService.email("email_tribunal_disciplina") == "td@aveit.test"
    assert SystemParameterService.email("email_tribunal_disciplina", fallback="x@y.zz") == (
        "td@aveit.test"
    )


# --- RF-08: plazo de apelación con una sola fuente ---


@pytest.mark.django_db
def test_appeal_deadline_is_shared_with_calendario(admin_client) -> None:
    response = admin_client.put(
        detail_url("plazo_apelacion_dias_habiles"), {"valor": 9}, format="json"
    )

    assert response.status_code == 200
    assert response.data["valor"] == 9
    assert ParametroPlazoApelacion.vigente() == 9
    assert not SystemParameterChange.objects.exists()
    assert admin_client.get(APPEAL_URL).data["dias_habiles"] == 9

    admin_client.put(APPEAL_URL, {"dias_habiles": 4}, format="json")

    assert by_key(admin_client.get(LIST_URL))["plazo_apelacion_dias_habiles"]["valor"] == 4
    historial = admin_client.get(history_url("plazo_apelacion_dias_habiles")).data
    assert [(c["valor"], c["valor_anterior"]) for c in historial] == [(4, 9), (9, 5)]


# --- RF-09: límites de adjuntos para cualquier usuario autenticado ---


@pytest.mark.django_db
def test_attachment_limits_are_readable_by_any_authenticated_socio(
    api_client, make_socio, authenticate
) -> None:
    assert api_client.get(ATTACHMENTS_URL).status_code == 401
    admin = authenticate(make_socio(legajo="403655", role=Role.ADMIN))
    admin.put(detail_url("adjuntos_tamano_maximo_mb"), {"valor": 8}, format="json")
    admin.put(detail_url("adjuntos_cantidad_maxima"), {"valor": 4}, format="json")

    socio = authenticate(make_socio(legajo="74907", role=Role.SOCIO))
    response = socio.get(ATTACHMENTS_URL)

    assert response.status_code == 200
    assert response.data == {"tamano_maximo_mb": 8, "cantidad_maxima": 4}
