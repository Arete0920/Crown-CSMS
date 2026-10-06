"""
drf-spectacular schema extensions for Crown API custom authentication.

Auto-discovered when imported in crown_api/apps.py ready() method.
"""
from drf_spectacular.extensions import OpenApiAuthenticationExtension


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


class CrownAccessTokenAuthenticationExtension(OpenApiAuthenticationExtension):
    target_class = "crown_api.auth_middleware.CrownAccessTokenAuthentication"
    name = "CrownAccessTokenAuthentication"

    def get_security_definition(self, auto_schema):
        return {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "CROWN access bearer token.",
        }
