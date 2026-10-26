"""Serializadores para el módulo de expedientes y descargos."""

import logging
from datetime import date
from decimal import Decimal
from zoneinfo import ZoneInfo

from django.utils import timezone
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from expedientes.domain.causal_resolution import (
    MIN_GROUNDS_LENGTH,
    CausalDecision,
    suggested_decision,
)
from expedientes.domain.descargo_rules import (
    MAX_DESCARGO_TEXT_LENGTH,
    descargo_text_too_long_message,
)
from expedientes.models import (
    DecisionCausalDescargo,
    DecisionCausalEnum,
    DescargoExpediente,
    DescargoVersion,
    EstadoExpedienteEnum,
    EvidenciaDescargo,
    Expediente,
    Holiday,
    SolicitudT01,
    TipoDescargoEnum,
    UrgenciaExpedienteEnum,
)
from expedientes.serializers.evento_serializers import (
    AsistenciaEventoBulkUpdateSerializer,
    AsistenciaEventoSerializer,
    AsistenciaItemInputSerializer,
    EventoInstitucionalCreateSerializer,
    EventoInstitucionalSerializer,
    RegistroApercibimientoSerializer,
    ReportarAsistenciaSerializer,
)
from expedientes.serializers.visor_serializers import ExpedienteVisorSerializer
from expedientes.services.causal_resolution_service import current_evidence_for
from padron.factory import get_padron_repository
from socios.models import Role, Socio, Subcomision

logger = logging.getLogger(__name__)


class EvidenciaMetadataSerializer(serializers.ModelSerializer):
    """Metadatos de un comprobante probatorio (sin contenido binario)."""

    socio_id = serializers.IntegerField(read_only=True)
    socio_nombre = serializers.SerializerMethodField()

    class Meta:
        model = EvidenciaDescargo
        fields = [
            "id",
            "socio_id",
            "socio_nombre",
            "nombre_original",
            "extension",
            "mime_type",
            "tamanio_bytes",
            "sha256_hash",
            "es_vigente",
            "created_at",
        ]
        read_only_fields = fields

    def get_socio_nombre(self, obj: EvidenciaDescargo) -> str:
        if obj.socio:
            return f"{obj.socio.first_name} {obj.socio.last_name}".strip()
        return ""


def _formatear_socio_creador(socio: Socio | None) -> str:
    if not socio:
        return ""
    last = (socio.last_name or "").strip()
    first = (socio.first_name or "").strip()
    legajo = (str(socio.legajo) if socio.legajo else "").strip()
    nombre_completo = f"{last}, {first}".strip().strip(",")
    if not nombre_completo:
        nombre_completo = str(socio)
    return f"{nombre_completo} ({legajo})" if legajo else nombre_completo


def _obtener_creador_expediente(obj: Expediente, context: dict | None = None) -> str:
    # 1. Si existe una solicitud T01, utilizar solicitud_t01.solicitante
    try:
        solicitud = getattr(obj, "solicitud_t01", None)
        if solicitud and solicitud.solicitante:
            return _formatear_socio_creador(solicitud.solicitante)
    except Exception:
        pass

    # 2. Si la causa se origina en inasistencia/evento/reunión (fallback con atributos dinámicos)
    reunion_autoridad = (
        getattr(obj, "creador_reunion", None)
        or getattr(obj, "autoridad_evento", None)
        or getattr(obj, "creador_evento", None)
    )
    if isinstance(reunion_autoridad, Socio):
        return _formatear_socio_creador(reunion_autoridad)

    # 3. En los demás casos, utilizar el actor del registro inicial de cambios_estado
    cambios = list(obj.cambios_estado.all()) if hasattr(obj, "cambios_estado") else []
    if cambios:
        primer_cambio = sorted(cambios, key=lambda c: (c.fecha_hora, c.id))[0]
        actor = (primer_cambio.actor or "").strip()
        if actor:
            actor_limpio = actor
            for prefix in ("SOLICITANTE_", "TD_", "CD_"):
                if actor_limpio.startswith(prefix):
                    actor_limpio = actor_limpio[len(prefix) :]
            # Optimización N+1: si el socio del expediente coincide con el actor
            if obj.socio and str(obj.socio.legajo) == actor_limpio:
                return _formatear_socio_creador(obj.socio)
            # Chequear en los socios precargados de la causa
            if hasattr(obj, "socios"):
                for s in obj.socios.all():
                    if str(s.legajo) == actor_limpio:
                        return _formatear_socio_creador(s)
            # Chequear o guardar en cache de context
            cache = None
            if context is not None:
                cache = context.setdefault("_socio_actor_cache", {})
                if actor_limpio in cache:
                    socio_cached = cache[actor_limpio]
                    return _formatear_socio_creador(socio_cached) if socio_cached else actor

            try:
                socio_actor = Socio.objects.filter(legajo=actor_limpio).first()
                if cache is not None:
                    cache[actor_limpio] = socio_actor
                if socio_actor:
                    return _formatear_socio_creador(socio_actor)
            except Exception:
                pass
            return actor

    return ""


