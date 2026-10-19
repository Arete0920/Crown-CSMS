"""
drf-spectacular schema extensions for Crown API custom authentication.

Auto-discovered when imported in crown_api/apps.py ready() method.
"""
from drf_spectacular.extensions import OpenApiAuthenticationExtension
from drf_spectacular.contrib.rest_framework_simplejwt import SimpleJWTScheme


class TenantJWTAuthenticationExtension(SimpleJWTScheme):
    """Keep the stock jwtAuth contract for the tenant-aware authenticator."""

    target_class = "crown_api.tenant_authentication.TenantJWTAuthentication"


class AADBearerAuthenticationExtension(OpenApiAuthenticationExtension):
    target_class = "core.auth.authentication.AADBearerAuthentication"
    name = "AADBearerAuthentication"

    def get_security_definition(self, auto_schema):
        return {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Azure Active Directory Bearer token (Microsoft Entra ID).",
        }
