"""Serializadores y utilidades de dominio para el Visor Autorizado de Expedientes (US S4-01 / SCRUM-51).

Implementa:
- CA1: Visor dedicado con cabecera oficial TD, composición colegiada de 3 jueces con grupo Gxx y timeline cronológico.
- CA2: Confidencialidad médica estricta (RBAC por campo/objeto: TD, CD, ADMIN y socio imputado titular).
- CA3: Trazabilidad de auditoría de consultas y descargas.
- CA4: Integridad documental SHA-256 (flags sha256_valido, archivo_danado) y rotulado explícito de 'Plazo vencido sin descargo'.
"""

import hashlib
import re
from typing import Any

from django.db import connection
from django.utils import timezone
from rest_framework import serializers

from expedientes.domain.causal_resolution import suggested_decision
from expedientes.models import (
    AuditoriaDescargaEvidencia,
    DecisionCausalDescargo,
    DescargoExpediente,
    EstadoExpedienteEnum,
    EvidenciaDescargo,
    Expediente,
    TipoDescargoEnum,
)
from expedientes.services.causal_resolution_service import current_evidence_for
from socios.models import Role, Socio


def check_evidencia_integrity(ev: EvidenciaDescargo) -> tuple[bool, bool]:
    """Verifica si el hash SHA-256 del contenido binario almacenado concuerda con sha256_hash registrado.

    Retorna (sha256_valido, archivo_danado).
    """
    if not ev.contenido_blob:
        return False, True
    try:
        data = bytes(ev.contenido_blob)
        digest = hashlib.sha256(data).hexdigest().lower()
        expected = (ev.sha256_hash or "").strip().lower()
        if expected and digest == expected:
            return True, False
        return False, True
    except Exception:
        return False, True


def es_causal_medica(causal: str, texto: str = "") -> bool:
    """Detecta si una causal o descargo contiene información médica o de salud protegida."""
    target = f"{causal or ''} {texto or ''}".lower()
    keywords = [
        "médic",
        "medic",
        "salud",
        "enfermedad",
        "diagnóstic",
        "diagnostic",
        "reposo",
        "tratamiento",
        "clínic",
        "clinic",
        "hospital",
        "certificado médico",
    ]
    return any(kw in target for kw in keywords)


def tiene_acceso_medico(user: Any, socio_imputado_id: int) -> bool:
    """Verifica si el usuario solicitante tiene autorización para ver datos médicos reservados (CA2).

    Autorizados:
    - Integrantes de TD, CD y ADMIN.
    - Staff / Administradores de Cómputos.
    - El propio socio imputado titular de su justificación.
    """
    if not user or not user.is_authenticated:
        return False
    if user.is_staff or user.is_superuser:
        return True
    socio = getattr(user, "socio", None)
    if not socio or not socio.is_enabled:
        return False
    if socio.role in (Role.TD, Role.CD, Role.ADMIN):
        return True
    return socio.id == socio_imputado_id


def cargar_mapa_grupos() -> dict[str, str]:
    """Carga mapa de grupo social (idGrupo) por nroSocio / nroLegajo desde la base de datos."""
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
                    grupo_str = f"G{id_grupo}" if not str(id_grupo).startswith("G") else str(id_grupo)
                    if nro_socio is not None:
                        mapa[str(nro_socio)] = grupo_str
                    if nro_legajo is not None:
                        mapa[str(nro_legajo)] = grupo_str
    except Exception:
        pass
    return mapa


