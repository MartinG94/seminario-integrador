"""Pruebas unitarias de seguridad y control de acceso RBAC por objeto (CA4).

Valida:
- CA4: Enlace seguro con autenticación forzada y permisos por objeto.
- 401 si el usuario es anónimo.
- 403 si un socio ordinario intenta acceder a causa ajena (con auditoría ACCESS_DENIED).
- 200/True si el socio es el imputado directo de la causa (con auditoría ACCESS_GRANTED).
- 200/True si el usuario integra TD, CD o ADMIN (con auditoría ACCESS_GRANTED).
"""

from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth.models import AnonymousUser

from expedientes.models import EstadoExpedienteEnum, Expediente
from expedientes.permissions import IsImputadoOrTribunal
from socios.models import Role, Socio, Subcomision


@pytest.fixture
def subcomision_test(db) -> Subcomision:
    return Subcomision.objects.create(name="Subcomisión de Cómputos")


@pytest.fixture
def socio_imputado(db, subcomision_test, django_user_model) -> Socio:
    user = django_user_model.objects.create_user(
        username="74101",
        email="imputado@aveit.utn.edu.ar",
        password="Test-Password-2026!",
    )
    return Socio.objects.create(
        user=user,
        legajo="74101",
        first_name="Martín",
        last_name="Guillén",
        email="imputado@aveit.utn.edu.ar",
        subcomision=subcomision_test,
        social_year=3,
        role=Role.SOCIO,
        is_enabled=True,
    )


@pytest.fixture
def socio_ajeno(db, subcomision_test, django_user_model) -> Socio:
    user = django_user_model.objects.create_user(
        username="74102",
        email="ajeno@aveit.utn.edu.ar",
        password="Test-Password-2026!",
    )
    return Socio.objects.create(
        user=user,
        legajo="74102",
        first_name="Lucas",
        last_name="Alvarez",
        email="ajeno@aveit.utn.edu.ar",
        subcomision=subcomision_test,
        social_year=2,
        role=Role.SOCIO,
        is_enabled=True,
    )


@pytest.fixture
def vocal_tribunal(db, subcomision_test, django_user_model) -> Socio:
    user = django_user_model.objects.create_user(
        username="74103",
        email="vocal.td@aveit.utn.edu.ar",
        password="Test-Password-2026!",
    )
    return Socio.objects.create(
        user=user,
        legajo="74103",
        first_name="Valeria",
        last_name="Gómez",
        email="vocal.td@aveit.utn.edu.ar",
        subcomision=subcomision_test,
        social_year=4,
        role=Role.TD,
        is_enabled=True,
    )


@pytest.fixture
def miembro_directiva(db, subcomision_test, django_user_model) -> Socio:
    user = django_user_model.objects.create_user(
        username="74104",
        email="cd@aveit.utn.edu.ar",
        password="Test-Password-2026!",
    )
    return Socio.objects.create(
        user=user,
        legajo="74104",
        first_name="Diego",
        last_name="Pérez",
        email="cd@aveit.utn.edu.ar",
        subcomision=subcomision_test,
        social_year=5,
        role=Role.CD,
        is_enabled=True,
    )


@pytest.fixture
def admin_user(db, subcomision_test, django_user_model) -> Socio:
    user = django_user_model.objects.create_user(
        username="74105",
        email="admin@aveit.utn.edu.ar",
        password="Test-Password-2026!",
    )
    return Socio.objects.create(
        user=user,
        legajo="74105",
        first_name="Admin",
        last_name="Root",
        email="admin@aveit.utn.edu.ar",
        subcomision=subcomision_test,
        social_year=5,
        role=Role.ADMIN,
        is_enabled=True,
    )


@pytest.fixture
def expediente_imputado(db, socio_imputado) -> Expediente:
    return Expediente.objects.create(
        numero="EXP-2026-0099",
        socio=socio_imputado,
        motivo="Inasistencia injustificada a comisiones",
        estado=EstadoExpedienteEnum.JUSTIFICANDO,
    )


