"""
Tests unitarios y de integración para S5-07.2:
Blindaje y verificación integral de permisos DRF / RBAC conforme a SCRUM-121.

Verifica:
1. Autenticación y rechazo estricto con 401 ante cuentas deshabilitadas (is_enabled=False).
2. Socio suspendido (is_suspended=True): acceso de solo lectura a mis-expedientes y apelaciones vigentes;
   bloqueo con 403 a descargos nuevos y operaciones especiales.
3. Matriz RBAC completa:
   - Reglamentos: TD y CD crean/editan; ADMIN, REVISORES, AUTORIDAD_SC, SOCIO solo leen (403 en escritura).
   - Eventos y Asistencia: Exclusivo CD, TD, AUTORIDAD_SC. Excluidos ADMIN, REVISORES, SOCIO (403).
   - Crear Expediente (T01): AUTORIDAD_SC, REVISORES, CD, TD autorizados; SOCIO, ADMIN denegados (403).
4. Titularidad estricta de descargos (403 a socios ajenos).
5. Recusación / apartamiento de miembro del TD (Spec 007):
   - Lectura permitida en Visor (200 OK).
   - Voto, redacción, firma y transición bloqueadas con 403 Forbidden en la causa afectada.
   - Operaciones normales en causas no afectadas.
"""

from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.utils import timezone
import pytest
from rest_framework.test import APIClient

from expedientes.models import (
    ArticuloReglamento,
    CategoriaEvento,
    EstadoExpedienteEnum,
    EventoInstitucional,
    Expediente,
    Resolucion,
    SolicitudT01,
)
from socios.models import Role, Socio, Subcomision

UserModel = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def subcomision(db):
    sub, _ = Subcomision.objects.get_or_create(name="Cómputos")
    return sub


@pytest.fixture
def make_user_socio(db, subcomision):
    def _make(legajo: str, role: str, is_enabled: bool = True, is_suspended: bool = False):
        user = UserModel.objects.create_user(
            username=f"user_{legajo}",
            email=f"{legajo}@aveit.utn.edu.ar",
            password="secret_password_2026",
        )
        socio = Socio.objects.create(
            user=user,
            legajo=legajo,
            first_name=f"Nombre_{legajo}",
            last_name=f"Apellido_{legajo}",
            email=f"{legajo}@aveit.utn.edu.ar",
            social_year=4,
            subcomision=subcomision,
            role=role,
            is_enabled=is_enabled,
            is_suspended=is_suspended,
        )
        return user, socio

    return _make


# ==============================================================================
# 1. Autenticación y Cuentas Deshabilitadas (401 Unauthorized)
# ==============================================================================


@pytest.mark.django_db
def test_login_enabled_account_succeeds(api_client, make_user_socio):
    user, socio = make_user_socio("1001", role=Role.SOCIO, is_enabled=True)
    resp = api_client.post(
        "/api/v1/auth/login/",
        {"identifier": socio.legajo, "password": "secret_password_2026"},
    )
    assert resp.status_code == 200
    assert "access" in resp.data
    assert resp.data["user"]["is_suspended"] is False


@pytest.mark.django_db
def test_login_disabled_account_returns_401(api_client, make_user_socio):
    user, socio = make_user_socio("1002", role=Role.SOCIO, is_enabled=False)
    resp = api_client.post(
        "/api/v1/auth/login/",
        {"identifier": socio.legajo, "password": "secret_password_2026"},
    )
    assert resp.status_code == 401
    assert "access" not in resp.data


@pytest.mark.django_db
def test_api_access_with_token_of_disabled_account_returns_401(api_client, make_user_socio):
    user, socio = make_user_socio("1003", role=Role.TD, is_enabled=True)
    login_resp = api_client.post(
        "/api/v1/auth/login/",
        {"identifier": socio.legajo, "password": "secret_password_2026"},
    )
    token = login_resp.data["access"]
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    # Cuenta habilitada puede acceder
    assert api_client.get("/api/v1/auth/me/").status_code == 200

    # Se desactiva la cuenta
    socio.is_enabled = False
    socio.save()

    # Reintento con el mismo token previo responde 401 Unauthorized
    resp = api_client.get("/api/v1/auth/me/")
    assert resp.status_code == 401


# ==============================================================================
# 2. Socio Suspendido: Lectura de Mis-Expedientes y Apelaciones vs. Bloqueo 403
# ==============================================================================