def obtener_responsables_td() -> list[dict[str, Any]]:
    """Devuelve la composición canónica oficial de los 3 vocales del TD con cohorte Gxx."""
    vocales = list(
        Socio.objects.filter(role=Role.TD, is_enabled=True)
        .select_related("subcomision")
        .order_by("id")
    )
    mapa_grupos = cargar_mapa_grupos()
    default_fallbacks = [
        {"legajo": "11239", "nombre": "Giuliano Toselli", "grupo": "G57"},
        {"legajo": "11737", "nombre": "Catalina Cerda Gallego", "grupo": "G58"},
        {"legajo": "11735", "nombre": "Candela Moreno Migliore", "grupo": "G59"},
    ]

    responsables = []
    for i in range(3):
        titulo = f"Vocal {i + 1}"
        if i < len(vocales):
            soc = vocales[i]
            legajo = str(soc.legajo or "").strip()
            nombre = f"{soc.first_name} {soc.last_name}".strip()
            grupo = mapa_grupos.get(legajo, "")
            if not grupo and getattr(soc, "social_year", 0):
                current_year = timezone.localdate().year
                grupo = f"G{(current_year - 1962) - int(soc.social_year)}"
            if not grupo:
                grupo = default_fallbacks[i]["grupo"]
            responsables.append({
                "titulo": titulo,
                "legajo": legajo,
                "nombre": nombre,
                "grupo": grupo,
                "es_suplente": False,
                "display": f"{legajo} - {nombre} - {grupo}",
            })
        else:
            fb = default_fallbacks[i]
            responsables.append({
                "titulo": titulo,
                "legajo": fb["legajo"],
                "nombre": fb["nombre"],
                "grupo": fb["grupo"],
                "es_suplente": False,
                "display": f"{fb['legajo']} - {fb['nombre']} - {fb['grupo']}",
            })
    return responsables


