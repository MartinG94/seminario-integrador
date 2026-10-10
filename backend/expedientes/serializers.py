import logging
from decimal import Decimal

from django.utils import timezone
from rest_framework import serializers

from expedientes.models import (
    DescargoExpediente,
    EstadoExpedienteEnum,
    Expediente,
    SolicitudT01,
    TipoDescargoEnum,
    UrgenciaExpedienteEnum,
)
from padron.factory import get_padron_repository
from socios.models import Role, Socio, Subcomision

logger = logging.getLogger(__name__)


class ExpedienteListSerializer(serializers.ModelSerializer):
    """Serializador para listado y detalle de expedientes."""

    socio_nombre = serializers.SerializerMethodField()
    socio_legajo = serializers.CharField(source="socio.legajo", read_only=True)
    subcomision = serializers.CharField(source="socio.subcomision.name", default="", read_only=True)
    urgencia_display = serializers.CharField(source="get_urgencia_display", read_only=True)
    descargo_presentado = serializers.SerializerMethodField()
    descargo_tipo = serializers.SerializerMethodField()
    descargo_causal = serializers.SerializerMethodField()
    descargo_archivo = serializers.SerializerMethodField()
    descargo_texto = serializers.SerializerMethodField()
    descargo_presentado_at = serializers.SerializerMethodField()
    esta_en_plazo = serializers.SerializerMethodField()
    horas_restantes = serializers.SerializerMethodField()
    socios = serializers.SerializerMethodField()
    historial = serializers.SerializerMethodField()

    class Meta:
        model = Expediente
        fields = [
            "id",
            "numero",
            "motivo",
            "puntos",
            "estado",
            "urgencia",
            "urgencia_display",
            "socio_nombre",
            "socio_legajo",
            "socios",
            "subcomision",
            "plazo_inicio_at",
            "plazo_limite_at",
            "descargo_presentado",
            "descargo_tipo",
            "descargo_causal",
            "descargo_archivo",
            "descargo_texto",
            "descargo_presentado_at",
            "esta_en_plazo",
            "horas_restantes",
            "created_at",
            "historial",
        ]

    def get_socio_nombre(self, obj: Expediente) -> str:
        return f"{obj.socio.first_name} {obj.socio.last_name}"

    def _descargo_for_requester(self, obj: Expediente) -> DescargoExpediente | None:
        request = self.context.get("request")
        socio = getattr(request.user, "socio", None) if request else None
        if socio is None:
            return None
        # Se recorre la colección precargada para no consultar una vez por campo y fila.
        return next((d for d in obj.descargos.all() if d.socio_id == socio.pk), None)

    def get_descargo_presentado(self, obj: Expediente) -> bool:
        descargo = self._descargo_for_requester(obj)
        if descargo:
            return True
        request = self.context.get("request")
        socio = getattr(request.user, "socio", None) if request else None
        return bool(obj.descargo_presentado and obj.socio_id == getattr(socio, "id", None))

    def get_descargo_tipo(self, obj: Expediente) -> str | None:
        descargo = self._descargo_for_requester(obj)
        if descargo:
            return descargo.tipo
        return obj.descargo_tipo if self._is_primary_socio(obj) else None

    def get_descargo_causal(self, obj: Expediente) -> str | None:
        descargo = self._descargo_for_requester(obj)
        if descargo:
            return descargo.causal
        return obj.descargo_causal if self._is_primary_socio(obj) else None

    def get_descargo_archivo(self, obj: Expediente) -> str | None:
        descargo = self._descargo_for_requester(obj)
        if descargo:
            return descargo.archivo
        return obj.descargo_archivo if self._is_primary_socio(obj) else None

    def get_descargo_texto(self, obj: Expediente) -> str | None:
        descargo = self._descargo_for_requester(obj)
        if descargo:
            return descargo.texto
        return obj.descargo_texto if self._is_primary_socio(obj) else None

    def get_descargo_presentado_at(self, obj: Expediente):
        descargo = self._descargo_for_requester(obj)
        if descargo:
            return descargo.presentado_at
        return obj.descargo_presentado_at if self._is_primary_socio(obj) else None

    def _is_primary_socio(self, obj: Expediente) -> bool:
        request = self.context.get("request")
        socio = getattr(request.user, "socio", None) if request else None
        return bool(socio and obj.socio_id == socio.pk)

    def get_esta_en_plazo(self, obj: Expediente) -> bool:
        return obj.esta_en_plazo()

    def get_horas_restantes(self, obj: Expediente) -> int:
        if not obj.plazo_limite_at or obj.estado != "justificando":
            return 0
        from django.utils import timezone

        diff = obj.plazo_limite_at - timezone.now()
        horas = int(diff.total_seconds() // 3600)
        return max(0, horas)

    def get_socios(self, obj: Expediente) -> list[dict[str, int | str]]:
        return [
            {
                "id": socio.id,
                "legajo": socio.legajo,
                "nombre": f"{socio.first_name} {socio.last_name}",
            }
            for socio in obj.socios.all()
        ]

    def get_historial(self, obj: Expediente) -> list[dict[str, str]]:
        changes = sorted(obj.cambios_estado.all(), key=lambda c: (c.fecha_hora, c.id))
        return [
            {
                "estado_anterior": change.estado_anterior,
                "estado_nuevo": change.estado_nuevo,
                "actor": change.actor,
                "fecha_hora": change.fecha_hora.isoformat(),
                "motivo": change.motivo,
            }
            for change in changes
        ]


class AperturaExpedienteSerializer(serializers.Serializer):
    motivo = serializers.CharField(max_length=5000)
    socios = serializers.ListField(child=serializers.IntegerField(min_value=1), allow_empty=False)
    urgencia = serializers.ChoiceField(
        choices=UrgenciaExpedienteEnum.choices,
        required=False,
        default=UrgenciaExpedienteEnum.NORMAL,
    )

    def validate_socios(self, value: list[int]) -> list[int]:
        if len(set(value)) != len(value):
            raise serializers.ValidationError("No se puede repetir un socio.")
        if set(value) != set(Socio.objects.filter(id__in=value).values_list("id", flat=True)):
            raise serializers.ValidationError("Uno o más socios no existen.")
        return value


class TransicionExpedienteSerializer(serializers.Serializer):
    estado = serializers.ChoiceField(choices=Expediente._meta.get_field("estado").choices)
    motivo = serializers.CharField(max_length=5000)


class DescargoExpedienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = DescargoExpediente
        fields = ["id", "socio", "tipo", "causal", "archivo", "texto", "presentado_at"]


class PresentarDescargoSerializer(serializers.Serializer):
    """Payload para presentación de descargo T02/T03."""

    tipo = serializers.ChoiceField(choices=TipoDescargoEnum.choices)
    causal = serializers.CharField(max_length=255, required=False, allow_blank=True)
    archivo = serializers.CharField(max_length=255, required=False, allow_blank=True)
    texto = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs: dict) -> dict:
        tipo = attrs.get("tipo")
        if tipo == TipoDescargoEnum.T02_CERTIFICADO:
            if not attrs.get("archivo"):
                raise serializers.ValidationError(
                    {"archivo": "Es obligatorio adjuntar comprobante para justificaciones T02."}
                )
        elif tipo == TipoDescargoEnum.T03_EXTRAORDINARIO:
            if not attrs.get("texto", "").strip():
                raise serializers.ValidationError(
                    {"texto": "Es obligatorio incluir la exposición fáctica para descargos T03."}
                )
        return attrs


