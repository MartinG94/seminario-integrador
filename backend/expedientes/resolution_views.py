from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import permissions, status
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from expedientes.models import CambioEstadoExpediente, EstadoExpedienteEnum, Expediente, Resolucion
from expedientes.permissions import CanTransitionExpedientes
from expedientes.resolution_serializers import (
    EnmiendaResolucionSerializer,
    ResolucionSerializer,
)
from expedientes.services.enmienda_service import EnmiendaService
from expedientes.services.resolution_pdf import build_resolution_preview_pdf
from expedientes.services.resolution_service import (
    DictamenNoCerradoError,
    ExpedienteConsolidatedDecisionProvider,
    emitir_resolucion,
    registrar_firma_resolucion,
)
from socios.models import Role


class ResolucionView(APIView):
    permission_classes = [permissions.IsAuthenticated, CanTransitionExpedientes]

    def get(self, request, expediente_id):
        resolucion = (
            Resolucion.objects.filter(expediente_id=expediente_id).order_by("-version").first()
        )
        if not resolucion:
            return Response(
                {"detail": "Resolución no encontrada."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(ResolucionSerializer(resolucion).data)

    @transaction.atomic
    def post(self, request, expediente_id):
        expediente = get_object_or_404(Expediente, pk=expediente_id)
        if Resolucion.objects.filter(expediente=expediente).exists():
            return Response(
                {"detail": "Ya existe una resolución para el expediente."},
                status=status.HTTP_409_CONFLICT,
            )
        serializer = ResolucionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        resolucion = serializer.save(
            expediente=expediente,
            created_by=request.user,
            numero_expediente_snapshot=expediente.numero,
        )

        if expediente.estado in (
            EstadoExpedienteEnum.REVISION_RESOLUCION,
            EstadoExpedienteEnum.ESPERA_RESOLUCION,
        ):
            estado_anterior = expediente.estado
            expediente.estado = EstadoExpedienteEnum.PENDIENTE_CORREOS
            expediente.save(update_fields=["estado", "updated_at"])
            actor_name = (
                request.user.username
                if getattr(request.user, "username", None)
                else str(request.user)
            )
            CambioEstadoExpediente.objects.create(
                expediente=expediente,
                estado_anterior=estado_anterior,
                estado_nuevo=EstadoExpedienteEnum.PENDIENTE_CORREOS,
                actor=actor_name,
                motivo="Resolución oficial generada y enviada a pendiente de firma.",
            )

        reglamentos = request.data.get("reglamentos_respaldantes")
        if isinstance(reglamentos, list):
            resolucion.reglamentos_respaldantes = reglamentos
            resolucion.save(update_fields=["reglamentos_respaldantes", "updated_at"])
            if hasattr(expediente, "solicitud_t01") and expediente.solicitud_t01:
                expediente.solicitud_t01.reglamentos_respaldantes = reglamentos
                expediente.solicitud_t01.save(
                    update_fields=["reglamentos_respaldantes", "updated_at"]
                )

        expedientes = request.data.get("expedientes_referenciados")
        if isinstance(expedientes, list):
            resolucion.expedientes_referenciados = expedientes
            resolucion.save(update_fields=["expedientes_referenciados", "updated_at"])

        data = request.data if isinstance(request.data, dict) else {}
        auto_firmar_raw = data.get("auto_firmar", True)
        if isinstance(auto_firmar_raw, str):
            auto_firmar = auto_firmar_raw.strip().lower() not in ("false", "0", "no")
        else:
            auto_firmar = bool(auto_firmar_raw)

        socio_user = getattr(request.user, "socio", None)
        es_td_activo = getattr(socio_user, "role", None) == Role.TD and getattr(
            socio_user, "is_active", True
        )
        if auto_firmar and (
            es_td_activo
            or getattr(request.user, "is_staff", False)
            or getattr(request.user, "is_superuser", False)
        ):
            es_suplente_raw = data.get("es_suplente")
            if es_suplente_raw is not None:
                if isinstance(es_suplente_raw, str):
                    es_suplente = es_suplente_raw.strip().lower() in ("true", "1", "yes")
                else:
                    es_suplente = bool(es_suplente_raw)
            else:
                es_suplente = None

            anio_social_raw = data.get("anio_social") or data.get("social_year")
            anio_social = None
            if anio_social_raw is not None:
                try:
                    anio_social = int(anio_social_raw)
                except (ValueError, TypeError):
                    anio_social = None

            try:
                resolucion = registrar_firma_resolucion(
                    resolucion,
                    request.user,
                    es_suplente=es_suplente,
                    anio_social=anio_social,
                )
            except ValidationError:
                pass

        return Response(ResolucionSerializer(resolucion).data, status=status.HTTP_201_CREATED)

    @transaction.atomic
    def patch(self, request, expediente_id):
        resolucion = (
            Resolucion.objects.filter(expediente_id=expediente_id).order_by("-version").first()
        )
        if not resolucion:
            return Response(
                {"detail": "Resolución no encontrada."},
                status=status.HTTP_404_NOT_FOUND,
            )
        if resolucion.estado == "ISSUED":
            return Response(
                {"detail": "Una resolución emitida es inmutable."},
                status=status.HTTP_409_CONFLICT,
            )
        serializer = ResolucionSerializer(resolucion, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        resolucion_guardada = serializer.save()

        expediente = resolucion.expediente
        if expediente and expediente.estado in (
            EstadoExpedienteEnum.REVISION_RESOLUCION,
            EstadoExpedienteEnum.ESPERA_RESOLUCION,
        ):
            estado_anterior = expediente.estado
            expediente.estado = EstadoExpedienteEnum.PENDIENTE_CORREOS
            expediente.save(update_fields=["estado", "updated_at"])
            actor_name = (
                request.user.username
                if getattr(request.user, "username", None)
                else str(request.user)
            )
            CambioEstadoExpediente.objects.create(
                expediente=expediente,
                estado_anterior=estado_anterior,
                estado_nuevo=EstadoExpedienteEnum.PENDIENTE_CORREOS,
                actor=actor_name,
                motivo="Resolución oficial generada y enviada a pendiente de firma.",
            )

        reglamentos = request.data.get("reglamentos_respaldantes")
        if isinstance(reglamentos, list):
            resolucion_guardada.reglamentos_respaldantes = reglamentos
            resolucion_guardada.save(update_fields=["reglamentos_respaldantes", "updated_at"])
            if hasattr(expediente, "solicitud_t01") and expediente.solicitud_t01:
                expediente.solicitud_t01.reglamentos_respaldantes = reglamentos
                expediente.solicitud_t01.save(
                    update_fields=["reglamentos_respaldantes", "updated_at"]
                )

        expedientes = request.data.get("expedientes_referenciados")
        if isinstance(expedientes, list):
            resolucion_guardada.expedientes_referenciados = expedientes
            resolucion_guardada.save(update_fields=["expedientes_referenciados", "updated_at"])

        return Response(ResolucionSerializer(resolucion_guardada).data)


class ResolucionFirmarView(APIView):
    permission_classes = [permissions.IsAuthenticated, CanTransitionExpedientes]

    def post(self, request, expediente_id):
        resolucion = (
            Resolucion.objects.filter(expediente_id=expediente_id).order_by("-version").first()
        )
        if not resolucion:
            return Response(
                {"detail": "Resolución no encontrada."},
                status=status.HTTP_404_NOT_FOUND,
            )

        data = request.data if isinstance(request.data, dict) else {}
        es_suplente_raw = data.get("es_suplente")
        if es_suplente_raw is not None:
            if isinstance(es_suplente_raw, str):
                es_suplente = es_suplente_raw.strip().lower() in ("true", "1", "yes")
            else:
                es_suplente = bool(es_suplente_raw)
        else:
            es_suplente = None

        anio_social_raw = data.get("anio_social") or data.get("social_year")
        anio_social = None
        if anio_social_raw is not None:
            try:
                anio_social = int(anio_social_raw)
            except (ValueError, TypeError):
                raise DRFValidationError(
                    {"anio_social": "El año social debe ser un número entero (4, 5 o 6)."}
                )

        try:
            resolucion = registrar_firma_resolucion(
                resolucion, request.user, es_suplente=es_suplente, anio_social=anio_social
            )
        except ValidationError as exc:
            msg = exc.message_dict if hasattr(exc, "message_dict") else exc.messages
            raise DRFValidationError(msg) from exc
        return Response(ResolucionSerializer(resolucion).data, status=status.HTTP_200_OK)


class ResolucionEmitirView(APIView):
    permission_classes = [permissions.IsAuthenticated, CanTransitionExpedientes]

    @transaction.atomic
    def post(self, request, expediente_id):
        resolucion = (
            Resolucion.objects.filter(expediente_id=expediente_id).order_by("-version").first()
        )
        if not resolucion:
            return Response(
                {"detail": "Resolución no encontrada."},
                status=status.HTTP_404_NOT_FOUND,
            )
        try:
            emitida = emitir_resolucion(
                resolucion, request.user, ExpedienteConsolidatedDecisionProvider()
            )
        except DictamenNoCerradoError as exc:
            raise DRFValidationError({"dictamen": str(exc)}) from exc
        return Response(ResolucionSerializer(emitida).data)


class ResolucionPreviewView(APIView):
    permission_classes = [permissions.IsAuthenticated, CanTransitionExpedientes]

    def get(self, request, expediente_id):
        resolucion = (
            Resolucion.objects.filter(expediente_id=expediente_id).order_by("-version").first()
        )
        if not resolucion:
            expediente = get_object_or_404(Expediente, pk=expediente_id)
            if expediente.estado != EstadoExpedienteEnum.EMITIDO:
                return Response(
                    {"detail": "Resolución no encontrada."},
                    status=status.HTTP_404_NOT_FOUND,
                )
            cambio_cierre = expediente.cambios_estado.filter(
                estado_nuevo=EstadoExpedienteEnum.EMITIDO
            ).first()
            considerando_fallback = (
                (cambio_cierre.motivo if cambio_cierre and cambio_cierre.motivo else "")
                or expediente.motivo
                or "Actuaciones administrativas finalizadas."
            )
            resolucion = Resolucion(
                expediente=expediente,
                version=1,
                plantilla_version="v1",
                estado="ISSUED",
                numero_expediente_snapshot=expediente.numero,
                vistos=(
                    f"Las actuaciones obrantes en el Expediente {expediente.numero} "
                    f"y las disposiciones reglamentarias vigentes de A.V.E.I.T."
                ),
                considerandos=considerando_fallback,
                articulos_resolutivos=(
                    "Artículo 1°: Téngase presente lo resuelto en las actuaciones "
                    f"con impacto de {expediente.puntos} puntos.\n\n"
                    "Artículo 2°: Notifíquese y archívese."
                ),
                puntos_finales=expediente.puntos,
                created_at=expediente.created_at,
                issued_at=cambio_cierre.fecha_hora if cambio_cierre else expediente.updated_at,
            )

        response = HttpResponse(
            build_resolution_preview_pdf(resolucion), content_type="application/pdf"
        )
        response["Content-Disposition"] = (
            f'inline; filename="resolucion-preview-{expediente_id}.pdf"'
        )
        return response


class EnmiendaResolucionView(APIView):
    permission_classes = [permissions.IsAuthenticated, CanTransitionExpedientes]

    @transaction.atomic
    def post(self, request, expediente_id):
        data = request.data if isinstance(request.data, dict) else {}
        motivo_enmienda = data.get("motivo_enmienda", "")
        considerandos = data.get("considerandos")
        articulos_resolutivos = data.get("articulos_resolutivos")
        nuevos_puntajes = data.get("nuevos_puntajes")

        try:
            enmienda, _ = EnmiendaService.solicitar_enmienda(
                expediente_id=expediente_id,
                user=request.user,
                motivo_enmienda=motivo_enmienda,
                considerandos=considerandos,
                articulos_resolutivos=articulos_resolutivos,
                nuevos_puntajes=nuevos_puntajes,
            )
        except ValidationError as exc:
            msg = exc.message_dict if hasattr(exc, "message_dict") else exc.messages
            raise DRFValidationError(msg) from exc

        return Response(
            EnmiendaResolucionSerializer(enmienda).data,
            status=status.HTTP_201_CREATED,
        )
