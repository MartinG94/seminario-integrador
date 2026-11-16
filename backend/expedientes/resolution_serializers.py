from rest_framework import serializers

from expedientes.models import Resolucion


class ResolucionSerializer(serializers.ModelSerializer):
    identificador_resolucion = serializers.SerializerMethodField()
    firmantes_td = serializers.SerializerMethodField()
    expedientes_referenciados_detalle = serializers.SerializerMethodField()
    plantilla_version = serializers.CharField(max_length=50, default="v1", required=False)

    class Meta:
        model = Resolucion
        fields = (
            "id",
            "expediente",
            "version",
            "plantilla_version",
            "estado",
            "numero_expediente_snapshot",
            "identificador_resolucion",
            "firmantes",
            "firmantes_td",
            "vistos",
            "considerandos",
            "articulos_resolutivos",
            "reglamentos_respaldantes",
            "expedientes_referenciados",
            "expedientes_referenciados_detalle",
            "puntos_finales",
            "medidas",
            "created_by",
            "created_at",
            "updated_at",
            "issued_by",
            "issued_at",
            "contenido_hash",
        )
        read_only_fields = (
            "expediente",
            "version",
            "estado",
            "numero_expediente_snapshot",
            "identificador_resolucion",
            "firmantes",
            "firmantes_td",
            "puntos_finales",
            "medidas",
            "created_by",
            "created_at",
            "updated_at",
            "issued_by",
            "issued_at",
            "contenido_hash",
        )

    def get_identificador_resolucion(self, obj: Resolucion) -> str:
        numero = obj.numero_expediente_snapshot or (obj.expediente.numero if obj.expediente else "")
        raw = numero.replace("EXP-", "").strip()
        return f"RESOLUCIÓN {raw}"

    def get_firmantes_td(self, obj: Resolucion) -> list:
        return obj.firmantes or []

    def validate_expedientes_referenciados(self, value):
        if value is None:
            return []
        if not isinstance(value, list):
            raise serializers.ValidationError(
                "Debe ser una lista de identificadores de expedientes."
            )
        vistos = set()
        for exp_id in value:
            if not isinstance(exp_id, int) or exp_id <= 0:
                raise serializers.ValidationError(
                    "Cada expediente referenciado debe ser un entero positivo."
                )
            if exp_id in vistos:
                raise serializers.ValidationError(
                    f"El expediente {exp_id} está duplicado en la lista."
                )
            vistos.add(exp_id)
        if vistos:
            from expedientes.models import EstadoExpedienteEnum, Expediente

            emitidos_ids = set(
                Expediente.objects.filter(
                    pk__in=vistos, estado=EstadoExpedienteEnum.EMITIDO
                ).values_list("id", flat=True)
            )
            faltantes = vistos - emitidos_ids
            if faltantes:
                raise serializers.ValidationError(
                    "Los siguientes expedientes no existen o no están en estado emitido: "
                    f"{sorted(faltantes)}."
                )
        return value

    def get_expedientes_referenciados_detalle(self, obj: Resolucion) -> list[dict]:
        from expedientes.services.t03_valuation_service import (
            build_expedientes_referenciados_detalle,
        )

        return build_expedientes_referenciados_detalle(
            getattr(obj, "expedientes_referenciados", None)
        )
