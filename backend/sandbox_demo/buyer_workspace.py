"""Server-enforced invitation workspace identity for hosted CROWN evaluations.

This path never creates a school, principal, student, application, or
entitlement. Operational provisioning and buyer release are separate gates.
The legacy shared Heritage demo remains available in isolated local mode.
"""
from __future__ import annotations

import os
import re
from dataclasses import asdict, replace

from django.conf import settings
from django.utils import timezone

from core.models import UserAccount, UserRole
from crown_api.jwt_utils import build_access_token

from .catalog import SANDBOX_PERSONAS, SANDBOX_SCHOOLS
from .models import SandboxBuyerWorkspace

SHA_RE = re.compile(r"[0-9a-f]{40}\Z")


class BuyerWorkspaceDenied(Exception):
    """A stable non-sensitive denial, never an identity disclosure."""


def hosted_buyer_mode() -> bool:
    """Enforce binding in every hosted runtime, including a misconfigured DEV."""
    env = str(getattr(settings, "CROWN_ENV", "") or "").strip().lower()
    return bool(os.environ.get("WEBSITE_HOSTNAME")) or env in {
        "dev", "staging", "sandbox", "prod", "production", "live"
    }


def buyer_username(school_id, persona_key: str) -> str:
    """Deterministic reserved identity; distinct across invited schools."""
    if persona_key not in SANDBOX_PERSONAS:
        raise BuyerWorkspaceDenied("sandbox_buyer_role_invalid")
    return f"buyer.{school_id.hex}.{persona_key}@fictional.crown.invalid"


def hosted_buyer_session(invite, *, persona_key: str, guidance: str, tour: str | None):
    """Authenticate an already-provisioned, verified school-bound principal.

    No fallbacks to the shared Heritage school, username or demo seeders.
    No refresh token is issued. A new session requires a usable invite.
    """
    if invite is None or not invite.is_usable():
        raise BuyerWorkspaceDenied("sandbox_buyer_invite_required")
    try:
        workspace = SandboxBuyerWorkspace.objects.select_related("school").get(invite=invite)
    except SandboxBuyerWorkspace.DoesNotExist as exc:
        raise BuyerWorkspaceDenied("sandbox_buyer_workspace_unprovisioned") from exc

    school = workspace.school
    source = str(getattr(settings, "BUILD_SHA", "") or "").lower()
    if (
        not SHA_RE.fullmatch(source)
        or workspace.source_sha != source
        or not school.is_active
        or str(school.pk) == SANDBOX_SCHOOLS["heritage-core"].id
    ):
        raise BuyerWorkspaceDenied("sandbox_buyer_workspace_unverified")

    persona = SANDBOX_PERSONAS.get(persona_key)
    if persona is None:
        raise BuyerWorkspaceDenied("sandbox_buyer_role_invalid")
    username = buyer_username(school.id, persona_key)
    principal = UserAccount.objects.filter(
        school=school, username=username, email=username,
        is_active=True, is_staff=False, is_superuser=False,
    ).first()
    if (
        principal is None
        or not UserRole.objects.filter(
            school=school, user=principal, role_code=persona.role_code
        ).exists()
    ):
        raise BuyerWorkspaceDenied("sandbox_buyer_principal_unprovisioned")

    remaining = int((invite.expires_at - timezone.now()).total_seconds())
    ttl = min(
        900,
        int(getattr(settings, "CROWN_SANDBOX_ACCESS_TTL_SECONDS", 900)),
        remaining,
    )
    if ttl <= 0:
        raise BuyerWorkspaceDenied("sandbox_buyer_invite_expired")
    access = build_access_token(
        user_id=str(principal.id),
        email=principal.email,
        role=persona.key,
        school_id=str(school.id),
        ttl_seconds=ttl,
    )
    presented = replace(SANDBOX_SCHOOLS["heritage-core"], id=str(school.id))
    return {
        "access": access,
        "refresh": "",
        "school_id": str(school.id),
        "school_name": presented.name,
        "role": persona.key,
        "role_code": persona.role_code,
        "route": persona.route,
        "guidance": guidance,
        "tour": tour or persona.tour_title,
        "command_center": {
            "track": presented.track,
            "school": asdict(presented),
            "persona": asdict(replace(persona, email=principal.email)),
            "guidance": guidance,
            "tour": tour or persona.tour_title,
        },
    }, principal
