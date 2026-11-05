"""Punto de acceso al dominio de umbrales cuantitativos y alertas de saldo (S5-06)."""

from ranking.domain.threshold_alerts import (
    ActoAprobado,
    ActoAprobadoResolver,
    AlertaSanitizer,
    EstadoDespachoAlerta,
    EvaluacionCruceResult,
    FaltaActoAprobadoError,
    InternalAlertRepository,
    PrivacyViolationError,
    RegistroAlerta,
    ThresholdAlertEngine,
    ThresholdAlertNotificationService,
    TipoAlerta,
    TipoCruce,
    UmbralConfig,
    get_default_from_email,
    resolver_destinatarios_alerta_critica,
)

__all__ = [
    "ActoAprobado",
    "ActoAprobadoResolver",
    "AlertaSanitizer",
    "EstadoDespachoAlerta",
    "EvaluacionCruceResult",
    "FaltaActoAprobadoError",
    "InternalAlertRepository",
    "PrivacyViolationError",
    "RegistroAlerta",
    "ThresholdAlertEngine",
    "ThresholdAlertNotificationService",
    "TipoAlerta",
    "TipoCruce",
    "UmbralConfig",
    "get_default_from_email",
    "resolver_destinatarios_alerta_critica",
]