class DispatchNotificationResponseSerializer(serializers.Serializer):
    """Payload de respuesta tras el despacho formal de la notificación de apertura."""

    expediente_id = serializers.IntegerField()
    numero = serializers.CharField()
    estado = serializers.CharField()
    plazo_inicio_at = serializers.DateTimeField()
    plazo_limite_at = serializers.DateTimeField()
    outbox_id = serializers.UUIDField()
    outbox_status = serializers.CharField()
    idempotency_key = serializers.CharField()
    mensaje = serializers.CharField(
        required=False, default="Notificación de apertura despachada correctamente."
    )


# Backward-compatible alias for existing imports
DespachoNotificacionResponseSerializer = DispatchNotificationResponseSerializer


class CaseNotificationAuditSerializer(serializers.ModelSerializer):
    """Serializador de auditoría y bitácora de entrega para operadores del TD."""

    destinatario = serializers.JSONField(source="to")
    asunto = serializers.CharField(source="subject")
    estado = serializers.CharField(source="status")
    reintentos = serializers.IntegerField(source="retry_count")
    max_reintentos = serializers.IntegerField(source="max_retries")
    proximo_reintento_at = serializers.DateTimeField(source="next_retry_at")
    ultimo_error = serializers.CharField(source="last_error", allow_null=True)
    despachado_at = serializers.DateTimeField(source="sent_at", allow_null=True)

    class Meta:
        from notifications.models import EmailOutbox

        model = EmailOutbox
        fields = [
            "id",
            "destinatario",
            "asunto",
            "estado",
            "reintentos",
            "max_reintentos",
            "proximo_reintento_at",
            "ultimo_error",
            "despachado_at",
            "created_at",
        ]


