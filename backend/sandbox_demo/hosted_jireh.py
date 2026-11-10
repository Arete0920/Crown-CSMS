"""Fail-closed authorization for separately reviewed hosted *fictional* Jireh APIs.

This is NOT the local Heritage intake gate. Neither a school role nor an SGO
membership alone authorizes partner access. Only explicit fictional bindings
to an active invite-owned workspace can expose canonical demo records.
"""
from __future__ import annotations

import os
import re
from uuid import UUID

from django.conf import settings
from django.db import connection
from django.db.models import F
from rest_framework.exceptions import NotFound, ValidationError

from core.models import Student, UserRole
from households.scoping import get_request_school_id
from jireh_sgo.models import SGOProgram
from .buyer_workspace import buyer_username
from .catalog import SANDBOX_PERSONAS, SANDBOX_SCHOOLS
from .models import (
    SandboxBuyerAidFamily, SandboxBuyerSGOProgram, SandboxBuyerWorkspace,
)

_SHA = re.compile(r"[a-f0-9]{40}\Z")
_DEV_HOST = "crown-api-dev.azurewebsites.net"
_SELECTOR_KEYS = frozenset(("school_id", "workspace_id", "invite_id", "family_id", "organization_id"))


def hosted_jireh_runtime() -> bool:
    """Opt-in, exact existing Azure DEV PostgreSQL deployment. Never local/prod."""
    return bool(
        getattr(settings, "CROWN_HOSTED_JIREH_DEMO_ENABLED", False)
        and getattr(settings, "CROWN_ENV", "") == "dev"
        and str(getattr(settings, "DJANGO_ENV", "") or "").lower() in ("", "dev", "development")
        and str(os.environ.get("AZURE_ENVIRONMENT", "") or "").lower() in ("", "dev")
        and os.environ.get("WEBSITE_HOSTNAME", "").strip().lower() == _DEV_HOST
        and settings.DEBUG is False
        and not getattr(settings, "CROWN_SANDBOX_ALLOW_OPEN_SESSION", True)
        and not getattr(settings, "CROWN_DEMO_MODE", False)
        and connection.vendor == "postgresql"
        and _SHA.fullmatch(str(getattr(settings, "BUILD_SHA", "") or "")) is not None
    )


def require_hosted_workspace(request, allowed_personas: tuple[str, ...]):
    """Authorize exact Django actor, invite, school, role and tenant context.

    A forged tenant header or a valid unrelated school/SGO role never suffices.
    The #625 request-time revocation guard provides an additional independent
    layer; this check remains fail-closed if middleware ordering ever changes.
    """
    if not hosted_jireh_runtime():
        raise NotFound("Not found.")
    user = request.user
    if (
        not getattr(user, "is_authenticated", False)
        or not getattr(user, "is_active", False)
        or getattr(user, "is_staff", False)
        or getattr(user, "is_superuser", False)
        or not getattr(user, "school_id", None)
    ):
        raise NotFound("Not found.")
    workspace = (
        SandboxBuyerWorkspace.objects.select_related("invite", "school")
        .filter(school_id=user.school_id, school__is_active=True)
        .first()
    )
    if (
        workspace is None
        or workspace.source_sha != settings.BUILD_SHA
        or str(workspace.school_id) == SANDBOX_SCHOOLS["heritage-core"].id
        or not workspace.invite.is_usable()
        or workspace.invite.track != "school"
        or workspace.invite.allowed_seed_packs != ["heritage-core"]
        or not isinstance(workspace.invite.allowed_roles, list)
    ):
        raise NotFound("Not found.")

    persona = next(
        (
            key for key in allowed_personas
            if key in SANDBOX_PERSONAS
            and user.username == buyer_username(workspace.school_id, key)
            and key in workspace.invite.allowed_roles
            and UserRole.objects.filter(
                school_id=workspace.school_id, user=user,
                role_code=SANDBOX_PERSONAS[key].role_code,
            ).exists()
        ),
        None,
    )
    if persona is None:
        raise NotFound("Not found.")
    if _SELECTOR_KEYS.intersection(request.query_params):
        raise ValidationError({"detail": "Untrusted buyer selector."})
    if get_request_school_id(request) != workspace.school_id:
        raise NotFound("Not found.")
    return workspace, persona


def demo_aid_family(workspace, user):
    record = (
        SandboxBuyerAidFamily.objects.select_related("family", "guardian")
        .filter(workspace=workspace, guardian_id=getattr(user, "guardian_id", None))
        .first()
    )
    if (
        record is None
        or str(record.family.school_id) != str(workspace.school_id)
        or record.family.status != "ACTIVE"
        or record.guardian.family_id != record.family_id
        or str(record.guardian.school_id) != str(workspace.school_id)
        or not record.guardian.portal_access
    ):
        raise NotFound("Not found.")
    return record.family


def demo_student_ids(workspace):
    return Student.objects.filter(
        school_id=workspace.school_id,
        family_id__in=SandboxBuyerAidFamily.objects.filter(
            workspace=workspace
        ).values("family_id"),
        status__in=("ACTIVE", "APPLICANT"),
    ).values_list("id", flat=True)


def demo_program(workspace, raw_id):
    try:
        program_id = UUID(str(raw_id))
    except (ValueError, TypeError, AttributeError) as exc:
        raise ValidationError({"program_id": "Opaque program UUID required."}) from exc
    program = (
        SGOProgram.objects.select_related("organization")
        .filter(
            pk=program_id,
            organization__active=True,
            sandbox_buyer_program__partner__workspace=workspace,
            sandbox_buyer_program__partner__organization_id=F("organization_id"),
        )
        .first()
    )
    if program is None:
        raise NotFound("Not found.")
    return program