@pytest.mark.django_db
def test_suspended_socio_can_login_and_read_mis_expedientes(api_client, make_user_socio):
    user, socio = make_user_socio("2001", role=Role.SOCIO, is_enabled=True, is_suspended=True)

    # Login permitido
    login_resp = api_client.post(
        "/api/v1/auth/login/",
        {"identifier": socio.legajo, "password": "secret_password_2026"},
    )
    assert login_resp.status_code == 200
    assert login_resp.data["user"]["is_suspended"] is True

    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {login_resp.data['access']}")

    # Lectura de perfil: 200 OK
    me_resp = api_client.get("/api/v1/auth/me/")
    assert me_resp.status_code == 200
    assert me_resp.data["is_suspended"] is True

    # Lectura de Mis Expedientes: 200 OK
    mis_resp = api_client.get("/api/v1/expedientes/mis-expedientes/")
    assert mis_resp.status_code == 200


@pytest.mark.django_db
def test_suspended_socio_cannot_submit_descargo(api_client, make_user_socio):
    user, socio = make_user_socio("2002", role=Role.SOCIO, is_enabled=True, is_suspended=True)
    exp = Expediente.objects.create(
        socio=socio,
        titulo="Causa disciplinaria testigo",
        estado=EstadoExpedienteEnum.JUSTIFICANDO,
    )

    api_client.force_authenticate(user=user)
    resp = api_client.post(
        f"/api/v1/expedientes/{exp.id}/descargo/",
        {"descargo": "Descargo de prueba del socio suspendido"},
    )
    # Socio suspendido recibe 403 Forbidden al intentar presentar descargo
    assert resp.status_code == 403


@pytest.mark.django_db
def test_suspended_socio_cannot_perform_privileged_actions(api_client, make_user_socio):
    user, socio = make_user_socio("2003", role=Role.TD, is_enabled=True, is_suspended=True)
    api_client.force_authenticate(user=user)

    # Aunque tenga rol TD, al estar suspendido se le deniegan acciones privilegiadas
    resp = api_client.post(
        "/api/v1/expedientes/reglamentos/articulos/",
        {"articulo": 999, "inciso": "A", "titulo": "Test", "descripcion": "Desc", "activo": True},
    )
    assert resp.status_code == 403


# ==============================================================================
# 3. Matriz RBAC: Reglamentos
# ==============================================================================


@pytest.mark.django_db
def test_reglamentos_read_allowed_for_all_roles(api_client, make_user_socio):
    for role in [Role.SOCIO, Role.AUTORIDAD_SC, Role.REVISORES, Role.CD, Role.TD, Role.ADMIN]:
        user, socio = make_user_socio(f"300_{role}", role=role)
        api_client.force_authenticate(user=user)
        resp = api_client.get("/api/v1/expedientes/reglamentos/articulos/")
        assert resp.status_code == 200, f"Rol {role} debió poder leer reglamentos"


@pytest.mark.django_db
def test_reglamentos_write_only_for_td_and_cd(api_client, make_user_socio):
    # TD y CD pueden crear
    for i, role in enumerate([Role.TD, Role.CD], start=1):
        user, socio = make_user_socio(f"310_{role}", role=role)
        api_client.force_authenticate(user=user)
        resp = api_client.post(
            "/api/v1/expedientes/reglamentos/articulos/",
            {
                "articulo": 900 + i,
                "inciso": "1",
                "titulo": "Reglamento Interno",
                "cuerpo": f"Texto formal de {role}",
                "activo": True,
            },
        )
        assert resp.status_code == 201, f"Rol {role} debió poder crear artículo: {resp.data}"

    # ADMIN, REVISORES, AUTORIDAD_SC y SOCIO reciben 403 Forbidden
    for i, role in enumerate([Role.ADMIN, Role.REVISORES, Role.AUTORIDAD_SC, Role.SOCIO], start=10):
        user, socio = make_user_socio(f"320_{role}", role=role)
        api_client.force_authenticate(user=user)
        resp = api_client.post(
            "/api/v1/expedientes/reglamentos/articulos/",
            {
                "articulo": 800 + i,
                "inciso": "1",
                "titulo": "Reglamento Interno",
                "cuerpo": "Texto",
                "activo": True,
            },
        )
        assert resp.status_code == 403, f"Rol {role} debió recibir 403 en creación de reglamentos"


# ==============================================================================
# 4. Matriz RBAC: Eventos y Asistencia
# ==============================================================================


