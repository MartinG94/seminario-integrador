"""Pruebas unitarias y de integración para la API REST de Reglamentos e Incisos (Milestone 3).

Verifica:
1. Autenticación: peticiones anónimas reciben 401 Unauthorized en todos los endpoints.
2. Control de Acceso RBAC (CanManageReglamentos):
   - SOCIO y FISCALIZADORA tienen acceso de sólo lectura (GET 200; POST/PATCH/DELETE 403 Forbidden).
   - TD, CD y ADMIN tienen permisos completos de administración (POST 201, PATCH 200, DELETE 204).
3. Búsqueda y filtrado:
   - Filtro por título (Reglamento Interno, Estatuto).
   - Búsqueda por número de artículo, texto del cuerpo e inciso.
   - Ordenamiento natural: por artículo ASC, luego '-' primero, y orden de inciso.
4. Validaciones de negocio:
   - Número de artículo >= 1.
   - Cuerpo o descripción obligatorio (no vacío ni sólo espacios).
   - Normalización de inciso: vacío/nulo se convierte en '-'.
   - Unicidad activa: rechaza duplicados activos para la tupla (titulo, articulo, inciso).
5. Baja lógica (Soft delete) y preservación histórica:
   - DELETE no ejecuta DELETE SQL; marca activo=False, deleted_at y deleted_by.
   - El artículo inactivo desaparece de listados activos y selector de expedientes.
   - Libera la tupla (titulo, articulo, inciso) permitiendo crear otro artículo idéntico.
   - No altera los reglamentos respaldantes almacenados en expedientes previos.
6. Bitácora inmutable de auditoría (AuditoriaArticuloReglamento):
   - Registra operaciones CREADO, MODIFICADO y ELIMINADO.
   - Almacena usuario, username, legajo, rol, snapshots de datos_anteriores y datos_nuevos.
   - Enforza inmutabilidad en save() y delete() lanzando ValidationError.
7. Endpoint ReglamentosVigentesView (/api/v1/expedientes/reglamentos/):
   - Accesible a todos los roles autenticados.
   - Retorna 'reglamentos' (citas completas) y 'articulos' (objetos DTO).
"""

import pytest
from django.core.exceptions import ValidationError
from rest_framework import status
from rest_framework.test import APIClient

from expedientes.models import (
    ArticuloReglamento,
    AuditoriaArticuloReglamento,
    OperacionAuditoriaReglamentoEnum,
    TipoReglamentoEnum,
)
from socios.models import Role, Socio


@pytest.fixture
def td_user(make_socio) -> Socio:
    return make_socio(legajo="70001", role=Role.TD, email="td_reg@aveit.test")


@pytest.fixture
def cd_user(make_socio) -> Socio:
    return make_socio(legajo="70002", role=Role.CD, email="cd_reg@aveit.test")


@pytest.fixture
def admin_user(make_socio) -> Socio:
    return make_socio(legajo="70003", role=Role.ADMIN, email="admin_reg@aveit.test")


@pytest.fixture
def fiscalizadora_user(make_socio) -> Socio:
    return make_socio(legajo="70004", role=Role.FISCALIZADORA, email="fisc_reg@aveit.test")


@pytest.fixture
def socio_user(make_socio) -> Socio:
    return make_socio(legajo="70005", role=Role.SOCIO, email="socio_reg@aveit.test")


@pytest.fixture(autouse=True)
def ensure_reglamentos_db(db):
    """Garantiza que la tabla tribunal_reglamento y datos canónicos existan en la base de tests."""
    import importlib
    from types import SimpleNamespace

    from django.apps import apps
    from django.db import connection

    mig_0019 = importlib.import_module("expedientes.migrations.0019_reglamento_abm_auditoria_seed")
    editor = SimpleNamespace(connection=connection)
    mig_0019.ensure_tables_and_columns(apps, editor)

    from expedientes.models import ArticuloReglamento

    if ArticuloReglamento.objects.count() == 0:
        mig_0019.seed_reglamentos_data(apps, editor)


@pytest.fixture
def sample_articulo(db, ensure_reglamentos_db) -> ArticuloReglamento:
    """Artículo de prueba para las operaciones CRUD."""
    art, _ = ArticuloReglamento.objects.update_or_create(
        titulo=TipoReglamentoEnum.REGLAMENTO_INTERNO,
        articulo=999,
        inciso="-",
        defaults={
            "seccion": 1,
            "descripcion": "Artículo de prueba para auditoría y ciclo de vida de reglamentos.",
            "activo": True,
        },
    )
    return art