@pytest.mark.django_db
class TestIsImputadoOrTribunalPermission:
    """Verifica las reglas de autorización RBAC por objeto del permiso IsImputadoOrTribunal."""

    def test_anonymous_user_has_permission_denied(self, expediente_imputado) -> None:
        perm = IsImputadoOrTribunal()
        request = MagicMock()
        request.user = AnonymousUser()

        assert perm.has_permission(request, None) is False

    @patch("accounts.audit.log_access_granted")
    def test_imputado_authorized_with_audit(
        self, mock_audit, socio_imputado, expediente_imputado
    ) -> None:
        perm = IsImputadoOrTribunal()
        request = MagicMock()
        request.user = socio_imputado.user
        request.path = f"/api/v1/expedientes/{expediente_imputado.id}/"

        assert perm.has_permission(request, None) is True
        assert perm.has_object_permission(request, None, expediente_imputado) is True

        mock_audit.assert_called_once_with(
            identifier="74101",
            role=Role.SOCIO,
            resource=request.path,
        )

    @patch("accounts.audit.log_access_denied")
    def test_other_socio_forbidden_with_security_audit(
        self, mock_audit_denied, socio_ajeno, expediente_imputado
    ) -> None:
        perm = IsImputadoOrTribunal()
        request = MagicMock()
        request.user = socio_ajeno.user
        request.path = f"/api/v1/expedientes/{expediente_imputado.id}/"

        assert perm.has_permission(request, None) is True
        assert perm.has_object_permission(request, None, expediente_imputado) is False

        mock_audit_denied.assert_called_once_with(
            identifier="74102",
            role=Role.SOCIO,
            resource=request.path,
        )

    @patch("accounts.audit.log_access_granted")
    def test_tribunal_member_authorized_for_any_case(
        self, mock_audit, vocal_tribunal, expediente_imputado
    ) -> None:
        perm = IsImputadoOrTribunal()
        request = MagicMock()
        request.user = vocal_tribunal.user
        request.path = f"/api/v1/expedientes/{expediente_imputado.id}/"

        assert perm.has_permission(request, None) is True
        assert perm.has_object_permission(request, None, expediente_imputado) is True

        mock_audit.assert_called_once_with(
            identifier="74103",
            role=Role.TD,
            resource=request.path,
        )

    @patch("accounts.audit.log_access_granted")
    def test_directiva_member_authorized(
        self, mock_audit, miembro_directiva, expediente_imputado
    ) -> None:
        perm = IsImputadoOrTribunal()
        request = MagicMock()
        request.user = miembro_directiva.user
        request.path = f"/api/v1/expedientes/{expediente_imputado.id}/"

        assert perm.has_permission(request, None) is True
        assert perm.has_object_permission(request, None, expediente_imputado) is True

        mock_audit.assert_called_once_with(
            identifier="74104",
            role=Role.CD,
            resource=request.path,
        )

    @patch("accounts.audit.log_access_granted")
    def test_admin_member_authorized(self, mock_audit, admin_user, expediente_imputado) -> None:
        perm = IsImputadoOrTribunal()
        request = MagicMock()
        request.user = admin_user.user
        request.path = f"/api/v1/expedientes/{expediente_imputado.id}/"

        assert perm.has_permission(request, None) is True
        assert perm.has_object_permission(request, None, expediente_imputado) is True

        mock_audit.assert_called_once_with(
            identifier="74105",
            role=Role.ADMIN,
            resource=request.path,
        )

    @patch("accounts.audit.log_access_denied")
    def test_disabled_imputado_rejected_with_audit(
        self, mock_audit_denied, socio_imputado, expediente_imputado
    ) -> None:
        socio_imputado.is_enabled = False
        socio_imputado.save(update_fields=["is_enabled"])

        perm = IsImputadoOrTribunal()
        request = MagicMock()
        request.user = socio_imputado.user
        request.path = f"/api/v1/expedientes/{expediente_imputado.id}/"

        assert perm.has_object_permission(request, None, expediente_imputado) is False
        mock_audit_denied.assert_called_once_with(
            identifier="74101",
            role=Role.SOCIO,
            resource=request.path,
        )
