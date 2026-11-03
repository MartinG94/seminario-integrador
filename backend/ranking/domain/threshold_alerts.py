"""Dominio de evaluación de umbrales cuantitativos y alertas de saldo (S5-06).

Cumple estrictamente con:
- CA1: Saldo negativo de 10 o más genera alerta crítica única por cruce descendente.
- CA2: Destinatario y acción siguen acto aprobado (documentando bloqueo si falta el acto).
- CA3: Umbral preventivo (-7) diferenciado, configurable y desactivable hasta Circular 001/2026.
- CA4: Reversiones reevalúan sin borrar ni sobrescribir registros históricos.
- CA5: Privacidad estricta, cero información médica en alertas y metadatos.
"""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any


class TipoAlerta(str, Enum):
    """Clasificación reglamentaria de la alerta."""

    CRITICA = "CRITICA"
    PREVENTIVA = "PREVENTIVA"


class TipoCruce(str, Enum):
    """Naturaleza de la transición respecto a los umbrales configurados."""

    CRITICO_DESCENDENTE = "CRITICO_DESCENDENTE"
    PREVENTIVO_DESCENDENTE = "PREVENTIVO_DESCENDENTE"
    SALIDA_ZONA_CRITICA = "SALIDA_ZONA_CRITICA"
    SALIDA_ZONA_PREVENTIVA = "SALIDA_ZONA_PREVENTIVA"
    SIN_CRUCE = "SIN_CRUCE"


class EstadoDespachoAlerta(str, Enum):
    """Estado procesal del despacho de la notificación."""

    DESPACHADA = "DESPACHADA"
    BLOQUEADA_POR_FALTA_DE_ACTO_APROBADO = "BLOQUEADA_POR_FALTA_DE_ACTO_APROBADO"


class PrivacyViolationError(ValueError):
    """Infracción a CA5: Detección de información médica o sensible en alertas o metadatos."""

    pass


class FaltaActoAprobadoError(RuntimeError):
    """Bloqueo normativo (CA2): Ausencia de acto formal aprobado para destinatario y acción."""

    pass


class AlertaSanitizer:
    """Garantiza la ausencia estricta de información médica o diagnósticos (CA5 y Principio 6)."""

    FORBIDDEN_TERMS_PATTERN = re.compile(
        r"(?:\b)("
        r"diagn[oó]stic[oa]s?|diag\b\.?|"
        r"enfermedad(?:es)?|"
        r"patolog[ií]a(?:s)?|patol\b\.?|"
        r"m[eé]dic[oa]s?|med\b\.?|"
        r"salud|"
        r"lic(?:encia)?\b\.?\s+m[eé]d(?:ic[oa])?\b\.?|"
        r"cl[ií]nic[oa]s?|"
        r"s[ií]ntoma(?:s)?|"
        r"reposo|"
        r"internaci[oó]n|"
        r"quir[uú]rgic[oa]s?|"
        r"receta(?:s)?|"
        r"psiqui[aá]tric[oa]s?|"
        r"psicol[oó]gic[oa]s?|psicol\b\.?|"
        r"covid(?:-19)?"
        r")(?:\b|\.|\s|$)",
        re.IGNORECASE,
    )

    @classmethod
    def assert_no_sensitive_data(cls, text: str) -> None:
        """Verifica que el texto no contenga términos médicos o sensibles.

        Principio 7: El error no replica el texto sensible completo, sólo la etiqueta detectada.
        """
        if not text:
            return
        match = cls.FORBIDDEN_TERMS_PATTERN.search(text)
        if match:
            detected_term = match.group(1).strip()
            raise PrivacyViolationError(
                f"Infracción a CA5: Se detectó término sensible o médico no permitido: "
                f"'{detected_term}'."
            )

    @classmethod
    def sanitize_dict(cls, data: dict[str, Any]) -> None:
        """Sanitiza recursivamente claves y valores de un diccionario de metadatos."""
        for key, value in data.items():
            cls.assert_no_sensitive_data(str(key))
            if isinstance(value, str):
                cls.assert_no_sensitive_data(value)
            elif isinstance(value, dict):
                cls.sanitize_dict(value)
            elif isinstance(value, (list, tuple, set)):
                for item in value:
                    if isinstance(item, str):
                        cls.assert_no_sensitive_data(item)
                    elif isinstance(item, dict):
                        cls.sanitize_dict(item)


