from __future__ import annotations

from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from .catalog import SANDBOX_PERSONAS, catalog_payload, get_school
from .models import SandboxEvent, SandboxFeedback, SandboxInvite
from .services import create_sandbox_session, note_has_prohibited_data


DISALLOWED_EVENT_FIELDS = {
    "real_name",
    "student_name",
    "child_name",
    "camper_name",
    "family_name",
    "phone",
    "address",
    "payment_identifier",
    "health_detail",
    "safety_detail",
    "discipline_detail",
    "full_form_payload",
}


def _ops_allowed(request) -> bool:
    expected = getattr(settings, "CROWN_OPS_SECRET", "") or getattr(
        settings, "DEV_OPS_SECRET", ""
    )
    provided = request.headers.get("X-Crown-Ops-Secret", "")
    if expected and provided and provided == expected:
        return True
    user = getattr(request, "user", None)
    return bool(
        getattr(user, "is_staff", False) or getattr(user, "is_superuser", False)
    )


def _get_invite(invite_id: str | None):
    if not invite_id:
        return None
    return SandboxInvite.objects.filter(pk=invite_id).first()


def _invite_expiry_from_request(request):
    expires_at_raw = request.data.get("expires_at")
    if expires_at_raw:
        try:
            dt = timezone.datetime.fromisoformat(str(expires_at_raw).replace("Z", "+00:00"))
            if timezone.is_naive(dt):
                raise ValueError("expires_at must include timezone information")
            return dt, None
        except (TypeError, ValueError):
            return None, Response(
                {
                    "detail": "Invalid sandbox invite expiration timestamp.",
                    "code": "sandbox_invite_expires_at_invalid",
                },
                status=400,
            )

    raw_days = request.data.get("days")
    if raw_days in (None, ""):
        return None, Response(
            {
                "detail": "Invite duration in days is required.",
                "code": "sandbox_invite_days_invalid",
            },
            status=400,
        )

    try:
        days = int(raw_days)
    except (TypeError, ValueError):
        return None, Response(
            {
                "detail": "Invite duration in days must be a whole number.",
                "code": "sandbox_invite_days_invalid",
            },
            status=400,
        )

    if days < 1 or days > 30:
        return None, Response(
            {
                "detail": "Invite duration in days must be between 1 and 30.",
                "code": "sandbox_invite_days_invalid",
            },
            status=400,
        )

    return timezone.now() + timedelta(days=days), None


def _validate_invite(
    invite: SandboxInvite | None, *, role: str, school_key: str, track: str
):
    open_session_allowed = bool(
        getattr(settings, "CROWN_SANDBOX_ALLOW_OPEN_SESSION", False)
    )
    if invite is None:
        if open_session_allowed:
            return None
        return Response(
            {
                "detail": "Sandbox invite is required.",
                "code": "sandbox_invite_required",
            },
            status=403,
        )

    if not invite.is_usable():
        return Response(
            {
                "detail": "Sandbox invite is expired or revoked.",
                "code": "sandbox_invite_invalid",
            },
            status=403,
        )

    if invite.track and invite.track != track:
        return Response(
            {
                "detail": "Invite is not valid for this sandbox track.",
                "code": "sandbox_invite_track_mismatch",
            },
            status=403,
        )

    if invite.allowed_roles and role not in invite.allowed_roles:
        return Response(
            {
                "detail": "Invite does not allow this role.",
                "code": "sandbox_invite_role_not_allowed",
            },
            status=403,
        )

    if invite.allowed_seed_packs and school_key not in invite.allowed_seed_packs:
        return Response(
            {
                "detail": "Invite does not allow this demo school.",
                "code": "sandbox_invite_school_not_allowed",
            },
            status=403,
        )

    invite.mark_used()
    return None


class SandboxCatalogView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        return Response(catalog_payload())


class SandboxInviteCreateView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        if not _ops_allowed(request):
            return Response(
                {
                    "detail": "Ops secret or admin user required.",
                    "code": "sandbox_ops_required",
                },
                status=403,
            )

        expires_at, expires_error = _invite_expiry_from_request(request)
        if expires_error:
            return expires_error

        invite = SandboxInvite.objects.create(
            organization_label=request.data.get("organization_label")
            or "External evaluator",
            track=request.data.get("track") or "school",
            allowed_roles=request.data.get("allowed_roles")
            or list(SANDBOX_PERSONAS.keys()),
            allowed_seed_packs=request.data.get("allowed_seed_packs")
            or ["heritage-core"],
            default_guidance=request.data.get("default_guidance") or "guided",
            expires_at=expires_at,
            created_by=request.user
            if getattr(request.user, "is_authenticated", False)
            and hasattr(request.user, "pk")
            else None,
        )

        base_url = request.data.get("base_url") or request.build_absolute_uri(
            "/"
        ).rstrip("/")
        return Response(
            {
                "invite_id": invite.id,
                "url": f"{base_url}/sandbox?invite={invite.id}",
                "expires_at": invite.expires_at.isoformat(),
            },
            status=201,
        )


