from rest_framework import serializers

from socios.models import Socio


class SocioLegajoSerializer(serializers.ModelSerializer):
    """
    Serializer para el detalle del legajo del socio (T7 / CA2).
    Expone los datos constitutivos y deja el espacio preparado para la futura agregación
    transaccional de puntos de T4 sin implementarla prematuramente.
    """

    category_display = serializers.CharField(source="get_category_display", read_only=True)
    subcomision_name = serializers.CharField(
        source="subcomision.name", default=None, read_only=True
    )
    points_balance = serializers.SerializerMethodField()

    class Meta:
        model = Socio
        fields = [
            "id",
            "legajo",
            "first_name",
            "last_name",
            "email",
            "role",
            "category",
            "category_display",
            "subcomision_name",
            "social_year",
            "is_enabled",
            "points_balance",
        ]
        read_only_fields = fields

    def get_points_balance(self, obj: Socio) -> float:
        return getattr(obj, "points_balance", 0.0)
