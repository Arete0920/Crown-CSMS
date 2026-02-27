"""
DRF authentication backend: validates Microsoft Entra ID Bearer tokens.

Register in settings.py REST_FRAMEWORK if you want MSAL-issued tokens
to authenticate directly against the API:

    "DEFAULT_AUTHENTICATION_CLASSES": [
        "core.auth.authentication.AADBearerAuthentication",
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
"""
from __future__ import annotations

import logging

from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from .aad_jwt import decode_and_validate_bearer, get_or_create_user_from_claims

logger = logging.getLogger(__name__)


class AADBearerAuthentication(BaseAuthentication):
    """
    Authenticates requests carrying a Microsoft-issued Bearer token.
    Silently returns None for tokens that don't look like Microsoft JWTs
    so other authenticators (SimpleJWT, Session) get a chance.
    """

    def authenticate(self, request):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return None

        token = auth_header.split(" ", 1)[1].strip()

        # Quick filter: Microsoft tokens are long RS256 JWTs.
        # Skip short / obviously non-Microsoft tokens to avoid redundant JWKS calls.
        if len(token) < 100:
            return None

        try:
            claims = decode_and_validate_bearer(token)
            user   = get_or_create_user_from_claims(claims)
            return (user, claims)
        except Exception as exc:
            logger.debug("AADBearerAuthentication: token rejected — %s", exc)
            # Raise only for tokens that appear to be Microsoft-issued
            if "matching JWKS" in str(exc) or "InvalidTokenError" in type(exc).__name__:
                raise AuthenticationFailed(f"Microsoft token invalid: {exc}")
            # Let other backends handle it
            return None
