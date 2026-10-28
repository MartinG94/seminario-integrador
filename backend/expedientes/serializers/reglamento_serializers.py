"""Serializadores para el articulado de reglamentos institucionales (Milestone 3)."""

from rest_framework import serializers

from expedientes.models import ArticuloReglamento


class ArticuloReglamentoSerializer(serializers.ModelSerializer):
    """Serializador para consulta, creación y edición del articulado de reglamentos."""

    cuerpo = serializers.CharField(source="descripcion", required=True)
    descripcion = serializers.CharField(required=False, allow_blank=True)
    cita_corta = serializers.CharField(read_only=True)
    cita_completa = serializers.CharField(read_only=True)
    created_by_display = serializers.SerializerMethodField(read_only=True)
    updated_by_display = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = ArticuloReglamento
        fields = (
            "id",
            "titulo",
            "seccion",
            "articulo",
            "inciso",
            "cuerpo",
            "descripcion",
            "cita_corta",
            "cita_completa",
            "activo",
            "created_at",
            "updated_at",
            "created_by_display",
            "updated_by_display",
        )
        read_only_fields = (
            "id",
            "cita_corta",
            "cita_completa",
            "created_at",
            "updated_at",
            "created_by_display",
            "updated_by_display",
        )
        extra_kwargs = {
            "seccion": {"required": False, "default": 1},
            "activo": {"required": False},
            "inciso": {"required": False, "allow_blank": True},
        }

    def to_internal_value(self, data):
        ret_data = data.copy() if hasattr(data, "copy") else dict(data)

        # Normalización del inciso: si está en el payload o no es actualización parcial
        if "inciso" in ret_data:
            inciso = ret_data.get("inciso")
            if inciso is None or str(inciso).strip() in ("", "null", "None"):
                ret_data["inciso"] = "-"
            else:
                ret_data["inciso"] = str(inciso).strip()
        elif not getattr(self, "partial", False):
            ret_data["inciso"] = "-"

        # Normalización bidireccional entre cuerpo y descripcion
        if "cuerpo" in ret_data and "descripcion" not in ret_data:
            ret_data["descripcion"] = ret_data["cuerpo"]
        elif "descripcion" in ret_data and "cuerpo" not in ret_data:
            ret_data["cuerpo"] = ret_data["descripcion"]

        return super().to_internal_value(ret_data)

    def validate(self, attrs):
        instance = getattr(self, "instance", None)
        titulo = attrs.get("titulo") or (instance.titulo if instance else None)
        articulo = (
            attrs.get("articulo")
            if "articulo" in attrs
            else (instance.articulo if instance else None)
        )
        inciso = (
            attrs.get("inciso") if "inciso" in attrs else (instance.inciso if instance else "-")
        )
        descripcion = attrs.get("descripcion") or (instance.descripcion if instance else "")

        if articulo is not None and articulo < 1:
            raise serializers.ValidationError(
                {"articulo": ["El número de artículo debe ser mayor o igual a 1."]}
            )

        if not str(descripcion).strip():
            raise serializers.ValidationError(
                {"cuerpo": ["El cuerpo del artículo no puede estar vacío."]}
            )

        activo = (
            attrs.get("activo") if "activo" in attrs else (instance.activo if instance else True)
        )

        if activo and titulo and articulo is not None and inciso is not None:
            qs = ArticuloReglamento.objects.filter(
                titulo=titulo,
                articulo=articulo,
                inciso=inciso,
                activo=True,
            )
            if instance:
                qs = qs.exclude(pk=instance.pk)
            if qs.exists():
                raise serializers.ValidationError(
                    {
                        "non_field_errors": [
                            "Ya existe un artículo activo con la misma combinación "
                            "de título, artículo e inciso."
                        ]
                    }
                )

        return attrs

    def get_created_by_display(self, obj: ArticuloReglamento) -> str | None:
        user = obj.created_by
        if not user:
            return None
        socio = getattr(user, "socio", None)
        name = (
            f"{socio.first_name} {socio.last_name}".strip()
            if socio is not None
            else user.get_full_name().strip()
        )
        username = user.get_username()
        return f"{name} ({username})" if name else username

    def get_updated_by_display(self, obj: ArticuloReglamento) -> str | None:
        user = obj.updated_by
        if not user:
            return None
        socio = getattr(user, "socio", None)
        name = (
            f"{socio.first_name} {socio.last_name}".strip()
            if socio is not None
            else user.get_full_name().strip()
        )
        username = user.get_username()
        return f"{name} ({username})" if name else username
