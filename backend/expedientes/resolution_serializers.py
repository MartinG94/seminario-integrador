from rest_framework import serializers

from expedientes.models import Resolucion


class ResolucionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resolucion
        fields = (
            "id",
            "expediente",
            "version",
            "plantilla_version",
            "estado",
            "numero_expediente_snapshot",
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
            "puntos_finales",
            "medidas",
            "created_by",
            "created_at",
            "updated_at",
            "issued_by",
            "issued_at",
            "contenido_hash",
        )
