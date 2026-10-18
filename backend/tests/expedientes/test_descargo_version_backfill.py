"""Migración de datos: versión 1 de los descargos preexistentes (SCRUM-49 / S3-05, tarea T4)."""

from datetime import timedelta
from importlib import import_module

import pytest
from django.apps import apps as global_apps
from django.contrib.auth import get_user_model
from django.utils import timezone

from expedientes.models import (
    DescargoExpediente,
    DescargoVersion,
    EstadoExpedienteEnum,
    EvidenciaDescargo,
    Expediente,
    OperacionDescargoEnum,
    TipoDescargoEnum,
)
from socios.models import Role, Socio, Subcomision

User = get_user_model()
backfill = import_module("expedientes.migrations.0014_backfill_descargo_version_inicial")


@pytest.fixture
def socio(db) -> Socio:
    user = User.objects.create_user(username="74907", password="secure_password_123")
    sub = Subcomision.objects.create(name="Cómputos")
    return Socio.objects.create(
        user=user,
        legajo="74907",
        first_name="Lucas",
        last_name="Prueba",
        email="74907@aveit.test",
        subcomision=sub,
        social_year=4,
        role=Role.SOCIO,
    )


def _evidencia(descargo: DescargoExpediente, nombre: str, *, vigente: bool) -> EvidenciaDescargo:
    return EvidenciaDescargo.objects.create(
        expediente=descargo.expediente,
        descargo=descargo,
        socio=descargo.socio,
        contenido_blob=b"%PDF-1.4 prueba",
        nombre_original=nombre,
        extension=".pdf",
        mime_type="application/pdf",
        tamanio_bytes=15,
        sha256_hash="b" * 64,
        es_vigente=vigente,
    )


@pytest.fixture
def descargo_preexistente(socio: Socio) -> DescargoExpediente:
    exp = Expediente.objects.create(
        numero="EXP-501/2026",
        socio=socio,
        motivo="Backfill",
        estado=EstadoExpedienteEnum.JUSTIFICANDO,
        plazo_inicio_at=timezone.now() - timedelta(days=1),
        plazo_limite_at=timezone.now() + timedelta(days=3),
    )
    exp.socios.add(socio)
    return DescargoExpediente.objects.create(
        expediente=exp,
        socio=socio,
        tipo=TipoDescargoEnum.T03_EXTRAORDINARIO,
        causal="Otro",
        archivo="escrito.pdf",
        texto="Escrito previo a la versión.",
    )


@pytest.mark.django_db
class TestBackfillVersionInicial:
    def test_crea_version_1_con_el_contenido_actual(
        self, descargo_preexistente: DescargoExpediente
    ) -> None:
        backfill.backfill_initial_versions(global_apps, None)

        version = DescargoVersion.objects.get(descargo=descargo_preexistente)
        assert version.numero == 1
        assert version.operacion == OperacionDescargoEnum.PRESENTADO
        assert version.tipo == TipoDescargoEnum.T03_EXTRAORDINARIO
        assert version.causal == "Otro"
        assert version.archivo == "escrito.pdf"
        assert version.texto == "Escrito previo a la versión."
        assert version.actor == "SOCIO_74907"
        assert version.created_at == descargo_preexistente.presentado_at

    def test_vincula_solo_las_evidencias_vigentes(
        self, descargo_preexistente: DescargoExpediente
    ) -> None:
        vigente = _evidencia(descargo_preexistente, "vigente.pdf", vigente=True)
        _evidencia(descargo_preexistente, "anterior.pdf", vigente=False)

        backfill.backfill_initial_versions(global_apps, None)

        version = DescargoVersion.objects.get(descargo=descargo_preexistente)
        assert list(version.evidencias.all()) == [vigente]

    def test_es_idempotente(self, descargo_preexistente: DescargoExpediente) -> None:
        backfill.backfill_initial_versions(global_apps, None)
        backfill.backfill_initial_versions(global_apps, None)

        assert DescargoVersion.objects.filter(descargo=descargo_preexistente).count() == 1

    def test_no_toca_descargos_que_ya_tienen_versiones(
        self, descargo_preexistente: DescargoExpediente
    ) -> None:
        DescargoVersion.objects.create(
            descargo=descargo_preexistente,
            numero=1,
            operacion=OperacionDescargoEnum.PRESENTADO,
            tipo=TipoDescargoEnum.T03_EXTRAORDINARIO,
            texto="Versión creada por la aplicación.",
            actor="SOCIO_74907",
        )

        backfill.backfill_initial_versions(global_apps, None)

        versiones = DescargoVersion.objects.filter(descargo=descargo_preexistente)
        assert [v.texto for v in versiones] == ["Versión creada por la aplicación."]
