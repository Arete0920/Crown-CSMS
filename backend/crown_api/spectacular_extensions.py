"""
drf-spectacular schema extensions for Crown API custom authentication.

Registered when crown_api.__init__ imports this module during Django startup.
"""
from drf_spectacular.extensions import OpenApiAuthenticationExtension


class CrownAccessTokenAuthenticationExtension(OpenApiAuthenticationExtension):
    target_class = "crown_api.auth_middleware.CrownAccessTokenAuthentication"
    name = "CrownAccessTokenAuthentication"

    def get_security_definition(self, auto_schema):
        return {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "CROWN access token",
            "description": "Authenticated CROWN access token used by supported CROWN clients.",
        }


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