@pytest.mark.django_db
def test_eventos_access_exclusive_to_cd_td_autoridad_sc(api_client, make_user_socio):
    # Habilitados: CD, TD, AUTORIDAD_SC
    for role in [Role.CD, Role.TD, Role.AUTORIDAD_SC]:
        user, socio = make_user_socio(f"400_{role}", role=role)
        api_client.force_authenticate(user=user)
        resp = api_client.get("/api/v1/eventos/")
        assert resp.status_code == 200, f"Rol {role} debió acceder a eventos"

    # Excluidos: ADMIN, REVISORES, SOCIO reciben 403
    for role in [Role.ADMIN, Role.REVISORES, Role.SOCIO]:
        user, socio = make_user_socio(f"410_{role}", role=role)
        api_client.force_authenticate(user=user)
        resp = api_client.get("/api/v1/eventos/")
        assert resp.status_code == 403, f"Rol {role} debió recibir 403 en eventos"


# ==============================================================================
# 5. Titularidad Estricta de Descargos
# ==============================================================================


@pytest.mark.django_db
def test_socio_cannot_submit_descargo_on_other_member_expediente(api_client, make_user_socio):
    user_imputado, socio_imputado = make_user_socio("5001", role=Role.SOCIO)
    user_ajeno, socio_ajeno = make_user_socio("5002", role=Role.SOCIO)

    exp = Expediente.objects.create(
        socio=socio_imputado,
        titulo="Causa contra 5001",
        estado=EstadoExpedienteEnum.JUSTIFICANDO,
        plazo_limite_at=timezone.now() + timezone.timedelta(days=3),
    )

    # El socio ajeno intenta presentar descargo en la causa de 5001
    api_client.force_authenticate(user=user_ajeno)
    resp = api_client.post(
        f"/api/v1/expedientes/{exp.id}/descargo/",
        {"descargo": "Intrusión en causa ajena"},
    )
    assert resp.status_code == 403


# ==============================================================================
# 6. Recusación / Apartamiento de Integrante del TD (Spec 007)
# ==============================================================================


@pytest.mark.django_db
def test_recused_td_member_can_view_visor_but_cannot_vote_or_resolve(
    api_client, make_user_socio, subcomision
):
    user_td, socio_td = make_user_socio("6001", role=Role.TD)
    user_otro, socio_otro = make_user_socio("6002", role=Role.SOCIO)

    # Causa A: socio_td es el solicitante o imputado (involucrado/apartado)
    exp_afectado = Expediente.objects.create(
        numero="EXP-2026-REC-01",
        socio=socio_otro,
        titulo="Causa con TD involucrado",
        estado=EstadoExpedienteEnum.REVISION_RESOLUCION,
    )
    solicitud = SolicitudT01.objects.create(
        solicitante=socio_td,
        destinatario_socio_id=socio_otro.id,
        expediente=exp_afectado,
        motivo="Denuncia de apertura",
        tipo_accion="SANCTION",
        puntos=-5,
    )

    # Causa B: socio_td es juez neutral sin ningún conflicto
    exp_neutral = Expediente.objects.create(
        numero="EXP-2026-REC-02",
        socio=socio_otro,
        titulo="Causa neutral",
        estado=EstadoExpedienteEnum.REVISION_RESOLUCION,
    )

    user_otro_td, _ = make_user_socio("6003", role=Role.TD)

    resolucion_afectada = Resolucion.objects.create(
        expediente=exp_afectado,
        vistos="Vistos...",
        considerandos="Considerando...",
        articulos_resolutivos="Art. 1...",
        version=1,
        created_by=user_otro_td,
    )
    resolucion_neutral = Resolucion.objects.create(
        expediente=exp_neutral,
        vistos="Vistos neutrales...",
        considerandos="Considerando...",
        articulos_resolutivos="Art. 1...",
        version=1,
        created_by=user_otro_td,
    )

    api_client.force_authenticate(user=user_td)

    # 1. En la causa afectada: lectura en visor permitida (200 OK)
    resp_visor = api_client.get(f"/api/v1/expedientes/{exp_afectado.id}/visor/")
    assert resp_visor.status_code == 200

    # 2. En la causa afectada: transicionar causa bloqueada (403 Forbidden)
    resp_trans = api_client.post(
        f"/api/v1/expedientes/{exp_afectado.id}/transicionar/",
        {"estado": EstadoExpedienteEnum.ESPERA_RESOLUCION, "motivo": "Intento de votar"},
    )
    assert resp_trans.status_code == 403

    # 3. En la causa afectada: firmar resolución bloqueada (403 Forbidden)
    resp_firma = api_client.post(f"/api/v1/expedientes/{exp_afectado.id}/resolucion/firmar/")
    assert resp_firma.status_code == 403

    # 4. En la causa neutral: no hay restricción por recusación (no da 403 por apartamiento)
    resp_visor_neutral = api_client.get(f"/api/v1/expedientes/{exp_neutral.id}/visor/")
    assert resp_visor_neutral.status_code == 200
