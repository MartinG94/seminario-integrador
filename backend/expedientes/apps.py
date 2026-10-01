"""Configuración de la aplicación Django expedientes."""

from django.apps import AppConfig


class ExpedientesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "expedientes"
    verbose_name = "Expedientes Disciplinarios y Descargos"
