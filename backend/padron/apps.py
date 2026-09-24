"""Configuración de la aplicación Django para el módulo de padrón institucional."""

from django.apps import AppConfig


class PadronConfig(AppConfig):
    """Configuración de la app padron — Capa Anticorrupción de sólo lectura."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "padron"
    verbose_name = "Padrón Institucional AVEIT"