def _obtener_razon_expediente(obj: Expediente) -> str:
    razon_directa = getattr(obj, "razon", None)
    if razon_directa and str(razon_directa).strip():
        return str(razon_directa).strip()
    try:
        solicitud = getattr(obj, "solicitud_t01", None)
        if solicitud:
            for attr in ("razon", "anexo_relato", "motivo"):
                val = getattr(solicitud, attr, None)
                if val and str(val).strip():
                    return str(val).strip()
    except Exception:
        pass
    return (obj.motivo or "").strip()


def _cargar_mapa_grupos_legado() -> dict[str, str]:
    """Obtiene en una única consulta el número de grupo (idGrupo) desde socio_estadoHistorial."""
    from django.db import connection

    mapa: dict[str, str] = {}
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT eh.nroSocio, se.nroLegajo, eh.idGrupo
                FROM socio_estadoHistorial eh
                LEFT JOIN socio_estudio se ON se.nroSocio = eh.nroSocio
                ORDER BY eh.fechaHora ASC, eh.idEstadoHistorial ASC
                """
            )
            for nro_socio, nro_legajo, id_grupo in cursor.fetchall():
                if id_grupo is not None:
                    grupo_str = str(id_grupo)
                    if nro_socio is not None:
                        mapa[str(nro_socio)] = grupo_str
                    if nro_legajo is not None:
                        mapa[str(nro_legajo)] = grupo_str
    except Exception:
        pass
    return mapa


def _serializar_socio_involucrado(
    socio: Socio, context: dict | None = None
) -> dict[str, int | str]:
    legajo = str(socio.legajo or "").strip()
    grupo = ""
    if context is not None:
        if "_socio_grupo_cache" not in context:
            context["_socio_grupo_cache"] = _cargar_mapa_grupos_legado()
        grupo = context["_socio_grupo_cache"].get(legajo, "")
    if not grupo and getattr(socio, "social_year", 0) and int(socio.social_year) > 0:
        # Cálculo dinámico anual: en el año Y, el 1° año social corresponde al grupo (Y - 1963)
        current_year = timezone.localdate().year
        grupo = str((current_year - 1962) - int(socio.social_year))

    if not getattr(socio, "is_enabled", True):
        estado = "Inactivo"
    else:
        estado = (
            socio.get_category_display() if hasattr(socio, "get_category_display") else "Activo"
        )

    return {
        "id": socio.id,
        "legajo": legajo,
        "nombre": f"{socio.first_name} {socio.last_name}".strip(),
        "first_name": socio.first_name,
        "last_name": socio.last_name,
        "grupo": grupo,
        "estado": estado,
    }


def _obtener_titulo_expediente(obj: Expediente) -> str:
    try:
        solicitud = getattr(obj, "solicitud_t01", None)
        if solicitud and getattr(solicitud, "titulo", None) and solicitud.titulo.strip():
            return solicitud.titulo.strip()
    except Exception:
        pass

    titulo_evento = getattr(obj, "titulo_evento", None) or getattr(obj, "titulo_hecho", None)
    if titulo_evento and str(titulo_evento).strip():
        return str(titulo_evento).strip()

    return obj.motivo or ""


def _obtener_reglamento_asociado(obj: Expediente) -> str:
    try:
        solicitud = getattr(obj, "solicitud_t01", None)
        if solicitud and solicitud.causal:
            return solicitud.causal
        if solicitud and solicitud.reglamentos_respaldantes:
            return solicitud.reglamentos_respaldantes[0]
    except Exception:
        pass
    return "Reglamento Procesal Disciplinario 2026"


def _obtener_reglamentos_respaldantes(obj: Expediente) -> list[str]:
    try:
        solicitud = getattr(obj, "solicitud_t01", None)
        if solicitud:
            if (
                solicitud.reglamentos_respaldantes
                and isinstance(solicitud.reglamentos_respaldantes, list)
                and len(solicitud.reglamentos_respaldantes) > 0
            ):
                return [str(r) for r in solicitud.reglamentos_respaldantes if str(r).strip()]
            if solicitud.causal and str(solicitud.causal).strip():
                return [str(solicitud.causal).strip()]
    except Exception:
        pass
    return [_obtener_reglamento_asociado(obj)]


class ExpedienteResumenSerializer(serializers.ModelSerializer):
    """Serializador acotado para consulta pública/autenticada de expedientes por socio."""

    titulo = serializers.SerializerMethodField()
    urgencia_display = serializers.CharField(source="get_urgencia_display", read_only=True)

    class Meta:
        model = Expediente
        fields = [
            "id",
            "numero",
            "titulo",
            "motivo",
            "puntos",
            "estado",
            "urgencia",
            "urgencia_display",
            "created_at",
        ]

    def get_titulo(self, obj: Expediente) -> str:
        return _obtener_titulo_expediente(obj)


class ExpedienteListSerializer(serializers.ModelSerializer):
    """Serializador para listado y detalle de expedientes."""

    socio_nombre = serializers.SerializerMethodField()
    socio_legajo = serializers.CharField(source="socio.legajo", read_only=True)
    subcomision = serializers.CharField(source="socio.subcomision.name", default="", read_only=True)
    urgencia_display = serializers.CharField(source="get_urgencia_display", read_only=True)
    reglamento_asociado = serializers.SerializerMethodField()
    reglamentos_respaldantes = serializers.SerializerMethodField()
    descargo_presentado = serializers.SerializerMethodField()
    descargo_tipo = serializers.SerializerMethodField()
    descargo_causal = serializers.SerializerMethodField()
    descargo_archivo = serializers.SerializerMethodField()
    descargo_texto = serializers.SerializerMethodField()
    descargo_presentado_at = serializers.SerializerMethodField()
    esta_en_plazo = serializers.SerializerMethodField()
    horas_restantes = serializers.SerializerMethodField()
    socios = serializers.SerializerMethodField()
    cantidad_socios = serializers.SerializerMethodField()
    creador = serializers.SerializerMethodField()
    solicitante = serializers.SerializerMethodField()
    razon = serializers.SerializerMethodField()
    titulo = serializers.SerializerMethodField()
    historial = serializers.SerializerMethodField()
    evidencias = serializers.SerializerMethodField()
    descargos = serializers.SerializerMethodField()
    es_t01 = serializers.SerializerMethodField()

    class Meta:
        model = Expediente
        fields = [
            "id",
            "numero",
            "titulo",
            "motivo",
            "razon",
            "reglamento_asociado",
            "reglamentos_respaldantes",
            "puntos",
            "estado",
            "urgencia",
            "urgencia_display",
            "socio_nombre",
            "socio_legajo",
            "creador",
            "solicitante",
            "socios",
            "cantidad_socios",
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
            "evidencias",
            "descargos",
            "es_t01",
        ]

    def get_socio_nombre(self, obj: Expediente) -> str:
        return f"{obj.socio.first_name} {obj.socio.last_name}"

    def get_cantidad_socios(self, obj: Expediente) -> int:
        socios = list(obj.socios.all())
        count = len(socios)
        return count if count > 0 else 1

    def get_creador(self, obj: Expediente) -> str:
        return _obtener_creador_expediente(obj, context=self.context)

    def get_solicitante(self, obj: Expediente) -> str:
        return _obtener_creador_expediente(obj, context=self.context)

    def get_razon(self, obj: Expediente) -> str:
        return _obtener_razon_expediente(obj)

    def get_titulo(self, obj: Expediente) -> str:
        return _obtener_titulo_expediente(obj)

    def get_reglamento_asociado(self, obj: Expediente) -> str:
        return _obtener_reglamento_asociado(obj)

    def get_reglamentos_respaldantes(self, obj: Expediente) -> list[str]:
        return _obtener_reglamentos_respaldantes(obj)

    def _descargo_for_requester(self, obj: Expediente) -> DescargoExpediente | None:
        descargos = [d for d in obj.descargos.all() if d.es_vigente]
        if not descargos:
            return None
        request = self.context.get("request")
        if not request:
            return descargos[0]
        user = getattr(request, "user", None)
        socio = getattr(user, "socio", None) if user else None
        role = getattr(socio, "role", "")
        # Si es TD/CD/Admin o staff, puede consultar los descargos de la causa
        if (socio and socio.is_enabled and role in (Role.TD, Role.CD, Role.ADMIN)) or (
            user and user.is_staff
        ):
            return next(
                (d for d in descargos if d.socio_id == obj.socio_id),
                descargos[0],
            )
        if socio is None:
            return None
        return next((d for d in descargos if d.socio_id == socio.pk), None)

    def get_descargo_presentado(self, obj: Expediente) -> bool:
        request = self.context.get("request")
        user = getattr(request, "user", None)
        socio = getattr(user, "socio", None) if user else None
        role = getattr(socio, "role", "")
        if (socio and socio.is_enabled and role in (Role.TD, Role.CD, Role.ADMIN)) or (
            user and user.is_staff
        ):
            vigentes = [d for d in obj.descargos.all() if d.es_vigente]
            return bool(vigentes or obj.descargo_presentado)
        descargo = self._descargo_for_requester(obj)
        if descargo:
            return True
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
        socios = list(obj.socios.all())
        if not socios and obj.socio:
            socios = [obj.socio]
        return [_serializar_socio_involucrado(socio, self.context) for socio in socios]

    def get_evidencias(self, obj: Expediente) -> list[dict]:
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return []
        socio = getattr(user, "socio", None)
        role = getattr(socio, "role", "")
        # Usar .all() precargado por prefetch_related para no disparar
        # queries adicionales por cada expediente
        todas = obj.evidencias.all()
        if (socio and socio.is_enabled and role in (Role.TD, Role.CD, Role.ADMIN)) or user.is_staff:
            vigentes = [ev for ev in todas if ev.es_vigente]
        elif socio and socio.is_enabled:
            vigentes = [ev for ev in todas if ev.es_vigente and ev.socio_id == socio.pk]
        else:
            return []
        return EvidenciaMetadataSerializer(vigentes, many=True).data

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

    def get_es_t01(self, obj: Expediente) -> bool:
        """En los expedientes de T01 se apela en lugar de presentar T02/T03 (PB-02)."""
        try:
            return obj.solicitud_t01 is not None
        except SolicitudT01.DoesNotExist:
            return False

    def get_descargos(self, obj: Expediente) -> list[dict]:
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return []
        socio = getattr(user, "socio", None)
        role = getattr(socio, "role", "")
        is_authority = (
            socio and socio.is_enabled and role in (Role.TD, Role.CD, Role.ADMIN)
        ) or user.is_staff

        descargos_list = [d for d in obj.descargos.all() if d.es_vigente]
        if not is_authority and socio:
            descargos_list = [d for d in descargos_list if d.socio_id == socio.pk]
        elif not is_authority:
            return []

        # Mismo criterio que el servicio de decisión, sobre las evidencias ya prefetcheadas.
        evidencias = list(obj.evidencias.all())

        result = []
        for d in descargos_list:
            evs = current_evidence_for(d, evidencias)
            decisiones_qs = list(d.decisiones_causal.all())
            leido = bool(decisiones_qs)
            puntaje_ratificado = None
            if decisiones_qs:
                primera = decisiones_qs[0]
                if primera.decision == DecisionCausalEnum.ACCEPTED:
                    puntaje_ratificado = 0
                elif primera.decision == DecisionCausalEnum.REJECTED:
                    puntaje_ratificado = float(obj.puntos) if obj.puntos is not None else 0.0

            item = {
                "id": d.id,
                "socio_id": d.socio_id,
                "socio_legajo": d.socio.legajo if d.socio else "",
                "socio_nombre": f"{d.socio.first_name} {d.socio.last_name}".strip()
                if d.socio
                else "",
                "socio_first_name": d.socio.first_name if d.socio else "",
                "socio_last_name": d.socio.last_name if d.socio else "",
                "tipo": d.tipo,
                "causal": d.causal,
                "archivo": d.archivo,
                "texto": d.texto,
                "presentado_at": d.presentado_at.isoformat() if d.presentado_at else None,
                "evidencias": EvidenciaMetadataSerializer(evs, many=True).data,
                "leido": leido,
                "puntaje_ratificado": puntaje_ratificado,
            }
            # La valoración del TD es reservada hasta la emisión (confidencialidad).
            if is_authority:
                item["decisiones_causal"] = DecisionCausalSerializer(decisiones_qs, many=True).data
                if d.tipo == TipoDescargoEnum.T02_CERTIFICADO:
                    item["regla_sugerida"] = suggested_decision(
                        has_current_evidence=bool(evs)
                    ).value
            result.append(item)
        return result


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


class EvidenciaVersionSerializer(EvidenciaMetadataSerializer):
    """Metadatos de una evidencia dentro de una versión (sin la vigencia actual)."""

    class Meta(EvidenciaMetadataSerializer.Meta):
        fields = [f for f in EvidenciaMetadataSerializer.Meta.fields if f != "es_vigente"]
        read_only_fields = fields


class DescargoVersionSerializer(serializers.ModelSerializer):
    """Versión inmutable de un descargo para el historial por API (SCRUM-49)."""

    operacion_display = serializers.CharField(source="get_operacion_display", read_only=True)
    socio_id = serializers.IntegerField(source="descargo.socio_id", read_only=True)
    socio_legajo = serializers.CharField(source="descargo.socio.legajo", read_only=True)
    socio_nombre = serializers.SerializerMethodField()
    evidencias = EvidenciaVersionSerializer(many=True, read_only=True)

    class Meta:
        model = DescargoVersion
        fields = [
            "id",
            "numero",
            "operacion",
            "operacion_display",
            "tipo",
            "causal",
            "texto",
            "archivo",
            "evidencias",
            "actor",
            "socio_id",
            "socio_legajo",
            "socio_nombre",
            "created_at",
        ]
        read_only_fields = fields

    def get_socio_nombre(self, obj: DescargoVersion) -> str:
        socio = obj.descargo.socio
        return f"{socio.first_name} {socio.last_name}".strip()


class DescargoExpedienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = DescargoExpediente
        fields = ["id", "socio", "tipo", "causal", "archivo", "texto", "presentado_at"]


class DecisionCausalSerializer(serializers.ModelSerializer):
    """Decisión versionada sobre una causal T02 (S4-02, CA1 y CA3)."""

    decision_display = serializers.CharField(source="get_decision_display", read_only=True)
    regla_sugerida_display = serializers.CharField(
        source="get_regla_sugerida_display", read_only=True
    )
    autor = serializers.CharField(source="autor.get_username", read_only=True)

    class Meta:
        model = DecisionCausalDescargo
        fields = [
            "id",
            "descargo",
            "version",
            "decision",
            "decision_display",
            "regla_sugerida",
            "regla_sugerida_display",
            "se_aparta_de_regla",
            "fundamento",
            "evidencias_valoradas",
            "descargo_snapshot",
            "autor",
            "autor_legajo",
            "autor_rol",
            "created_at",
        ]
        read_only_fields = fields


class RegistrarDecisionCausalSerializer(serializers.Serializer):
    """Payload de la decisión del miembro del TD sobre una causal T02."""

    decision = serializers.ChoiceField(choices=[(d.value, d.value) for d in CausalDecision])
    fundamento = serializers.CharField(
        required=False,
        allow_blank=True,
        default="",
        max_length=5000,
        help_text=f"Obligatorio (mín. {MIN_GROUNDS_LENGTH} caracteres) al rechazar o apartarse.",
    )
    evidencia_ids = serializers.ListField(
        child=serializers.UUIDField(), required=False, allow_empty=True
    )


class PlazoApelacionSerializer(serializers.Serializer):
    """Plazo de apelación del T01 en días hábiles (PB-02)."""

    dias_habiles = serializers.IntegerField()


class ApelarT01Serializer(serializers.Serializer):
    """Apelación del socio involucrado en un T01 (PB-02)."""

    texto = serializers.CharField(allow_blank=True, max_length=10000)


class AdecuarT01Serializer(serializers.Serializer):
    """Adecuación de puntos e involucrados decidida en el debate del TD (PB-02)."""

    puntos = serializers.DecimalField(max_digits=10, decimal_places=2)
    socios = serializers.ListField(child=serializers.IntegerField(min_value=1), allow_empty=True)
    motivos = serializers.CharField(allow_blank=True, max_length=5000)
    reabrir_plazo = serializers.BooleanField(default=False)


class PresentarDescargoSerializer(serializers.Serializer):
    """Payload para presentación de descargo T02/T03."""

    tipo = serializers.ChoiceField(choices=TipoDescargoEnum.choices)
    causal = serializers.CharField(max_length=255, required=False, allow_blank=True)
    archivo = serializers.CharField(max_length=255, required=False, allow_blank=True)
    texto = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=MAX_DESCARGO_TEXT_LENGTH,
        error_messages={"max_length": descargo_text_too_long_message()},
    )
    evidencia_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        allow_empty=True,
        default=list,
    )

    def validate(self, attrs: dict) -> dict:
        tipo = attrs.get("tipo")
        evidencia_ids = attrs.get("evidencia_ids", [])
        if tipo == TipoDescargoEnum.T02_CERTIFICADO:
            if not attrs.get("archivo") and not evidencia_ids:
                raise serializers.ValidationError(
                    {"archivo": "Es obligatorio adjuntar comprobante para justificaciones T02."}
                )
            if len(evidencia_ids) > 3:
                raise serializers.ValidationError(
                    {"evidencia_ids": "El Formulario T02 admite un máximo de 3 comprobantes."}
                )
        elif tipo == TipoDescargoEnum.T03_EXTRAORDINARIO:
            texto = attrs.get("texto", "").strip()
            if not texto:
                raise serializers.ValidationError(
                    {"texto": "Es obligatorio incluir la exposición fáctica para descargos T03."}
                )
            if len(texto) > MAX_DESCARGO_TEXT_LENGTH:
                raise serializers.ValidationError({"texto": descargo_text_too_long_message()})
            if len(evidencia_ids) > 5:
                raise serializers.ValidationError(
                    {"evidencia_ids": "El Formulario T03 admite un máximo de 5 comprobantes."}
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
        "grupo": getattr(socio, "grupo", None),
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
    socios = serializers.SerializerMethodField()
    creador = serializers.SerializerMethodField()
    solicitante = serializers.SerializerMethodField()
    razon = serializers.SerializerMethodField()
    titulo = serializers.SerializerMethodField()
    reglamento_asociado = serializers.SerializerMethodField()
    reglamentos_respaldantes = serializers.SerializerMethodField()

    class Meta:
        model = Expediente
        fields = [
            "id",
            "numero",
            "titulo",
            "motivo",
            "razon",
            "reglamento_asociado",
            "reglamentos_respaldantes",
            "socio",
            "socio_nombre",
            "socio_legajo",
            "creador",
            "solicitante",
            "socios",
            "subcomision",
            "estado",
            "estado_display",
            "urgencia",
            "urgencia_display",
            "puntos",
            "created_at",
            "plazo_limite_at",
            "transiciones_permitidas",
            "cantidad_socios",
        ]

    def get_socio_nombre(self, obj: Expediente) -> str:
        return f"{obj.socio.first_name} {obj.socio.last_name}"

    def get_cantidad_socios(self, obj: Expediente) -> int:
        socios = list(obj.socios.all())
        count = len(socios)
        return count if count > 0 else 1

    def get_socios(self, obj: Expediente) -> list[dict[str, int | str]]:
        socios = list(obj.socios.all())
        if not socios and obj.socio:
            socios = [obj.socio]
        return [_serializar_socio_involucrado(socio, self.context) for socio in socios]

    def get_creador(self, obj: Expediente) -> str:
        return _obtener_creador_expediente(obj, context=self.context)

    def get_solicitante(self, obj: Expediente) -> str:
        return _obtener_creador_expediente(obj, context=self.context)

    def get_razon(self, obj: Expediente) -> str:
        return _obtener_razon_expediente(obj)

    def get_titulo(self, obj: Expediente) -> str:
        return _obtener_titulo_expediente(obj)

    def get_reglamento_asociado(self, obj: Expediente) -> str:
        return _obtener_reglamento_asociado(obj)

    def get_reglamentos_respaldantes(self, obj: Expediente) -> list[str]:
        return _obtener_reglamentos_respaldantes(obj)

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
                    "grupo": s.get("grupo"),
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
                    "grupo": s.get("grupo"),
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
                "grupo": getattr(s, "grupo", None),
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


class HolidaySerializer(serializers.ModelSerializer):
    """Feriados con fecha única y auditoría asignada por el servidor."""

    fecha = serializers.DateField(
        source="date",
        validators=[
            UniqueValidator(
                queryset=Holiday.objects.all(), message="Ya existe un feriado para esa fecha."
            )
        ],
    )
    descripcion = serializers.CharField(source="description", max_length=200)
    creado_por = serializers.PrimaryKeyRelatedField(source="created_by", read_only=True)
    creado_por_nombre = serializers.SerializerMethodField()

    class Meta:
        model = Holiday
        fields = ["id", "fecha", "descripcion", "creado_por", "creado_por_nombre", "created_at"]
        read_only_fields = ["id", "created_at"]

    def validate_fecha(self, value: date) -> date:
        today = timezone.localdate(timezone=ZoneInfo("America/Argentina/Buenos_Aires"))
        if value < today:
            raise serializers.ValidationError("La fecha debe ser hoy o posterior.")
        return value

    def get_creado_por_nombre(self, obj: Holiday) -> str:
        if obj.created_by_id is None:
            return (
                "Sistema (carga inicial)"
                if obj.origin == Holiday.Origin.SYSTEM
                else "Autor no registrado (registro previo)"
            )
        user = obj.created_by
        socio = getattr(user, "socio", None)
        name = (
            f"{socio.first_name} {socio.last_name}".strip()
            if socio is not None
            else user.get_full_name().strip()
        )
        username = user.get_username()
        return f"{name} ({username})" if name else username


class CalendarQuerySerializer(serializers.Serializer):
    """Valida los únicos filtros y el orden de la consulta institucional."""

    year = serializers.IntegerField(min_value=1, max_value=9999, required=False)
    month = serializers.IntegerField(min_value=1, max_value=12, required=False)
    ordering = serializers.ChoiceField(choices=["fecha", "-fecha"], default="fecha")


class CalcularPlazoSerializer(serializers.Serializer):
    """Entrada del simulador del calendario institucional."""

    start_at = serializers.DateTimeField(
        default_timezone=ZoneInfo("America/Argentina/Buenos_Aires")
    )
    business_days = serializers.IntegerField(min_value=1, default=5)


__all__ = [
    "AsistenciaEventoBulkUpdateSerializer",
    "AsistenciaEventoSerializer",
    "AsistenciaItemInputSerializer",
    "EventoInstitucionalCreateSerializer",
    "EventoInstitucionalSerializer",
    "ExpedienteResumenSerializer",
    "RegistroApercibimientoSerializer",
    "ReportarAsistenciaSerializer",
    "ExpedienteVisorSerializer",
]
