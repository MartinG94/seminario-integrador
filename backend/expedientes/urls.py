"""Rutas de URL para el módulo expedientes."""

from django.urls import path

from expedientes.views import (
    ExpedienteCollectionView,
    MisExpedientesView,
    PresentarDescargoView,
    TransicionExpedienteView,
)

app_name = "expedientes"

urlpatterns = [
    path("", ExpedienteCollectionView.as_view(), name="expedientes"),
    path("mis-expedientes/", MisExpedientesView.as_view(), name="mis-expedientes"),
    path("<int:pk>/estado/", TransicionExpedienteView.as_view(), name="transicionar-expediente"),
    path("<int:pk>/descargo/", PresentarDescargoView.as_view(), name="presentar-descargo"),
]
