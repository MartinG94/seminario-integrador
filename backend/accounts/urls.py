from django.urls import path

from accounts.views import CurrentSocioTokenRefreshView, LoginView, MeView

app_name = "accounts"

urlpatterns = [
    path("login/", LoginView.as_view(), name="login"),
    path("refresh/", CurrentSocioTokenRefreshView.as_view(), name="refresh"),
    path("me/", MeView.as_view(), name="me"),
]
