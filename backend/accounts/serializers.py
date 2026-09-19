from django.contrib.auth import authenticate, get_user_model
from django.db.models import Q
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import RefreshToken

from accounts import audit

UserModel = get_user_model()

# CA1: una única respuesta para todos los motivos de rechazo. No debe permitir
# distinguir si el legajo existe, si la contraseña es incorrecta o si la cuenta
# está deshabilitada. El motivo real sólo viaja a la pista de auditoría.
INVALID_CREDENTIALS_DETAIL = "Credenciales inválidas."


class LoginSerializer(serializers.Serializer):
    """RF-01-WS / RF-02-WS: autenticación por legajo o email."""

    identifier = serializers.CharField(write_only=True, trim_whitespace=True)
    password = serializers.CharField(
        write_only=True, trim_whitespace=False, style={"input_type": "password"}
    )

    def _reject(self, identifier: str, reason_code: str):
        audit.log_authentication_failure(
            identifier=identifier, reason_code=reason_code
        )
        raise AuthenticationFailed(INVALID_CREDENTIALS_DETAIL)

    def validate(self, attrs: dict) -> dict:
        identifier = attrs["identifier"]
        password = attrs["password"]

        user = UserModel.objects.filter(
            Q(username=identifier)
            | Q(email__iexact=identifier)
            | Q(socio__legajo=identifier)
            | Q(socio__email__iexact=identifier)
        ).first()

        if user is None:
            # Se ejecuta igual el hasher para que el tiempo de respuesta no
            # delate la existencia o inexistencia del usuario.
            UserModel().set_password(password)
            self._reject(identifier, "USER_NOT_FOUND")

        if authenticate(username=user.get_username(), password=password) is None:
            self._reject(identifier, "BAD_PASSWORD")

        socio = getattr(user, "socio", None)
        if socio is None:
            self._reject(identifier, "NO_SOCIO_PROFILE")
        if not socio.is_enabled:
            self._reject(identifier, "ACCOUNT_DISABLED")

        refresh = RefreshToken.for_user(user)
        refresh["legajo"] = socio.legajo
        refresh["role"] = socio.role
        refresh["category"] = socio.category

        audit.log_authentication_success(
            identifier=socio.legajo, role=socio.role
        )

        return {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": SocioProfileSerializer(socio).data,
        }


class SocioProfileSerializer(serializers.Serializer):
    """Perfil devuelto al autenticar. Nunca incluye credenciales ni tokens."""

    legajo = serializers.CharField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    email = serializers.EmailField()
    role = serializers.CharField()
    category = serializers.CharField()
    category_display = serializers.CharField(source="get_category_display")
    subcomision = serializers.CharField(source="subcomision.name", default=None)
