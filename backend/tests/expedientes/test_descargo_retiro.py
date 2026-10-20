"""Pruebas de caracterización del retiro de descargos (SCRUM-49 / S3-05, tarea T1).

Fijan el comportamiento observable del endpoint ``DELETE /expedientes/<id>/descargo/``
antes de convertirlo en retiro lógico, de modo que el cambio no altere el contrato
que consumen SCRUM-48 y SCRUM-83:

1. Retiro dentro del plazo: respuesta 200 con el mensaje vigente, copias del expediente
   limpias, recálculo de ``descargo_presentado`` y registro en el historial de estados.
2. Retiro fuera de plazo: 409 sin modificar el descargo.
3. Retiro por quien no es parte del expediente: 403.
4. Lectura del descargo propio a través del detalle del expediente.
"""

from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from expedientes.models import (
    CambioEstadoExpediente,
    DescargoExpediente,
    EstadoExpedienteEnum,
    Expediente,
    TipoDescargoEnum,
)
from socios.models import Role, Socio, Subcomision

User = get_user_model()


def _crear_socio(legajo: str, nombre: str, subcomision: str) -> Socio:
    user = User.objects.create_user(
        username=legajo,
        email=f"{legajo}@aveit.test",
        password="secure_password_123",
    )
    sub, _ = Subcomision.objects.get_or_create(name=subcomision)
    return Socio.objects.create(
        user=user,
        legajo=legajo,
        first_name=nombre,
        last_name="Prueba",
        email=f"{legajo}@aveit.test",
        subcomision=sub,
        social_year=4,
        role=Role.SOCIO,
    )


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture
def socio_titular(db) -> Socio:
    return _crear_socio("74907", "Lucas", "Cómputos")


@pytest.fixture
def socio_ajeno(db) -> Socio:
    return _crear_socio("85194", "Martín", "Deportes")


def _expediente_con_descargo(socio: Socio, *, plazo_abierto: bool = True) -> Expediente:
    limite = timezone.now() + (timedelta(days=3) if plazo_abierto else -timedelta(minutes=1))
    exp = Expediente.objects.create(
        numero="EXP-301/2026",
        socio=socio,
        motivo="Caracterización del retiro",
        estado=EstadoExpedienteEnum.JUSTIFICANDO,
        plazo_inicio_at=timezone.now() - timedelta(days=1),
        plazo_limite_at=limite,
        descargo_presentado=True,
        descargo_tipo=TipoDescargoEnum.T03_EXTRAORDINARIO,
        descargo_causal="Otro",
        descargo_texto="Exposición de los hechos.",
        descargo_presentado_at=timezone.now(),
    )
    exp.socios.add(socio)
    DescargoExpediente.objects.create(
        expediente=exp,
        socio=socio,
        tipo=TipoDescargoEnum.T03_EXTRAORDINARIO,
        causal="Otro",
        texto="Exposición de los hechos.",
    )
    return exp


@pytest.mark.django_db(transaction=True)
class TestRetiroDescargoCaracterizacion:
    """El retiro actual debe conservar su contrato externo tras volverse lógico."""

    def test_retiro_dentro_del_plazo_responde_200_y_limpia_copias(
        self, api_client: APIClient, socio_titular: Socio
    ) -> None:
        exp = _expediente_con_descargo(socio_titular)
        api_client.force_authenticate(user=socio_titular.user)

        response = api_client.delete(f"/api/v1/expedientes/{exp.id}/descargo/")

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"detail": "Justificativo eliminado correctamente."}
        exp.refresh_from_db()
        assert exp.descargo_presentado is False
        assert exp.descargo_tipo == ""
        assert exp.descargo_causal == ""
        assert exp.descargo_archivo == ""
        assert exp.descargo_texto == ""
        assert exp.descargo_presentado_at is None

    def test_retiro_registra_cambio_en_el_historial_del_expediente(
        self, api_client: APIClient, socio_titular: Socio
    ) -> None:
        exp = _expediente_con_descargo(socio_titular)
        api_client.force_authenticate(user=socio_titular.user)

        api_client.delete(f"/api/v1/expedientes/{exp.id}/descargo/")

        cambio = CambioEstadoExpediente.objects.filter(expediente=exp).latest("id")
        assert cambio.actor == f"SOCIO_{socio_titular.legajo}"
        assert cambio.estado_anterior == cambio.estado_nuevo == EstadoExpedienteEnum.JUSTIFICANDO
        assert cambio.motivo == "Eliminación de descargo dentro del plazo reglamentario."

    def test_retiro_fuera_de_plazo_devuelve_409_y_no_modifica_el_descargo(
        self, api_client: APIClient, socio_titular: Socio
    ) -> None:
        exp = _expediente_con_descargo(socio_titular, plazo_abierto=False)
        api_client.force_authenticate(user=socio_titular.user)

        response = api_client.delete(f"/api/v1/expedientes/{exp.id}/descargo/")

        assert response.status_code == status.HTTP_409_CONFLICT
        assert "plazo perentorio" in response.json()["detail"]
        exp.refresh_from_db()
        assert exp.descargo_presentado is True
        assert DescargoExpediente.objects.filter(expediente=exp, socio=socio_titular).exists()

    def test_retiro_por_socio_ajeno_al_expediente_devuelve_403(
        self, api_client: APIClient, socio_titular: Socio, socio_ajeno: Socio
    ) -> None:
        exp = _expediente_con_descargo(socio_titular)
        api_client.force_authenticate(user=socio_ajeno.user)

        response = api_client.delete(f"/api/v1/expedientes/{exp.id}/descargo/")

        assert response.status_code == status.HTTP_403_FORBIDDEN
        exp.refresh_from_db()
        assert exp.descargo_presentado is True

    def test_retiro_de_expediente_inexistente_devuelve_404(
        self, api_client: APIClient, socio_titular: Socio
    ) -> None:
        api_client.force_authenticate(user=socio_titular.user)

        response = api_client.delete("/api/v1/expedientes/999999/descargo/")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_socio_titular_lee_su_descargo_en_el_detalle_del_expediente(
        self, api_client: APIClient, socio_titular: Socio
    ) -> None:
        exp = _expediente_con_descargo(socio_titular)
        api_client.force_authenticate(user=socio_titular.user)

        response = api_client.get(f"/api/v1/expedientes/{exp.id}/")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["descargo_presentado"] is True
        assert data["descargo_tipo"] == TipoDescargoEnum.T03_EXTRAORDINARIO
        assert data["descargo_texto"] == "Exposición de los hechos."
        assert [d["socio_id"] for d in data["descargos"]] == [socio_titular.id]