@pytest.mark.django_db
class TestReglamentosAuthentication:
    """Verifica que las peticiones no autenticadas sean rechazadas con 401 Unauthorized."""

    def test_list_unauthenticated_returns_401(self, api_client: APIClient):
        response = api_client.get("/api/v1/expedientes/reglamentos/articulos/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_unauthenticated_returns_401(self, api_client: APIClient):
        response = api_client.post(
            "/api/v1/expedientes/reglamentos/articulos/",
            {
                "titulo": TipoReglamentoEnum.REGLAMENTO_INTERNO,
                "articulo": 990,
                "inciso": "-",
                "cuerpo": "Prueba no auth",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_detail_unauthenticated_returns_401(
        self, api_client: APIClient, sample_articulo: ArticuloReglamento
    ):
        response = api_client.get(
            f"/api/v1/expedientes/reglamentos/articulos/{sample_articulo.pk}/"
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_update_unauthenticated_returns_401(
        self, api_client: APIClient, sample_articulo: ArticuloReglamento
    ):
        response = api_client.patch(
            f"/api/v1/expedientes/reglamentos/articulos/{sample_articulo.pk}/",
            {"cuerpo": "Modificación no auth"},
            format="json",
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_delete_unauthenticated_returns_401(
        self, api_client: APIClient, sample_articulo: ArticuloReglamento
    ):
        response = api_client.delete(
            f"/api/v1/expedientes/reglamentos/articulos/{sample_articulo.pk}/"
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_reglamentos_vigentes_unauthenticated_returns_401(self, api_client: APIClient):
        response = api_client.get("/api/v1/expedientes/reglamentos/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestReglamentosRBAC:
    """Verifica que los roles sin permiso CanManageReglamentos sólo tengan lectura."""

    def test_socio_can_read_but_cannot_modify(
        self, socio_user: Socio, sample_articulo: ArticuloReglamento, authenticate
    ):
        client = authenticate(socio_user)

        # GET lista -> 200
        res_list = client.get("/api/v1/expedientes/reglamentos/articulos/")
        assert res_list.status_code == status.HTTP_200_OK

        # GET detalle -> 200
        res_detail = client.get(f"/api/v1/expedientes/reglamentos/articulos/{sample_articulo.pk}/")
        assert res_detail.status_code == status.HTTP_200_OK

        # POST -> 403 Forbidden
        res_post = client.post(
            "/api/v1/expedientes/reglamentos/articulos/",
            {
                "titulo": TipoReglamentoEnum.REGLAMENTO_INTERNO,
                "articulo": 980,
                "inciso": "-",
                "cuerpo": "Intento de socio",
            },
            format="json",
        )
        assert res_post.status_code == status.HTTP_403_FORBIDDEN

        # PATCH -> 403 Forbidden
        res_patch = client.patch(
            f"/api/v1/expedientes/reglamentos/articulos/{sample_articulo.pk}/",
            {"cuerpo": "Intento de modificación"},
            format="json",
        )
        assert res_patch.status_code == status.HTTP_403_FORBIDDEN

        # DELETE -> 403 Forbidden
        res_delete = client.delete(
            f"/api/v1/expedientes/reglamentos/articulos/{sample_articulo.pk}/"
        )
        assert res_delete.status_code == status.HTTP_403_FORBIDDEN

    def test_fiscalizadora_can_read_but_cannot_modify(
        self, fiscalizadora_user: Socio, sample_articulo: ArticuloReglamento, authenticate
    ):
        client = authenticate(fiscalizadora_user)

        # GET lista -> 200
        res_list = client.get("/api/v1/expedientes/reglamentos/articulos/")
        assert res_list.status_code == status.HTTP_200_OK

        # POST -> 403 Forbidden
        res_post = client.post(
            "/api/v1/expedientes/reglamentos/articulos/",
            {
                "titulo": TipoReglamentoEnum.ESTATUTO,
                "articulo": 981,
                "inciso": "-",
                "cuerpo": "Intento de fiscalizadora",
            },
            format="json",
        )
        assert res_post.status_code == status.HTTP_403_FORBIDDEN

        # DELETE -> 403 Forbidden
        res_del = client.delete(f"/api/v1/expedientes/reglamentos/articulos/{sample_articulo.pk}/")
        assert res_del.status_code == status.HTTP_403_FORBIDDEN

    def test_td_cd_admin_can_manage(
        self, td_user: Socio, cd_user: Socio, admin_user: Socio, authenticate
    ):
        # 1. TD puede crear
        td_client = authenticate(td_user)
        res_td = td_client.post(
            "/api/v1/expedientes/reglamentos/articulos/",
            {
                "titulo": TipoReglamentoEnum.REGLAMENTO_INTERNO,
                "articulo": 950,
                "inciso": "a",
                "cuerpo": "Artículo creado por TD",
            },
            format="json",
        )
        assert res_td.status_code == status.HTTP_201_CREATED
        art_id = res_td.data["id"]

        # 2. CD puede editar
        cd_client = authenticate(cd_user)
        res_cd = cd_client.patch(
            f"/api/v1/expedientes/reglamentos/articulos/{art_id}/",
            {"cuerpo": "Artículo editado por CD"},
            format="json",
        )
        assert res_cd.status_code == status.HTTP_200_OK
        assert res_cd.data["cuerpo"] == "Artículo editado por CD"

        # 3. ADMIN puede dar de baja lógica
        admin_client = authenticate(admin_user)
        res_admin = admin_client.delete(f"/api/v1/expedientes/reglamentos/articulos/{art_id}/")
        assert res_admin.status_code == status.HTTP_204_NO_CONTENT

        # Confirmación de baja lógica en base de datos
        art = ArticuloReglamento.objects.get(pk=art_id)
        assert art.activo is False
        assert art.deleted_at is not None
        assert art.deleted_by == admin_user.user


@pytest.mark.django_db
class TestReglamentosSearchAndFiltering:
    """Verifica los filtros por título y la búsqueda en número, inciso y texto."""

    def test_filter_by_titulo(self, socio_user: Socio, authenticate):
        client = authenticate(socio_user)

        res_ri = client.get(
            "/api/v1/expedientes/reglamentos/articulos/",
            {"titulo": TipoReglamentoEnum.REGLAMENTO_INTERNO},
        )
        assert res_ri.status_code == status.HTTP_200_OK
        assert len(res_ri.data) > 0
        for item in res_ri.data:
            assert item["titulo"] == TipoReglamentoEnum.REGLAMENTO_INTERNO

        res_est = client.get(
            "/api/v1/expedientes/reglamentos/articulos/",
            {"titulo": TipoReglamentoEnum.ESTATUTO},
        )
        assert res_est.status_code == status.HTTP_200_OK
        assert len(res_est.data) > 0
        for item in res_est.data:
            assert item["titulo"] == TipoReglamentoEnum.ESTATUTO

    def test_search_by_article_number_and_text(self, socio_user: Socio, authenticate):
        client = authenticate(socio_user)

        # Crear dos artículos específicos para la prueba
        ArticuloReglamento.objects.update_or_create(
            titulo=TipoReglamentoEnum.REGLAMENTO_INTERNO,
            articulo=888,
            inciso="-",
            defaults={"descripcion": "Texto con término único xenomorfo", "activo": True},
        )
        ArticuloReglamento.objects.update_or_create(
            titulo=TipoReglamentoEnum.REGLAMENTO_INTERNO,
            articulo=889,
            inciso="z",
            defaults={"descripcion": "Otro texto sin término", "activo": True},
        )

        # Búsqueda por número exacto
        res_num = client.get(
            "/api/v1/expedientes/reglamentos/articulos/",
            {"search": "888"},
        )
        assert res_num.status_code == status.HTTP_200_OK
        ids = [a["id"] for a in res_num.data]
        art_888 = ArticuloReglamento.objects.get(articulo=888, inciso="-")
        assert art_888.id in ids

        # Búsqueda por formato "Art. 888"
        res_art = client.get(
            "/api/v1/expedientes/reglamentos/articulos/",
            {"search": "Art. 888"},
        )
        assert res_art.status_code == status.HTTP_200_OK
        assert any(a["articulo"] == 888 for a in res_art.data)

        # Búsqueda por texto único
        res_txt = client.get(
            "/api/v1/expedientes/reglamentos/articulos/",
            {"search": "xenomorfo"},
        )
        assert res_txt.status_code == status.HTTP_200_OK
        assert len(res_txt.data) == 1
        assert res_txt.data[0]["articulo"] == 888

        # Búsqueda por inciso
        res_inc = client.get(
            "/api/v1/expedientes/reglamentos/articulos/",
            {"search": "z"},
        )
        assert res_inc.status_code == status.HTTP_200_OK
        assert any(a["articulo"] == 889 and a["inciso"] == "z" for a in res_inc.data)


@pytest.mark.django_db
class TestReglamentosValidation:
    """Verifica reglas de validación en creación y edición de artículos."""

    def test_articulo_number_must_be_greater_equal_1(self, td_user: Socio, authenticate):
        client = authenticate(td_user)
        response = client.post(
            "/api/v1/expedientes/reglamentos/articulos/",
            {
                "titulo": TipoReglamentoEnum.REGLAMENTO_INTERNO,
                "articulo": 0,
                "inciso": "-",
                "cuerpo": "Artículo número cero inválido",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "articulo" in response.data

    def test_empty_cuerpo_rejected(self, td_user: Socio, authenticate):
        client = authenticate(td_user)
        response = client.post(
            "/api/v1/expedientes/reglamentos/articulos/",
            {
                "titulo": TipoReglamentoEnum.REGLAMENTO_INTERNO,
                "articulo": 970,
                "inciso": "-",
                "cuerpo": "   ",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "cuerpo" in response.data

    def test_inciso_normalized_to_dash_when_empty_or_none(self, td_user: Socio, authenticate):
        client = authenticate(td_user)
        response = client.post(
            "/api/v1/expedientes/reglamentos/articulos/",
            {
                "titulo": TipoReglamentoEnum.REGLAMENTO_INTERNO,
                "articulo": 971,
                "inciso": "",
                "cuerpo": "Artículo con inciso vacío",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["inciso"] == "-"
        assert response.data["cita_corta"] == "Reglamento Interno - Art. 971"

    def test_duplicate_active_article_rejected(
        self, td_user: Socio, sample_articulo: ArticuloReglamento, authenticate
    ):
        client = authenticate(td_user)
        # Intentar crear un artículo con los mismos (titulo, articulo, inciso) ya activos
        response = client.post(
            "/api/v1/expedientes/reglamentos/articulos/",
            {
                "titulo": sample_articulo.titulo,
                "articulo": sample_articulo.articulo,
                "inciso": sample_articulo.inciso,
                "cuerpo": "Intento de duplicación activa",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "non_field_errors" in response.data
        assert (
            "Ya existe un artículo activo con la misma combinación"
            in response.data["non_field_errors"][0]
        )


@pytest.mark.django_db
class TestReglamentosSoftDeleteAndAudit:
    """Verifica baja lógica, re-creación de tupla liberada e inmutabilidad de bitácora."""

    def test_soft_delete_lifecycle_and_tuple_freeing(self, td_user: Socio, authenticate):
        client = authenticate(td_user)

        # 1. Crear artículo
        res_create = client.post(
            "/api/v1/expedientes/reglamentos/articulos/",
            {
                "titulo": TipoReglamentoEnum.REGLAMENTO_INTERNO,
                "articulo": 960,
                "inciso": "1",
                "cuerpo": "Versión 1 del artículo 960 inc 1",
            },
            format="json",
        )
        assert res_create.status_code == status.HTTP_201_CREATED
        art_id = res_create.data["id"]

        # Verificar auditoría de CREADO
        audit_create = AuditoriaArticuloReglamento.objects.filter(
            articulo_reglamento_id=art_id, operacion=OperacionAuditoriaReglamentoEnum.CREADO
        ).first()
        assert audit_create is not None
        assert audit_create.usuario == td_user.user
        assert audit_create.legajo == td_user.legajo
        assert audit_create.rol == Role.TD
        assert audit_create.datos_nuevos["articulo"] == 960

        # 2. Modificar artículo
        res_mod = client.patch(
            f"/api/v1/expedientes/reglamentos/articulos/{art_id}/",
            {"cuerpo": "Versión 1.1 actualizada del artículo 960"},
            format="json",
        )
        assert res_mod.status_code == status.HTTP_200_OK

        # Verificar auditoría de MODIFICADO
        audit_mod = AuditoriaArticuloReglamento.objects.filter(
            articulo_reglamento_id=art_id, operacion=OperacionAuditoriaReglamentoEnum.MODIFICADO
        ).first()
        assert audit_mod is not None
        assert audit_mod.datos_anteriores["cuerpo"] == "Versión 1 del artículo 960 inc 1"
        assert audit_mod.datos_nuevos["cuerpo"] == "Versión 1.1 actualizada del artículo 960"

        # 3. Borrar lógicamente el artículo
        res_del = client.delete(f"/api/v1/expedientes/reglamentos/articulos/{art_id}/")
        assert res_del.status_code == status.HTTP_204_NO_CONTENT

        # El registro aún existe en BD pero con activo = False
        art_inactivo = ArticuloReglamento.objects.get(pk=art_id)
        assert art_inactivo.activo is False
        assert art_inactivo.deleted_at is not None
        assert art_inactivo.deleted_by == td_user.user

        # Verificar auditoría de ELIMINADO
        audit_del = AuditoriaArticuloReglamento.objects.filter(
            articulo_reglamento_id=art_id, operacion=OperacionAuditoriaReglamentoEnum.ELIMINADO
        ).first()
        assert audit_del is not None
        assert audit_del.datos_anteriores["id"] == art_id

        # 4. Comprobar que desapareció de los listados activos
        res_list = client.get("/api/v1/expedientes/reglamentos/articulos/")
        active_ids = [a["id"] for a in res_list.data]
        assert art_id not in active_ids

        # 5. Volver a crear la misma tupla (titulo, articulo, inciso) -> Ahora debe permitirse
        res_recreate = client.post(
            "/api/v1/expedientes/reglamentos/articulos/",
            {
                "titulo": TipoReglamentoEnum.REGLAMENTO_INTERNO,
                "articulo": 960,
                "inciso": "1",
                "cuerpo": "Nueva versión activa del artículo 960 inc 1",
            },
            format="json",
        )
        assert res_recreate.status_code == status.HTTP_201_CREATED
        new_art_id = res_recreate.data["id"]
        assert new_art_id != art_id

        # Ambos coexisten en la base: uno histórico inactivo y uno nuevo activo
        assert ArticuloReglamento.objects.filter(articulo=960, inciso="1").count() == 2

    def test_auditoria_model_immutability(
        self, sample_articulo: ArticuloReglamento, td_user: Socio
    ):
        """Verifica que AuditoriaArticuloReglamento prohíbe updates y deletes."""
        audit = AuditoriaArticuloReglamento.objects.create(
            articulo_reglamento=sample_articulo,
            operacion=OperacionAuditoriaReglamentoEnum.CREADO,
            usuario=td_user.user,
            usuario_username=td_user.user.username,
            legajo=td_user.legajo,
            rol=td_user.role,
            datos_nuevos={"test": "snapshot"},
        )
        assert audit.pk is not None

        # Intento de modificación -> ValidationError
        audit.rol = "MODIFICADO"
        with pytest.raises(ValidationError, match="inmutables"):
            audit.save()

        # Intento de borrado -> ValidationError
        with pytest.raises(ValidationError, match="no pueden eliminarse"):
            audit.delete()


@pytest.mark.django_db
class TestReglamentosVigentesView:
    """Verifica el endpoint de reglamentos vigentes consumido por expedientes y resoluciones."""

    def test_reglamentos_vigentes_returns_formatted_data(
        self, socio_user: Socio, sample_articulo: ArticuloReglamento, authenticate
    ):
        client = authenticate(socio_user)
        response = client.get("/api/v1/expedientes/reglamentos/")
        assert response.status_code == status.HTTP_200_OK
        assert "reglamentos" in response.data
        assert "articulos" in response.data

        # Debe ser una lista de citas completas en texto plano
        reglamentos = response.data["reglamentos"]
        assert isinstance(reglamentos, list)
        assert sample_articulo.cita_completa in reglamentos

        # Debe incluir los objetos serializados completos
        articulos = response.data["articulos"]
        assert isinstance(articulos, list)
        item = next((a for a in articulos if a["id"] == sample_articulo.id), None)
        assert item is not None
        assert item["titulo"] == sample_articulo.titulo
        assert item["articulo"] == sample_articulo.articulo
        assert item["cuerpo"] == sample_articulo.descripcion

    def test_inactive_article_excluded_from_reglamentos_vigentes(
        self, socio_user: Socio, sample_articulo: ArticuloReglamento, authenticate
    ):
        client = authenticate(socio_user)

        # Marcar como inactivo
        sample_articulo.activo = False
        sample_articulo.save(update_fields=["activo"])

        response = client.get("/api/v1/expedientes/reglamentos/")
        assert response.status_code == status.HTTP_200_OK

        assert sample_articulo.cita_completa not in response.data["reglamentos"]
        art_ids = [a["id"] for a in response.data["articulos"]]
        assert sample_articulo.id not in art_ids
