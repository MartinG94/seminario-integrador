"""Modelo de versiones inmutables del descargo (SCRUM-49 / S3-05, tarea T3).

Cubre:
1. Numeración única por descargo.
2. Inmutabilidad de la versión (no se actualiza ni se borra).
3. ``PROTECT`` desde el descargo y desde la evidencia: ningún borrado en cascada.
4. Vigencia por defecto del descargo y vínculo de evidencias por versión.
"""

from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import ProtectedError
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


@pytest.fixture
def descargo(socio: Socio) -> DescargoExpediente:
    exp = Expediente.objects.create(
        numero="EXP-401/2026",
        socio=socio,
        motivo="Modelo de versiones",
        estado=EstadoExpedienteEnum.JUSTIFICANDO,
        plazo_inicio_at=timezone.now() - timedelta(days=1),
        plazo_limite_at=timezone.now() + timedelta(days=3),
    )
    exp.socios.add(socio)
    return DescargoExpediente.objects.create(
        expediente=exp,
        socio=socio,
        tipo=TipoDescargoEnum.T03_EXTRAORDINARIO,
        texto="Texto inicial.",
    )


def _version(descargo: DescargoExpediente, numero: int = 1, **extra) -> DescargoVersion:
    data = {
        "descargo": descargo,
        "numero": numero,
        "operacion": OperacionDescargoEnum.PRESENTADO,
        "tipo": TipoDescargoEnum.T03_EXTRAORDINARIO,
        "texto": "Texto inicial.",
        "actor": "SOCIO_74907",
    }
    data.update(extra)
    return DescargoVersion.objects.create(**data)


def _evidencia(descargo: DescargoExpediente) -> EvidenciaDescargo:
    return EvidenciaDescargo.objects.create(
        expediente=descargo.expediente,
        descargo=descargo,
        socio=descargo.socio,
        contenido_blob=b"%PDF-1.4 prueba",
        nombre_original="prueba.pdf",
        extension=".pdf",
        mime_type="application/pdf",
        tamanio_bytes=15,
        sha256_hash="a" * 64,
    )


@pytest.mark.django_db
class TestDescargoVersionModel:
    def test_descargo_nace_vigente(self, descargo: DescargoExpediente) -> None:
        assert descargo.es_vigente is True

    def test_numero_de_version_es_unico_por_descargo(self, descargo: DescargoExpediente) -> None:
        _version(descargo, numero=1)

        with pytest.raises(IntegrityError), transaction.atomic():
            _version(descargo, numero=1)

    def test_versiones_se_listan_ordenadas_por_numero(self, descargo: DescargoExpediente) -> None:
        _version(descargo, numero=2, operacion=OperacionDescargoEnum.CORREGIDO)
        _version(descargo, numero=1)

        assert [v.numero for v in descargo.versiones.all()] == [1, 2]

    def test_version_no_se_puede_modificar_una_vez_creada(
        self, descargo: DescargoExpediente
    ) -> None:
        version = _version(descargo)
        version.texto = "Texto alterado."

        with pytest.raises(ValidationError):
            version.save()

        version.refresh_from_db()
        assert version.texto == "Texto inicial."

    def test_version_no_se_puede_eliminar(self, descargo: DescargoExpediente) -> None:
        version = _version(descargo)

        with pytest.raises(ValidationError):
            version.delete()

        assert DescargoVersion.objects.filter(pk=version.pk).exists()

    def test_descargo_con_versiones_no_se_puede_borrar(self, descargo: DescargoExpediente) -> None:
        _version(descargo)

        with pytest.raises(ProtectedError):
            descargo.delete()

        assert DescargoVersion.objects.filter(descargo=descargo).count() == 1

    def test_descargo_con_evidencia_no_se_puede_borrar_en_cascada(
        self, descargo: DescargoExpediente
    ) -> None:
        evidencia = _evidencia(descargo)

        with pytest.raises(ProtectedError):
            descargo.delete()

        assert EvidenciaDescargo.objects.filter(pk=evidencia.pk).exists()

    def test_version_conserva_el_juego_de_evidencias_asociado(
        self, descargo: DescargoExpediente
    ) -> None:
        evidencia = _evidencia(descargo)
        version = _version(descargo)
        version.evidencias.add(evidencia)

        assert list(version.evidencias.all()) == [evidencia]
        assert list(evidencia.versiones.all()) == [version]
