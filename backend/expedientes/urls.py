"""Rutas de URL para el módulo expedientes."""

from django.urls import path

from expedientes.views import MisExpedientesView, PresentarDescargoView

app_name = "expedientes"

urlpatterns = [
    path("mis-expedientes/", MisExpedientesView.as_view(), name="mis-expedientes"),
    path("<int:pk>/descargo/", PresentarDescargoView.as_view(), name="presentar-descargo"),
]
