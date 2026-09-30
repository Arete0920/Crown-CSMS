from __future__ import annotations

import json
from functools import wraps
from uuid import UUID

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from rest_framework.exceptions import APIException

from core.models import AcademicYear, School
from core.permissions import user_has_permission
from households.scoping import get_request_school_id
from spiritual_life.formation_models import PortraitDomain

from crm_marketing.models import CampaignTouchpoint, MarketingCampaign, MarketingLead
from crm_marketing.services import build_campaign_snapshot, record_touchpoint


def require_permission(code):
    def decorator(view):
        @wraps(view)
        def wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return JsonResponse({"detail": "Permission denied."}, status=403)
            try:
                school_id = get_request_school_id(request, required=True)
            except APIException as exc:
                return JsonResponse({"detail": str(exc.detail)}, status=exc.status_code)
            school = School.objects.filter(id=school_id).first()
            if school is None or not user_has_permission(request.user, code, school=school):
                return JsonResponse({"detail": "Permission denied."}, status=403)
            request.school = school
            return view(request, *args, **kwargs)
        return wrapped
    return decorator


def _json_body(request):
    try:
        return json.loads(request.body.decode("utf-8") or "{}")
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None


def _campaign_for_school(*, school_id, campaign_id):
    return MarketingCampaign.objects.filter(school_id=school_id, id=campaign_id).first()


def _integer(value, *, minimum=0, maximum=2**63 - 1):
    if isinstance(value, bool) or not isinstance(value, (int, str)):
        raise ValueError("Expected an integer")
    result = int(value)
    if not minimum <= result <= maximum:
        raise ValueError("Integer out of range")
    return result


@require_http_methods(["GET", "POST"])
@require_permission("marketing.view")
def campaign_collection(request):
    school_id = get_request_school_id(request, required=True)
    if request.method == "GET":
        campaigns = MarketingCampaign.objects.filter(school_id=school_id).select_related("academic_year")[:100]
        return JsonResponse({"results": [build_campaign_snapshot(campaign) for campaign in campaigns]})

    school = getattr(request, "school", None)
    if not user_has_permission(request.user, "marketing.edit", school=school):
        return JsonResponse({"detail": "Permission denied."}, status=403)
    payload = _json_body(request)
    if not isinstance(payload, dict):
        return JsonResponse({"detail": "Invalid JSON body."}, status=400)

    name = str(payload.get("name") or "").strip()
    if not name:
        return JsonResponse({"detail": "name is required."}, status=400)
    campaign_type = str(payload.get("campaign_type") or "general").strip()
    valid_types = {choice[0] for choice in MarketingCampaign.TYPE_CHOICES}
    if campaign_type not in valid_types:
        return JsonResponse({"detail": "Invalid campaign_type."}, status=400)

    academic_year = None
    academic_year_id = payload.get("academic_year_id")
    if academic_year_id:
        try:
            academic_year_id = UUID(str(academic_year_id))
        except ValueError:
            return JsonResponse({"detail": "academic_year_id must be a UUID."}, status=400)
        academic_year = AcademicYear.objects.filter(school_id=school_id, id=academic_year_id).first()
        if academic_year is None:
            return JsonResponse({"detail": "Academic year not found for school."}, status=400)

    portrait_ids = payload.get("portrait_domain_ids", [])
    if not isinstance(portrait_ids, list):
        return JsonResponse({"detail": "portrait_domain_ids must be a list of UUIDs."}, status=400)
    try:
        portrait_ids = [str(UUID(str(value))) for value in portrait_ids]
    except ValueError:
        return JsonResponse({"detail": "portrait_domain_ids must be a list of UUIDs."}, status=400)
    if portrait_ids:
        matched = set(str(value) for value in PortraitDomain.objects.filter(
            school_id=school_id, id__in=portrait_ids, is_active=True
        ).values_list("id", flat=True))
        if set(portrait_ids) != matched:
            return JsonResponse({"detail": "One or more Portrait domains are invalid for school."}, status=400)

    numeric_fields = {
        "enrollment_goal": 0,
        "budget_cents": 0,
        "actual_spend_cents": 0,
        "tuition_per_student_cents": 0,
        "minimum_net_tuition_cents": 0,
        "expected_retention_years": 1,
    }
    normalized = {}
    for field, default in numeric_fields.items():
        try:
            maximum = 32767 if field == "expected_retention_years" else 2**31 - 1 if field == "enrollment_goal" else 2**63 - 1
            normalized[field] = _integer(payload.get(field, default), minimum=1 if field == "expected_retention_years" else 0, maximum=maximum)
        except (TypeError, ValueError):
            return JsonResponse({"detail": f"{field} must be an integer within its supported range."}, status=400)

    target_segment = payload.get("target_segment", {})
    aid_strategy = payload.get("aid_strategy", {})
    if not isinstance(target_segment, dict) or not isinstance(aid_strategy, dict):
        return JsonResponse({"detail": "target_segment and aid_strategy must be objects."}, status=400)
    if "planned_aid_per_enrollment_cents" in aid_strategy:
        try:
            aid_strategy["planned_aid_per_enrollment_cents"] = _integer(aid_strategy["planned_aid_per_enrollment_cents"])
        except (TypeError, ValueError):
            return JsonResponse({"detail": "planned_aid_per_enrollment_cents must be a non-negative integer."}, status=400)

    campaign = MarketingCampaign.objects.create(
        school_id=school_id,
        academic_year=academic_year,
        name=name[:180],
        campaign_type=campaign_type,
        status="draft",
        target_grade_code=str(payload.get("target_grade_code") or "").strip()[:3],
        target_segment=target_segment,
        portrait_domain_ids=portrait_ids,
        aid_strategy=aid_strategy,
        created_by_user_id=getattr(request.user, "id", None),
        **normalized,
    )
    return JsonResponse(build_campaign_snapshot(campaign), status=201)


