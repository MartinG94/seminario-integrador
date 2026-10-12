from django.contrib.auth import authenticate, get_user_model
from django.core.exceptions import ValidationError
from django.db.models import Q
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

from accounts import audit
from socios.models import Socio

UserModel = get_user_model()

# CA1: una única respuesta para todos los motivos de rechazo. No debe permitir
# distinguir si el legajo existe, si la contraseña es incorrecta o si la cuenta
# está deshabilitada. El motivo real sólo viaja a la pista de auditoría.
INVALID_CREDENTIALS_DETAIL = "Credenciales inválidas."


class LoginSerializer(serializers.Serializer):
    """RF-01-WS / RF-02-WS: autenticación por legajo o email (con o sin contraseña)."""

    identifier = serializers.CharField(write_only=True, trim_whitespace=True)
    password = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        default="",
        trim_whitespace=False,
        style={"input_type": "password"},
    )

    def _reject(self, identifier: str, reason_code: str):
        audit.log_authentication_failure(identifier=identifier, reason_code=reason_code)
        raise AuthenticationFailed(INVALID_CREDENTIALS_DETAIL)

    def validate(self, attrs: dict) -> dict:
        identifier = attrs["identifier"]
        password = attrs.get("password", "")

        user = UserModel.objects.filter(
            Q(username=identifier)
            | Q(email__iexact=identifier)
            | Q(socio__legajo=identifier)
            | Q(socio__email__iexact=identifier)
        ).first()

        if user is None:
            socio_obj = Socio.objects.filter(
                Q(legajo=identifier) | Q(email__iexact=identifier)
            ).first()
            if socio_obj is not None:
                if socio_obj.user is None:
                    user, _ = UserModel.objects.get_or_create(
                        username=socio_obj.legajo,
                        defaults={"email": socio_obj.email},
                    )
                    socio_obj.user = user
                    socio_obj.save(update_fields=["user"])
                else:
                    user = socio_obj.user

        if user is None:
            # Se ejecuta igual el hasher para que el tiempo de respuesta no
            # delate la existencia o inexistencia del usuario.
            if password:
                UserModel().set_password(password)
            self._reject(identifier, "USER_NOT_FOUND")

        # Si se envía contraseña no vacía, se valida con authenticate.
        # Si NO se envía contraseña, se permite el acceso directo por legajo para pruebas.
        if password and authenticate(username=user.get_username(), password=password) is None:
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

        audit.log_authentication_success(identifier=socio.legajo, role=socio.role)

        return {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": SocioProfileSerializer(socio).data,
        }


class SocioProfileSerializer(serializers.Serializer):
    """Perfil devuelto al autenticar. Nunca incluye credenciales ni tokens."""

    id = serializers.IntegerField(read_only=True)
    legajo = serializers.CharField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    email = serializers.EmailField()
    role = serializers.CharField()
    category = serializers.CharField()
    category_display = serializers.CharField(source="get_category_display")
    subcomision = serializers.CharField(source="subcomision.name", default=None)


class CurrentSocioRefreshToken(RefreshToken):
    """Conserva la validación JWT y lee la clasificación al emitir el access."""

    def verify(self) -> None:
        super().verify()
        user_id = self.get(api_settings.USER_ID_CLAIM)
        if user_id is None:
            raise AuthenticationFailed(INVALID_CREDENTIALS_DETAIL)
        try:
            UserModel.objects.get(**{api_settings.USER_ID_FIELD: user_id})
        except (
            UserModel.DoesNotExist,
            UserModel.MultipleObjectsReturned,
            TypeError,
            ValueError,
            ValidationError,
        ):
            raise AuthenticationFailed(INVALID_CREDENTIALS_DETAIL) from None

    @property
    def access_token(self) -> AccessToken:
        try:
            socio = Socio.objects.only("category").get(
                **{f"user__{api_settings.USER_ID_FIELD}": self[api_settings.USER_ID_CLAIM]}
            )
        except (Socio.DoesNotExist, Socio.MultipleObjectsReturned):
            raise AuthenticationFailed(INVALID_CREDENTIALS_DETAIL) from None
        self["category"] = socio.category
        return super().access_token


class CurrentSocioTokenRefreshSerializer(TokenRefreshSerializer):
    """Delega rotation, blacklist y opciones al serializador JWT instalado."""

    token_class = CurrentSocioRefreshToken
