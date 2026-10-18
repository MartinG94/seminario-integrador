"""Backfill de la versión 1 para los descargos preexistentes (SCRUM-49 / S3-05).

Cada descargo que todavía no tiene historial recibe una versión ``PRESENTADO`` con su contenido
actual y sus evidencias vigentes, de modo que el historial por API no arranque vacío.
La operación es idempotente y la reversa es un no-op deliberado: borrar versiones podría
destruir historial creado por la aplicación luego del despliegue.
"""

from django.db import migrations


def backfill_initial_versions(apps, schema_editor) -> None:
    DescargoExpediente = apps.get_model("expedientes", "DescargoExpediente")
    DescargoVersion = apps.get_model("expedientes", "DescargoVersion")
    EvidenciaDescargo = apps.get_model("expedientes", "EvidenciaDescargo")

    pendientes = DescargoExpediente.objects.filter(versiones__isnull=True).select_related("socio")
    for descargo in pendientes:
        version = DescargoVersion.objects.create(
            descargo=descargo,
            numero=1,
            operacion="PRESENTADO",
            tipo=descargo.tipo,
            causal=descargo.causal,
            archivo=descargo.archivo,
            texto=descargo.texto,
            actor=f"SOCIO_{descargo.socio.legajo}",
        )
        # auto_now_add ignora el valor recibido al crear: se conserva la fecha original.
        DescargoVersion.objects.filter(pk=version.pk).update(created_at=descargo.presentado_at)
        evidencias = EvidenciaDescargo.objects.filter(descargo=descargo, es_vigente=True)
        version.evidencias.set(evidencias)


class Migration(migrations.Migration):
    dependencies = [
        ("expedientes", "0013_descargo_version"),
    ]

    operations = [
        migrations.RunPython(backfill_initial_versions, migrations.RunPython.noop),
    ]
