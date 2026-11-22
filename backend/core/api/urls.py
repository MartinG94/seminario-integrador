"""Rutas del panel de administración y de los parámetros de lectura general (Spec 011)."""

from django.urls import path

from core.api.views import (
    AttachmentLimitsView,
    DeadlinesView,
    SystemParameterDetailView,
    SystemParameterHistoryView,
    SystemParameterListView,
    ThresholdsView,
    TribunalCandidateListView,
    TribunalMemberDetailView,
    TribunalMemberListView,
)

admin_urlpatterns = [
    path("parametros/", SystemParameterListView.as_view(), name="admin-parametros"),
    path(
        "parametros/<str:clave>/",
        SystemParameterDetailView.as_view(),
        name="admin-parametro-detalle",
    ),
    path(
        "parametros/<str:clave>/historial/",
        SystemParameterHistoryView.as_view(),
        name="admin-parametro-historial",
    ),
    path(
        "usuarios-td/candidatos/",
        TribunalCandidateListView.as_view(),
        name="admin-usuarios-td-candidatos",
    ),
    path("usuarios-td/", TribunalMemberListView.as_view(), name="admin-usuarios-td"),
    path(
        "usuarios-td/<int:socio_id>/",
        TribunalMemberDetailView.as_view(),
        name="admin-usuario-td-detalle",
    ),
]

public_urlpatterns = [
    path("adjuntos/", AttachmentLimitsView.as_view(), name="parametros-adjuntos"),
    path("umbrales/", ThresholdsView.as_view(), name="parametros-umbrales"),
    path("plazos/", DeadlinesView.as_view(), name="parametros-plazos"),
]
