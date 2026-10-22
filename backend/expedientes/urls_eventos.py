"""Rutas directas para /api/v1/eventos/ mapeadas a EventoInstitucionalViewSet."""

from rest_framework.routers import DefaultRouter

from expedientes.views import EventoInstitucionalViewSet

router = DefaultRouter()
router.register(r"", EventoInstitucionalViewSet, basename="evento-direct")

urlpatterns = router.urls
