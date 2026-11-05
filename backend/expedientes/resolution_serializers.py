from rest_framework import serializers

from expedientes.models import Resolucion


class ResolucionSerializer(serializers.ModelSerializer):
    identificador_resolucion = serializers.SerializerMethodField()
    firmantes_td = serializers.SerializerMethodField()
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
