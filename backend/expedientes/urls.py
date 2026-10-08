from django.urls import path

from expedientes.views import (
    BoardExpedientesView,
    CalcularPlazoView,
    CalendarioFeriadosView,
    CalendarioVersionDetailView,
    CalendarioVersionListView,
    CaseNotificationAuditView,
    DispatchCaseOpeningView,
    ExpedienteCollectionView,
    ExpedienteDetailView,
    MisExpedientesView,
    MisSolicitudesT01View,
    PresentarDescargoView,
    ReglamentosVigentesView,
    SolicitudT01CreateView,
    SolicitudT01DetailView,
    SolicitudT01EmitView,
    TransicionarExpedienteView,
    TransicionExpedienteView,
)

app_name = "expedientes"

urlpatterns = [
    path("calendario/versiones/", CalendarioVersionListView.as_view(), name="calendario-versiones"),
    path(
        "calendario/versiones/<int:pk>/",
        CalendarioVersionDetailView.as_view(),
        name="calendario-version-detail",
    ),
    path("calendario/feriados/", CalendarioFeriadosView.as_view(), name="calendario-feriados"),
    path(
        "calendario/calcular-plazo/", CalcularPlazoView.as_view(), name="calendario-calcular-plazo"
    ),
    path("reglamentos/", ReglamentosVigentesView.as_view(), name="reglamentos-vigentes"),
    path("", SolicitudT01CreateView.as_view(), name="solicitud-create"),
    path("gestion/", ExpedienteCollectionView.as_view(), name="expedientes"),
    path("mis-expedientes/", MisExpedientesView.as_view(), name="mis-expedientes"),
    path("mis-solicitudes/", MisSolicitudesT01View.as_view(), name="mis-solicitudes"),
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
