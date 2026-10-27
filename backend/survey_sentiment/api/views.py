"""Authenticated, tenant-scoped school survey draft management.

This deliberately cannot publish questionnaires, distribute tokens, accept
responses, or reveal raw response/identity data.
"""
import json

from django.db import transaction
from django.http import JsonResponse
from drf_spectacular.utils import OpenApiTypes, extend_schema
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import APIException
from rest_framework.permissions import IsAuthenticated

from core.models import School
from core.permissions import user_has_permission
from households.scoping import get_request_school_id
from survey_sentiment.models import SurveyDefinition, SurveyQuestion
from survey_sentiment.validation import KEY_PATTERN, valid_choices, valid_storage_text
MAX_BODY_BYTES = 65536


def _authorize(request, permission_code):
    user = getattr(request, "user", None)
    if not user or not user.is_authenticated or not getattr(user, "is_active", True):
        return None, JsonResponse({"detail": "Permission denied."}, status=403)
    try:
        school_id = get_request_school_id(request, required=True)
    except APIException as exc:
        return None, JsonResponse({"detail": str(exc.detail)}, status=exc.status_code)
    school = School.objects.filter(pk=school_id, is_active=True).first()
    if school is None or not user_has_permission(user, permission_code, school=school):
        return None, JsonResponse({"detail": "Permission denied."}, status=403)
    return school, None


def _serialize(survey):
    return {
        "id": str(survey.pk), "name": survey.name, "purpose": survey.purpose,
        "status": survey.status, "audience": survey.audience,
        "questions": [
            {
                "key": q.key, "prompt": q.prompt,
                "question_type": q.question_type,
                "choices": q.choices, "required": q.required,
                "sort_order": q.sort_order,
            }
            for q in survey.questions.all()
        ],
    }


def _unique_json_object(pairs):
    # Draft APIs reject ambiguous JSON even in nested question definitions.
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON member.")
        result[key] = value
    return result


def _validated_draft_payload(request):
    if len(request.body) > MAX_BODY_BYTES:
        return None, {"body": "Survey request is too large."}
    try:
        payload = json.loads(
            request.body.decode("utf-8"), object_pairs_hook=_unique_json_object,
        )
    except (UnicodeError, json.JSONDecodeError, ValueError, RecursionError):
        return None, {"body": "Invalid JSON body."}
    if not isinstance(payload, dict) or set(payload) - {"name", "purpose", "questions"}:
        return None, {"body": "Only name, purpose and questions can be supplied."}
    name = payload.get("name")
    purpose = payload.get("purpose")
    questions = payload.get("questions")
    if not valid_storage_text(name) or not 1 <= len(name.strip()) <= 180:
        return None, {"name": "Enter a survey name of 1 to 180 characters."}
    if not isinstance(purpose, str) or purpose not in dict(SurveyDefinition.PURPOSE_CHOICES):
        return None, {"purpose": "Select a supported survey purpose."}
    if not isinstance(questions, list) or not 1 <= len(questions) <= 40:
        return None, {"questions": "Provide 1 to 40 questions."}

    validated = []
    used_keys = set()
    for index, row in enumerate(questions):
        field = f"questions[{index}]"
        if not isinstance(row, dict) or set(row) - {
            "key", "prompt", "question_type", "choices", "required",
        }:
            return None, {field: "Unsupported question definition."}
        key = row.get("key")
        prompt = row.get("prompt")
        kind = row.get("question_type")
        choices = row.get("choices", [])
        required = row.get("required", False)
        if not isinstance(key, str) or not KEY_PATTERN.fullmatch(key) or key in used_keys:
            return None, {field: "Question keys must be unique lowercase identifiers."}
        if not valid_storage_text(prompt) or not 1 <= len(prompt.strip()) <= 300:
            return None, {field: "Question text must have 1 to 300 characters."}
        if not isinstance(kind, str) or kind not in dict(SurveyQuestion.TYPE_CHOICES) or type(required) is not bool:
            return None, {field: "Unsupported question type or required flag."}
        if not isinstance(choices, list):
            return None, {field: "Choices must be an array."}
        if kind in {"choice", "multi"}:
            if not valid_choices(choices):
                return None, {field: "Provide 2 to 40 distinct choices."}
        elif choices:
            return None, {field: "Choices are not allowed for this question type."}
        used_keys.add(key)
        validated.append({
            "key": key, "prompt": prompt.strip(), "question_type": kind,
            "choices": choices, "required": required, "sort_order": index + 1,
        })
    return {"name": name.strip(), "purpose": purpose, "questions": validated}, None


@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def survey_drafts(request):
    school, error = _authorize(request, "survey.view" if request.method == "GET" else "survey.edit")
    if error is not None:
        return error

    if request.method == "GET":
        surveys = (
            SurveyDefinition.objects.filter(school=school)
            .prefetch_related("questions")[:100]
        )
        return JsonResponse({
            "results": [_serialize(survey) for survey in surveys],
            "can_create": user_has_permission(request.user, "survey.edit", school=school),
        })

    validated, errors = _validated_draft_payload(request)
    if errors:
        return JsonResponse({"detail": "Invalid survey draft.", "errors": errors}, status=400)

    with transaction.atomic():
        survey = SurveyDefinition.objects.create(
            school=school, name=validated["name"],
            purpose=validated["purpose"], status="draft",
            anonymous_allowed=False, public_enabled=False,
            created_by_user_id=request.user.pk,
        )
        SurveyQuestion.objects.bulk_create([
            SurveyQuestion(survey=survey, **row) for row in validated["questions"]
        ])
    survey = SurveyDefinition.objects.filter(pk=survey.pk).prefetch_related("questions").get()
    return JsonResponse(_serialize(survey), status=201)


@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def survey_draft_detail(request, survey_id):
    school, error = _authorize(request, "survey.view")
    if error is not None:
        return error
    survey = SurveyDefinition.objects.filter(pk=survey_id, school=school).prefetch_related("questions").first()
    if survey is None:
        return JsonResponse({"detail": "Survey not found."}, status=404)
    return JsonResponse(_serialize(survey))
