from django.urls import path

from expedientes.views import (
    CaseNotificationAuditView,
    DispatchCaseOpeningView,
    ExpedienteDetailView,
    MisExpedientesView,
    PresentarDescargoView,
    ReglamentosVigentesView,
    SolicitudT01CreateView,
    SolicitudT01DetailView,
    SolicitudT01EmitView,
)

app_name = "expedientes"

urlpatterns = [
    path("reglamentos/", ReglamentosVigentesView.as_view(), name="reglamentos-vigentes"),
    path("", SolicitudT01CreateView.as_view(), name="solicitud-create"),
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
    path("<uuid:pk>/", SolicitudT01DetailView.as_view(), name="solicitud-detail"),
    path("<uuid:pk>/emitir/", SolicitudT01EmitView.as_view(), name="solicitud-emit"),
]