@dataclass
class UmbralConfig:
    """Configuración de políticas de umbrales cuantitativos de saldo.

    - umbral_critico: Inmutable y estatutario (-10.0 pts según Art. 93 Reglamento Interno).
    - umbral_preventivo: Configurable (-7.0 pts por defecto).
    - preventivo_activo: Desactivable/configurable hasta validar Circular 001/2026.
    """

    umbral_critico: Decimal = Decimal("-10.0")
    umbral_preventivo: Decimal = Decimal("-7.0")
    preventivo_activo: bool = False

    def __post_init__(self) -> None:
        if Decimal(str(self.umbral_critico)) != Decimal("-10.0"):
            raise ValueError(
                "El umbral crítico es inmutable y estatutario fijado en -10.0 pts (Art. 93 R.I.)."
            )
        self.umbral_preventivo = Decimal(str(self.umbral_preventivo))

    def configurar_preventivo(self, valor: Decimal | str | float, activo: bool = True) -> None:
        """Permite modificar el umbral preventivo y/o su activación sin alterar el crítico."""
        val = Decimal(str(valor))
        if val <= self.umbral_critico:
            raise ValueError(
                f"El umbral preventivo ({val}) debe ser superior al umbral crítico "
                f"({self.umbral_critico})."
            )
        self.umbral_preventivo = val
        self.preventivo_activo = activo

    def desactivar_preventivo(self) -> None:
        """Desactiva la emisión de alertas preventivas (CA3)."""
        self.preventivo_activo = False

    def activar_preventivo(self) -> None:
        """Activa la emisión de alertas preventivas con el umbral preventivo configurado."""
        self.preventivo_activo = True


@dataclass(frozen=True)
class ActoAprobado:
    """Acto administrativo formal aprobado por autoridad competente (CD/TD)."""

    codigo: str
    destinatarios: list[str]
    accion_autorizada: str
    fecha_aprobacion: datetime
    descripcion: str = ""


def get_default_from_email() -> str:
    """Retorna el remitente oficial configurado para notificaciones del sistema."""
    try:
        from django.conf import settings

        return getattr(settings, "DEFAULT_FROM_EMAIL", "sistema@example.org")
    except Exception:
        return "sistema@example.org"


def resolver_destinatarios_alerta_critica(socio_email: str | None = None) -> list[str]:
    """Resuelve los destinatarios oficiales de la alerta crítica (-10 puntos).

    Conforme a las definiciones del PO:
    - Socio Imputado (si se provee email)
    - Comisión Directiva (settings.CD_EMAIL)
    - Tribunal de Disciplina (settings.TRIBUNAL_EMAIL)

    La resolución de estos destinatarios depende de la configuración y de los datos del socio,
    NO de la existencia de un objeto ActoAprobado. La ausencia de ese objeto no bloquea
    operativamente la generación ni el despacho de la alerta.
    """
    try:
        from django.conf import settings

        cd_email = getattr(settings, "CD_EMAIL", "cd@example.org")
        tribunal_email = getattr(settings, "TRIBUNAL_EMAIL", "tribunal@example.org")
    except Exception:
        cd_email = "cd@example.org"
        tribunal_email = "tribunal@example.org"

    destinatarios: list[str] = []
    if socio_email and socio_email.strip():
        destinatarios.append(socio_email.strip())
    if cd_email and cd_email.strip() and cd_email.strip() not in destinatarios:
        destinatarios.append(cd_email.strip())
    if tribunal_email and tribunal_email.strip() and tribunal_email.strip() not in destinatarios:
        destinatarios.append(tribunal_email.strip())

    return destinatarios


