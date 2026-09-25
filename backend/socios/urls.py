from django.urls import path

from socios.views import PadronListView, SocioLegajoDetailView

app_name = "socios"

urlpatterns = [
    path("", PadronListView.as_view(), name="padron-list"),
    path("<str:pk>/legajo/", SocioLegajoDetailView.as_view(), name="socio-legajo"),
]
