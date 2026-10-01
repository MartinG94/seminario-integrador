"""URL configuration for SGD-AVEIT core project."""

from django.contrib import admin
from django.urls import include, path

from core.views import HealthCheckView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", HealthCheckView.as_view(), name="health-check"),
    path("api/v1/auth/", include("accounts.urls")),
    path("api/v1/socios/", include("socios.urls")),
    path("api/v1/padron/", include("padron.urls")),
    path("api/v1/notifications/", include("notifications.urls")),
    path("api/v1/ranking/", include("ranking.urls", namespace="ranking-v1")),
    path("api/v1/ranking", include(("ranking.urls", "ranking"), namespace="ranking-v1-noslash")),
    path("api/ranking/", include("ranking.urls", namespace="ranking")),
    path("api/ranking", include(("ranking.urls", "ranking"), namespace="ranking-noslash")),
]
