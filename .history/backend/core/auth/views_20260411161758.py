"""
core/auth/views.py — AAD-backed identity endpoints.

These endpoints are secured via AADBearerAuthentication (JWKS-validated
Entra ID Bearer tokens) and live under /api/iam/ to avoid collision with
the legacy Crown JWT routes at /api/auth/me/.
"""
from __future__ import annotations

from django.http import JsonResponse
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request

from core.auth.authentication import AADBearerAuthentication


@extend_schema(tags=["IAM"], responses={200: OpenApiTypes.OBJECT})
@api_view(["GET"])
@authentication_classes([AADBearerAuthentication])
@permission_classes([IsAuthenticated])
def me(request: Request) -> JsonResponse:
    """
    GET /api/iam/me/

    Returns the AAD-authenticated identity for the Bearer token in the request.
    Mirrors the claims that were validated in the JWKS check.
    """
    user = request.user
    claims: dict = getattr(request, "aad_claims", {})

    return JsonResponse(
        {
            "id":         str(user.pk),
            "email":      getattr(user, "email", ""),
            "name":       getattr(user, "get_full_name", lambda: "")(),
            "username":   getattr(user, "username", ""),
            "aad_claims": {
                "oid":               claims.get("oid", ""),
                "tid":               claims.get("tid", ""),
                "preferred_username": claims.get("preferred_username", ""),
                "name":              claims.get("name", ""),
                "roles":             claims.get("roles", []),
                "scp":               claims.get("scp", ""),
            },
        }
    )


@extend_schema(tags=["IAM"], responses={200: OpenApiTypes.OBJECT})
@api_view(["GET"])
@authentication_classes([AADBearerAuthentication])
@permission_classes([IsAuthenticated])
def health_auth(request: Request) -> JsonResponse:
    """
    GET /api/iam/health-auth/

    Smoke-test endpoint for the AAD Bearer auth chain.
    Returns 200 only when the Bearer token is valid and the user resolves.
    Used by verify_m365_sso_and_outbox.ps1.
    """
    return JsonResponse(
        {
            "status":       "ok",
            "auth_backend": "AADBearerAuthentication",
            "user":         str(request.user),
        }
    )
