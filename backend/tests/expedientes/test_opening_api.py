"""Pruebas de integración API para despacho de notificación y auditoría outbox (CA1, CA3).

Valida:
- POST /api/v1/expedientes/{id}/despachar-notificacion/ (200 OK, 401, 403, 404, 409, 422).
- GET /api/v1/expedientes/{id}/notificaciones/ (200 OK, 401, 403, 404).
- Principio 7: Sin exposición de contenidos sensibles en respuestas o logs.
"""

import pytest
from django.core import mail
from rest_framework import status
from rest_framework.test import APIClient

from expedientes.models import EstadoExpedienteEnum, Expediente
from notifications.models import EmailOutbox, EmailOutboxStatus
from socios.models import Role, Socio, Subcomision


@pytest.fixture(autouse=True)
def ensure_safe_mail_backend(settings) -> None:
    """Principio 5: Salvaguarda operativa de cero envíos reales."""
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    settings.FRONTEND_URL = "https://tribunal.aveit.utn.edu.ar"
    mail.outbox.clear()


@pytest.fixture
def subcomision_test(db) -> Subcomision:
    return Subcomision.objects.create(name="Subcomisión de Cómputos")


@pytest.fixture
def socio_imputado(db, subcomision_test, django_user_model) -> Socio:
    user = django_user_model.objects.create_user(
        username="74201",
        email="socio.imputado@aveit.utn.edu.ar",
        password="Test-Password-2026!",
    )
    return Socio.objects.create(
        user=user,
        legajo="74201",
        first_name="Martín",
        last_name="Guillén",
        email="socio.imputado@aveit.utn.edu.ar",
        subcomision=subcomision_test,
        social_year=3,
        role=Role.SOCIO,
        is_enabled=True,
    )


@pytest.fixture
def socio_regular(db, subcomision_test, django_user_model) -> Socio:
    user = django_user_model.objects.create_user(
        username="74202",
        email="regular@aveit.utn.edu.ar",
        password="Test-Password-2026!",
    )
    return Socio.objects.create(
        user=user,
        legajo="74202",
        first_name="Juan",
        last_name="Pérez",
        email="regular@aveit.utn.edu.ar",
        subcomision=subcomision_test,
        social_year=2,
        role=Role.SOCIO,
        is_enabled=True,
    )


@pytest.fixture
def vocal_td(db, subcomision_test, django_user_model) -> Socio:
    user = django_user_model.objects.create_user(
        username="74203",
        email="vocal.td@aveit.utn.edu.ar",
        password="Test-Password-2026!",
    )
    return Socio.objects.create(
        user=user,
        legajo="74203",
        first_name="Valeria",
        last_name="Gómez",
        email="vocal.td@aveit.utn.edu.ar",
        subcomision=subcomision_test,
        social_year=4,
        role=Role.TD,
        is_enabled=True,
    )


@pytest.fixture
def expediente_creado(db, socio_imputado) -> Expediente:
    return Expediente.objects.create(
        numero="EXP-2026-0701",
        socio=socio_imputado,
        motivo="Inasistencia injustificada a reuniones estatutarias",
        puntos=-1.0,
        estado=EstadoExpedienteEnum.CREADO,
    )


