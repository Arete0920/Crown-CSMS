"""
Microsoft 365 OAuth2 views for Crown2026.

Flow:
  1. /auth/microsoft/login/      → redirect to Microsoft Entra ID
  2. /auth/microsoft/callback/   → exchange code → create session → redirect to /dash/<role>
  3. /auth/logout/               → clear session → redirect to /login
  4. /auth/me/                   → session probe for frontend auth guard

App is named `msauth` (not `auth`) to avoid shadowing django.contrib.auth.
URL prefix is still `auth/` so frontend paths match the spec.
"""
from __future__ import annotations

import json
import logging
import os
import secrets

from django.conf import settings
from django.contrib.auth import get_user_model, login, logout
from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import redirect
from django.views.decorators.csrf import csrf_exempt

from authlib.integrations.requests_client import OAuth2Session

logger = logging.getLogger(__name__)

User = get_user_model()

# ---------------------------------------------------------------------------
# Azure AD env-driven config
# ---------------------------------------------------------------------------
AZURE_CLIENT_ID     = os.getenv("AZURE_CLIENT_ID", "")
AZURE_CLIENT_SECRET = os.getenv("AZURE_CLIENT_SECRET", "")
AZURE_TENANT_ID     = os.getenv("AZURE_TENANT_ID", "")
AZURE_REDIRECT_URI  = os.getenv("AZURE_REDIRECT_URI", "")

_AUTHORITY    = f"https://login.microsoftonline.com/{AZURE_TENANT_ID}"
AUTHORIZE_URL = f"{_AUTHORITY}/oauth2/v2.0/authorize"
TOKEN_URL     = f"{_AUTHORITY}/oauth2/v2.0/token"
SCOPE         = "openid profile email User.Read GroupMember.Read.All"

_FRONTEND_BASE = getattr(settings, "FRONTEND_BASE_URL", "")

# JSON map: {"admin": "<group-id>", "teacher": "<group-id>", ...}
ROLE_GROUP_MAP: dict[str, str] = json.loads(os.getenv("AZURE_ROLE_GROUP_MAP", "{}"))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _frontend_url(path: str) -> str:
    return f"{_FRONTEND_BASE.rstrip('/')}{path}"


def _resolve_role_from_groups(group_ids: set[str]) -> str | None:
    """
    Walk ROLE_GROUP_MAP in definition order and return the first
    role whose Entra group ID appears in the user’s membership set.
    Returns None when no match is found.
    """
    for role, gid in ROLE_GROUP_MAP.items():
        if gid in group_ids:
            return role
    return None


# ---------------------------------------------------------------------------
# Views
# ---------------------------------------------------------------------------

def microsoft_login(request):
    """Initiate Microsoft OAuth2 flow."""
    if not AZURE_CLIENT_ID or not AZURE_TENANT_ID:
        logger.error("AZURE_CLIENT_ID / AZURE_TENANT_ID not configured")
        return JsonResponse({"error": "SSO not configured"}, status=503)

    state = secrets.token_urlsafe(32)
    request.session["oauth_state"] = state
    request.session.modified = True

    oauth = OAuth2Session(
        AZURE_CLIENT_ID,
        redirect_uri=AZURE_REDIRECT_URI,
        scope=SCOPE,
    )
    uri, _ = oauth.create_authorization_url(AUTHORIZE_URL, state=state)
    return redirect(uri)


@csrf_exempt   # Microsoft redirects back — CSRF token is not in the callback
def microsoft_callback(request):
    """
    Exchange authorization code for token, resolve group-based role,
    create Django session, redirect to /dash/<role>.
    """
    returned_state = request.GET.get("state", "")
    expected_state = request.session.get("oauth_state", "")

    if not expected_state or returned_state != expected_state:
        logger.warning("OAuth state mismatch (possible CSRF or session expiry)")
        return JsonResponse({"error": "Invalid state — please try logging in again"}, status=400)

    request.session.pop("oauth_state", None)

    # ---- Token exchange -------------------------------------------------
    try:
        oauth = OAuth2Session(
            AZURE_CLIENT_ID,
            AZURE_CLIENT_SECRET,
            redirect_uri=AZURE_REDIRECT_URI,
        )
        token = oauth.fetch_token(
            TOKEN_URL,
            authorization_response=request.build_absolute_uri(),
        )
    except Exception:
        logger.exception("OAuth token exchange failed")
        return JsonResponse({"error": "Authentication failed"}, status=502)

    # ---- Call Microsoft Graph -------------------------------------------
    try:
        graph = OAuth2Session(AZURE_CLIENT_ID, token=token)
        userinfo = graph.get("https://graph.microsoft.com/v1.0/me").json()
        groups_resp = graph.get(
            "https://graph.microsoft.com/v1.0/me/memberOf?$select=id"
        ).json()
    except Exception:
        logger.exception("Microsoft Graph call failed")
        return JsonResponse({"error": "Graph API error"}, status=502)

    # ---- Resolve email -------------------------------------------------
    email = userinfo.get("mail") or userinfo.get("userPrincipalName")
    if not email:
        logger.error("Microsoft profile returned no email: %s", list(userinfo.keys()))
        return JsonResponse({"error": "Email not found in Microsoft profile"}, status=400)

    # ---- Resolve group-based role --------------------------------------
    user_group_ids = {
        g["id"] for g in groups_resp.get("value", []) if "id" in g
    }
    resolved_role = _resolve_role_from_groups(user_group_ids)
    if not resolved_role:
        logger.warning(
            "SSO login blocked — no authorized role group: %s groups=%s",
            email, user_group_ids,
        )
        return JsonResponse({"error": "No authorized role group found"}, status=403)

    # ---- Lookup provisioned user ---------------------------------------
    try:
        user = User.objects.get(email__iexact=email)
    except User.DoesNotExist:
        logger.warning("SSO login blocked — email not provisioned: %s", email)
        return JsonResponse({"error": "User not provisioned in Crown2026"}, status=403)
    except Exception:
        logger.exception("DB error looking up user by email")
        return JsonResponse({"error": "Internal error"}, status=500)

    # ---- Sync role if Entra groups diverge from DB --------------------
    if getattr(user, "role", None) != resolved_role:
        try:
            user.role = resolved_role
            user.save(update_fields=["role"])
            logger.info("Role updated for %s: %s", email, resolved_role)
        except Exception:
            logger.exception("Failed to sync role for %s", email)

    # ---- Create session ------------------------------------------------
    user.backend = "django.contrib.auth.backends.ModelBackend"
    login(request, user)
    logger.info("SSO login: %s → /dash/%s", email, resolved_role)

    return HttpResponseRedirect(_frontend_url(f"/dash/{resolved_role}"))


def logout_view(request):
    """Clear server session and redirect to login."""
    logout(request)
    return redirect(_frontend_url("/login"))


def me_view(request):
    """
    Session probe for the frontend auth guard.
    Returns 401 when unauthenticated — no redirect.
    """
    if not getattr(request.user, "is_authenticated", False):
        return JsonResponse({"authenticated": False}, status=401)

    return JsonResponse({
        "authenticated": True,
        "email":     getattr(request.user, "email", ""),
        "role":      str(getattr(request.user, "role", "") or ""),
        "school_id": str(getattr(request.user, "school_id", "") or ""),
    })
