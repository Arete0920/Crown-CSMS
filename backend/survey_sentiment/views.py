from __future__ import annotations

import json
import uuid
from datetime import timedelta

from django.core.cache import cache
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny

from core.permissions import require_permission, user_has_permission
from households.scoping import get_request_school_id
from .models import SurveyAnswer, SurveyDefinition, SurveyQuestion, SurveyResponse
from .services import build_template_questions, survey_insights


def _body(request):
    try:
        return json.loads(request.body.decode("utf-8") or "{}")
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None


PUBLIC_SURVEY_RATE_LIMIT = 20
PUBLIC_SURVEY_RATE_WINDOW_SECONDS = 60 * 60


def _public_client_key(request, public_token):
    remote = str(request.META.get("REMOTE_ADDR") or "unknown").strip() or "unknown"
    return f"public_survey:{public_token}:{remote}"


def _rate_limit_public_submission(request, public_token):
    key = _public_client_key(request, public_token)
    if cache.add(key, 1, timeout=PUBLIC_SURVEY_RATE_WINDOW_SECONDS):
        return False
    try:
        count = int(cache.incr(key))
    except ValueError:
        cache.set(key, 1, timeout=PUBLIC_SURVEY_RATE_WINDOW_SECONDS)
        return False
    return count > PUBLIC_SURVEY_RATE_LIMIT


def _validate_answers(questions, answers):
    errors = {}
    for question in questions.values():
        if question.required and question.key not in answers:
            errors[question.key] = "This response is required."
            continue
        if question.key not in answers:
            continue
        raw = answers[question.key]
        if question.question_type == "scale":
            try:
                value = float(raw)
            except (TypeError, ValueError):
                errors[question.key] = "A numeric rating is required."
                continue
            if value < 1 or value > 5:
                errors[question.key] = "Rating must be between 1 and 5."
        elif question.question_type == "choice":
            if raw not in (question.choices or []):
                errors[question.key] = "Select one of the available choices."
        elif question.question_type == "multi":
            if not isinstance(raw, list):
                errors[question.key] = "A list of choices is required."
            else:
                invalid = [item for item in raw if item not in (question.choices or [])]
                if invalid:
                    errors[question.key] = "One or more selected choices are invalid."
        elif question.question_type == "boolean":
            if not isinstance(raw, bool):
                errors[question.key] = "A yes/no response is required."
        elif question.question_type == "text":
            if not isinstance(raw, str):
                errors[question.key] = "A text response is required."
            elif len(raw) > 4000:
                errors[question.key] = "Response is too long."
    return errors


def _serialize(survey):
    return {
        "id": str(survey.id), "name": survey.name, "purpose": survey.purpose,
        "status": survey.status, "anonymous_allowed": survey.anonymous_allowed,
        "public_enabled": survey.public_enabled,
        "public_token": str(survey.public_token),
        "public_expires_at": survey.public_expires_at.isoformat() if survey.public_expires_at else None,
        "linked_campaign_id": str(survey.linked_campaign_id) if survey.linked_campaign_id else None,
        "grade_code": survey.grade_code,
        "questions": [
            {"id": str(q.id), "key": q.key, "prompt": q.prompt, "question_type": q.question_type,
             "choices": q.choices, "required": q.required, "strategic_tags": q.strategic_tags}
            for q in survey.questions.all()
        ],
    }


@require_http_methods(["GET", "POST"])
@require_permission("marketing.view")
def survey_collection(request):
    school_id = get_request_school_id(request, required=True)
    if request.method == "GET":
        rows = SurveyDefinition.objects.filter(school_id=school_id).prefetch_related("questions")[:100]
        return JsonResponse({"results": [_serialize(row) for row in rows]})
    if not user_has_permission(request.user, "marketing.edit", school=getattr(request, "school", None)):
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


@require_http_methods(["GET", "PATCH"])
@require_permission("marketing.view")
def survey_detail(request, survey_id):
    school_id = get_request_school_id(request, required=True)
    survey = SurveyDefinition.objects.filter(school_id=school_id, id=survey_id).prefetch_related("questions").first()
    if survey is None:
        return JsonResponse({"detail": "Survey not found."}, status=404)
    if request.method == "PATCH":
        if not user_has_permission(request.user, "marketing.edit", school=getattr(request, "school", None)):
            return JsonResponse({"detail": "Permission denied."}, status=403)
        payload = _body(request)
        if not isinstance(payload, dict):
            return JsonResponse({"detail": "Invalid JSON body."}, status=400)
        if payload.get("status") is not None:
            status = str(payload["status"])
            if status not in {x[0] for x in SurveyDefinition.STATUS_CHOICES}:
                return JsonResponse({"detail": "Invalid status."}, status=400)
            survey.status = status
        if payload.get("public_enabled") is not None:
            next_public_enabled = bool(payload["public_enabled"])
            if next_public_enabled and not survey.public_enabled:
                survey.public_token = uuid.uuid4()
                survey.public_expires_at = timezone.now() + timedelta(days=30)
            elif not next_public_enabled:
                survey.public_expires_at = None
            survey.public_enabled = next_public_enabled
        survey.save(update_fields=["status", "public_enabled", "public_token", "public_expires_at", "updated_at"])
    return JsonResponse(_serialize(survey))


@api_view(["GET", "POST"])
@permission_classes([AllowAny])
def public_survey(request, public_token):
    survey = SurveyDefinition.objects.filter(
        public_token=public_token,
        public_enabled=True,
        status="active",
        public_expires_at__gt=timezone.now(),
    ).prefetch_related("questions").first()
    if survey is None:
        return JsonResponse({"detail": "Survey not found."}, status=404)
    if request.method == "GET":
        data = _serialize(survey)
        data.pop("public_token", None)
        data.pop("linked_campaign_id", None)
        return JsonResponse(data)

    payload = _body(request)
    if not isinstance(payload, dict):
        return JsonResponse({"detail": "Invalid JSON body."}, status=400)
    if _rate_limit_public_submission(request, public_token):
        return JsonResponse({"detail": "Too many submissions. Please try again later."}, status=429)
    answers = payload.get("answers") if isinstance(payload.get("answers"), dict) else {}
    questions = {q.key: q for q in survey.questions.all()}
    errors = _validate_answers(questions, answers)
    if errors:
        return JsonResponse({"detail": "Survey response is invalid.", "errors": errors}, status=400)
    response = SurveyResponse.objects.create(
        school=survey.school,
        survey=survey,
        anonymous=True,
        campaign_id=survey.linked_campaign_id,
        metadata_json={"source": "public_token"},
    )
    for key, raw in answers.items():
        question = questions.get(key)
        if question is not None:
            SurveyAnswer.objects.create(response=response, question=question, value_json={"value": raw})
    return JsonResponse({"response_id": str(response.id), "submitted_at": response.submitted_at.isoformat()}, status=201)


@require_http_methods(["POST"])
@require_permission("marketing.view")
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
    errors = _validate_answers(questions, answers)
    if errors:
        return JsonResponse({"detail": "Survey response is invalid.", "errors": errors}, status=400)
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
@require_permission("marketing.view")
def survey_insights_view(request):
    school_id = get_request_school_id(request, required=True)
    purpose = request.GET.get("purpose") or None
    return JsonResponse(survey_insights(school_id=school_id, purpose=purpose))
