"""Rutas de URL para el módulo expedientes."""

from django.urls import path

from expedientes.views import (
    CaseNotificationAuditView,
    DispatchCaseOpeningView,
    ExpedienteDetailView,
    MisExpedientesView,
    PresentarDescargoView,
)

app_name = "expedientes"

urlpatterns = [
    path("mis-expedientes/", MisExpedientesView.as_view(), name="mis-expedientes"),
    path("<int:pk>/descargo/", PresentarDescargoView.as_view(), name="presentar-descargo"),
    path(
        "<int:pk>/despachar-notificacion/",
        DispatchCaseOpeningView.as_view(),
        name="expediente-despachar-notificacion",
    ),
    path(
        "<int:pk>/notificaciones/",
        CaseNotificationAuditView.as_view(),
        name="expediente-notificaciones",
    ),
    path("<int:pk>/", ExpedienteDetailView.as_view(), name="expediente-detail"),
]
