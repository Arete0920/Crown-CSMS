from __future__ import annotations

import json
from datetime import date
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from core.models import AcademicYear
from core.permissions import require_permission, user_has_permission
from households.scoping import get_request_school_id
from .models import MarketStudy, MarketStudyWizardSession
from .services import build_internal_school_context, build_market_study_snapshot, validate_market_inputs


def _body(request):
    try:
        return json.loads(request.body.decode("utf-8") or "{}")
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None


@require_http_methods(["GET"])
@require_permission("marketing.view")
def study_collection(request):
    school_id = get_request_school_id(request, required=True)
    studies = MarketStudy.objects.filter(school_id=school_id).prefetch_related("recommendations")[:50]
    return JsonResponse({"results": [build_market_study_snapshot(item) for item in studies]})


@require_http_methods(["GET"])
@require_permission("marketing.view")
def study_detail(request, study_id):
    school_id = get_request_school_id(request, required=True)
    study = MarketStudy.objects.filter(school_id=school_id, id=study_id).prefetch_related("recommendations").first()
    if study is None:
        return JsonResponse({"detail": "Study not found."}, status=404)
    return JsonResponse(build_market_study_snapshot(study))


@require_http_methods(["GET", "POST"])
@require_permission("marketing.view")
def wizard_collection(request):
    school_id = get_request_school_id(request, required=True)
    if request.method == "GET":
        rows = MarketStudyWizardSession.objects.filter(school_id=school_id)[:25]
        return JsonResponse({"results": [{"id": str(x.id), "status": x.status, "current_step": x.current_step, "updated_at": x.updated_at.isoformat()} for x in rows]})
    if not user_has_permission(request.user, "marketing.edit", school=getattr(request, "school", None)):
        return JsonResponse({"detail": "Permission denied."}, status=403)
    payload = _body(request)
    if not isinstance(payload, dict):
        return JsonResponse({"detail": "Invalid JSON body."}, status=400)
    session = MarketStudyWizardSession.objects.create(
        school_id=school_id,
        draft_data=payload.get("draft_data") if isinstance(payload.get("draft_data"), dict) else {},
        created_by_user_id=getattr(request.user, "id", None),
    )
    return JsonResponse({"id": str(session.id), "status": session.status, "current_step": session.current_step}, status=201)


@require_http_methods(["GET", "PATCH", "POST"])
@require_permission("marketing.view")
def wizard_detail(request, session_id):
    school_id = get_request_school_id(request, required=True)
    session = MarketStudyWizardSession.objects.filter(school_id=school_id, id=session_id).first()
    if session is None:
        return JsonResponse({"detail": "Wizard session not found."}, status=404)
    if request.method == "GET":
        return JsonResponse({"id": str(session.id), "status": session.status, "current_step": session.current_step, "draft_data": session.draft_data, "committed_study_id": str(session.committed_study_id) if session.committed_study_id else None})
    if not user_has_permission(request.user, "marketing.edit", school=getattr(request, "school", None)):
        return JsonResponse({"detail": "Permission denied."}, status=403)
    payload = _body(request)
    if not isinstance(payload, dict):
        return JsonResponse({"detail": "Invalid JSON body."}, status=400)
    if request.method == "PATCH":
        if isinstance(payload.get("draft_data"), dict):
            session.draft_data = {**(session.draft_data or {}), **payload["draft_data"]}
        if payload.get("current_step") is not None:
            session.current_step = max(1, min(10, int(payload["current_step"])))
        session.status = "configured" if session.current_step > 1 else session.status
        session.save(update_fields=["draft_data", "current_step", "status", "updated_at"])
        return JsonResponse({"id": str(session.id), "status": session.status, "current_step": session.current_step})

    data = session.draft_data or {}
    missing = validate_market_inputs(data)
    if missing:
        return JsonResponse({"detail": "Market study is incomplete.", "missing_sections": missing}, status=400)
    year_id = data.get("school_profile", {}).get("academic_year_id")
    academic_year = AcademicYear.objects.filter(school_id=school_id, id=year_id).first() if year_id else None
    internal_context = build_internal_school_context(school_id=school_id, academic_year=academic_year)
    study = MarketStudy.objects.create(
        school_id=school_id,
        name=str(data.get("school_profile", {}).get("study_name") or f"Strategic Market Study {date.today().year}")[:180],
        status="ready",
        analysis_year=int(data.get("school_profile", {}).get("analysis_year") or date.today().year),
        geography=data.get("geography", {}),
        population=data.get("student_market", {}),
        economics=data.get("economics", {}),
        education_market=data.get("enrollment_performance", {}),
        faith_community=data.get("faith_community", {}),
        competition=data.get("competition", {}),
        internal_context={**internal_context, "financial_profile": data.get("financial_profile", {}), "program_capacity": data.get("program_capacity", {})},
        strategic_objectives=data.get("strategic_objectives", {}),
        source_provenance=data.get("source_provenance") if isinstance(data.get("source_provenance"), list) else [],
        created_by_user_id=getattr(request.user, "id", None),
    )
    session.status = "committed"
    session.current_step = 10
    session.committed_study = study
    session.save(update_fields=["status", "current_step", "committed_study", "updated_at"])
    return JsonResponse(build_market_study_snapshot(study), status=201)
