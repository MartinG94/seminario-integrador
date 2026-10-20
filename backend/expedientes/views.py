"""Vistas API REST para expedientes y descargos reglamentarios."""

from datetime import timedelta

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from expedientes.domain.calendar import compute_business_deadline
from expedientes.domain.causal_resolution import CausalDecision
from expedientes.domain.evidence_validator import EvidenceValidationError, EvidenceValidator
from expedientes.domain.holiday_provider import DbHolidayProvider
from expedientes.filters import ExpedienteFilter
from expedientes.models import (
    CambioEstadoExpediente,
    DescargoExpediente,
    DescargoVersion,
    EstadoExpedienteEnum,
    EvidenciaDescargo,
    Expediente,
    Holiday,
    OperacionDescargoEnum,
    SolicitudT01,
    UrgenciaExpedienteEnum,
)
from expedientes.permissions import (
    CanCreateT01,
    CanManageCalendar,
    CanOpenExpedientes,
    CanResolveCausal,
    CanTransitionExpedientes,
    IsImputadoOrTribunal,
    IsTribunalOrDirectiva,
)
from expedientes.serializers import (
    AperturaExpedienteSerializer,
    CalcularPlazoSerializer,
    CalendarQuerySerializer,
    CaseNotificationAuditSerializer,
    DecisionCausalSerializer,
    DescargoVersionSerializer,
    DispatchNotificationResponseSerializer,
    EmitirT01Serializer,
    EvidenciaMetadataSerializer,
    ExpedienteListSerializer,
    HolidaySerializer,
    MisSolicitudesT01Serializer,
    PresentarDescargoSerializer,
    RegistrarDecisionCausalSerializer,
    SolicitudT01Serializer,
    TransicionExpedienteSerializer,
    UpdateUrgenciaExpedienteSerializer,
)
from expedientes.services.board_service import build_board_payload
from expedientes.services.causal_resolution_service import (
    CausalResolutionNotFound,
    CausalResolutionService,
    CausalResolutionStateError,
    CausalResolutionValidationError,
)
from expedientes.services.descargo_version_service import DescargoVersionService
from expedientes.services.evidence_service import EvidenceService
from expedientes.services.opening_notification_service import (
    CaseNotificationQueryService,
    InvalidCaseStatusError,
    MissingSocioEmailError,
    OpeningNotificationService,
)
from expedientes.services.workflow_service import ExpedienteWorkflowService
from padron.models import SocioEstudio
from socios.models import Role, Socio


def _actor_for_user(user) -> str:
    return user.get_username()


# Relaciones que lee ExpedienteListSerializer; compartidas para evitar N+1 (S4-02).
EXPEDIENTE_LIST_PREFETCH = (
    "socios",
    "cambios_estado",
    "descargos__socio",
    "descargos__decisiones_causal__autor",
    "evidencias__socio",
)