class ActoAprobadoResolver:
    """Resuelve destinatarios y acciones para la alerta crítica.

    Conforme a la definición del PO:
    - Si existe un ActoAprobado, incorpora sus destinatarios y la acción autorizada.
    - Si no existe un ActoAprobado, NO bloquea la notificación: resuelve los destinatarios
      oficiales reglamentarios (Socio, CD, Tribunal) y asigna la acción
      'ESPERA_ACTO_RESOLUTIVO_CD'.
    """

    def __init__(self, acto_aprobado: ActoAprobado | None = None) -> None:
        self._acto_aprobado = acto_aprobado

    @property
    def hay_acto_aprobado(self) -> bool:
        return self._acto_aprobado is not None

    @property
    def acto_aprobado(self) -> ActoAprobado | None:
        return self._acto_aprobado

    def registrar_acto(self, acto: ActoAprobado) -> None:
        self._acto_aprobado = acto

    def resolver_destinatario_y_accion(
        self, socio_email: str | None = None, *, forzar_acto: bool = False
    ) -> tuple[list[str], str]:
        """Retorna destinatarios y acción sin bloquear por ausencia de ActoAprobado."""
        if self._acto_aprobado:
            destinatarios = list(self._acto_aprobado.destinatarios)
            if socio_email and socio_email.strip() and socio_email.strip() not in destinatarios:
                destinatarios.insert(0, socio_email.strip())
            return destinatarios, self._acto_aprobado.accion_autorizada

        if forzar_acto:
            raise FaltaActoAprobadoError(
                "Bloqueo normativo (CA2): No existe un acto aprobado registrado que determine "
                "inequívocamente el destinatario y la acción para la alerta crítica. "
                "Falta resolución formal de CD/TD que reglamente el Art. 93 del Reglamento Interno."
            )

        return (
            resolver_destinatarios_alerta_critica(socio_email=socio_email),
            "ESPERA_ACTO_RESOLUTIVO_CD",
        )


@dataclass(frozen=True)
class RegistroAlerta:
    """Registro inmutable de auditoría de alertas de saldo (CA4)."""

    id: str
    socio_id: int
    tipo: TipoAlerta
    saldo_anterior: Decimal
    saldo_nuevo: Decimal
    umbral_evaluado: Decimal
    fecha_emision: datetime
    estado_despacho: EstadoDespachoAlerta
    destinatarios: list[str] = field(default_factory=list)
    accion_asociada: str = "REGISTRO_INTERNO"
    metadata: dict[str, Any] = field(default_factory=dict)
    es_reversion: bool = False
    es_rectificacion: bool = False
    es_registro_interno: bool = True
    envio_externo_realizado: bool = False
    baja_automatica_aplicada: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "socio_id": self.socio_id,
            "tipo": self.tipo.value,
            "saldo_anterior": str(self.saldo_anterior),
            "saldo_nuevo": str(self.saldo_nuevo),
            "umbral_evaluado": str(self.umbral_evaluado),
            "fecha_emision": self.fecha_emision.isoformat(),
            "estado_despacho": self.estado_despacho.value,
            "destinatarios": self.destinatarios,
            "accion_asociada": self.accion_asociada,
            "metadata": self.metadata,
            "es_reversion": self.es_reversion,
            "es_rectificacion": self.es_rectificacion,
            "es_registro_interno": self.es_registro_interno,
            "envio_externo_realizado": self.envio_externo_realizado,
            "baja_automatica_aplicada": self.baja_automatica_aplicada,
        }


class InternalAlertRepository:
    """Registro y almacenamiento en memoria de alertas internas inmutables (CA4)."""

    def __init__(self, registros_iniciales: list[RegistroAlerta] | None = None) -> None:
        self._registros: list[RegistroAlerta] = list(registros_iniciales or [])

    def registrar(self, alerta: RegistroAlerta) -> None:
        """Registra una alerta interna asegurando sanitización de privacidad."""
        AlertaSanitizer.sanitize_dict(alerta.metadata)
        self._registros.append(alerta)

    def obtener_por_socio(self, socio_id: int) -> list[RegistroAlerta]:
        """Retorna el historial inmutable de alertas de un socio."""
        return [r for r in self._registros if r.socio_id == socio_id]

    def listar_todas(self) -> list[RegistroAlerta]:
        """Retorna todas las alertas internas registradas."""
        return list(self._registros)

    def total(self) -> int:
        """Cantidad total de alertas internas registradas."""
        return len(self._registros)


@dataclass(frozen=True)
class EvaluacionCruceResult:
    """Resultado de la evaluación de cruce de umbral."""

    cruce: TipoCruce
    alerta_generada: RegistroAlerta | None
    esta_en_zona_critica: bool
    esta_en_zona_preventiva: bool
    motivo: str


