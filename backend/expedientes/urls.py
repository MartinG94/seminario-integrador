from django.urls import path

from .views import SolicitudT01CreateView, SolicitudT01DetailView, SolicitudT01EmitView

app_name = "expedientes"

urlpatterns = [
    path("", SolicitudT01CreateView.as_view(), name="solicitud-create"),
    path("<uuid:pk>/", SolicitudT01DetailView.as_view(), name="solicitud-detail"),
    path("<uuid:pk>/emitir/", SolicitudT01EmitView.as_view(), name="solicitud-emit"),
]