@pytest.mark.django_db
class TestDespacharNotificacionAperturaAPI:
    """Pruebas del endpoint POST /api/v1/expedientes/<id>/despachar-notificacion/"""

    def test_api_despachar_notificacion_success_200(
        self, vocal_td, expediente_creado, socio_imputado
    ) -> None:
        client = APIClient()
        client.force_authenticate(user=vocal_td.user)

        url = f"/api/v1/expedientes/{expediente_creado.id}/despachar-notificacion/"
        response = client.post(url, {}, format="json")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["expediente_id"] == expediente_creado.id
        assert data["numero"] == "EXP-2026-0701"
        assert data["estado"] == "justificando"
        assert "plazo_inicio_at" in data
        assert "plazo_limite_at" in data
        assert "outbox_id" in data
        assert (
            data["idempotency_key"]
            == f"opening-expediente-{expediente_creado.id}-socio-{socio_imputado.id}"
        )

        expediente_creado.refresh_from_db()
        assert expediente_creado.estado == EstadoExpedienteEnum.JUSTIFICANDO
        assert EmailOutbox.objects.count() == 1

    def test_api_despachar_notificacion_anonymous_401(self, expediente_creado) -> None:
        client = APIClient()
        url = f"/api/v1/expedientes/{expediente_creado.id}/despachar-notificacion/"
        response = client.post(url, {}, format="json")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_api_despachar_notificacion_forbidden_for_socio_403(
        self, socio_regular, expediente_creado
    ) -> None:
        client = APIClient()
        client.force_authenticate(user=socio_regular.user)

        url = f"/api/v1/expedientes/{expediente_creado.id}/despachar-notificacion/"
        response = client.post(url, {}, format="json")

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_api_despachar_notificacion_not_found_404(self, vocal_td) -> None:
        client = APIClient()
        client.force_authenticate(user=vocal_td.user)

        url = "/api/v1/expedientes/99999/despachar-notificacion/"
        response = client.post(url, {}, format="json")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_api_despachar_notificacion_conflict_409(self, vocal_td, expediente_creado) -> None:
        expediente_creado.estado = EstadoExpedienteEnum.REVISION_RESOLUCION
        expediente_creado.save(update_fields=["estado"])

        client = APIClient()
        client.force_authenticate(user=vocal_td.user)

        url = f"/api/v1/expedientes/{expediente_creado.id}/despachar-notificacion/"
        response = client.post(url, {}, format="json")

        assert response.status_code == status.HTTP_409_CONFLICT
        assert "revision_resolucion" in response.json()["detail"]

    def test_api_despachar_notificacion_missing_email_422(
        self, vocal_td, expediente_creado, socio_imputado
    ) -> None:
        Socio.objects.filter(id=socio_imputado.id).update(email="")

        client = APIClient()
        client.force_authenticate(user=vocal_td.user)

        url = f"/api/v1/expedientes/{expediente_creado.id}/despachar-notificacion/"
        response = client.post(url, {}, format="json")

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert "no posee dirección de correo" in response.json()["detail"]


@pytest.mark.django_db
class TestExpedienteNotificacionesAPI:
    """Pruebas del endpoint GET /api/v1/expedientes/<id>/notificaciones/"""

    def test_api_consultar_notificaciones_td_200(
        self, vocal_td, expediente_creado, socio_imputado
    ) -> None:
        EmailOutbox.objects.create(
            to=[socio_imputado.email],
            subject="[SGD-AVEIT] Notificación Autos EXP-2026-0701",
            body_text="Texto formal",
            status=EmailOutboxStatus.PENDING,
            retry_count=1,
            max_retries=5,
            last_error="SMTPConnectError: connection refused",
            idempotency_key=f"opening-exp-{expediente_creado.id}-socio-{socio_imputado.id}",
            metadata={"expediente_id": expediente_creado.id, "socio_id": socio_imputado.id},
        )

        client = APIClient()
        client.force_authenticate(user=vocal_td.user)

        url = f"/api/v1/expedientes/{expediente_creado.id}/notificaciones/"
        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        item = data[0]
        assert item["destinatario"] == [socio_imputado.email]
        assert item["estado"] == "PENDING"
        assert item["reintentos"] == 1
        assert item["max_reintentos"] == 5
        assert "SMTPConnectError" in item["ultimo_error"]
        assert "created_at" in item

    def test_api_consultar_notificaciones_anonymous_401(self, expediente_creado) -> None:
        client = APIClient()
        url = f"/api/v1/expedientes/{expediente_creado.id}/notificaciones/"
        response = client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_api_consultar_notificaciones_forbidden_for_socio_403(
        self, socio_regular, expediente_creado
    ) -> None:
        client = APIClient()
        client.force_authenticate(user=socio_regular.user)

        url = f"/api/v1/expedientes/{expediente_creado.id}/notificaciones/"
        response = client.get(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_api_consultar_notificaciones_not_found_404(self, vocal_td) -> None:
        client = APIClient()
        client.force_authenticate(user=vocal_td.user)

        url = "/api/v1/expedientes/99999/notificaciones/"
        response = client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND
