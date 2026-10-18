from __future__ import annotations

import re
from datetime import timedelta
from uuid import UUID

from django.core.cache import cache
from django.db import transaction
from django.utils import timezone
from django.utils.crypto import salted_hmac
from django.utils.dateparse import parse_datetime
from drf_spectacular.utils import OpenApiTypes, extend_schema
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import APIException
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from core.models import School
from core.permissions import user_has_permission
from households.scoping import get_request_school_id
from crm_marketing.inquiry_services import (
    bounded_text, capture_inquiry, eligible_owners, lock_inquiry,
    mark_application_started, public_receipt,
)
from crm_marketing.models import CampaignTouchpoint, LeadStage, MarketingLead
from crm_marketing.services import record_touchpoint


ACTIVE_INQUIRY_STAGES = (LeadStage.INQUIRY, LeadStage.TOUR_SCHEDULED, LeadStage.APPLICATION_STARTED)


def _response(data, status=200):
    response = Response(data, status=status)
    response["Cache-Control"] = "no-store"
    return response


def _body(request):
    if len(request.body) > 16384:
        raise ValueError("Request body exceeds the inquiry limit.")
    if not isinstance(request.data, dict):
        raise ValueError("A JSON object is required.")
    return request.data


def _public_school(request, payload):
    header = request.headers.get("X-School-Id")
    supplied = payload.get("school_id")
    try:
        if header and supplied and UUID(header) != UUID(str(supplied)):
            return None
        school_id = UUID(str(header or supplied)) if header or supplied else None
    except (ValueError, TypeError, AttributeError):
        return None
    schools = School.objects.filter(is_active=True)
    if school_id:
        return schools.filter(id=school_id).first()
    campus = bounded_text(payload, "campus", 120, required=True)
    matches = list(schools.filter(name__iexact=campus)[:2])
    return matches[0] if len(matches) == 1 else None


def _staff_school(request, permission):
    if not request.user.is_authenticated:
        return None
    try:
        school_id = get_request_school_id(request, required=True)
    except APIException:
        return None
    school = School.objects.filter(id=school_id, is_active=True).first()
    return school if school and user_has_permission(request.user, permission, school=school) else None


def _throttle(request, school, *, email="", action="capture"):
    buckets = [(f"{action}:{school.id}:ip:{request.META.get('REMOTE_ADDR', '')}", 30, 900)]
    if email:
        buckets.append((f"{action}:{school.id}:email:{email.lower()}", 6, 3600))
    try:
        for value, limit, seconds in buckets:
            key = "inquiry-rate:" + salted_hmac("inquiry-rate", value, algorithm="sha256").hexdigest()
            if cache.add(key, 1, timeout=seconds):
                count = 1
            else:
                count = cache.incr(key)
            if count > limit:
                response = _response({"detail": "Please wait before trying again."}, 429)
                response["Retry-After"] = str(seconds)
                return response
    except Exception:
        return _response({"detail": "Inquiry protection is temporarily unavailable. Please retry."}, 503)
    return None


def _serialize(lead):
    from crm_marketing.inquiry_notifications import inquiry_notification_status
    data = {field: getattr(lead, field) for field in (
        "parent_name", "email", "phone", "grade_interest", "entry_year", "campus",
        "request_type", "contact_preference", "response_consent", "follow_up_consent",
        "family_follow_up_enabled", "stage", "first_source", "primary_source",
        "referral_type", "referral_detail",
    )}
    data.update({
        "id": str(lead.id), "utm": lead.attribution_json,
        "assigned_to_user_id": str(lead.assigned_to_user_id) if lead.assigned_to_user_id else None,
        "application_ids": [str(app.id) for app in lead.applications.filter(school_id=lead.school_id)],
        "notification_status": inquiry_notification_status(lead),
        "duplicate_candidates": list(MarketingLead.objects.filter(
            school_id=lead.school_id, email=lead.email, inquiry_received_at__isnull=False,
        ).exclude(id=lead.id).values("id", "parent_name", "email", "stage")[:5]),
        "touchpoints": list(lead.touchpoints.filter(school_id=lead.school_id).values("id", "channel", "summary", "outcome", "occurred_at")[:10]),
    })
    for field in ("next_follow_up_at", "last_touch_at", "created_at", "inquiry_received_at", "application_started_at", "consent_at"):
        value = getattr(lead, field)
        data[field] = value.isoformat() if value else None
    return data


@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(["GET", "POST"])
@permission_classes([AllowAny])
def inquiry_collection(request):
    if request.method == "GET":
        school = _staff_school(request, "admissions.view")
        if school is None:
            return _response({"detail": "Permission denied."}, 403)
        leads = MarketingLead.objects.filter(school=school, inquiry_received_at__isnull=False).prefetch_related("applications", "touchpoints")
        stage = request.query_params.get("stage")
        if stage and stage != "all":
            if stage not in LeadStage.values:
                return _response({"detail": "Invalid stage."}, 400)
            leads = leads.filter(stage=stage)
        elif stage != "all":
            leads = leads.filter(stage__in=ACTIVE_INQUIRY_STAGES, application__isnull=True)
        if request.query_params.get("unassigned") == "1":
            leads = leads.filter(assigned_to_user_id__isnull=True)
        if request.query_params.get("overdue") == "1":
            leads = leads.filter(next_follow_up_at__lte=timezone.now(), stage__in=ACTIVE_INQUIRY_STAGES, application__isnull=True)
        return _response({
            "results": [_serialize(lead) for lead in leads.order_by("next_follow_up_at", "created_at")[:100]],
            "count": leads.count(),
            "can_edit": user_has_permission(request.user, "admissions.edit", school=school),
            "owners": [{"id": str(user.id), "name": user.get_full_name() or user.username, "email": user.email} for user in eligible_owners(school)],
        })
    try:
        payload = _body(request)
        if payload.get("website"):
            return _response({"detail": "Unable to accept this inquiry."}, 400)
        request_key = request.headers.get("Idempotency-Key", "")
        if not re.fullmatch(r"[A-Za-z0-9_-]{16,128}", request_key):
            raise ValueError("A random Idempotency-Key of 16-128 characters is required.")
        school = _public_school(request, payload)
        if school is None:
            return _response({"detail": "School could not be resolved."}, 400)
        email = bounded_text(payload, "email", 254, required=True)
        limited = _throttle(request, school, email=email)
        if limited is not None:
            return limited
        lead, created = capture_inquiry(school=school, payload=payload, request_key=request_key)
    except ValueError as exc:
        return _response({"detail": str(exc)}, 400)
    return _response(public_receipt(lead, replayed=not created), 201 if created else 200)


