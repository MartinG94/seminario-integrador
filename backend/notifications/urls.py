"""
Rutas para la API de notificaciones por correo.
"""

from django.urls import path

from notifications.views import RetryEmailQueueView, SendEmailView

app_name = "notifications"

urlpatterns = [
    path("email/", SendEmailView.as_view(), name="send-email"),
    path("email/retry/", RetryEmailQueueView.as_view(), name="retry-email-queue"),
]
