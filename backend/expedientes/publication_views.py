"""Saldo del socio y publicación oficial protegida (Spec 011, S5-02.2 y S5-02.3)."""

import ipaddress
import re

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import permissions, status
from rest_framework.exceptions import NotFound
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from expedientes.models import (
    AuditoriaConsultaExpediente,
    EstadoResolucionEnum,
    Expediente,
    Resolucion,
    TipoAccesoAuditoriaEnum,
)
from expedientes.permissions import IsImputadoOrTribunal
from expedientes.services.ledger_service import LedgerService
from expedientes.services.publication_service import (
    construir_publicacion,
    documento_pdf_publicado,
)
from expedientes.services.resolution_pdf import build_resolution_preview_pdf


class MiSaldoView(APIView):
    """GET /api/v1/expedientes/mis-expedientes/saldo/ — solo los datos del socio autenticado."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request: Request) -> Response:
        socio = getattr(request.user, "socio", None)
        if socio is None:
            raise NotFound("Tu usuario no tiene un perfil de socio asociado.")
        resumen = LedgerService.resumen_socio(socio)
        return Response(
            {
                "saldo": f"{resumen['saldo']:.2f}",
                "llamados_pendientes": resumen["llamados_pendientes"],
                "felicitaciones_pendientes": resumen["felicitaciones_pendientes"],
                "movimientos": [
                    {
                        **movimiento,
                        "fecha": movimiento["fecha"].isoformat(),
                        "puntos": f"{movimiento['puntos']:.2f}",
                    }
                    for movimiento in resumen["movimientos"]
                ],
            }
        )


class _PublicacionBaseView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsImputadoOrTribunal]

    def _publicacion(self, request: Request, expediente_id: int) -> dict:
        expediente = get_object_or_404(Expediente.objects.select_related("socio"), pk=expediente_id)
        self.check_object_permissions(request, expediente)
        resolucion = (
            Resolucion.objects.filter(expediente=expediente, estado=EstadoResolucionEnum.ISSUED)
            .select_related("expediente")
            .order_by("-version")
            .first()
        )
        if resolucion is None:
            raise NotFound("La resolución de este expediente todavía no fue publicada.")
        self._auditar(request, expediente, self.tipo_acceso)
        return construir_publicacion(resolucion, request.user)

    tipo_acceso = TipoAccesoAuditoriaEnum.CONSULTA

    @staticmethod
    def _auditar(request: Request, expediente: Expediente, tipo_acceso: str) -> None:
        ip_address = ip_cliente(request)
        user = request.user
        socio = getattr(user, "socio", None)
        legajo = str(socio.legajo) if socio and socio.legajo else ""
        rol = str(socio.role) if socio and socio.role else ("ADMIN" if user.is_staff else "USUARIO")
        AuditoriaConsultaExpediente.objects.create(
            expediente=expediente,
            usuario=user.username or legajo or str(user),
            legajo=legajo,
            rol=rol,
            tipo_acceso=tipo_acceso,
            ip_address=ip_address,
            user_agent=request.META.get("HTTP_USER_AGENT", "")[:500],
        )


class ResolucionPublicadaView(_PublicacionBaseView):
    """GET /api/v1/expedientes/<id>/resolucion/publicada/"""

    def get(self, request: Request, expediente_id: int) -> Response:
        return Response(self._publicacion(request, expediente_id), status=status.HTTP_200_OK)


class ResolucionPublicadaPdfView(_PublicacionBaseView):
    """GET /api/v1/expedientes/<id>/resolucion/publicada/pdf/"""

    tipo_acceso = TipoAccesoAuditoriaEnum.DESCARGA_PDF

    def get(self, request: Request, expediente_id: int) -> HttpResponse:
        publicacion = self._publicacion(request, expediente_id)
        response = HttpResponse(
            build_resolution_preview_pdf(documento_pdf_publicado(publicacion)),
            content_type="application/pdf",
        )
        response["Content-Disposition"] = (
            f'attachment; filename="{nombre_archivo_pdf(publicacion["expediente_numero"])}"'
        )
        response["X-Content-Type-Options"] = "nosniff"
        response["Cache-Control"] = "no-store"
        return response


def nombre_archivo_pdf(numero_expediente: str) -> str:
    """Nombre de archivo seguro: sólo letras, dígitos, guiones y guiones bajos."""
    seguro = re.sub(r"[^A-Za-z0-9_-]+", "-", numero_expediente or "").strip("-")
    return f"resolucion-{seguro or 'expediente'}.pdf"


def ip_cliente(request: Request) -> str | None:
    """IP del cliente validada; un `X-Forwarded-For` malformado no se guarda."""
    candidatos = []
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        candidatos.append(forwarded.split(",")[0].strip())
    candidatos.append(request.META.get("REMOTE_ADDR") or "")
    for candidato in candidatos:
        try:
            return str(ipaddress.ip_address(candidato))
        except ValueError:
            continue
    return None
