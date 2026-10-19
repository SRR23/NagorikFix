"""Swagger UI with optional DEBUG auto-auth."""
from django.conf import settings
from django.urls import reverse
from drf_spectacular.utils import extend_schema
from drf_spectacular.views import SpectacularSwaggerView


@extend_schema(exclude=True)
class NagorikFixSwaggerView(SpectacularSwaggerView):
    """Inject DEBUG auto-auth URL into Swagger template context."""

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        if settings.DEBUG:
            response.data["debug_swagger_auto_auth"] = True
            response.data["swagger_dev_token_url"] = reverse(
                "accounts:swagger-dev-token"
            )
        else:
            response.data["debug_swagger_auto_auth"] = False
            response.data["swagger_dev_token_url"] = ""
        return response