class SandboxInviteResolveView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, invite_id: str):
        invite = SandboxInvite.objects.filter(pk=invite_id).first()
        if not invite:
            return Response(
                {"detail": "Invite not found.", "code": "sandbox_invite_not_found"},
                status=404,
            )
        return Response(
            {
                "invite_id": invite.id,
                "organization_label": invite.organization_label,
                "track": invite.track,
                "allowed_roles": invite.allowed_roles,
                "allowed_seed_packs": invite.allowed_seed_packs,
                "default_guidance": invite.default_guidance,
                "expires_at": invite.expires_at.isoformat(),
                "revoked_at": invite.revoked_at.isoformat()
                if invite.revoked_at
                else None,
                "usable": invite.is_usable(),
            }
        )


class SandboxInviteRevokeView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, invite_id: str):
        if not _ops_allowed(request):
            return Response(
                {
                    "detail": "Ops secret or admin user required.",
                    "code": "sandbox_ops_required",
                },
                status=403,
            )
        invite = SandboxInvite.objects.filter(pk=invite_id).first()
        if not invite:
            return Response(
                {"detail": "Invite not found.", "code": "sandbox_invite_not_found"},
                status=404,
            )
        invite.revoked_at = timezone.now()
        invite.save(update_fields=["revoked_at"])
        return Response(
            {"invite_id": invite.id, "revoked_at": invite.revoked_at.isoformat()}
        )


class SandboxSessionView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        role = request.data.get("role") or "school_admin"
        requested_school_key = request.data.get("school") or "heritage-core"
        school = get_school(requested_school_key)
        school_key = school.key
        guidance = request.data.get("guidance") or "guided"
        track = request.data.get("track") or school.track
        tour = request.data.get("tour") or ""
        invite_id = request.data.get("invite_id") or request.query_params.get("invite")

        invite = _get_invite(invite_id)
        invite_error = _validate_invite(
            invite, role=role, school_key=school_key, track=track
        )
        if invite_error:
            return invite_error

        session = create_sandbox_session(
            persona_key=role,
            school_key_or_id=school_key,
            guidance=guidance,
            tour=tour,
        )

        SandboxEvent.objects.create(
            invite=invite,
            event="sandbox_session_created",
            track=track,
            guidance=guidance,
            persona=role,
            school=school_key,
            tour=session.get("tour", ""),
            route=session.get("route", ""),
        )

        return Response(session, status=201)


class SandboxEventView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        if DISALLOWED_EVENT_FIELDS.intersection(set(request.data.keys())):
            return Response(
                {
                    "detail": "Unsafe sandbox event payload.",
                    "code": "sandbox_event_payload_unsafe",
                },
                status=400,
            )

        invite = _get_invite(request.data.get("invite_id"))
        event = SandboxEvent.objects.create(
            invite=invite,
            event=request.data.get("event") or "sandbox_event",
            track=request.data.get("track") or "school",
            guidance=request.data.get("guidance") or "guided",
            persona=request.data.get("persona") or "",
            school=request.data.get("school") or "",
            tour=request.data.get("tour") or "",
            step=request.data.get("step"),
            route=request.data.get("route") or "",
        )
        return Response({"ok": True, "event_id": event.id}, status=201)


class SandboxFeedbackView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        note = request.data.get("note") or ""
        if note_has_prohibited_data(note):
            return Response(
                {
                    "detail": "Feedback appears to contain prohibited real-data patterns.",
                    "code": "sandbox_feedback_real_data_blocked",
                },
                status=400,
            )

        rating = request.data.get("rating") or "clear"
        if rating not in {"clear", "unclear", "not_relevant", "blocked"}:
            return Response(
                {
                    "detail": "Invalid rating.",
                    "code": "sandbox_feedback_invalid_rating",
                },
                status=400,
            )

        invite = _get_invite(request.data.get("invite_id"))
        feedback = SandboxFeedback.objects.create(
            invite=invite,
            track=request.data.get("track") or "school",
            guidance=request.data.get("guidance") or "guided",
            persona=request.data.get("persona") or "",
            school=request.data.get("school") or "",
            scenario=request.data.get("scenario") or "",
            step=request.data.get("step"),
            rating=rating,
            note=note[:2000],
            follow_up_requested=bool(request.data.get("follow_up_requested")),
        )
        return Response({"ok": True, "feedback_id": feedback.id}, status=201)
