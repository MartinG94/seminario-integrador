from django.urls import path

from socios.views import (
    MyPointsBalanceView,
    MyPointsHistoryView,
    PadronListView,
    SocioLegajoDetailView,
    SocioPointsHistoryView,
)

app_name = "socios"

urlpatterns = [
    path("", PadronListView.as_view(), name="padron-list"),
    path("me/points-balance/", MyPointsBalanceView.as_view(), name="my-points-balance"),
    path("me/points-history/", MyPointsHistoryView.as_view(), name="my-points-history"),
    path("<str:pk>/points-history/", SocioPointsHistoryView.as_view(), name="socio-points-history"),
    path("<str:pk>/legajo/", SocioLegajoDetailView.as_view(), name="socio-legajo"),
]
