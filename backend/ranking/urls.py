"""URLs para el módulo ranking."""

from django.urls import path

from ranking.views import RankingListView

app_name = "ranking"

urlpatterns = [
    path("", RankingListView.as_view(), name="ranking-list"),
]