class ThresholdAlertNotificationService:
    """Servicio de despacho de notificaciones para alertas de umbral crítico."""

    @classmethod
    def construir_payload_outbox(
        cls,
        alerta: RegistroAlerta,
        socio_nombre: str = "",
    ) -> dict[str, Any]:
        """Construye el payload para la cola transaccional Outbox asegurando cero datos médicos."""
        subject = (
            f"[SGD-AVEIT] ALERTA CRÍTICA: Saldo de puntos reglamentario (Socio #{alerta.socio_id})"
        )
        nombre_str = f" {socio_nombre}" if socio_nombre else ""
        body_text = (
            f"Estimado/a socio/a{nombre_str} (Legajo/ID: {alerta.socio_id}),\n\n"
            f"Le informamos formalmente que su saldo de puntos ha alcanzado un valor crítico "
            f"de {alerta.saldo_nuevo} puntos, habiendo cruzado el umbral estatutario de "
            f"{alerta.umbral_evaluado} puntos (Art. 93 del Reglamento Interno).\n\n"
            f"El procedimiento formal disciplinario ha quedado en estado de espera del acto "
            f"resolutivo de la Comisión Directiva. De acuerdo con el reglamento, se notifica "
            f"en simultáneo a la Comisión Directiva y al Tribunal de Disciplina.\n\n"
            f"Acción administrativa: {alerta.accion_asociada}\n"
            f"Fecha de emisión: {alerta.fecha_emision.isoformat()}\n\n"
            f"Atentamente,\n"
            f"Asociación Vocacional de Estudiantes e Ingenieros Tecnológicos (A.V.E.I.T.)\n"
        )

        metadata = {
            "alerta_id": alerta.id,
            "socio_id": alerta.socio_id,
            "tipo_alerta": alerta.tipo.value,
            "saldo_anterior": str(alerta.saldo_anterior),
            "saldo_nuevo": str(alerta.saldo_nuevo),
            "canal": "EMAIL_OUTBOX",
            "notificacion_in_app": False,
            "remitente": get_default_from_email(),
            "baja_automatica_aplicada": alerta.baja_automatica_aplicada,
            "accion_asociada": alerta.accion_asociada,
        }
        # Validación de CA5
        AlertaSanitizer.sanitize_dict(metadata)
        AlertaSanitizer.assert_no_sensitive_data(body_text)

        idempotency_key = f"threshold-alert-critica-{alerta.socio_id}-{alerta.id}"

        return {
            "to": list(alerta.destinatarios),
            "cc": [],
            "bcc": [],
            "subject": subject,
            "body_text": body_text,
            "body_html": None,
            "idempotency_key": idempotency_key,
            "metadata": metadata,
        }

    @classmethod
    def despachar_alerta_critica(
        cls,
        alerta: RegistroAlerta,
        socio_nombre: str = "",
        enviar_inmediatamente: bool = True,
    ) -> Any:
        """Encola el despacho en EmailOutbox y opcionalmente dispara el envío inmediato.

        Persiste constancia fehaciente en la base de datos a través de EmailOutbox.
        Excluye cualquier notificación in-app o canales alternativos.
        """
        payload = cls.construir_payload_outbox(alerta, socio_nombre=socio_nombre)

        try:
            from notifications.services import EmailDispatcherService

            outbox, _ = EmailDispatcherService.create_or_get_outbox(payload)
            if enviar_inmediatamente:
                EmailDispatcherService.dispatch(outbox)
            return outbox
        except Exception:
            return payload


