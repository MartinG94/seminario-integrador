from django.urls import include, path
from rest_framework.routers import DefaultRouter

from expedientes.resolution_views import (
    ResolucionEmitirView,
    ResolucionPreviewView,
    ResolucionView,
)
from expedientes.views import (
    BoardExpedientesView,
    CalcularPlazoView,
    CalendarioFeriadosView,
    CaseNotificationAuditView,
    DecisionCausalView,
    DescargoVersionesView,
    DispatchCaseOpeningView,
    EventoInstitucionalViewSet,
    EvidenciaDownloadView,
    EvidenciaUploadView,
    ExpedienteCollectionView,
    ExpedienteDetailView,
    MisExpedientesView,
    MisSolicitudesT01View,
    PresentarDescargoView,
    RegistroApercibimientoViewSet,
    ReglamentosVigentesView,
    SocioApercibimientosView,
    SolicitudT01CreateView,
    SolicitudT01DetailView,
    SolicitudT01EmitView,
    TransicionarExpedienteView,
    TransicionExpedienteView,
)

app_name = "expedientes"

router = DefaultRouter()
router.register(r"eventos", EventoInstitucionalViewSet, basename="evento")
router.register(r"apercibimientos", RegistroApercibimientoViewSet, basename="apercibimiento")

urlpatterns = [
    path(
        "<int:expediente_id>/resolucion/preview/",
        ResolucionPreviewView.as_view(),
        name="resolucion-preview",
    ),
    path("<int:expediente_id>/resolucion/", ResolucionView.as_view(), name="resolucion"),
    path(
        "<int:expediente_id>/resolucion/emitir/",
        ResolucionEmitirView.as_view(),
        name="resolucion-emitir",
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
        "<int:pk>/descargos/<int:descargo_id>/decisiones/",
        DecisionCausalView.as_view(),
        name="descargo-decisiones-causal",
    ),
    path(
        "<int:pk>/descargo/versiones/",
        DescargoVersionesView.as_view(),
        name="descargo-versiones",
    ),
    path("<int:pk>/evidencia/", EvidenciaUploadView.as_view(), name="expediente-evidencia-upload"),
    path(
        "<int:pk>/evidencia/<uuid:evidencia_id>/",
        EvidenciaDownloadView.as_view(),
        name="expediente-evidencia-download",
    ),
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
    path(
        "socios/<int:socio_id>/apercibimientos/",
        SocioApercibimientosView.as_view(),
        name="socio-apercibimientos",
    ),
    path("", include(router.urls)),
]