class ExpedienteCollectionView(APIView):
    permission_classes = [CanOpenExpedientes]

    def get(self, request: Request) -> Response:
        queryset = Expediente.objects.select_related(
            "socio",
            "socio__subcomision",
            "solicitud_t01",
            "solicitud_t01__solicitante",
        ).prefetch_related(*EXPEDIENTE_LIST_PREFETCH)

        # SCRUM-82: el legajo puede corresponder al socio principal o a cualquiera
        # de los socios involucrados/adicionales.
        legajo = request.query_params.get("legajo")
        if legajo is not None and legajo.strip():
            legajo = legajo.strip()
            padron_user_ids = SocioEstudio.objects.filter(
                nroLegajo=legajo,
                socio__user_id__isnull=False,
            ).values("socio__user_id")
            local_socio_ids = Socio.objects.filter(
                user_id__in=padron_user_ids,
            ).values("pk")
            queryset = queryset.filter(
                Q(socio__legajo=legajo)
                | Q(socios__legajo=legajo)
                | Q(socio_id__in=local_socio_ids)
                | Q(socios__id__in=local_socio_ids)
            ).distinct()
        return Response(
            ExpedienteListSerializer(queryset, many=True, context={"request": request}).data
        )

    def post(self, request: Request) -> Response:
        serializer = AperturaExpedienteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            expediente = ExpedienteWorkflowService.open_expediente(
                motivo=serializer.validated_data["motivo"],
                socio_ids=serializer.validated_data["socios"],
                actor=_actor_for_user(request.user),
                urgencia=serializer.validated_data.get("urgencia", UrgenciaExpedienteEnum.NORMAL),
            )
        except IntegrityError as exc:
            raise DRFValidationError("No se pudo asignar el nÃºmero de expediente.") from exc
        expediente = (
            Expediente.objects.select_related("socio", "socio__subcomision")
            .prefetch_related(*EXPEDIENTE_LIST_PREFETCH)
            .get(pk=expediente.pk)
        )
        return Response(
            ExpedienteListSerializer(expediente, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class TransicionExpedienteView(APIView):
    permission_classes = [CanTransitionExpedientes]

    def post(self, request: Request, pk: int) -> Response:
        serializer = TransicionExpedienteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            expediente = ExpedienteWorkflowService.transition(
                expediente_id=pk,
                estado_nuevo=serializer.validated_data["estado"],
                actor=_actor_for_user(request.user),
                motivo=serializer.validated_data["motivo"],
            )
        except Expediente.DoesNotExist as exc:
            raise NotFound("Expediente no encontrado.") from exc
        except ValidationError as exc:
            raise DRFValidationError(
                exc.message_dict if hasattr(exc, "message_dict") else exc.messages
            )
        expediente = (
            Expediente.objects.select_related("socio", "socio__subcomision")
            .prefetch_related(*EXPEDIENTE_LIST_PREFETCH)
            .get(pk=expediente.pk)
        )
        return Response(ExpedienteListSerializer(expediente, context={"request": request}).data)


class MisExpedientesView(APIView):
    """Retorna la lista de expedientes asignados al socio autenticado."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request: Request) -> Response:
        socio = getattr(request.user, "socio", None)
        if not socio:
            return Response([], status=status.HTTP_200_OK)

        queryset = (
            Expediente.objects.filter(Q(socio=socio) | Q(socios=socio))
            .distinct()
            .select_related("socio", "socio__subcomision")
            .prefetch_related(*EXPEDIENTE_LIST_PREFETCH)
        )
        serializer = ExpedienteListSerializer(queryset, many=True, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class PresentarDescargoView(APIView):
    """Endpoint para presentaciÃ³n de descargo reglamentario (CA2 y buzzer-beater CA5).

    Regla:
    - EvaluaciÃ³n de plazo en el servidor con select_for_update().
    - Acepta si now <= plazo_limite_at (inclusivo).
    - Rechaza con 409 Conflict si now > plazo_limite_at.
    - Mientras el plazo siga abierto, un nuevo envÃ­o corrige el descargo ya presentado
      (Notas del PO, Ã­tem 31) y responde 200 OK en lugar de 201 Created.
    - Valida titularidad del socio sobre el expediente.
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request: Request, pk: int) -> Response:
        socio = getattr(request.user, "socio", None)
        if not socio:
            raise PermissionDenied("El usuario autenticado no posee un perfil de socio vinculado.")

        serializer = PresentarDescargoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        now = timezone.now()

        with transaction.atomic():
            expediente = Expediente.objects.select_for_update().filter(id=pk).first()
            if not expediente:
                return Response(
                    {"detail": "Expediente no encontrado."},
                    status=status.HTTP_404_NOT_FOUND,
                )

            # Verificar titularidad (salvo staff o TD)
            if (
                not expediente.socios.filter(pk=socio.pk).exists()
                and expediente.socio_id != socio.id
            ):
                raise PermissionDenied(
                    "No tiene autorizaciÃ³n para presentar descargo en este expediente."
                )

            # Si no estÃ¡ en estado 'justificando'
            if expediente.estado != EstadoExpedienteEnum.JUSTIFICANDO:
                msg = (
                    f"El expediente estÃ¡ en '{expediente.get_estado_display()}', "
                    "no admitiendo descargos."
                )
                return Response({"detail": msg}, status=status.HTTP_409_CONFLICT)

            # VerificaciÃ³n del plazo perentorio en servidor
            if not expediente.esta_en_plazo(ahora=now):
                return Response(
                    {
                        "detail": "El plazo perentorio de 5 dÃ­as hÃ¡biles ha expirado.",
                        "plazo_limite_at": expediente.plazo_limite_at,
                        "server_time": now,
                    },
                    status=status.HTTP_409_CONFLICT,
                )

            # Registro o correcciÃ³n del descargo dentro del plazo
            validated_data = serializer.validated_data
            previo = DescargoExpediente.objects.filter(expediente=expediente, socio=socio).first()
            if previo is not None:
                es_correccion = previo.es_vigente
            else:
                es_correccion = bool(
                    expediente.descargo_presentado and expediente.socio_id == socio.id
                )
            descargo, _ = DescargoExpediente.objects.update_or_create(
                expediente=expediente,
                socio=socio,
                defaults={
                    "tipo": validated_data["tipo"],
                    "causal": validated_data.get("causal", ""),
                    "archivo": validated_data.get("archivo", ""),
                    "texto": validated_data.get("texto", ""),
                    "presentado_at": now,
                    "es_vigente": True,
                },
            )
            if "evidencia_ids" in validated_data:
                evidencia_ids = validated_data.get("evidencia_ids") or []
                EvidenciaDescargo.objects.filter(expediente=expediente, socio=socio).exclude(
                    id__in=evidencia_ids
                ).update(es_vigente=False)
                if evidencia_ids:
                    EvidenciaDescargo.objects.filter(
                        expediente=expediente, socio=socio, id__in=evidencia_ids
                    ).update(descargo=descargo, es_vigente=True)
                    if not descargo.archivo:
                        first_ev = EvidenciaDescargo.objects.filter(id__in=evidencia_ids).first()
                        if first_ev:
                            descargo.archivo = first_ev.nombre_original
                            descargo.save(update_fields=["archivo"])
                else:
                    if not validated_data.get("archivo"):
                        descargo.archivo = ""
                        descargo.save(update_fields=["archivo"])
            es_version_posterior = es_correccion and descargo.versiones.exists()
            DescargoVersionService.registrar_version(
                descargo,
                (
                    OperacionDescargoEnum.CORREGIDO
                    if es_version_posterior
                    else OperacionDescargoEnum.PRESENTADO
                ),
                socio,
            )
            expediente.descargo_presentado = self._todos_presentaron(expediente)
            fields_to_update = ["descargo_presentado"]
            if expediente.socio_id == socio.id:
                expediente.descargo_tipo = validated_data["tipo"]
                expediente.descargo_causal = validated_data.get("causal", "")
                expediente.descargo_archivo = descargo.archivo or validated_data.get("archivo", "")
                expediente.descargo_texto = validated_data.get("texto", "")
                expediente.descargo_presentado_at = now
                fields_to_update.extend(
                    [
                        "descargo_tipo",
                        "descargo_causal",
                        "descargo_archivo",
                        "descargo_texto",
                        "descargo_presentado_at",
                    ]
                )
            expediente.save(update_fields=fields_to_update)

            CambioEstadoExpediente.objects.create(
                expediente=expediente,
                estado_anterior=expediente.estado,
                estado_nuevo=expediente.estado,
                actor=f"SOCIO_{socio.legajo}",
                motivo=(
                    f"CorrecciÃ³n de descargo {validated_data['tipo']} dentro del plazo."
                    if es_correccion
                    else f"PresentaciÃ³n formal de descargo {validated_data['tipo']}."
                ),
            )

            return Response(
                {
                    "detail": (
                        "Descargo actualizado dentro de los tÃ©rminos reglamentarios."
                        if es_correccion
                        else "Descargo registrado dentro de los tÃ©rminos reglamentarios."
                    ),
                    "expediente_id": expediente.id,
                    "descargo_presentado_at": now,
                },
                status=status.HTTP_200_OK if es_correccion else status.HTTP_201_CREATED,
            )

    @staticmethod
    def _todos_presentaron(expediente: Expediente) -> bool:
        """True si hay al menos un descargo vigente y cubre a todos los socios del expediente."""
        vigentes = expediente.descargos.filter(es_vigente=True).count()
        return vigentes > 0 and vigentes >= expediente.socios.count()

    def delete(self, request: Request, pk: int) -> Response:
        """Retiro lÃ³gico del descargo: registra la baja y conserva todo el historial."""
        socio = getattr(request.user, "socio", None)
        if not socio:
            raise PermissionDenied("El usuario autenticado no posee un perfil de socio vinculado.")

        with transaction.atomic():
            return self._retirar(pk, socio)

    def _retirar(self, pk: int, socio) -> Response:
        expediente = Expediente.objects.select_for_update().filter(id=pk).first()
        if not expediente:
            return Response(
                {"detail": "Expediente no encontrado."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not expediente.socios.filter(pk=socio.pk).exists() and expediente.socio_id != socio.id:
            raise PermissionDenied(
                "No tiene autorizaciÃ³n para gestionar el descargo de este expediente."
            )

        if expediente.estado != EstadoExpedienteEnum.JUSTIFICANDO:
            msg = (
                f"El expediente estÃ¡ en '{expediente.get_estado_display()}', "
                "no admitiendo el retiro del descargo."
            )
            return Response({"detail": msg}, status=status.HTTP_409_CONFLICT)

        now = timezone.now()
        if not expediente.esta_en_plazo(ahora=now):
            return Response(
                {
                    "detail": "El plazo perentorio de 5 dÃ­as hÃ¡biles ha expirado.",
                    "plazo_limite_at": expediente.plazo_limite_at,
                    "server_time": now,
                },
                status=status.HTTP_409_CONFLICT,
            )

        descargo = DescargoExpediente.objects.filter(
            expediente=expediente, socio=socio, es_vigente=True
        ).first()
        if descargo:
            DescargoVersionService.retirar(descargo, socio)

        # Dar de baja evidencias del socio aÃºn sin vincular a un descargo (es_vigente=False)
        EvidenciaDescargo.objects.filter(expediente=expediente, socio=socio).update(
            es_vigente=False
        )

        expediente.descargo_presentado = self._todos_presentaron(expediente)
        fields_to_update = ["descargo_presentado"]
        if expediente.socio_id == socio.id:
            expediente.descargo_tipo = ""
            expediente.descargo_causal = ""
            expediente.descargo_archivo = ""
            expediente.descargo_texto = ""
            expediente.descargo_presentado_at = None
            fields_to_update.extend(
                [
                    "descargo_tipo",
                    "descargo_causal",
                    "descargo_archivo",
                    "descargo_texto",
                    "descargo_presentado_at",
                ]
            )
        expediente.save(update_fields=fields_to_update)

        CambioEstadoExpediente.objects.create(
            expediente=expediente,
            estado_anterior=expediente.estado,
            estado_nuevo=expediente.estado,
            actor=f"SOCIO_{socio.legajo}",
            motivo="EliminaciÃ³n de descargo dentro del plazo reglamentario.",
        )

        return Response(
            {"detail": "Justificativo eliminado correctamente."},
            status=status.HTTP_200_OK,
        )


class DescargoVersionesView(APIView):
    """Historial inmutable de versiones del descargo (SCRUM-49 / S3-05).

    - GET /api/v1/expedientes/<pk>/descargo/versiones/
    - IsAuthenticated e IsImputadoOrTribunal (RBAC por objeto, mismos controles que la
      lectura de descargos).
    - El socio imputado ve sÃ³lo sus versiones; TD, CD, ADMIN y staff ven las de todos.
    """

    permission_classes = [permissions.IsAuthenticated, IsImputadoOrTribunal]

    def get(self, request: Request, pk: int) -> Response:
        expediente = get_object_or_404(Expediente, pk=pk)
        self.check_object_permissions(request, expediente)

        versiones = DescargoVersion.objects.filter(descargo__expediente=expediente).select_related(
            "descargo__socio"
        )
        socio = getattr(request.user, "socio", None)
        es_autoridad = request.user.is_staff or bool(
            socio and socio.is_enabled and socio.role in (Role.TD, Role.CD, Role.ADMIN)
        )
        if not es_autoridad:
            versiones = versiones.filter(descargo__socio=socio)

        versiones = versiones.prefetch_related("evidencias__socio").order_by(
            "descargo__socio__legajo", "numero"
        )
        return Response(DescargoVersionSerializer(versiones, many=True).data)


class EvidenciaUploadView(APIView):
    """Endpoint para carga multipart protegida de comprobantes probatorios (CA1, CA2, CA3).

    - POST /api/v1/expedientes/<pk>/evidencia/
    - Requiere autenticaciÃ³n.
    - Valida titularidad del socio (imputado en la causa).
    - Valida que el expediente estÃ© en estado 'justificando' y dentro del plazo de 5 dÃ­as hÃ¡biles.
    - Valida cupos (T02 mÃ¡x 3, T03 mÃ¡x 5) y formatos vÃ¡lidos (PDF/JPG/PNG <= 5 MB).
    - Persiste en BD LONGBLOB (Directiva PO).
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request: Request, pk: int) -> Response:
        socio = getattr(request.user, "socio", None)
        if not socio:
            raise PermissionDenied("El usuario autenticado no posee un perfil de socio vinculado.")

        expediente = Expediente.objects.filter(id=pk).first()
        if not expediente:
            return Response(
                {"detail": "Expediente no encontrado."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not expediente.socios.filter(pk=socio.pk).exists() and expediente.socio_id != socio.id:
            raise PermissionDenied(
                "No tiene autorizaciÃ³n para presentar evidencias en este expediente."
            )

        if expediente.estado != EstadoExpedienteEnum.JUSTIFICANDO:
            msg = (
                f"El expediente estÃ¡ en '{expediente.get_estado_display()}', "
                "no admitiendo evidencias."
            )
            return Response({"detail": msg}, status=status.HTTP_409_CONFLICT)

        now = timezone.now()
        if not expediente.esta_en_plazo(ahora=now):
            return Response(
                {
                    "detail": "El plazo perentorio de 5 dÃ­as hÃ¡biles ha expirado.",
                    "plazo_limite_at": expediente.plazo_limite_at,
                    "server_time": now,
                },
                status=status.HTTP_409_CONFLICT,
            )

        files = request.FILES.getlist("archivos")
        if not files and "archivo" in request.FILES:
            files = [request.FILES["archivo"]]
        if not files:
            return Response(
                {"detail": "Debe enviar al menos un archivo."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        tipo_descargo = request.data.get("tipo_descargo")
        if not tipo_descargo:
            descargo_existente = DescargoExpediente.objects.filter(
                expediente=expediente, socio=socio, es_vigente=True
            ).first()
            if descargo_existente:
                tipo_descargo = descargo_existente.tipo
            elif expediente.descargo_tipo:
                tipo_descargo = expediente.descargo_tipo

        if tipo_descargo:
            vigentes_count = EvidenciaDescargo.objects.filter(
                expediente=expediente, socio=socio, es_vigente=True
            ).count()
            total_count = vigentes_count + len(files)
            try:
                EvidenceValidator.validate_quota(tipo_descargo, total_count)
            except EvidenceValidationError as exc:
                return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        created = []
        try:
            with transaction.atomic():
                for file_obj in files:
                    evidencia = EvidenceService.save_evidence(
                        expediente=expediente,
                        socio=socio,
                        file_obj=file_obj,
                    )
                    created.append(evidencia)
        except EvidenceValidationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            EvidenciaMetadataSerializer(created, many=True).data,
            status=status.HTTP_201_CREATED,
        )


class EvidenciaDownloadView(APIView):
    """Endpoint para descarga segura y deserializaciÃ³n en streaming de evidencias (CA3, CA4).

    - GET /api/v1/expedientes/<pk>/evidencia/<uuid:evidencia_id>/
    - Protegido por IsAuthenticated e IsImputadoOrTribunal (RBAC por objeto).
    - Deserializa bytes de la base de datos (BinaryField).
    - Asienta fila inmutable en AuditoriaDescargaEvidencia y log de seguridad.
    - Emite respuesta con cabeceras nosniff y Content-Disposition inline.
    """

    permission_classes = [permissions.IsAuthenticated, IsImputadoOrTribunal]

    def get(self, request: Request, pk: int, evidencia_id: str) -> HttpResponse:
        evidencia = EvidenciaDescargo.objects.filter(id=evidencia_id, expediente_id=pk).first()
        if not evidencia:
            raise NotFound("Comprobante probatorio no encontrado.")

        self.check_object_permissions(request, evidencia)

        ip_address = request.META.get("HTTP_X_FORWARDED_FOR")
        if ip_address:
            ip_address = ip_address.split(",")[0].strip()
        else:
            ip_address = request.META.get("REMOTE_ADDR")
        user_agent = request.META.get("HTTP_USER_AGENT", "")

        EvidenceService.record_download_audit(
            evidencia=evidencia,
            user=request.user,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        response = HttpResponse(evidencia.contenido_blob, content_type=evidencia.mime_type)
        response["Content-Disposition"] = f'inline; filename="{evidencia.nombre_original}"'
        response["X-Content-Type-Options"] = "nosniff"
        return response


class DispatchCaseOpeningView(APIView):
    """Endpoint para que el Tribunal de Disciplina despache la notificaciÃ³n formal (CA1, CA3).

    - Protegido con IsAuthenticated e IsTribunalOrDirectiva.
    - Transiciona atÃ³micamente a Estado 2 ('justificando').
    - Congela plazo_inicio_at y plazo_limite_at.
    - Encola en EmailOutbox con idempotency_key e intenta envÃ­o SMTP no bloqueante.
    """

    permission_classes = [permissions.IsAuthenticated, IsTribunalOrDirectiva]

    def post(self, request: Request, pk: int) -> Response:
        if not Expediente.objects.filter(pk=pk).exists():
            return Response(
                {"detail": "Expediente no encontrado."},
                status=status.HTTP_404_NOT_FOUND,
            )

        actor = getattr(getattr(request.user, "socio", None), "legajo", request.user.username)

        try:
            expediente, outbox = OpeningNotificationService.dispatch_opening(
                expediente_id=pk,
                actor=f"TD_{actor}",
            )
        except InvalidCaseStatusError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_409_CONFLICT,
            )
        except MissingSocioEmailError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        response_data = {
            "expediente_id": expediente.id,
            "numero": expediente.numero,
            "estado": expediente.estado,
            "plazo_inicio_at": expediente.plazo_inicio_at,
            "plazo_limite_at": expediente.plazo_limite_at,
            "outbox_id": outbox.id,
            "outbox_status": outbox.status,
            "idempotency_key": outbox.idempotency_key,
            "mensaje": "NotificaciÃ³n de apertura despachada correctamente.",
        }
        serializer = DispatchNotificationResponseSerializer(response_data)
        return Response(serializer.data, status=status.HTTP_200_OK)


class DecisionCausalView(APIView):
    """Decisiones versionadas de un vocal sobre la causal T02 de un descargo (S4-02).

    - GET: historial de versiones (TD, CD y Administrador).
    - POST: registra una nueva versiÃ³n (sÃ³lo TD) sin modificar el descargo (CA4).
    """

    def get_permissions(self) -> list[permissions.BasePermission]:
        if self.request.method == "POST":
            return [permissions.IsAuthenticated(), CanResolveCausal()]
        return [permissions.IsAuthenticated(), IsTribunalOrDirectiva()]

    def get(self, request: Request, pk: int, descargo_id: int) -> Response:
        try:
            descargo = CausalResolutionService.get_descargo(pk, descargo_id)
        except CausalResolutionNotFound as exc:
            raise NotFound(str(exc)) from exc
        decisiones = descargo.decisiones_causal.select_related("autor")
        return Response(DecisionCausalSerializer(decisiones, many=True).data)

    def post(self, request: Request, pk: int, descargo_id: int) -> Response:
        serializer = RegistrarDecisionCausalSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            decision = CausalResolutionService.decide(
                expediente_id=pk,
                descargo_id=descargo_id,
                decision=CausalDecision(data["decision"]),
                fundamento=data["fundamento"],
                evidencia_ids=data.get("evidencia_ids"),
                user=request.user,
            )
        except CausalResolutionNotFound as exc:
            raise NotFound(str(exc)) from exc
        except CausalResolutionStateError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_409_CONFLICT)
        except CausalResolutionValidationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(DecisionCausalSerializer(decision).data, status=status.HTTP_201_CREATED)


# Backward-compatible alias for existing imports
DespacharNotificacionAperturaView = DispatchCaseOpeningView


class CaseNotificationAuditView(APIView):
    """Endpoint para que operadores del Tribunal consulten la bitÃ¡cora outbox (CA3).

    - Protegido con IsAuthenticated e IsTribunalOrDirectiva.
    """

    permission_classes = [permissions.IsAuthenticated, IsTribunalOrDirectiva]

    def get(self, request: Request, pk: int) -> Response:
        if not Expediente.objects.filter(pk=pk).exists():
            return Response(
                {"detail": "Expediente no encontrado."},
                status=status.HTTP_404_NOT_FOUND,
            )

        notifications = CaseNotificationQueryService.get_case_notifications(expediente_id=pk)
        serializer = CaseNotificationAuditSerializer(notifications, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


# Backward-compatible alias for existing imports
ExpedienteNotificacionesView = CaseNotificationAuditView


class ExpedienteDetailView(APIView):
    """Endpoint seguro de detalle de causa para el enlace provisto en la notificaciÃ³n (CA4).

    - Protegido con IsAuthenticated e IsImputadoOrTribunal (RBAC por objeto).
    - 401 si es anÃ³nimo.
    - 403 si es un socio ajeno a la causa.
    - 200 si es el socio imputado o integra TD/CD/Admin.
    """

    permission_classes = [permissions.IsAuthenticated, IsImputadoOrTribunal]

    def get(self, request: Request, pk: int) -> Response:
        expediente = (
            Expediente.objects.filter(pk=pk)
            .select_related(
                "socio",
                "socio__subcomision",
                "solicitud_t01",
                "solicitud_t01__solicitante",
            )
            .prefetch_related(*EXPEDIENTE_LIST_PREFETCH)
            .first()
        )
        if not expediente:
            return Response(
                {"detail": "Expediente no encontrado."},
                status=status.HTTP_404_NOT_FOUND,
            )

        self.check_object_permissions(request, expediente)
        serializer = ExpedienteListSerializer(expediente, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request: Request, pk: int) -> Response:
        expediente = (
            Expediente.objects.filter(pk=pk)
            .select_related("socio", "socio__subcomision")
            .prefetch_related(*EXPEDIENTE_LIST_PREFETCH)
            .first()
        )
        if not expediente:
            return Response(
                {"detail": "Expediente no encontrado."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not IsTribunalOrDirectiva().has_permission(request, self):
            raise PermissionDenied(
                "Solo integrantes del Tribunal o ComisiÃ³n Directiva pueden actualizar la urgencia."
            )

        serializer = UpdateUrgenciaExpedienteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        expediente.urgencia = serializer.validated_data["urgencia"]
        expediente.save(update_fields=["urgencia", "updated_at"])

        return Response(
            ExpedienteListSerializer(expediente, context={"request": request}).data,
            status=status.HTTP_200_OK,
        )


REGLAMENTOS_VIGENTES = (
    "Estatuto AVEIT Reforma 2026",
    "Reglamento Procesal Disciplinario 2026",
    "Reglamento Interno de Disciplina",
)


class ReglamentosVigentesView(APIView):
    """Lista de reglamentos institucionales vigentes para respaldar un T01."""

    permission_classes = (CanCreateT01,)

    def get(self, request):
        return Response({"reglamentos": list(REGLAMENTOS_VIGENTES)})


class SolicitudT01CreateView(APIView):
    permission_classes = (CanCreateT01,)

    def post(self, request):
        serializer = SolicitudT01Serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        solicitud = serializer.save(solicitante=request.user.socio)
        return Response(SolicitudT01Serializer(solicitud).data, status=status.HTTP_201_CREATED)


class SolicitudT01DetailView(APIView):
    permission_classes = (CanCreateT01,)

    def get_object(self, request, pk):
        solicitud = get_object_or_404(SolicitudT01, pk=pk)
        if solicitud.solicitante_id != request.user.socio.pk:
            raise Http404
        return solicitud

    def get(self, request, pk):
        return Response(SolicitudT01Serializer(self.get_object(request, pk)).data)

    def patch(self, request, pk):
        solicitud = self.get_object(request, pk)
        serializer = SolicitudT01Serializer(solicitud, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        return Response(SolicitudT01Serializer(serializer.save()).data)

    def delete(self, request, pk):
        solicitud = self.get_object(request, pk)
        if solicitud.estado == SolicitudT01.Estado.ISSUED:
            return Response(
                {"detail": "Una solicitud emitida no puede eliminarse."},
                status=status.HTTP_409_CONFLICT,
            )
        solicitud.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class SolicitudT01EmitView(APIView):
    permission_classes = (CanCreateT01,)

    @transaction.atomic
    def post(self, request, pk):
        solicitud = get_object_or_404(SolicitudT01.objects.select_for_update(), pk=pk)
        if solicitud.solicitante_id != request.user.socio.pk:
            raise Http404
        serializer = EmitirT01Serializer(data=request.data, context={"solicitud": solicitud})
        serializer.is_valid(raise_exception=True)
        solicitud = serializer.save()
        return Response(SolicitudT01Serializer(solicitud).data)


class BoardExpedientesView(APIView):
    """GET /api/v1/expedientes/board/

    Tablero de 6 columnas del TD con expedientes agrupados por estado (S2-05 CA1).
    Soporta filtros por estado, socio (legajo/nombre) y rango de fechas (CA2).
    """

    permission_classes = [permissions.IsAuthenticated, IsTribunalOrDirectiva]

    def get(self, request: Request) -> Response:
        qs = (
            Expediente.objects.select_related(
                "socio",
                "socio__subcomision",
                "solicitud_t01",
                "solicitud_t01__solicitante",
            )
            .prefetch_related("socios", "cambios_estado")
            .all()
        )
        filterset = ExpedienteFilter(request.query_params, queryset=qs)
        payload = build_board_payload(filterset.qs)
        return Response(payload, status=status.HTTP_200_OK)


class TransicionarExpedienteView(APIView):
    """POST /api/v1/expedientes/<pk>/transicionar/

    Ejecuta una transiciÃ³n de estado autorizada (S2-05 CA3).
    Delega estrictamente en ExpedienteWorkflowService.transition().
    """

    permission_classes = [permissions.IsAuthenticated, CanTransitionExpedientes]

    def post(self, request: Request, pk: int) -> Response:
        # Aceptar tanto to_status/justificacion como estado/motivo
        target_status = request.data.get("to_status") or request.data.get("estado")
        reason = request.data.get("justificacion") or request.data.get("motivo")

        if not target_status:
            return Response(
                {"detail": "El estado destino es obligatorio."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        actor = _actor_for_user(request.user)
        motivo = reason or f"TransiciÃ³n a {target_status}"

        try:
            expediente = ExpedienteWorkflowService.transition(
                expediente_id=pk,
                estado_nuevo=target_status,
                actor=actor,
                motivo=motivo,
            )
        except Expediente.DoesNotExist:
            return Response(
                {"detail": "Expediente no encontrado."},
                status=status.HTTP_404_NOT_FOUND,
            )
        except ValidationError as exc:
            return Response(
                exc.message_dict if hasattr(exc, "message_dict") else {"detail": exc.messages},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "detail": f"Expediente transicionado a '{expediente.get_estado_display()}'.",
                "expediente_id": expediente.id,
                "estado_nuevo": expediente.estado,
            },
            status=status.HTTP_200_OK,
        )


class MisSolicitudesT01View(APIView):
    """Consulta de expedientes y solicitudes iniciadas por la autoridad autenticada (CA1, CA4)."""

    permission_classes = (permissions.IsAuthenticated, CanCreateT01)

    def get(self, request: Request) -> Response:
        socio = getattr(request.user, "socio", None)
        if not socio:
            return Response([], status=status.HTTP_200_OK)

        queryset = (
            SolicitudT01.objects.filter(solicitante=socio)
            .select_related("expediente", "solicitante")
            .order_by("-created_at")
        )

        # Filtro por estado
        estado = request.query_params.get("estado", "").strip()
        if estado:
            if estado.upper() == "DRAFT":
                queryset = queryset.filter(estado=SolicitudT01.Estado.DRAFT)
            elif estado.upper() == "ISSUED":
                queryset = queryset.filter(estado=SolicitudT01.Estado.ISSUED)
            else:
                queryset = queryset.filter(expediente__estado=estado)

        # BÃºsqueda por texto (tÃ­tulo, motivo, causal, nÃºmero o socios involucrados)
        search = request.query_params.get("search", "").strip()
        if search:
            queryset = queryset.filter(
                Q(titulo__icontains=search)
                | Q(motivo__icontains=search)
                | Q(causal__icontains=search)
                | Q(numero_expediente__icontains=search)
                | Q(expediente__numero__icontains=search)
                | Q(snapshots_destinatarios__icontains=search)
            )

        serializer = MisSolicitudesT01Serializer(queryset, many=True, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class CalendarioFeriadosView(APIView):
    """Lectura autenticada y alta auditada en el Ãºnico calendario institucional."""

    def get_permissions(self) -> list[permissions.BasePermission]:
        if self.request.method == "POST":
            return [permissions.IsAuthenticated(), CanManageCalendar()]
        return [permissions.IsAuthenticated()]

    def get(self, request: Request) -> Response:
        query = CalendarQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        filters = query.validated_data
        holidays = Holiday.objects.select_related("created_by__socio")
        if "year" in filters:
            holidays = holidays.filter(date__year=filters["year"])
        if "month" in filters:
            holidays = holidays.filter(date__month=filters["month"])
        order = "-date" if filters["ordering"] == "-fecha" else "date"
        return Response(HolidaySerializer(holidays.order_by(order), many=True).data)

    def post(self, request: Request) -> Response:
        serializer = HolidaySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            with transaction.atomic():
                holiday = serializer.save(created_by=request.user, created_at=timezone.now())
        except IntegrityError:
            if Holiday.objects.filter(date=serializer.validated_data["date"]).exists():
                raise DRFValidationError({"fecha": ["Ya existe un feriado para esa fecha."]})
            raise
        return Response(HolidaySerializer(holiday).data, status=status.HTTP_201_CREATED)


class CalcularPlazoView(APIView):
    """SimulaciÃ³n con el mismo calendario que los plazos de expedientes."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request: Request) -> Response:
        serializer = CalcularPlazoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        start_at = serializer.validated_data["start_at"]
        business_days = serializer.validated_data["business_days"]
        holidays = dict(Holiday.objects.values_list("date", "description"))
        provider = DbHolidayProvider(holidays=set(holidays))
        deadline = compute_business_deadline(
            start_at=start_at, business_days=business_days, holiday_provider=provider
        )
        current_date = start_at.date()
        counted_days = []
        excluded_days = []
        weekday_names = ["Lunes", "Martes", "MiÃ©rcoles", "Jueves", "Viernes", "SÃ¡bado", "Domingo"]
        while current_date < deadline.date():
            current_date += timedelta(days=1)
            weekday = current_date.weekday()
            if weekday >= 5:
                excluded_days.append(
                    {
                        "date": current_date.isoformat(),
                        "reason": f"{weekday_names[weekday]} (Fin de semana)",
                    }
                )
            elif provider.is_holiday(current_date):
                excluded_days.append(
                    {
                        "date": current_date.isoformat(),
                        "reason": f"Feriado: {holidays[current_date]}",
                    }
                )
            else:
                counted_days.append(
                    {
                        "day_number": len(counted_days) + 1,
                        "date": current_date.isoformat(),
                        "weekday": weekday_names[weekday],
                    }
                )
        return Response(
            {
                "start_at": start_at.isoformat(),
                "business_days": business_days,
                "deadline": deadline.isoformat(),
                "dias_habiles_computados": counted_days,
                "dias_excluidos": excluded_days,
            }
        )
