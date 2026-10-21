"""Servicio de aplicación del historial inmutable de descargos (SCRUM-49 / S3-05).

Debe invocarse dentro de la transacción y del ``select_for_update`` del expediente que ya
abre la vista, de modo que la numeración correlativa no compita con otro envío.
"""

from django.db.models import Max

from expedientes.models import (
    DescargoExpediente,
    DescargoVersion,
    EvidenciaDescargo,
    OperacionDescargoEnum,
)
from socios.models import Socio


class DescargoVersionService:
    """Registra versiones y retiros lógicos de descargos sin borrar ninguna fila."""

    @staticmethod
    def actor_for(socio: Socio) -> str:
        return f"SOCIO_{socio.legajo}"

    @classmethod
    def registrar_version(
        cls, descargo: DescargoExpediente, operacion: str, socio: Socio
    ) -> DescargoVersion:
        """Crea la versión siguiente con una copia del contenido y las evidencias vigentes."""
        ultimo = descargo.versiones.aggregate(ultimo=Max("numero"))["ultimo"] or 0
        version = DescargoVersion.objects.create(
            descargo=descargo,
            numero=ultimo + 1,
            operacion=operacion,
            tipo=descargo.tipo,
            causal=descargo.causal,
            archivo=descargo.archivo,
            texto=descargo.texto,
            actor=cls.actor_for(socio),
        )
        version.evidencias.set(descargo.evidencias.filter(es_vigente=True))
        return version

    @classmethod
    def retirar(cls, descargo: DescargoExpediente, socio: Socio) -> DescargoVersion:
        """Baja lógica: registra la versión RETIRADO y desactiva el descargo y sus evidencias."""
        version = cls.registrar_version(descargo, OperacionDescargoEnum.RETIRADO, socio)
        EvidenciaDescargo.objects.filter(descargo=descargo, es_vigente=True).update(
            es_vigente=False
        )
        descargo.es_vigente = False
        descargo.save(update_fields=["es_vigente"])
        return version
