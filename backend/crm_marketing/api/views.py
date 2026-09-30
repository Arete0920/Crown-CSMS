from __future__ import annotations

import json

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from core.models import AcademicYear
from core.permissions import require_permission
from households.scoping import get_request_school_id
from spiritual_life.formation_models import PortraitDomain

from crm_marketing.models import CampaignTouchpoint, MarketingCampaign, MarketingLead
from crm_marketing.services import build_campaign_snapshot, record_touchpoint


def _json_body(request):
    try:
        return json.loads(request.body.decode("utf-8") or "{}")
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None


def _campaign_for_school(*, school_id, campaign_id):
    return MarketingCampaign.objects.filter(school_id=school_id, id=campaign_id).first()


@require_http_methods(["GET", "POST"])
@require_permission("marketing.view")
def campaign_collection(request):
    school_id = get_request_school_id(request, required=True)
    if request.method == "GET":
        campaigns = MarketingCampaign.objects.filter(school_id=school_id).select_related("academic_year")[:100]
        return JsonResponse({"results": [build_campaign_snapshot(campaign) for campaign in campaigns]})

    from core.permissions import user_has_permission
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
        academic_year = AcademicYear.objects.filter(school_id=school_id, id=academic_year_id).first()
        if academic_year is None:
            return JsonResponse({"detail": "Academic year not found for school."}, status=400)

    portrait_ids = [str(value) for value in (payload.get("portrait_domain_ids") or [])]
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
            normalized[field] = max(0, int(payload.get(field, default) or 0))
        except (TypeError, ValueError):
            return JsonResponse({"detail": f"{field} must be a non-negative integer."}, status=400)
    normalized["expected_retention_years"] = max(1, normalized["expected_retention_years"])

    campaign = MarketingCampaign.objects.create(
        school_id=school_id,
        academic_year=academic_year,
        name=name[:180],
        campaign_type=campaign_type,
        status="draft",
        target_grade_code=str(payload.get("target_grade_code") or "").strip()[:3],
        target_segment=payload.get("target_segment") if isinstance(payload.get("target_segment"), dict) else {},
        portrait_domain_ids=portrait_ids,
        aid_strategy=payload.get("aid_strategy") if isinstance(payload.get("aid_strategy"), dict) else {},
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
