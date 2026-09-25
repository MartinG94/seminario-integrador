"""Tests unitarios para los serializadores de validación y enrutamiento del padrón.

Cobertura:
  - SocioFilterParamsSerializer: validación de query params (MED-001).
  - SubcomisionSerializer: serialización de catálogo.
  - SocioInstitucionalSerializer: serialización canónica de socio (CA1-CA4).
  - PaginatedSociosSerializer: convención canónica count/results (LOW-IT2-001).
  - HealthStatusSerializer: 6 campos de observabilidad (CA5 / MED-003).
  - Enrutamiento base: resolución de URLs sin errores (HIGH-005).

Referencia: spec.md §RF-PADRON-01, plan.md §5.
"""

from django.urls import resolve

from padron.domain import (
    HealthStatusDTO,
    MembershipStatusEnum,
    PaginatedSociosDTO,
    SocioCategoryEnum,
    SocioInstitucionalDTO,
    SubcomisionDTO,
)

# ==============================================================================
# 1. SocioFilterParamsSerializer (MED-001)
# ==============================================================================


class TestSocioFilterParamsSerializer:
    """Pruebas de validación de query parameters para /api/v1/padron/socios/."""

    def test_empty_params_valid_with_defaults(self) -> None:
        """Query string vacío es válido y asigna page=1, page_size=20 por defecto."""
        from padron.serializers import SocioFilterParamsSerializer

        serializer = SocioFilterParamsSerializer(data={})
        assert serializer.is_valid(), serializer.errors
        data = serializer.validated_data
        assert data.get("page", 1) == 1
        assert data.get("page_size", 20) == 20

    def test_all_valid_parameters(self) -> None:
        """Query params con todos los filtros válidos es aceptado."""
        from padron.serializers import SocioFilterParamsSerializer

        payload = {
            "search": "Pérez",
            "subcomision_id": 1,
            "category": "ACTIVE",
            "is_active": "true",
            "membership_status": "ENABLED",
            "page": 2,
            "page_size": 50,
        }
        serializer = SocioFilterParamsSerializer(data=payload)
        assert serializer.is_valid(), serializer.errors
        data = serializer.validated_data
        assert data["search"] == "Pérez"
        assert data["subcomision_id"] == 1
        assert data["category"] == "ACTIVE"
        assert data["is_active"] is True
        assert data["membership_status"] == "ENABLED"
        assert data["page"] == 2
        assert data["page_size"] == 50

    def test_invalid_category_fails_validation(self) -> None:
        """Categoría no reconocida en SocioCategoryEnum falla validación (HTTP 400)."""
        from padron.serializers import SocioFilterParamsSerializer

        serializer = SocioFilterParamsSerializer(data={"category": "SENIOR_INVALID"})
        assert not serializer.is_valid()
        assert "category" in serializer.errors

    def test_invalid_membership_status_fails_validation(self) -> None:
        """Estado de membresía no reconocido falla validación (HTTP 400)."""
        from padron.serializers import SocioFilterParamsSerializer

        serializer = SocioFilterParamsSerializer(data={"membership_status": "EXPELLED"})
        assert not serializer.is_valid()
        assert "membership_status" in serializer.errors

    def test_page_zero_or_negative_fails_validation(self) -> None:
        """page < 1 falla validación (min_value=1)."""
        from padron.serializers import SocioFilterParamsSerializer

        serializer_zero = SocioFilterParamsSerializer(data={"page": 0})
        assert not serializer_zero.is_valid()
        assert "page" in serializer_zero.errors

        serializer_neg = SocioFilterParamsSerializer(data={"page": -5})
        assert not serializer_neg.is_valid()
        assert "page" in serializer_neg.errors

    def test_page_size_exceeding_max_fails_validation(self) -> None:
        """page_size > 100 falla validación (max_value=100)."""
        from padron.serializers import SocioFilterParamsSerializer

        serializer = SocioFilterParamsSerializer(data={"page_size": 101})
        assert not serializer.is_valid()
        assert "page_size" in serializer.errors

    def test_subcomision_id_zero_or_negative_fails_validation(self) -> None:
        """subcomision_id < 1 falla validación (min_value=1)."""
        from padron.serializers import SocioFilterParamsSerializer

        serializer = SocioFilterParamsSerializer(data={"subcomision_id": 0})
        assert not serializer.is_valid()
        assert "subcomision_id" in serializer.errors


# ==============================================================================
# 2. SubcomisionSerializer
# ==============================================================================


class TestSubcomisionSerializer:
    """Pruebas para el serializador de subcomisiones."""

    def test_serialization_from_dto(self) -> None:
        """Serializa SubcomisionDTO a diccionario JSON."""
        from padron.serializers import SubcomisionSerializer

        dto = SubcomisionDTO(id=1, name="Cómputos")
        serializer = SubcomisionSerializer(dto)
        assert serializer.data == {"id": 1, "name": "Cómputos"}


# ==============================================================================
# 3. SocioInstitucionalSerializer
# ==============================================================================


