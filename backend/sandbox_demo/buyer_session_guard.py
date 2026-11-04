"""Reject revoked or source-drifted hosted buyer sessions on EVERY request.

Runs after Django and CROWN JWT authentication but before tenant resolution.
Existing school users and the separate local Heritage demo are unaffected.
"""
from __future__ import annotations

import re

from django.conf import settings
from django.http import JsonResponse

from core.models import UserAccount, UserRole
from .catalog import SANDBOX_PERSONAS, SANDBOX_SCHOOLS
from .models import SandboxBuyerWorkspace

_RESERVED = re.compile(
    r"buyer\.([0-9a-f]{32})\.([a-z_]+)@fictional\.crown\.invalid\Z"
)


def _buyer_session_allowed(request, actor, match) -> bool:
    """Re-read authoritative records; never use a JWT school claim as authority."""
    from .buyer_workspace import hosted_buyer_mode

    if not hosted_buyer_mode():
        return False
    if (
        not isinstance(actor, UserAccount)
        or not actor.is_active
        or actor.is_staff
        or actor.is_superuser
    ):
        return False
    stored = UserAccount.objects.filter(pk=actor.pk).values(
        "school_id", "is_active", "is_staff", "is_superuser",
    ).first()
    if (
        stored is None or not stored["is_active"]
        or stored["is_staff"] or stored["is_superuser"]
        or stored["school_id"] is None
        or stored["school_id"].hex != match.group(1)
    ):
        return False

    persona_key = match.group(2)
    persona = SANDBOX_PERSONAS.get(persona_key)
    if persona is None:
        return False
    workspace = (
        SandboxBuyerWorkspace.objects
        .select_related("invite", "school")
        .filter(school_id=stored["school_id"])
        .first()
    )
    if (
        workspace is None
        or not workspace.invite.is_usable()
        or not workspace.school.is_active
        or str(workspace.school_id) == SANDBOX_SCHOOLS["heritage-core"].id
        or workspace.source_sha != getattr(settings, "BUILD_SHA", "")
        or workspace.invite.track != "school"
        or workspace.invite.allowed_seed_packs != ["heritage-core"]
        or persona_key not in workspace.invite.allowed_roles
        or not UserRole.objects.filter(
            user_id=actor.pk, school_id=workspace.school_id,
            role_code=persona.role_code,
        ).exists()
    ):
        return False

    # A CROWN JWT is verified upstream. Validate its subject, school and
    # specific persona once more against persisted grant and workspace.
    authenticated = getattr(request, "_crown_authenticated", None)
    if authenticated is not None:
        claims = authenticated[1]
        if (
            claims.get("typ") != "access"
            or str(claims.get("sub")) != str(actor.pk)
            or str(claims.get("school_id")) != str(workspace.school_id)
            or claims.get("role") != persona_key
        ):
            return False
    return True


class HostedBuyerSessionGuardMiddleware:
    """A previously issued session stops working immediately on revocation."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        actor = getattr(request, "user", None)
        if actor is None or not getattr(actor, "is_authenticated", False):
            return self.get_response(request)

        username = str(getattr(actor, "username", "") or "")
        if not username.startswith("buyer."):
            return self.get_response(request)

        match = _RESERVED.fullmatch(username)
        try:
            allowed = bool(match) and _buyer_session_allowed(request, actor, match)
        except Exception:
            # A missing/migrating schema must block synthetic buyers, never
            # allow them through to the canonical school and finance APIs.
            allowed = False
        if not allowed:
            return JsonResponse({
                "detail": "The buyer session is no longer authorized.",
                "code": "sandbox_buyer_session_invalid",
            }, status=403)
        return self.get_response(request)
