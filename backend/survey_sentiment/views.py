from __future__ import annotations

import json
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from core.permissions import require_permission, user_has_permission
from households.scoping import get_request_school_id
from .models import SurveyAnswer, SurveyDefinition, SurveyQuestion, SurveyResponse
from .services import build_template_questions, survey_insights


def _body(request):
    try:
        return json.loads(request.body.decode("utf-8") or "{}")
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None


def _serialize(survey):
    return {
        "id": str(survey.id), "name": survey.name, "purpose": survey.purpose,
        "status": survey.status, "anonymous_allowed": survey.anonymous_allowed,
        "linked_campaign_id": str(survey.linked_campaign_id) if survey.linked_campaign_id else None,
        "grade_code": survey.grade_code,
        "questions": [
            {"id": str(q.id), "key": q.key, "prompt": q.prompt, "question_type": q.question_type,
             "choices": q.choices, "required": q.required, "strategic_tags": q.strategic_tags}
            for q in survey.questions.all()
        ],
    }


@require_http_methods(["GET", "POST"])
@require_permission("survey.view")
def survey_collection(request):
    school_id = get_request_school_id(request, required=True)
    if request.method == "GET":
        rows = SurveyDefinition.objects.filter(school_id=school_id).prefetch_related("questions")[:100]
        return JsonResponse({"results": [_serialize(row) for row in rows]})
    if not user_has_permission(request.user, "survey.edit", school=getattr(request, "school", None)):
        return JsonResponse({"detail": "Permission denied."}, status=403)
    payload = _body(request)
    if not isinstance(payload, dict):
        return JsonResponse({"detail": "Invalid JSON body."}, status=400)
    purpose = str(payload.get("purpose") or "").strip()
    if purpose not in {x[0] for x in SurveyDefinition.PURPOSE_CHOICES}:
        return JsonResponse({"detail": "Invalid purpose."}, status=400)
    name = str(payload.get("name") or "").strip()
    if not name:
        return JsonResponse({"detail": "name is required."}, status=400)
    survey = SurveyDefinition.objects.create(
        school_id=school_id, name=name[:180], purpose=purpose,
        anonymous_allowed=bool(payload.get("anonymous_allowed", False)),
        linked_campaign_id=payload.get("linked_campaign_id") or None,
        grade_code=str(payload.get("grade_code") or "")[:3],
        created_by_user_id=getattr(request.user, "id", None),
    )
    questions = payload.get("questions") if isinstance(payload.get("questions"), list) else build_template_questions(purpose)
    for order, row in enumerate(questions, start=1):
        SurveyQuestion.objects.create(
            survey=survey,
            key=str(row.get("key") or f"q{order}")[:64],
            prompt=str(row.get("prompt") or "")[:300],
            question_type=str(row.get("question_type") or "text"),
            choices=row.get("choices") if isinstance(row.get("choices"), list) else [],
            required=bool(row.get("required", False)),
            strategic_tags=row.get("strategic_tags") if isinstance(row.get("strategic_tags"), list) else [],
            sort_order=int(row.get("sort_order") or order),
        )
    return JsonResponse(_serialize(survey), status=201)


@require_http_methods(["GET"])
@require_permission("survey.view")
def survey_detail(request, survey_id):
    school_id = get_request_school_id(request, required=True)
    survey = SurveyDefinition.objects.filter(school_id=school_id, id=survey_id).prefetch_related("questions").first()
    if survey is None:
        return JsonResponse({"detail": "Survey not found."}, status=404)
    return JsonResponse(_serialize(survey))


@require_http_methods(["POST"])
@require_permission("survey.view")
def survey_response_submit(request, survey_id):
    school_id = get_request_school_id(request, required=True)
    survey = SurveyDefinition.objects.filter(school_id=school_id, id=survey_id, status="active").prefetch_related("questions").first()
    if survey is None:
        return JsonResponse({"detail": "Active survey not found."}, status=404)
    payload = _body(request)
    if not isinstance(payload, dict):
        return JsonResponse({"detail": "Invalid JSON body."}, status=400)
    anonymous = bool(payload.get("anonymous", False))
    if anonymous and not survey.anonymous_allowed:
        return JsonResponse({"detail": "Anonymous responses are not allowed for this survey."}, status=400)
    answers = payload.get("answers") if isinstance(payload.get("answers"), dict) else {}
    questions = {q.key: q for q in survey.questions.all()}
    missing = [q.key for q in questions.values() if q.required and q.key not in answers]
    if missing:
        return JsonResponse({"detail": "Required answers are missing.", "missing": missing}, status=400)
    response = SurveyResponse.objects.create(
        school_id=school_id, survey=survey, anonymous=anonymous,
        household_id=None if anonymous else payload.get("household_id"),
        application_id=None if anonymous else payload.get("application_id"),
        student_id=None if anonymous else payload.get("student_id"),
        campaign_id=survey.linked_campaign_id,
        metadata_json=payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {},
    )
    for key, raw in answers.items():
        question = questions.get(key)
        if question is not None:
            SurveyAnswer.objects.create(response=response, question=question, value_json={"value": raw})
    return JsonResponse({"response_id": str(response.id), "submitted_at": response.submitted_at.isoformat()}, status=201)


@require_http_methods(["GET"])
@require_permission("survey.view")
def survey_insights_view(request):
    school_id = get_request_school_id(request, required=True)
    purpose = request.GET.get("purpose") or None
    return JsonResponse(survey_insights(school_id=school_id, purpose=purpose))