def construir_timeline(expediente: Expediente) -> list[dict[str, Any]]:
    """Construye la línea de tiempo procesal unificada y cronológica (CA1).

    Garantiza:
    - Orden descendente: lo más reciente primero.
    - Formateo consistente de actores: 'Nombre Apellido (Legajo)'.
    - Inclusión discreta de descargas de piezas probatorias (AuditoriaDescargaEvidencia).
    """
    hitos: list[dict[str, Any]] = []

    # Mapa de socios para normalizar a formato 'Nombre Apellido (Legajo)'
    socios_por_legajo: dict[str, str] = {
        str(s.legajo).strip(): f"{s.first_name} {s.last_name} ({s.legajo})".strip()
        for s in Socio.objects.all().only("legajo", "first_name", "last_name")
    }

    def formatear_actor(actor_raw: Any) -> str:
        if not actor_raw:
            return "SISTEMA"
        raw = str(actor_raw).strip()
        if raw.startswith("SOCIO_"):
            raw = raw.replace("SOCIO_", "").strip()
        m = re.search(r"(\d{4,7})", raw)
        if m:
            legajo_encontrado = m.group(1)
            if legajo_encontrado in socios_por_legajo:
                return socios_por_legajo[legajo_encontrado]
        if raw in socios_por_legajo:
            return socios_por_legajo[raw]
        return raw

    # 1. Hito de apertura formal / Solicitud T01
    creador_display = "Comisión Directiva / Autoridad Solicitante"
    solicitud = getattr(expediente, "solicitud_t01", None)
    if solicitud and solicitud.solicitante:
        s = solicitud.solicitante
        creador_display = formatear_actor(s.legajo)

    fecha_creacion = expediente.created_at or timezone.now()
    hitos.append({
        "id": f"creacion-{expediente.id}",
        "fecha_hora": fecha_creacion.isoformat(),
        "tipo": "CREACION",
        "tipo_display": "Apertura formal de expediente",
        "titulo": f"Apertura formal: {expediente.numero}",
        "descripcion": f"Causa formalizada con motivo: '{expediente.motivo}'.",
        "actor": creador_display,
        "icono": "folder_open",
        "color": "#1e3a8a",
    })

    # 2. Hito de notificación y plazo preclusivo (si aplica)
    if expediente.plazo_inicio_at:
        limite_str = (
            expediente.plazo_limite_at.strftime("%d/%m/%Y %H:%M hs")
            if expediente.plazo_limite_at
            else "s/d"
        )
        hitos.append({
            "id": f"plazo-{expediente.id}",
            "fecha_hora": expediente.plazo_inicio_at.isoformat(),
            "tipo": "NOTIFICACION_PLAZO",
            "tipo_display": "Notificación procesal de apertura",
            "titulo": "Inicio de plazo de justificaciones (5 días hábiles)",
            "descripcion": f"Plazo perentorio congelado hasta el {limite_str}.",
            "actor": "Tribunal de Disciplina",
            "icono": "schedule",
            "color": "#d97706",
        })

    # 3. Presentaciones de descargos (incluye versiones históricas si existen)
    for d in expediente.descargos.all():
        fecha_desc = d.presentado_at or expediente.created_at or timezone.now()
        soc_display = (
            formatear_actor(d.socio.legajo)
            if d.socio
            else "Socio imputado"
        )
        hitos.append({
            "id": f"descargo-{d.id}",
            "fecha_hora": fecha_desc.isoformat(),
            "tipo": "DESCARGO",
            "tipo_display": f"Presentación de {d.get_tipo_display()}",
            "titulo": f"Descargo presentado por {soc_display}",
            "descripcion": f"Modalidad: {d.get_tipo_display()}. Estado: {'Vigente' if d.es_vigente else 'Retirado'}.",
            "actor": soc_display,
            "icono": "description",
            "color": "#059669",
        })

    # 4. Decisiones tomadas por vocales sobre causales T02 (S4-02)
    for dec in expediente.decisiones_causal.all():
        autor_fmt = formatear_actor(dec.autor_legajo)
        hitos.append({
            "id": f"decision-causal-{dec.id}",
            "fecha_hora": dec.created_at.isoformat(),
            "tipo": "DECISION_CAUSAL",
            "tipo_display": f"Valoración de causal T02 (v{dec.version})",
            "titulo": f"Decisión de causal: {dec.get_decision_display()} (v{dec.version})",
            "descripcion": f"Resolución: {dec.get_decision_display()}. Fundamento: {dec.fundamento or 'Sin observaciones'}.",
            "actor": autor_fmt,
            "icono": "gavel",
            "color": "#7c3aed",
        })

    # 5. Historial de transiciones de estado
    for c in expediente.cambios_estado.all():
        if c.estado_anterior:
            actor_c = formatear_actor(c.actor)
            hitos.append({
                "id": f"cambio-estado-{c.id}",
                "fecha_hora": c.fecha_hora.isoformat(),
                "tipo": "CAMBIO_ESTADO",
                "tipo_display": f"Transición de estado: {c.estado_nuevo}",
                "titulo": f"Estado procesal actualizado: {c.estado_nuevo}",
                "descripcion": f"Motivo registrado: {c.motivo or 'Cambio formal de etapa procesal'}.",
                "actor": actor_c,
                "icono": "sync_alt",
                "color": "#2563eb",
            })

    # 6. Descargas y consultas de documentos probatorios auditadas (AuditoriaDescargaEvidencia)
    descargas = (
        AuditoriaDescargaEvidencia.objects.filter(
            evidencia__descargo__expediente=expediente
        )
        .select_related("evidencia")
        .order_by("fecha_hora")
    )
    for dsc in descargas:
        actor_dsc = formatear_actor(dsc.usuario)
        doc_nombre = dsc.evidencia.nombre_original if dsc.evidencia else "Documento probatorio"
        es_consulta = "[CONSULTA]" in (dsc.user_agent or "")

        if es_consulta:
            tipo_key = "CONSULTA_DOCUMENTO"
            tipo_disp = "Consulta de documento"
            titulo = f"Consulta: {doc_nombre}"
            desc = f"Documento '{doc_nombre}' consultado en pantalla."
            icono = "visibility"
        else:
            tipo_key = "DESCARGA_DOCUMENTO"
            tipo_disp = "Descarga de documento"
            titulo = f"Descarga: {doc_nombre}"
            desc = f"Documento '{doc_nombre}' descargado."
            icono = "file_download"

        hitos.append({
            "id": f"descarga-{dsc.id}",
            "fecha_hora": dsc.fecha_hora.isoformat(),
            "tipo": tipo_key,
            "tipo_display": tipo_disp,
            "titulo": titulo,
            "descripcion": desc,
            "actor": actor_dsc,
            "icono": icono,
            "color": "#94a3b8",
            "es_secundario": True,
        })

    # Orden descendente canónico: lo más nuevo primero
    hitos.sort(key=lambda h: h["fecha_hora"], reverse=True)
    return hitos


class DecisionCausalVisorSerializer(serializers.ModelSerializer):
    decision_display = serializers.CharField(source="get_decision_display", read_only=True)
    regla_sugerida_display = serializers.CharField(
        source="get_regla_sugerida_display", read_only=True
    )

    class Meta:
        model = DecisionCausalDescargo
        fields = [
            "id",
            "descargo_id",
            "version",
            "decision",
            "decision_display",
            "regla_sugerida",
            "regla_sugerida_display",
            "se_aparta_de_regla",
            "fundamento",
            "evidencias_valoradas",
            "autor_id",
            "autor_legajo",
            "autor_rol",
            "created_at",
        ]


