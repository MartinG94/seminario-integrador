from django.urls import path

from socios.views import PadronListView

app_name = "socios"

urlpatterns = [
    path("", PadronListView.as_view(), name="padron-list"),
]
