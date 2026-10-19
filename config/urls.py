"""
Root URL configuration.
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView
from rest_framework.permissions import AllowAny

from apps.accounts.swagger import NagorikFixSwaggerView


def health_check(_request):
    """Liveness check for local runs and Docker."""
    return JsonResponse({"status": "ok", "service": "nagorikfix-api"})


class PublicSchemaView(SpectacularAPIView):
    """OpenAPI schema stays public even when Swagger holds a JWT."""

    authentication_classes = []
    permission_classes = [AllowAny]


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", health_check, name="health-check"),
    path("api/schema/", PublicSchemaView.as_view(), name="schema"),
    path("api/docs/", NagorikFixSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    path("api/", include("apps.accounts.urls")),
    path("api/", include("apps.reports.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