class EvidenciaVisorSerializer(serializers.ModelSerializer):
    sha256_valido = serializers.SerializerMethodField()
    archivo_danado = serializers.SerializerMethodField()

    class Meta:
        model = EvidenciaDescargo
        fields = [
            "id",
            "nombre_original",
            "extension",
            "mime_type",
            "tamanio_bytes",
            "sha256_hash",
            "sha256_valido",
            "archivo_danado",
            "es_vigente",
            "created_at",
        ]
        read_only_fields = fields

    def get_sha256_valido(self, obj: EvidenciaDescargo) -> bool:
        valido, _ = check_evidencia_integrity(obj)
        return valido

    def get_archivo_danado(self, obj: EvidenciaDescargo) -> bool:
        _, danado = check_evidencia_integrity(obj)
        return danado


class ExpedienteVisorSerializer(serializers.ModelSerializer):
    """Serializador consolidado para el Visor Autorizado de Expedientes (US S4-01 / SCRUM-51)."""

    anio = serializers.SerializerMethodField()
    titulo = serializers.SerializerMethodField()
    razon = serializers.SerializerMethodField()
    causal = serializers.SerializerMethodField()
    reglamento_asociado = serializers.SerializerMethodField()
    reglamentos_respaldantes = serializers.SerializerMethodField()
    estado_display = serializers.CharField(source="get_estado_display", read_only=True)
    urgencia_display = serializers.CharField(source="get_urgencia_display", read_only=True)
    fecha_solicitud = serializers.DateTimeField(source="created_at", read_only=True)
    solicitante = serializers.SerializerMethodField()
    anexo = serializers.SerializerMethodField()
    esta_en_plazo = serializers.SerializerMethodField()
    horas_restantes = serializers.SerializerMethodField()
    responsables_td = serializers.SerializerMethodField()
    involucrados = serializers.SerializerMethodField()
    timeline = serializers.SerializerMethodField()
    puede_resolver_causal = serializers.SerializerMethodField()
    puede_dictar_resolucion = serializers.SerializerMethodField()

    class Meta:
        model = Expediente
        fields = [
            "id",
            "numero",
            "anio",
            "titulo",
            "motivo",
            "razon",
            "causal",
            "reglamento_asociado",
            "reglamentos_respaldantes",
            "puntos",
            "estado",
            "estado_display",
            "urgencia",
            "urgencia_display",
            "fecha_solicitud",
            "created_at",
            "solicitante",
            "anexo",
            "plazo_inicio_at",
            "plazo_limite_at",
            "esta_en_plazo",
            "horas_restantes",
            "responsables_td",
            "involucrados",
            "timeline",
            "puede_resolver_causal",
            "puede_dictar_resolucion",
        ]

    def get_anio(self, obj: Expediente) -> int:
        if obj.numero and "/" in obj.numero:
            part = obj.numero.split("/")[-1].strip()
            if part.isdigit():
                return int(part)
        if obj.created_at:
            return obj.created_at.year
        return timezone.localdate().year

    def get_titulo(self, obj: Expediente) -> str:
        solicitud = getattr(obj, "solicitud_t01", None)
        if solicitud and getattr(solicitud, "titulo", None) and solicitud.titulo.strip():
            return solicitud.titulo.strip()
        titulo_evento = getattr(obj, "titulo_evento", None) or getattr(obj, "titulo_hecho", None)
        if titulo_evento and str(titulo_evento).strip():
            return str(titulo_evento).strip()
        return obj.motivo or ""

    def get_razon(self, obj: Expediente) -> str:
        razon_directa = getattr(obj, "razon", None)
        if razon_directa and str(razon_directa).strip():
            return str(razon_directa).strip()
        solicitud = getattr(obj, "solicitud_t01", None)
        if solicitud:
            for attr in ("razon", "anexo_relato", "motivo"):
                val = getattr(solicitud, attr, None)
                if val and str(val).strip():
                    return str(val).strip()
        return (obj.motivo or "").strip()

    def get_causal(self, obj: Expediente) -> str:
        solicitud = getattr(obj, "solicitud_t01", None)
        if solicitud and getattr(solicitud, "causal", None) and solicitud.causal.strip():
            return solicitud.causal.strip()
        return obj.descargo_causal or ""

    def get_reglamento_asociado(self, obj: Expediente) -> str:
        solicitud = getattr(obj, "solicitud_t01", None)
        if solicitud and solicitud.causal:
            return solicitud.causal
        if solicitud and solicitud.reglamentos_respaldantes:
            return solicitud.reglamentos_respaldantes[0]
        return "Reglamento Procesal Disciplinario 2026"

    def get_reglamentos_respaldantes(self, obj: Expediente) -> list[str]:
        solicitud = getattr(obj, "solicitud_t01", None)
        if solicitud and solicitud.reglamentos_respaldantes:
            return list(solicitud.reglamentos_respaldantes)
        return [self.get_reglamento_asociado(obj)]

    def get_solicitante(self, obj: Expediente) -> dict[str, str]:
        solicitud = getattr(obj, "solicitud_t01", None)
        if solicitud and solicitud.solicitante:
            s = solicitud.solicitante
            last = (s.last_name or "").strip()
            first = (s.first_name or "").strip()
            legajo = str(s.legajo or "").strip()
            nombre = f"{last}, {first}".strip().strip(",")
            return {
                "legajo": legajo,
                "nombre": nombre,
                "grupo": "",
                "display": f"{nombre} ({legajo})" if legajo else nombre,
            }
        # Fallback con creador
        return {
            "legajo": "",
            "nombre": "Comisión Directiva / Autoridad Solicitante",
            "grupo": "",
            "display": "Comisión Directiva",
        }

    def get_anexo(self, obj: Expediente) -> dict[str, Any]:
        solicitud = getattr(obj, "solicitud_t01", None)
        if solicitud:
            return {
                "anexo_fecha": solicitud.anexo_fecha.isoformat() if solicitud.anexo_fecha else None,
                "anexo_lugar": solicitud.anexo_lugar or "",
                "anexo_relato": solicitud.anexo_relato or "",
                "anexo_testigos": solicitud.anexo_testigos or "",
            }
        return {
            "anexo_fecha": None,
            "anexo_lugar": "",
            "anexo_relato": "",
            "anexo_testigos": "",
        }

    def get_esta_en_plazo(self, obj: Expediente) -> bool:
        return obj.esta_en_plazo()

    def get_horas_restantes(self, obj: Expediente) -> int:
        if not obj.plazo_limite_at or obj.estado != "justificando":
            return 0
        diff = obj.plazo_limite_at - timezone.now()
        horas = int(diff.total_seconds() // 3600)
        return max(0, horas)

    def get_responsables_td(self, obj: Expediente) -> list[dict[str, Any]]:
        return obtener_responsables_td()

    def get_involucrados(self, obj: Expediente) -> list[dict[str, Any]]:
        request = self.context.get("request")
        user = getattr(request, "user", None)
        mapa_grupos = cargar_mapa_grupos()

        socios_list = list(obj.socios.all())
        if not socios_list and obj.socio:
            socios_list = [obj.socio]

        descargos_all = list(obj.descargos.all())
        evidencias_all = list(obj.evidencias.all())

        # Determinar si el plazo de descargos ha expirado para la causa
        plazo_expirado = False
        if obj.plazo_limite_at and timezone.now() > obj.plazo_limite_at:
            plazo_expirado = True
        elif obj.estado not in (EstadoExpedienteEnum.CREADO, EstadoExpedienteEnum.JUSTIFICANDO):
            plazo_expirado = True

        involucrados_data = []
        for soc in socios_list:
            legajo = str(soc.legajo or "").strip()
            grupo = mapa_grupos.get(legajo, "")
            if not grupo and getattr(soc, "social_year", 0):
                current_year = timezone.localdate().year
                grupo = f"G{(current_year - 1962) - int(soc.social_year)}"

            # Estado social (Pasivo/Activo/Inactivo)
            if not getattr(soc, "is_enabled", True):
                estado_social = "Inactivo"
            else:
                estado_social = (
                    soc.get_category_display()
                    if hasattr(soc, "get_category_display")
                    else "Activo"
                )

            # Buscar descargo vigente del socio
            descargo_vigente = next(
                (d for d in descargos_all if d.socio_id == soc.id and d.es_vigente),
                None,
            )

            descargo_dto = None
            if descargo_vigente:
                tiene_descargo = True
                estado_descargo = "PRESENTADO"
                estado_descargo_display = "Descargo presentado"

                # Comprobar confidencialidad médica (CA2)
                es_med = es_causal_medica(descargo_vigente.causal, descargo_vigente.texto)
                acceso_medico = tiene_acceso_medico(user, soc.id)

                if es_med and not acceso_medico:
                    causal_final = "[Información médica reservada]"
                    texto_final = "[Información médica reservada]"
                    evidencias_final = []
                    contiene_datos_medicos = True
                    datos_medicos_restringidos = True
                else:
                    causal_final = descargo_vigente.causal
                    texto_final = descargo_vigente.texto
                    evs = current_evidence_for(descargo_vigente, evidencias_all)
                    evidencias_final = EvidenciaVisorSerializer(
                        evs, many=True, context=self.context
                    ).data
                    contiene_datos_medicos = es_med
                    datos_medicos_restringidos = False

                # Decisión sobre causal T02 si corresponde
                decisiones_causal_data = []
                regla_sugerida_val = None
                if descargo_vigente.tipo == TipoDescargoEnum.T02_CERTIFICADO:
                    evs_vigentes = current_evidence_for(descargo_vigente, evidencias_all)
                    regla_sugerida_val = suggested_decision(
                        has_current_evidence=bool(evs_vigentes)
                    ).value
                    decisiones_causal_data = DecisionCausalVisorSerializer(
                        descargo_vigente.decisiones_causal.all(), many=True
                    ).data

                descargo_dto = {
                    "id": descargo_vigente.id,
                    "socio_id": soc.id,
                    "socio_legajo": legajo,
                    "socio_nombre": f"{soc.first_name} {soc.last_name}".strip(),
                    "tipo": descargo_vigente.tipo,
                    "tipo_display": descargo_vigente.get_tipo_display(),
                    "causal": causal_final,
                    "texto": texto_final,
                    "archivo": descargo_vigente.archivo,
                    "presentado_at": (
                        descargo_vigente.presentado_at.isoformat()
                        if descargo_vigente.presentado_at
                        else None
                    ),
                    "contiene_datos_medicos": contiene_datos_medicos,
                    "datos_medicos_restringidos": datos_medicos_restringidos,
                    "evidencias": evidencias_final,
                    "regla_sugerida": regla_sugerida_val,
                    "decisiones_causal": decisiones_causal_data,
                }
            else:
                tiene_descargo = False
                if plazo_expirado:
                    estado_descargo = "PLAZO_VENCIDO_SIN_DESCARGO"
                    estado_descargo_display = "Plazo vencido sin descargo"
                elif obj.estado == EstadoExpedienteEnum.JUSTIFICANDO and obj.esta_en_plazo():
                    estado_descargo = "PENDIENTE"
                    estado_descargo_display = "En plazo sin descargo"
                else:
                    estado_descargo = "NO_INICIADO"
                    estado_descargo_display = "Plazo no iniciado"

            involucrados_data.append({
                "id": soc.id,
                "legajo": legajo,
                "nombre": f"{soc.first_name} {soc.last_name}".strip(),
                "first_name": soc.first_name,
                "last_name": soc.last_name,
                "grupo": grupo,
                "estado": estado_social,
                "tiene_descargo": tiene_descargo,
                "estado_descargo": estado_descargo,
                "estado_descargo_display": estado_descargo_display,
                "descargo": descargo_dto,
            })

        return involucrados_data

    def get_timeline(self, obj: Expediente) -> list[dict[str, Any]]:
        return construir_timeline(obj)

    def get_puede_resolver_causal(self, obj: Expediente) -> bool:
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return False
        socio = getattr(user, "socio", None)
        role = getattr(socio, "role", "")
        is_td = (socio and socio.is_enabled and role == Role.TD) or user.is_staff
        puede_estado = obj.estado in (
            EstadoExpedienteEnum.REVISION_RESOLUCION,
            EstadoExpedienteEnum.ESPERA_RESOLUCION,
        )
        return is_td and puede_estado

    def get_puede_dictar_resolucion(self, obj: Expediente) -> bool:
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return False
        socio = getattr(user, "socio", None)
        role = getattr(socio, "role", "")
        return (socio and socio.is_enabled and role in (Role.TD, Role.ADMIN)) or user.is_staff
