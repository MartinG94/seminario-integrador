from rest_framework.generics import ListAPIView

from accounts.permissions import IsTribunalOrDirectiva
from accounts.serializers import SocioProfileSerializer
from socios.models import Socio


class PadronListView(ListAPIView):
    """GET /api/v1/socios/ — nómina del padrón, restringida a TD, CD y ADMIN.

    La autorización se resuelve en el servidor: da igual si la SPA muestra u
    oculta el enlace, un socio ordinario que llame a esta URL recibe 403.
    """

    permission_classes = [IsTribunalOrDirectiva]
    serializer_class = SocioProfileSerializer
    queryset = Socio.objects.select_related("subcomision").filter(is_enabled=True)
