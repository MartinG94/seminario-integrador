"""Lectura y modificación auditada de los parámetros del sistema (Spec 011).

El valor vigente de una clave es su último registro; si nunca se modificó, rige el valor
inicial del catálogo. Cada cambio inserta un registro nuevo: nada se actualiza ni se borra.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any, Final

from django.conf import settings
from django.db import transaction

from core.domain import system_parameters as catalog
from core.domain.system_parameters import (
    ParameterDefinition,
    ParameterValidationError,
    get_definition,
    normalize_value,
    to_python,
)
from core.models import SystemParameterChange

BYTES_PER_MB: Final = 1024 * 1024

# Variable de entorno que rige mientras el correo no se haya configurado desde el panel.
_EMAIL_SETTINGS: Final[dict[str, str]] = {
    catalog.EMAIL_COMISION_DIRECTIVA: "CD_EMAIL",
    catalog.EMAIL_TRIBUNAL: "TRIBUNAL_EMAIL",
}


@dataclass(frozen=True)
class ParameterChange:
    """Un cambio registrado, sea cual sea la tabla que lo almacena."""

    valor: Any
    valor_anterior: Any
    autor: Any
    created_at: datetime | None


@dataclass(frozen=True)
class AttachmentLimits:
    tamano_maximo_mb: int
    cantidad_maxima: int

    @property
    def tamano_maximo_bytes(self) -> int:
        return self.tamano_maximo_mb * BYTES_PER_MB


def _appeal_changes(limit: int | None = None) -> list[ParameterChange]:
    """El plazo de apelación se almacena en su tabla propia (PB-02).

    Con `limit`, sólo se leen los últimos `limit` cambios (más uno para su valor anterior).
    """
    from expedientes.models import ParametroPlazoApelacion

    queryset = ParametroPlazoApelacion.objects.select_related("autor").order_by(
        "-created_at", "-id"
    )
    registros = list(queryset[: limit + 1] if limit is not None else queryset)
    cambios: list[ParameterChange] = []
    for index, registro in enumerate(registros):
        anterior = (
            registros[index + 1].dias_habiles
            if index + 1 < len(registros)
            else ParametroPlazoApelacion.DEFAULT_DIAS_HABILES
        )
        cambios.append(
            ParameterChange(
                valor=registro.dias_habiles,
                valor_anterior=anterior,
                autor=registro.autor,
                created_at=registro.created_at,
            )
        )
    return cambios[:limit] if limit is not None else cambios


def _to_change(definition: ParameterDefinition, registro: SystemParameterChange) -> ParameterChange:
    return ParameterChange(
        valor=to_python(definition, registro.value),
        valor_anterior=to_python(definition, registro.previous_value),
        autor=registro.author,
        created_at=registro.created_at,
    )


class SystemParameterService:
    """Punto único de acceso a los parámetros configurables."""

    # --- Lectura ---

    @staticmethod
    def default_for(definition: ParameterDefinition) -> Any:
        setting_name = _EMAIL_SETTINGS.get(definition.clave)
        if setting_name:
            return getattr(settings, setting_name, "")
        return definition.default

    @classmethod
    def history(cls, clave: str) -> list[ParameterChange]:
        definition = get_definition(clave)
        if clave == catalog.PLAZO_APELACION:
            return _appeal_changes()
        return [
            _to_change(definition, registro)
            for registro in SystemParameterChange.objects.filter(key=clave).select_related("author")
        ]

    @classmethod
    def last_change(cls, clave: str) -> ParameterChange | None:
        definition = get_definition(clave)
        if clave == catalog.PLAZO_APELACION:
            cambios = _appeal_changes(limit=1)
            return cambios[0] if cambios else None
        registro = SystemParameterChange.objects.filter(key=clave).select_related("author").first()
        return _to_change(definition, registro) if registro else None

    @classmethod
    def get(cls, clave: str) -> Any:
        """Valor vigente de `clave`, ya convertido a su tipo de dominio."""
        definition = get_definition(clave)
        ultimo = cls.last_change(clave)
        return ultimo.valor if ultimo else cls.default_for(definition)

    # --- Escritura ---

    @classmethod
    @transaction.atomic
    def set(cls, clave: str, raw: Any, *, user: Any) -> ParameterChange:
        """Registra un nuevo valor. Levanta `ParameterValidationError` si es inválido."""
        definition = get_definition(clave)
        valor = normalize_value(definition, raw)

        if clave == catalog.PLAZO_APELACION:
            from expedientes.services.t01_appeal_service import T01AppealError, T01AppealService

            try:
                T01AppealService.set_business_days(dias_habiles=valor, user=user)
            except T01AppealError as exc:
                raise ParameterValidationError(str(exc)) from exc
            return _appeal_changes(limit=1)[0]

        # Se bloquea el último registro de la clave para que dos cambios simultáneos no
        # tomen el mismo valor anterior.
        ultimo = SystemParameterChange.objects.select_for_update().filter(key=clave).first()
        anterior = ultimo.value if ultimo else cls.default_for(definition)
        if definition.tipo == catalog.ParameterType.DECIMAL and anterior is not None:
            anterior = format(Decimal(str(anterior)), "f")
        registro = SystemParameterChange.objects.create(
            key=clave, value=valor, previous_value=anterior, author=user
        )
        return _to_change(definition, registro)

    # --- Accesos tipados para los consumidores ---

    @classmethod
    def descargo_business_days(cls) -> int:
        return int(cls.get(catalog.PLAZO_DESCARGO))

    @classmethod
    def preventive_threshold(cls) -> tuple[Decimal, bool]:
        """Umbral preventivo vigente y si su alerta está activa."""
        return (
            Decimal(str(cls.get(catalog.UMBRAL_PREVENTIVO))),
            bool(cls.get(catalog.UMBRAL_PREVENTIVO_ACTIVO)),
        )

    @classmethod
    def critical_threshold(cls) -> Decimal:
        return Decimal(str(cls.get(catalog.UMBRAL_CRITICO)))

    @classmethod
    def email(cls, clave: str, *, fallback: str | None = None) -> str:
        """Correo configurado; si nunca se configuró, `fallback` o la variable de entorno."""
        definition = get_definition(clave)
        ultimo = cls.last_change(clave)
        if ultimo and ultimo.valor:
            return str(ultimo.valor)
        if fallback is not None:
            return fallback
        return str(cls.default_for(definition) or "")

    @classmethod
    def attachment_limits(cls) -> AttachmentLimits:
        return AttachmentLimits(
            tamano_maximo_mb=int(cls.get(catalog.ADJUNTOS_TAMANO_MB)),
            cantidad_maxima=int(cls.get(catalog.ADJUNTOS_CANTIDAD)),
        )
