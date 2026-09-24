"""Configuración de URLs para la Capa Anticorrupción del padrón institucional."""

from django.urls import path

from padron.views import (
    PadronHealthCheckView,
    PadronSocioDetailView,
    PadronSocioLegajoDetailView,
    PadronSocioListView,
    PadronSubcomisionListView,
)

app_name = "padron"

urlpatterns = [
    path("health/", PadronHealthCheckView.as_view(), name="health"),
    path("socios/", PadronSocioListView.as_view(), name="socio-list"),
    path("socios/<int:socio_id>/", PadronSocioDetailView.as_view(), name="socio-detail"),
    path(
        "socios/legajo/<str:legajo>/",
        PadronSocioLegajoDetailView.as_view(),
        name="socio-legajo-detail",
    ),
    path("subcomisiones/", PadronSubcomisionListView.as_view(), name="subcomision-list"),
]