class TestSocioInstitucionalSerializer:
    """Pruebas para el serializador canónico de socio institucional."""

    def test_serialization_full_dto(self) -> None:
        """Serializa un socio completo con subcomisión y campos poblados."""
        from padron.serializers import SocioInstitucionalSerializer

        dto = SocioInstitucionalDTO(
            socio_id=1001,
            legajo="85421",
            dni="41234567",
            first_name="Esteban",
            last_name="Pérez",
            email="esteban.perez@aveit.utn.edu.ar",
            subcomision=SubcomisionDTO(id=10, name="Tribunal de Disciplina"),
            social_year=4,
            category=SocioCategoryEnum.ACTIVE,
            is_active=True,
            membership_status=MembershipStatusEnum.ENABLED,
        )
        serializer = SocioInstitucionalSerializer(dto)
        data = serializer.data

        assert data["socio_id"] == 1001
        assert data["legajo"] == "85421"
        assert data["dni"] == "41234567"
        assert data["first_name"] == "Esteban"
        assert data["last_name"] == "Pérez"
        assert data["email"] == "esteban.perez@aveit.utn.edu.ar"
        assert data["subcomision"] == {"id": 10, "name": "Tribunal de Disciplina"}
        assert data["social_year"] == 4
        assert data["category"] == "ACTIVE"
        assert data["is_active"] is True
        assert data["membership_status"] == "ENABLED"

    def test_serialization_nullable_fields(self) -> None:
        """Serializa correctamente socio con legajo, dni, email y subcomisión nulos."""
        from padron.serializers import SocioInstitucionalSerializer

        dto = SocioInstitucionalDTO(
            socio_id=1002,
            legajo=None,
            dni=None,
            first_name="María",
            last_name="García",
            email=None,
            subcomision=None,
            social_year=1,
            category=SocioCategoryEnum.PASSIVE,
            is_active=False,
            membership_status=MembershipStatusEnum.TERMINATED,
        )
        serializer = SocioInstitucionalSerializer(dto)
        data = serializer.data

        assert data["socio_id"] == 1002
        assert data["legajo"] is None
        assert data["dni"] is None
        assert data["email"] is None
        assert data["subcomision"] is None
        assert data["category"] == "PASSIVE"
        assert data["is_active"] is False
        assert data["membership_status"] == "TERMINATED"


# ==============================================================================
# 4. PaginatedSociosSerializer (LOW-IT2-001)
# ==============================================================================


class TestPaginatedSociosSerializer:
    """Pruebas para el serializador de listado paginado con count y results."""

    def test_serialization_paginated_dto(self) -> None:
        """Serializa PaginatedSociosDTO a JSON con estructura count/results."""
        from padron.serializers import PaginatedSociosSerializer

        socio_dto = SocioInstitucionalDTO(
            socio_id=1001,
            legajo="85421",
            dni="41234567",
            first_name="Esteban",
            last_name="Pérez",
            email="esteban.perez@aveit.utn.edu.ar",
            subcomision=None,
            social_year=4,
            category=SocioCategoryEnum.ACTIVE,
            is_active=True,
            membership_status=MembershipStatusEnum.ENABLED,
        )
        paginated_dto = PaginatedSociosDTO(
            count=1,
            results=[socio_dto],
            page=1,
            page_size=20,
        )

        serializer = PaginatedSociosSerializer(paginated_dto)
        data = serializer.data

        assert data["count"] == 1
        assert data["page"] == 1
        assert data["page_size"] == 20
        assert len(data["results"]) == 1
        assert data["results"][0]["socio_id"] == 1001


# ==============================================================================
# 5. HealthStatusSerializer (MED-003)
# ==============================================================================


class TestHealthStatusSerializer:
    """Pruebas para el serializador del estado de salud y observabilidad."""

    def test_serialization_health_dto(self) -> None:
        """Serializa HealthStatusDTO con sus 6 atributos canónicos."""
        from padron.serializers import HealthStatusSerializer

        dto = HealthStatusDTO(
            status="HEALTHY",
            latency_ms=12.5,
            source="mysql_institutional",
            record_count=515,
            last_checked_at="2026-09-22T12:00:00Z",
            message="Conexión operativa.",
        )
        serializer = HealthStatusSerializer(dto)
        data = serializer.data

        assert data["status"] == "HEALTHY"
        assert data["latency_ms"] == 12.5
        assert data["source"] == "mysql_institutional"
        assert data["record_count"] == 515
        assert data["last_checked_at"] == "2026-09-22T12:00:00Z"
        assert data["message"] == "Conexión operativa."


# ==============================================================================
# 6. Enrutamiento Base (HIGH-005)
# ==============================================================================


class TestPadronUrlsRouting:
    """Pruebas para la integración de URLs base del padrón en core/urls.py."""

    def test_health_url_resolves(self) -> None:
        """La ruta /api/v1/padron/health/ se resuelve correctamente."""
        match = resolve("/api/v1/padron/health/")
        assert match is not None

    def test_socios_list_url_resolves(self) -> None:
        """La ruta /api/v1/padron/socios/ se resuelve correctamente."""
        match = resolve("/api/v1/padron/socios/")
        assert match is not None

    def test_socio_detail_url_resolves(self) -> None:
        """La ruta /api/v1/padron/socios/<id>/ se resuelve correctamente."""
        match = resolve("/api/v1/padron/socios/42/")
        assert match is not None

    def test_socio_legajo_url_resolves(self) -> None:
        """La ruta /api/v1/padron/socios/legajo/<legajo>/ se resuelve correctamente."""
        match = resolve("/api/v1/padron/socios/legajo/85421/")
        assert match is not None

    def test_subcomisiones_url_resolves(self) -> None:
        """La ruta /api/v1/padron/subcomisiones/ se resuelve correctamente."""
        match = resolve("/api/v1/padron/subcomisiones/")
        assert match is not None
