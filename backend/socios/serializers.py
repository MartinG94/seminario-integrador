from rest_framework import serializers

from padron.domain import SocioCategoryEnum
from socios.models import Socio


class SocioLegajoSerializer(serializers.ModelSerializer):
    """
    Serializer para el detalle del legajo del socio (T7 / CA2).
    Expone datos constitutivos y el saldo aplicado acreditado por la vista.
    Un saldo desconocido conserva null, sin sustituirlo por cero.
    """

    legajo = serializers.CharField(allow_null=True, read_only=True)
    category = serializers.ChoiceField(
        choices=[(category.value, category.label) for category in SocioCategoryEnum],
        read_only=True,
    )
    category_display = serializers.CharField(source="get_category_display", read_only=True)
    subcomision = serializers.CharField(source="subcomision.name", default=None, read_only=True)
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
            "subcomision",
            "social_year",
            "is_enabled",
            "points_balance",
        ]
        read_only_fields = fields

    def get_points_balance(self, obj: Socio) -> float | None:
        return getattr(obj, "points_balance", None)