# Backward-compatible alias for existing imports
ExpedienteNotificationAuditSerializer = CaseNotificationAuditSerializer


class SolicitudT01Serializer(serializers.ModelSerializer):
    urgencia = serializers.ChoiceField(
        choices=UrgenciaExpedienteEnum.choices,
        required=False,
        default=UrgenciaExpedienteEnum.NORMAL,
    )

    class Meta:
        model = SolicitudT01
        fields = "__all__"
        read_only_fields = (
            "id",
            "estado",
            "solicitante",
            "snapshot_destinatario",
            "snapshots_destinatarios",
            "snapshot_emitido",
            "numero_expediente",
            "expediente",
            "created_at",
            "updated_at",
            "issued_at",
        )

    def validate_tipo_accion(self, value):
        if value not in SolicitudT01.TipoAccion.values:
            raise serializers.ValidationError("Tipo de acción inválido.")
        return value

    def validate_destinatarios_socios_ids(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError("Debe ser una lista de identificadores de socios.")
        vistos = set()
        for sid in value:
            if not isinstance(sid, int) or sid <= 0:
                raise serializers.ValidationError(
                    "Cada identificador de socio debe ser un entero positivo."
                )
            if sid in vistos:
                raise serializers.ValidationError(f"El socio {sid} está duplicado en la lista.")
            vistos.add(sid)
        return value

    def validate(self, attrs):
        if self.instance and self.instance.estado == SolicitudT01.Estado.ISSUED:
            raise serializers.ValidationError("Una solicitud emitida es inmutable.")
        puntos = attrs.get("puntos", getattr(self.instance, "puntos", None))
        accion = attrs.get("tipo_accion", getattr(self.instance, "tipo_accion", None))
        if puntos is not None and accion:
            if accion == SolicitudT01.TipoAccion.SANCTION and puntos >= Decimal("0"):
                raise serializers.ValidationError({"puntos": "La sanción debe ser negativa."})
            if accion == SolicitudT01.TipoAccion.MERIT and puntos <= Decimal("0"):
                raise serializers.ValidationError({"puntos": "El mérito debe ser positivo."})
        return attrs


def _snapshot(socio):
    sub = socio.subcomision
    category = getattr(socio.category, "value", socio.category)
    status = getattr(socio.membership_status, "value", socio.membership_status)
    return {
        "socio_id": socio.socio_id,
        "legajo": socio.legajo,
        "dni": socio.dni,
        "first_name": socio.first_name,
        "last_name": socio.last_name,
        "email": socio.email,
        "subcomision": {"id": sub.id, "name": sub.name} if sub else None,
        "social_year": socio.social_year,
        "category": category,
        "is_active": socio.is_active,
        "membership_status": status,
    }


class EmitirT01Serializer(serializers.Serializer):
    def validate(self, attrs):
        solicitud = self.context["solicitud"]
        if solicitud.estado == SolicitudT01.Estado.ISSUED:
            return attrs
        socios_ids = solicitud.destinatarios_socios_ids or (
            [solicitud.destinatario_socio_id] if solicitud.destinatario_socio_id else []
        )
        if not socios_ids:
            raise serializers.ValidationError(
                {"destinatarios_socios_ids": "Es requerido al menos un socio al emitir."}
            )
        if solicitud.puntos is None:
            raise serializers.ValidationError({"puntos": "Los puntos son requeridos al emitir."})
        if not (solicitud.motivo and solicitud.motivo.strip()):
            raise serializers.ValidationError({"motivo": "Es requerido al emitir."})

        padron_repo = get_padron_repository()
        for sid in socios_ids:
            socio = padron_repo.get_by_id(sid)
            if socio is None:
                raise serializers.ValidationError(
                    {"destinatarios_socios_ids": f"El socio ID {sid} no existe en el padrón."}
                )
            if not socio.is_active:
                raise serializers.ValidationError(
                    {"destinatarios_socios_ids": f"El socio ID {sid} no está activo."}
                )
        return attrs

    def save(self):
        solicitud = self.context["solicitud"]
        if solicitud.estado == SolicitudT01.Estado.ISSUED:
            return solicitud
        padron_repo = get_padron_repository()
        socios_ids = solicitud.destinatarios_socios_ids or (
            [solicitud.destinatario_socio_id] if solicitud.destinatario_socio_id else []
        )
        snapshots = []
        for sid in socios_ids:
            s = padron_repo.get_by_id(sid)
            if s:
                snapshots.append(_snapshot(s))
        solicitud.snapshots_destinatarios = snapshots
        solicitud.snapshot_destinatario = snapshots[0] if snapshots else None
        solicitud.destinatarios_socios_ids = socios_ids
        solicitud.destinatario_socio_id = socios_ids[0] if socios_ids else None

        solicitud.snapshot_emitido = {
            "id": str(solicitud.id),
            "tipo_accion": solicitud.tipo_accion,
            "urgencia": solicitud.urgencia,
            "causal": solicitud.causal,
            "puntos": str(solicitud.puntos),
            "motivo": solicitud.motivo,
            "titulo": solicitud.titulo,
            "razon": solicitud.razon,
            "reglamentos_respaldantes": solicitud.reglamentos_respaldantes,
            "destinatario": solicitud.snapshot_destinatario,
            "destinatarios": solicitud.snapshots_destinatarios,
            "anexo_fecha": solicitud.anexo_fecha.isoformat() if solicitud.anexo_fecha else None,
            "anexo_lugar": solicitud.anexo_lugar,
            "anexo_relato": solicitud.anexo_relato,
            "anexo_testigos": solicitud.anexo_testigos,
        }
        solicitud.estado = SolicitudT01.Estado.ISSUED
        solicitud.issued_at = timezone.now()
        solicitud.numero_expediente = (
            f"T01-{solicitud.issued_at:%Y}-{solicitud.id.hex[:12].upper()}"
        )

        # Apertura atómica y vinculación formal con Expediente
        # Resolver socios (ya sea por PK local de Socio o por padrón institucional)
        resolved_socio_ids = []
        for sid in socios_ids:
            local_socio = Socio.objects.filter(pk=sid).first()
            if not local_socio:
                s_dto = padron_repo.get_by_id(sid)
                if s_dto:
                    if s_dto.legajo:
                        local_socio = Socio.objects.filter(legajo=s_dto.legajo).first()
                    if not local_socio and s_dto.email:
                        local_socio = Socio.objects.filter(email__iexact=s_dto.email).first()
                    if not local_socio and s_dto.legajo:
                        from django.contrib.auth import get_user_model

                        UserModel = get_user_model()
                        username = str(s_dto.legajo)
                        email = s_dto.email or f"{username}@aveit.utn.edu.ar"
                        user, _ = UserModel.objects.get_or_create(
                            username=username,
                            defaults={"email": email},
                        )
                        subcom = None
                        if s_dto.subcomision:
                            subcom, _ = Subcomision.objects.get_or_create(
                                name=s_dto.subcomision.name
                            )
                        local_socio = Socio.objects.create(
                            user=user,
                            legajo=s_dto.legajo,
                            first_name=s_dto.first_name,
                            last_name=s_dto.last_name,
                            email=email,
                            subcomision=subcom,
                            social_year=s_dto.social_year or 1,
                            role=Role.SOCIO,
                            is_enabled=s_dto.is_active,
                        )
            if local_socio:
                resolved_socio_ids.append(local_socio.pk)

        if resolved_socio_ids and not solicitud.expediente:
            from expedientes.services.workflow_service import ExpedienteWorkflowService

            actor_name = getattr(solicitud.solicitante, "legajo", str(solicitud.solicitante_id))
            try:
                motivo_apertura = (
                    solicitud.motivo or solicitud.titulo or "Apertura formal por Formulario T01"
                )
                expediente = ExpedienteWorkflowService.open_expediente(
                    motivo=motivo_apertura,
                    socio_ids=resolved_socio_ids,
                    actor=f"SOLICITANTE_{actor_name}",
                    urgencia=solicitud.urgencia,
                    points=solicitud.puntos,
                )
                solicitud.expediente = expediente
            except Exception:
                logger.exception("Error al abrir formalmente el expediente desde SolicitudT01")

        solicitud.save()
        return solicitud


# ── Transiciones autorizadas (Art. 12 Reglamento Procesal 2026) ──────────

ALLOWED_TRANSITIONS: dict[str, list[str]] = {
    EstadoExpedienteEnum.CREADO: [EstadoExpedienteEnum.JUSTIFICANDO],
    EstadoExpedienteEnum.JUSTIFICANDO: [EstadoExpedienteEnum.REVISION_RESOLUCION],
    EstadoExpedienteEnum.REVISION_RESOLUCION: [EstadoExpedienteEnum.ESPERA_RESOLUCION],
    EstadoExpedienteEnum.ESPERA_RESOLUCION: [EstadoExpedienteEnum.PENDIENTE_CORREOS],
    EstadoExpedienteEnum.PENDIENTE_CORREOS: [EstadoExpedienteEnum.EMITIDO],
    EstadoExpedienteEnum.EMITIDO: [],
}


class BoardExpedienteSerializer(serializers.ModelSerializer):
    """Tarjeta compacta de expediente para el tablero Kanban del TD (S2-05 CA1 / S3-07)."""

    estado_display = serializers.CharField(source="get_estado_display", read_only=True)
    urgencia_display = serializers.CharField(source="get_urgencia_display", read_only=True)
    socio_nombre = serializers.SerializerMethodField()
    socio_legajo = serializers.CharField(source="socio.legajo", read_only=True)
    subcomision = serializers.CharField(source="socio.subcomision.name", default="", read_only=True)
    transiciones_permitidas = serializers.SerializerMethodField()
    cantidad_socios = serializers.SerializerMethodField()

    class Meta:
        model = Expediente
        fields = [
            "id",
            "numero",
            "socio",
            "socio_nombre",
            "socio_legajo",
            "subcomision",
            "estado",
            "estado_display",
            "urgencia",
            "urgencia_display",
            "puntos",
            "motivo",
            "created_at",
            "plazo_limite_at",
            "transiciones_permitidas",
            "cantidad_socios",
        ]

    def get_socio_nombre(self, obj: Expediente) -> str:
        return f"{obj.socio.first_name} {obj.socio.last_name}"

    def get_cantidad_socios(self, obj: Expediente) -> int:
        count = obj.socios.count()
        return count if count > 0 else 1

    def get_transiciones_permitidas(self, obj: Expediente) -> list[str]:
        return ALLOWED_TRANSITIONS.get(obj.estado, [])


class UpdateUrgenciaExpedienteSerializer(serializers.Serializer):
    """Payload para actualizar el nivel de urgencia de un expediente."""

    urgencia = serializers.ChoiceField(choices=UrgenciaExpedienteEnum.choices)


class TransicionarExpedienteSerializer(serializers.Serializer):
    """Valida y ejecuta una transición de estado autorizada (S2-05 CA3)."""

    to_status = serializers.ChoiceField(choices=EstadoExpedienteEnum.choices)
    justificacion = serializers.CharField(required=False, default="", allow_blank=True)

    def validate_to_status(self, value: str) -> str:
        expediente: Expediente = self.context["expediente"]
        allowed = ALLOWED_TRANSITIONS.get(expediente.estado, [])
        if value not in allowed:
            raise serializers.ValidationError(
                f"Transición no permitida de '{expediente.get_estado_display()}' "
                f"a '{EstadoExpedienteEnum(value).label}'."
            )
        return value


class MisSolicitudesT01Serializer(serializers.ModelSerializer):
    """Serializador sanitizado para monitoreo de solicitudes T01 (CA2 y CA3)."""

    numero = serializers.SerializerMethodField()
    fecha = serializers.SerializerMethodField()
    estado_procesal = serializers.SerializerMethodField()
    estado_procesal_display = serializers.SerializerMethodField()
    involucrados = serializers.SerializerMethodField()
    resolucion_final = serializers.SerializerMethodField()
    urgencia = serializers.SerializerMethodField()
    urgencia_display = serializers.SerializerMethodField()

    class Meta:
        model = SolicitudT01
        fields = [
            "id",
            "numero",
            "numero_expediente",
            "fecha",
            "estado",
            "tipo_accion",
            "puntos",
            "titulo",
            "motivo",
            "causal",
            "razon",
            "reglamentos_respaldantes",
            "anexo_fecha",
            "anexo_lugar",
            "anexo_relato",
            "anexo_testigos",
            "destinatarios_socios_ids",
            "estado_procesal",
            "estado_procesal_display",
            "urgencia",
            "urgencia_display",
            "involucrados",
            "resolucion_final",
            "created_at",
            "issued_at",
        ]

    def get_urgencia(self, obj: SolicitudT01) -> str:
        if obj.expediente:
            return obj.expediente.urgencia
        return obj.urgencia or UrgenciaExpedienteEnum.NORMAL

    def get_urgencia_display(self, obj: SolicitudT01) -> str:
        if obj.expediente:
            return obj.expediente.get_urgencia_display()
        return UrgenciaExpedienteEnum(obj.urgencia).label if obj.urgencia else "Normal"

    def get_numero(self, obj: SolicitudT01) -> str:
        if obj.expediente:
            return obj.expediente.numero
        return obj.numero_expediente or "Borrador sin número"

    def get_fecha(self, obj: SolicitudT01):
        return obj.issued_at or obj.created_at

    def get_estado_procesal(self, obj: SolicitudT01) -> str:
        if obj.estado == SolicitudT01.Estado.DRAFT:
            return "borrador"
        if obj.expediente:
            return obj.expediente.estado
        return "creado"

    def get_estado_procesal_display(self, obj: SolicitudT01) -> str:
        if obj.estado == SolicitudT01.Estado.DRAFT:
            return "Borrador"
        if obj.expediente:
            return obj.expediente.get_estado_display()
        return "Expediente Creado"

    def get_involucrados(self, obj: SolicitudT01) -> list[dict]:
        if obj.snapshots_destinatarios:
            return [
                {
                    "socio_id": s.get("socio_id"),
                    "legajo": s.get("legajo", "S/D"),
                    "first_name": s.get("first_name", ""),
                    "last_name": s.get("last_name", ""),
                    "subcomision": (
                        s.get("subcomision", {}).get("name")
                        if isinstance(s.get("subcomision"), dict)
                        else (s.get("subcomision") or "Sin subcomisión")
                    ),
                }
                for s in obj.snapshots_destinatarios
            ]
        if obj.snapshot_destinatario:
            s = obj.snapshot_destinatario
            return [
                {
                    "socio_id": s.get("socio_id"),
                    "legajo": s.get("legajo", "S/D"),
                    "first_name": s.get("first_name", ""),
                    "last_name": s.get("last_name", ""),
                    "subcomision": (
                        s.get("subcomision", {}).get("name")
                        if isinstance(s.get("subcomision"), dict)
                        else (s.get("subcomision") or "Sin subcomisión")
                    ),
                }
            ]
        socios_ids = obj.destinatarios_socios_ids or (
            [obj.destinatario_socio_id] if obj.destinatario_socio_id else []
        )
        if not socios_ids:
            return []
        socios = Socio.objects.filter(pk__in=socios_ids).select_related("subcomision")
        return [
            {
                "socio_id": s.id,
                "legajo": s.legajo,
                "first_name": s.first_name,
                "last_name": s.last_name,
                "subcomision": s.subcomision.name if s.subcomision else "Sin subcomisión",
            }
            for s in socios
        ]

    def get_resolucion_final(self, obj: SolicitudT01):
        if obj.expediente and obj.expediente.estado == EstadoExpedienteEnum.EMITIDO:
            return {
                "emitido": True,
                "fecha": obj.expediente.updated_at,
                "dictamen": f"Resolución firme emitida para causa {obj.expediente.numero}.",
            }
        return None
