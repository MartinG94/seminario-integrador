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


class ActoAprobadoResolver:
    """Resuelve destinatarios y acciones conforme a un acto formal aprobado (CA2).

    Si no existe un acto aprobado registrado en el sistema que determine inequívocamente
    destinatarios y acción, NO inventa ni sustituye reglas arbitrarias. Reporta
    un bloqueo formal que detiene el despacho o marca la alerta en espera de resolución.
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

    def resolver_destinatario_y_accion(self) -> tuple[list[str], str]:
        """Retorna destinatarios y acción si el acto está aprobado; sino lanza error."""
        if not self._acto_aprobado:
            raise FaltaActoAprobadoError(
                "Bloqueo normativo (CA2): No existe un acto aprobado registrado que determine "
                "inequívocamente el destinatario y la acción para la alerta crítica. "
                "Falta resolución formal de CD/TD que reglamente el Art. 93 del Reglamento Interno."
            )
        return list(self._acto_aprobado.destinatarios), self._acto_aprobado.accion_autorizada


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
                dests, accion = resolver.resolver_destinatario_y_accion()
                estado_despacho = EstadoDespachoAlerta.DESPACHADA
            else:
                dests = []
                accion = "PENDIENTE_DEFINICION_ACTO_APROBADO"
                estado_despacho = EstadoDespachoAlerta.BLOQUEADA_POR_FALTA_DE_ACTO_APROBADO
                meta["bloqueo_ca2"] = (
                    "Falta acto aprobado formal emitido por CD/TD que defina destinatarios "
                    "y acción reglamentaria para alerta de pérdida de condición de socio."
                )

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
                envio_externo_realizado=False,
                baja_automatica_aplicada=False,
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
            historial_alertas=historial_preservado,
            resolver_acto=resolver_acto,
            fecha_evaluacion=fecha_evaluacion,
            metadata_adicional={"motivo_rectificacion": motivo_rectificacion},
            es_rectificacion=True,
        )

        if resultado.alerta_generada:
            historial_preservado.append(resultado.alerta_generada)

        return resultado, historial_preservado
