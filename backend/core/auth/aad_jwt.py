"""
Microsoft Entra ID (Azure AD) JWT validation.

Validates Bearer tokens issued by Microsoft's /oauth2/v2.0/token endpoint.
JWKS are cached for 1 hour to avoid hammering the discovery endpoint.
"""
from __future__ import annotations

import json
import logging
import time

import requests
from django.conf import settings
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)

User = get_user_model()

_JWKS_CACHE: dict = {"ts": 0, "jwks": None}


def _get_jwks() -> dict:
    now = int(time.time())
    if _JWKS_CACHE["jwks"] and now - _JWKS_CACHE["ts"] < 3600:
        return _JWKS_CACHE["jwks"]

    tenant = getattr(settings, "AAD_TENANT_ID", "")
    if not tenant:
        raise ValueError("AAD_TENANT_ID is not configured")

    url = f"https://login.microsoftonline.com/{tenant}/discovery/v2.0/keys"
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    jwks = resp.json()
    _JWKS_CACHE.update({"ts": now, "jwks": jwks})
    return jwks


def decode_and_validate_bearer(token: str) -> dict:
    """
    Validate a Microsoft-issued JWT against the tenant's JWKS.
    Returns the decoded claims dict on success, raises jwt.InvalidTokenError on failure.
    """
    try:
        import jwt
        from jwt.algorithms import RSAAlgorithm
    except ImportError as exc:
        raise ImportError("PyJWT and cryptography must be installed: pip install pyjwt cryptography") from exc

    jwks = _get_jwks()
    unverified_header = jwt.get_unverified_header(token)

    key = None
    for k in jwks.get("keys", []):
        if k.get("kid") == unverified_header.get("kid"):
            key = RSAAlgorithm.from_jwk(json.dumps(k))
            break

    if not key:
        raise jwt.InvalidTokenError("No matching JWKS key for kid")

    audience = getattr(settings, "AAD_API_AUDIENCE", "")
    tenant   = getattr(settings, "AAD_TENANT_ID", "")
    issuer   = f"https://login.microsoftonline.com/{tenant}/v2.0"

    return jwt.decode(
        token,
        key=key,
        algorithms=["RS256"],
        audience=audience if audience else None,
        issuer=issuer,
        options={"verify_exp": True, "verify_aud": bool(audience)},
    )


def get_or_create_user_from_claims(claims: dict):
    """
    Map Entra claims → Django UserAccount.
    Role is taken from the first app role claim, defaulting to 'staff'.
    """
    email = (
        claims.get("preferred_username")
        or claims.get("upn")
        or claims.get("email")
    )
    if not email:
        raise ValueError("No email/username claim in Microsoft token")

    roles: list[str] = claims.get("roles") or []
    role = roles[0].lower() if roles else "staff"

    user, created = User.objects.get_or_create(
        email=email,
        defaults={
            "username": email,
            "role": role,
        },
    )

    if not created and roles and getattr(user, "role", None) != role:
        user.role = role
        user.save(update_fields=["role"])

    return user