@require_http_methods(["GET"])
@require_permission("marketing.view")
def campaign_detail(request, campaign_id):
    school_id = get_request_school_id(request, required=True)
    campaign = _campaign_for_school(school_id=school_id, campaign_id=campaign_id)
    if campaign is None:
        return JsonResponse({"detail": "Campaign not found."}, status=404)
    return JsonResponse(build_campaign_snapshot(campaign))


@require_http_methods(["POST"])
@require_permission("marketing.edit")
def campaign_touchpoint(request, campaign_id):
    school_id = get_request_school_id(request, required=True)
    campaign = _campaign_for_school(school_id=school_id, campaign_id=campaign_id)
    if campaign is None:
        return JsonResponse({"detail": "Campaign not found."}, status=404)
    payload = _json_body(request)
    if not isinstance(payload, dict):
        return JsonResponse({"detail": "Invalid JSON body."}, status=400)
    lead_id = payload.get("lead_id")
    try:
        lead_id = UUID(str(lead_id))
    except ValueError:
        return JsonResponse({"detail": "lead_id must be a UUID."}, status=400)
    lead = MarketingLead.objects.filter(school_id=school_id, campaign=campaign, id=lead_id).first()
    if lead is None:
        return JsonResponse({"detail": "Lead not found for campaign."}, status=404)
    channel = str(payload.get("channel") or "").strip()
    valid_channels = {choice[0] for choice in CampaignTouchpoint.CHANNEL_CHOICES}
    if channel not in valid_channels:
        return JsonResponse({"detail": "Invalid channel."}, status=400)
    summary = str(payload.get("summary") or "").strip()
    if not summary:
        return JsonResponse({"detail": "summary is required."}, status=400)
    touchpoint = record_touchpoint(
        lead=lead,
        channel=channel,
        summary=summary,
        outcome=str(payload.get("outcome") or ""),
        metadata=payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {},
        created_by=request.user,
    )
    return JsonResponse({"touchpoint_id": str(touchpoint.id), "occurred_at": touchpoint.occurred_at.isoformat()}, status=201)
