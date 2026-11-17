"""
Autenticación personalizada para SGD-AVEIT.

Diferenciación de estados operativos:
- is_enabled=False (cesanteado / baja definitiva): bloquea el acceso mediante
  credenciales a la API, respondiendo 401 Unauthorized.
"""

from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication


class SocioJWTAuthentication(JWTAuthentication):
    """
    Extiende JWTAuthentication de SimpleJWT para validar el estado operativo
    del socio en cada petición protegida.

    Si el socio tiene `is_enabled=False`, levanta AuthenticationFailed lo que
    provoca que DRF responda con HTTP 401 Unauthorized.
    """

    def get_user(self, validated_token):
        user = super().get_user(validated_token)
        socio = getattr(user, "socio", None)
        if socio is not None and not socio.is_enabled:
            raise AuthenticationFailed(
                "La cuenta del socio se encuentra deshabilitada o cesanteada.",
                code="account_disabled",
            )
        return user