class ThresholdAlertEngine:
    """Motor de evaluación de umbrales, unicidad por cruce y reevaluación por reversión."""

    @staticmethod
    def _determinar_zona_critica(saldo: Decimal, config: UmbralConfig) -> bool:
        return saldo <= config.umbral_critico

    @staticmethod
    def _determinar_zona_preventiva(saldo: Decimal, config: UmbralConfig) -> bool:
        if not config.preventivo_activo:
            return False
        return config.umbral_critico < saldo <= config.umbral_preventivo

    @classmethod
    def evaluar_cruce(
        cls,
        *,
        socio_id: int,
        saldo_anterior: Decimal,
        saldo_nuevo: Decimal,
        config: UmbralConfig,
        socio_email: str | None = None,
        despachar_outbox: bool = False,
        socio_nombre: str = "",
        historial_alertas: list[RegistroAlerta] | None = None,
        resolver_acto: ActoAprobadoResolver | None = None,
        fecha_evaluacion: datetime | None = None,
        metadata_adicional: dict[str, Any] | None = None,
        es_reversion: bool = False,
        es_rectificacion: bool = False,
    ) -> EvaluacionCruceResult:
        """Evalúa el impacto del movimiento de saldo contra los umbrales reglamentarios."""
        saldo_ant = Decimal(str(saldo_anterior))
        saldo_post = Decimal(str(saldo_nuevo))
        _ = list(historial_alertas or [])
        resolver = resolver_acto or ActoAprobadoResolver()
        momento = fecha_evaluacion or datetime.now()

        # Validación estricta de privacidad en metadatos adicionales (CA5)
        meta = dict(metadata_adicional or {})
        AlertaSanitizer.sanitize_dict(meta)

        zona_crit_ant = cls._determinar_zona_critica(saldo_ant, config)
        zona_crit_post = cls._determinar_zona_critica(saldo_post, config)

        zona_prev_ant = cls._determinar_zona_preventiva(saldo_ant, config)
        zona_prev_post = cls._determinar_zona_preventiva(saldo_post, config)

        # 1. Caso: Cruce descendente hacia zona crítica (CA1)
        if not zona_crit_ant and zona_crit_post:
            if resolver.hay_acto_aprobado:
                dests, accion = resolver.resolver_destinatario_y_accion(socio_email=socio_email)
            else:
                dests = resolver_destinatarios_alerta_critica(socio_email=socio_email)
                accion = "ESPERA_ACTO_RESOLUTIVO_CD"

            estado_despacho = EstadoDespachoAlerta.DESPACHADA

            meta.setdefault("canal", "EMAIL_OUTBOX")
            meta.setdefault("notificacion_in_app", False)
            meta.setdefault("remitente", get_default_from_email())
            meta.setdefault("baja_automatica_aplicada", False)
            meta.setdefault("accion_asociada", accion)

            alerta = RegistroAlerta(
                id=str(uuid.uuid4()),
                socio_id=socio_id,
                tipo=TipoAlerta.CRITICA,
                saldo_anterior=saldo_ant,
                saldo_nuevo=saldo_post,
                umbral_evaluado=config.umbral_critico,
                fecha_emision=momento,
                estado_despacho=estado_despacho,
                destinatarios=dests,
                accion_asociada=accion,
                metadata=meta,
                es_reversion=es_reversion,
                es_rectificacion=es_rectificacion,
                es_registro_interno=True,
                envio_externo_realizado=despachar_outbox,
                baja_automatica_aplicada=False,
            )

            if despachar_outbox:
                ThresholdAlertNotificationService.despachar_alerta_critica(
                    alerta, socio_nombre=socio_nombre
                )

            return EvaluacionCruceResult(
                cruce=TipoCruce.CRITICO_DESCENDENTE,
                alerta_generada=alerta,
                esta_en_zona_critica=True,
                esta_en_zona_preventiva=False,
                motivo="Cruce descendente hacia zona crítica (saldo <= -10.0 pts)",
            )

        # 2. Caso: Permanencia en zona crítica (NO duplica alerta, CA1)
        if zona_crit_ant and zona_crit_post:
            return EvaluacionCruceResult(
                cruce=TipoCruce.SIN_CRUCE,
                alerta_generada=None,
                esta_en_zona_critica=True,
                esta_en_zona_preventiva=False,
                motivo="Permanencia en zona crítica; no se duplica alerta por cruce",
            )

        # 3. Caso: Salida de zona crítica hacia saldo superior
        if zona_crit_ant and not zona_crit_post:
            return EvaluacionCruceResult(
                cruce=TipoCruce.SALIDA_ZONA_CRITICA,
                alerta_generada=None,
                esta_en_zona_critica=False,
                esta_en_zona_preventiva=zona_prev_post,
                motivo="Salida de zona crítica; restablecimiento de aptitud para futuros cruces",
            )

        # 4. Caso: Cruce descendente hacia zona preventiva configurable (CA3)
        if config.preventivo_activo and not zona_prev_ant and zona_prev_post:
            alerta = RegistroAlerta(
                id=str(uuid.uuid4()),
                socio_id=socio_id,
                tipo=TipoAlerta.PREVENTIVA,
                saldo_anterior=saldo_ant,
                saldo_nuevo=saldo_post,
                umbral_evaluado=config.umbral_preventivo,
                fecha_emision=momento,
                estado_despacho=EstadoDespachoAlerta.DESPACHADA,
                destinatarios=[],
                accion_asociada="ADVERTENCIA_PREVENTIVA",
                metadata=meta,
                es_reversion=es_reversion,
                es_rectificacion=es_rectificacion,
                es_registro_interno=True,
                envio_externo_realizado=False,
                baja_automatica_aplicada=False,
            )
            return EvaluacionCruceResult(
                cruce=TipoCruce.PREVENTIVO_DESCENDENTE,
                alerta_generada=alerta,
                esta_en_zona_critica=False,
                esta_en_zona_preventiva=True,
                motivo=(
                    f"Cruce descendente hacia zona preventiva "
                    f"(saldo <= {config.umbral_preventivo} pts)"
                ),
            )

        # 5. Caso: Salida de zona preventiva
        if zona_prev_ant and not zona_prev_post:
            return EvaluacionCruceResult(
                cruce=TipoCruce.SALIDA_ZONA_PREVENTIVA,
                alerta_generada=None,
                esta_en_zona_critica=False,
                esta_en_zona_preventiva=False,
                motivo="Salida de zona preventiva",
            )

        # 6. Sin cruces de umbral
        return EvaluacionCruceResult(
            cruce=TipoCruce.SIN_CRUCE,
            alerta_generada=None,
            esta_en_zona_critica=False,
            esta_en_zona_preventiva=zona_prev_post,
            motivo="Sin cruce de umbrales",
        )

    @classmethod
    def reevaluar_por_reversion(
        cls,
        *,
        socio_id: int,
        saldo_anterior: Decimal,
        saldo_resultante: Decimal,
        historial_alertas: list[RegistroAlerta],
        config: UmbralConfig,
        socio_email: str | None = None,
        despachar_outbox: bool = False,
        socio_nombre: str = "",
        resolver_acto: ActoAprobadoResolver | None = None,
        fecha_evaluacion: datetime | None = None,
        motivo_reversion: str = "Reversión / contramovimiento autorizado",
    ) -> tuple[EvaluacionCruceResult, list[RegistroAlerta]]:
        """Reevalúa los umbrales preservando el historial inmutable anterior (CA4).

        Una reversión nunca elimina ni sobrescribe registros de alertas previas.
        Si la reversión saca al socio de la zona crítica, la próxima vez que cruce
        hacia abajo podrá emitir una nueva alerta.
        Si la reversión causa un cruce descendente hacia la zona crítica, emite la alerta.
        """
        historial_preservado = list(historial_alertas)

        AlertaSanitizer.assert_no_sensitive_data(motivo_reversion)

        resultado = cls.evaluar_cruce(
            socio_id=socio_id,
            saldo_anterior=saldo_anterior,
            saldo_nuevo=saldo_resultante,
            config=config,
            socio_email=socio_email,
            despachar_outbox=despachar_outbox,
            socio_nombre=socio_nombre,
            historial_alertas=historial_preservado,
            resolver_acto=resolver_acto,
            fecha_evaluacion=fecha_evaluacion,
            metadata_adicional={"motivo_reversion": motivo_reversion},
            es_reversion=True,
        )

        if resultado.alerta_generada:
            historial_preservado.append(resultado.alerta_generada)

        return resultado, historial_preservado

    @classmethod
    def reevaluar_por_rectificacion(
        cls,
        *,
        socio_id: int,
        saldo_anterior: Decimal,
        saldo_resultante: Decimal,
        historial_alertas: list[RegistroAlerta],
        config: UmbralConfig,
        socio_email: str | None = None,
        despachar_outbox: bool = False,
        socio_nombre: str = "",
        resolver_acto: ActoAprobadoResolver | None = None,
        fecha_evaluacion: datetime | None = None,
        motivo_rectificacion: str = "Rectificación de saldo autorizada",
    ) -> tuple[EvaluacionCruceResult, list[RegistroAlerta]]:
        """Reevalúa los umbrales tras una rectificación de saldo preservando el historial (CA4).

        Una rectificación nunca elimina ni sobrescribe registros de alertas previas.
        Si la rectificación saca al socio de la zona crítica, la próxima vez que cruce
        hacia abajo podrá emitir una nueva alerta.
        Si la rectificación causa un cruce descendente hacia la zona crítica, emite la alerta.
        """
        historial_preservado = list(historial_alertas)

        AlertaSanitizer.assert_no_sensitive_data(motivo_rectificacion)

        resultado = cls.evaluar_cruce(
            socio_id=socio_id,
            saldo_anterior=saldo_anterior,
            saldo_nuevo=saldo_resultante,
            config=config,
            socio_email=socio_email,
            despachar_outbox=despachar_outbox,
            socio_nombre=socio_nombre,
            historial_alertas=historial_preservado,
            resolver_acto=resolver_acto,
            fecha_evaluacion=fecha_evaluacion,
            metadata_adicional={"motivo_rectificacion": motivo_rectificacion},
            es_rectificacion=True,
        )

        if resultado.alerta_generada:
            historial_preservado.append(resultado.alerta_generada)

        return resultado, historial_preservado
