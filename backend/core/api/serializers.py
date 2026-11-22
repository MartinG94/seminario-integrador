"""Contratos REST del panel de administración (Spec 011)."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from rest_framework import serializers

from core.domain.system_parameters import ParameterDefinition
from core.services.system_parameters import ParameterChange, SystemParameterService
from socios.models import Socio


def json_value(value: Any) -> Any:
    """Los decimales viajan como texto para no perder precisión."""
    return format(value, "f") if isinstance(value, Decimal) else value


def author_label(user: Any) -> str:
    """Autoría legible: `Apellido, Nombre (N° de socio)` o el nombre de usuario."""
    if user is None:
        return ""
    socio = getattr(user, "socio", None)
    if socio is not None:
        numero = socio.numero_socio if socio.numero_socio is not None else "s/n"
        return f"{socio.last_name}, {socio.first_name} (N° de socio {numero})"
    return user.get_username()


def parameter_payload(definition: ParameterDefinition) -> dict[str, Any]:
    ultimo = SystemParameterService.last_change(definition.clave)
    default = SystemParameterService.default_for(definition)
    return {
        "clave": definition.clave,
        "categoria": definition.categoria,
        "etiqueta": definition.etiqueta,
        "descripcion": definition.descripcion,
        "tipo": definition.tipo.value,
        "unidad": definition.unidad,
        "editable": definition.editable,
        "minimo": json_value(definition.minimo),
        "maximo": json_value(definition.maximo),
        "valor": json_value(ultimo.valor if ultimo else default),
        "valor_inicial": json_value(default),
        "actualizado_at": ultimo.created_at if ultimo else None,
        "actualizado_por": author_label(ultimo.autor) if ultimo else "",
    }


def change_payload(change: ParameterChange) -> dict[str, Any]:
    return {
        "valor": json_value(change.valor),
        "valor_anterior": json_value(change.valor_anterior),
        "autor": author_label(change.autor),
        "created_at": change.created_at,
    }


class ParameterValueSerializer(serializers.Serializer):
    """Sólo exige que `valor` esté presente: el tipo lo valida el catálogo."""

    valor = serializers.JSONField(allow_null=True)


class TribunalMemberSerializer(serializers.ModelSerializer):
    subcomision = serializers.CharField(source="subcomision.name", default=None, read_only=True)

    class Meta:
        model = Socio
        fields = [
            "id",
            "numero_socio",
            "legajo",
            "last_name",
            "first_name",
            "social_year",
            "email",
            "subcomision",
        ]
        read_only_fields = fields


class TribunalCandidateSerializer(serializers.ModelSerializer):
    subcomision = serializers.CharField(source="subcomision.name", default=None, read_only=True)

    class Meta:
        model = Socio
        fields = ["id", "numero_socio", "last_name", "first_name", "social_year", "subcomision"]
        read_only_fields = fields


class AssignTribunalMemberSerializer(serializers.Serializer):
    socio_id = serializers.IntegerField(
        min_value=1,
        error_messages={
            "required": "Seleccioná un socio.",
            "invalid": "Seleccioná un socio válido.",
            "null": "Seleccioná un socio.",
            "min_value": "Seleccioná un socio válido.",
        },
    )
