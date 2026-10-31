"""
Microsoft Entra ID (Azure AD) JWT validation.

Validates Bearer tokens issued by Microsoft's /oauth2/v2.0/token endpoint.
JWKS are cached for 1 hour to avoid hammering the discovery endpoint.
"""
from __future__ import annotations

import json
import logging
import time
import uuid

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

_JWKS_CACHE: dict = {"ts": 0, "jwks": None}


class MicrosoftIdentityError(ValueError):
    """A validated Microsoft token cannot be mapped to an authorized CROWN identity."""



def _get_jwks(tenant: str | None = None) -> dict:
    now = int(time.time())
    if _JWKS_CACHE["jwks"] and now - _JWKS_CACHE["ts"] < 3600:
        return _JWKS_CACHE["jwks"]

    normalized_tenant = str(
        tenant if tenant is not None else getattr(settings, "AAD_TENANT_ID", "")
    ).strip()
    if not normalized_tenant:
        raise ValueError("AAD_TENANT_ID is not configured")

    url = (
        "https://login.microsoftonline.com/"
        f"{normalized_tenant}/discovery/v2.0/keys"
    )
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    jwks = resp.json()
    _JWKS_CACHE.update({"ts": now, "jwks": jwks})
    return jwks


def decode_and_validate_bearer(token: str) -> dict:
    """Validate a Microsoft-issued JWT and require the configured API audience."""
    try:
        import jwt
        from jwt.algorithms import RSAAlgorithm
    except ImportError as exc:
        raise ImportError("PyJWT and cryptography must be installed: pip install pyjwt cryptography") from exc

    audience = str(getattr(settings, "AAD_API_AUDIENCE", "") or "").strip()
    if not audience:
        raise ValueError("AAD_API_AUDIENCE is not configured")

    tenant = str(getattr(settings, "AAD_TENANT_ID", "") or "").strip()
    if not tenant:
        raise ValueError("AAD_TENANT_ID is not configured")

    jwks = _get_jwks(tenant)
    unverified_header = jwt.get_unverified_header(token)

    key = None
    for candidate in jwks.get("keys", []):
        if candidate.get("kid") == unverified_header.get("kid"):
            key = RSAAlgorithm.from_jwk(json.dumps(candidate))
            break

    if not key:
        raise jwt.InvalidTokenError("No matching JWKS key for kid")

    issuer = f"https://login.microsoftonline.com/{tenant}/v2.0"

    claims = jwt.decode(
        token,
        key=key,
        algorithms=["RS256"],
        audience=audience,
        issuer=issuer,
        options={"verify_exp": True, "verify_aud": True},
    )
    token_tenant = str(claims.get("tid") or "").strip().lower()
    if token_tenant != tenant.lower():
        raise jwt.InvalidTokenError("Microsoft token tenant mismatch")
    return claims


def _require_uuid_claim(claims: dict, name: str) -> uuid.UUID:
    raw = str(claims.get(name) or "").strip()
    if not raw:
        raise MicrosoftIdentityError(f"Microsoft token missing required {name} claim")
    try:
        return uuid.UUID(raw)
    except (TypeError, ValueError) as exc:
        raise MicrosoftIdentityError(f"Microsoft token has invalid {name} claim") from exc


def get_user_from_claims(claims: dict):
    """Resolve a pre-provisioned CROWN user from immutable Entra tid + oid."""
    from integrations.models import MicrosoftIdentityLink

    tenant_id = _require_uuid_claim(claims, "tid")
    object_id = _require_uuid_claim(claims, "oid")

    links = list(
        MicrosoftIdentityLink.objects.filter(
            binding__tenant_id=tenant_id,
            binding__is_active=True,
            binding__school__is_active=True,
            object_id=object_id,
            is_active=True,
        )
        .select_related("binding", "binding__school", "user")
        .order_by("binding__school_id", "user_id")
    )
    if not links:
        raise MicrosoftIdentityError("Microsoft identity is not provisioned in CROWN")

    user_ids = {link.user_id for link in links}
    if len(user_ids) != 1:
        raise MicrosoftIdentityError("Microsoft identity binding is ambiguous across CROWN schools")

    user = links[0].user
    if not getattr(user, "is_active", False):
        raise MicrosoftIdentityError("Microsoft identity is linked to an inactive CROWN user")

    bound_school_ids = {link.binding.school_id for link in links}
    member_school_ids = set(
        user.roles.filter(school_id__in=bound_school_ids).values_list("school_id", flat=True)
    )
    direct_school_id = getattr(user, "school_id", None)
    if direct_school_id in bound_school_ids:
        member_school_ids.add(direct_school_id)
    if bound_school_ids.issubset(member_school_ids):
        return user

    raise MicrosoftIdentityError("Microsoft identity link has no active CROWN school membership")