@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(["POST"])
@permission_classes([AllowAny])
@transaction.atomic
def inquiry_start(request, inquiry_id):
    try:
        payload = _body(request)
        school = _public_school(request, payload)
    except ValueError:
        school = None
    if school is None:
        return _response({"detail": "Inquiry continuation is unavailable."}, 404)
    limited = _throttle(request, school, action="start")
    if limited is not None:
        return limited
    lead = lock_inquiry(school_id=school.id, inquiry_id=inquiry_id, token=payload.get("continuation_token"))
    if lead is None:
        return _response({"detail": "Inquiry continuation is unavailable."}, 404)
    mark_application_started(lead)
    return _response({"inquiry_id": str(lead.id), "school_id": str(school.id), "school_name": school.name, "stage": lead.stage, "expires_at": lead.continuation_expires_at.isoformat()})


@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
@transaction.atomic
def inquiry_update(request, inquiry_id):
    school = _staff_school(request, "admissions.edit")
    if school is None:
        return _response({"detail": "Permission denied."}, 403)
    lead = MarketingLead.objects.select_for_update().filter(id=inquiry_id, school=school, inquiry_received_at__isnull=False).first()
    if lead is None:
        return _response({"detail": "Inquiry not found."}, 404)
    try:
        payload = _body(request)
        allowed = {"assigned_to_user_id", "next_follow_up_at", "stage", "touchpoint", "family_follow_up_enabled", "follow_up_consent"}
        if not payload or set(payload) - allowed:
            raise ValueError("Provide supported inquiry update fields.")
        previous_owner = lead.assigned_to_user_id
        before = {key: str(getattr(lead, key)) for key in payload if key != "touchpoint"}
        if "assigned_to_user_id" in payload:
            value = payload["assigned_to_user_id"]
            owner_id = UUID(str(value)) if value is not None else None
            if owner_id and not eligible_owners(school).filter(id=owner_id).exists():
                raise ValueError("Owner must have admissions edit authority in this school.")
            lead.assigned_to_user_id = owner_id
        if "next_follow_up_at" in payload:
            value = payload["next_follow_up_at"]
            due = parse_datetime(value) if isinstance(value, str) else None
            if value is not None and (due is None or timezone.is_naive(due) or due > timezone.now() + timedelta(days=366)):
                raise ValueError("next_follow_up_at must be a timezone-aware date within one year, or null.")
            lead.next_follow_up_at = due
        if "stage" in payload:
            stage = payload["stage"]
            if stage not in {LeadStage.INQUIRY, LeadStage.TOUR_SCHEDULED, LeadStage.APPLICATION_STARTED, LeadStage.LOST} or lead.application_id:
                raise ValueError("Submitted application stages are controlled by admissions.")
            if stage == LeadStage.APPLICATION_STARTED:
                mark_application_started(lead)
            lead.stage = stage
        if "follow_up_consent" in payload:
            if payload["follow_up_consent"] is not False:
                raise ValueError("Staff may withdraw family reminder consent, but cannot grant it.")
            before["family_follow_up_enabled"] = str(lead.family_follow_up_enabled)
            lead.follow_up_consent = False
            lead.family_follow_up_enabled = False
        if "family_follow_up_enabled" in payload:
            enabled = payload["family_follow_up_enabled"]
            if not isinstance(enabled, bool) or (enabled and not lead.follow_up_consent):
                raise ValueError("Family follow-up requires the family's recorded permission.")
            lead.family_follow_up_enabled = enabled
        touch = payload.get("touchpoint")
        if touch is not None:
            if not isinstance(touch, dict) or touch.get("channel") not in {"email", "phone", "sms", "event", "tour", "referral", "church"}:
                raise ValueError("A valid contact channel is required.")
            summary = bounded_text(touch, "summary", 240, required=True)
            outcome = bounded_text(touch, "outcome", 120)
        lead.save()
        if touch is not None:
            record_touchpoint(lead=lead, channel=touch["channel"], summary=summary, outcome=outcome, created_by=request.user)
        CampaignTouchpoint.objects.create(
            school=school, campaign=lead.campaign, lead=lead, channel="system",
            summary="Admissions inquiry updated", outcome=lead.stage, occurred_at=timezone.now(),
            created_by_user_id=request.user.id,
            metadata_json={"before": before, "after": {key: str(getattr(lead, key)) for key in before}},
        )
        if previous_owner != lead.assigned_to_user_id:
            from crm_marketing.inquiry_notifications import queue_inquiry_notifications
            queue_inquiry_notifications(lead, event="owner_changed")
    except (ValueError, TypeError) as exc:
        transaction.set_rollback(True)
        return _response({"detail": str(exc)}, 400)
    return _response(_serialize(lead))
