from django.urls import path

from expedientes.views import (
    BoardExpedientesView,
    CaseNotificationAuditView,
    DispatchCaseOpeningView,
    ExpedienteCollectionView,
    ExpedienteDetailView,
    MisExpedientesView,
    PresentarDescargoView,
    ReglamentosVigentesView,
    SolicitudT01CreateView,
    SolicitudT01DetailView,
    SolicitudT01EmitView,
    TransicionExpedienteView,
    TransicionarExpedienteView,
)

app_name = "expedientes"

urlpatterns = [
    path("reglamentos/", ReglamentosVigentesView.as_view(), name="reglamentos-vigentes"),
    path("", SolicitudT01CreateView.as_view(), name="solicitud-create"),
    path("gestion/", ExpedienteCollectionView.as_view(), name="expedientes"),
    path("mis-expedientes/", MisExpedientesView.as_view(), name="mis-expedientes"),
    path("<int:pk>/estado/", TransicionExpedienteView.as_view(), name="transicionar-expediente"),
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
    path("board/", BoardExpedientesView.as_view(), name="board"),
    path("<int:pk>/transicionar/", TransicionarExpedienteView.as_view(), name="transicionar"),
]
