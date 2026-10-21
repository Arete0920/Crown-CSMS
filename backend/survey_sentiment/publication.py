"""Internal audited instrument publication boundary (not exposed to HTTP)."""
import hashlib
import json
from uuid import UUID

from django.db import transaction

from .models import SurveyDefinition, SurveyPublication
from .validation import validate_answers, SurveyAnswerValidationError, valid_storage_text


class PublicationRejected(ValueError):
    pass


@transaction.atomic
def publish_anonymous_instrument(*, school_id, survey_id, approved_by_user_id, notice):
    """Freeze a first version of a school-scoped, independently authored survey.

    Callers must separately prove the approving user's action permission and
    the school's consent/legal notice policy. This service does not distribute,
    invite, expose public tokens or provide a respondent route.
    """
    if not valid_storage_text(notice) or not 30 <= len(notice.strip()) <= 2000:
        raise PublicationRejected("A reviewed respondent notice is required.")
    if not isinstance(approved_by_user_id, UUID):
        raise PublicationRejected("A trusted approving user identifier is required.")
    survey = (
        SurveyDefinition.objects.select_for_update()
        .filter(pk=survey_id, school_id=school_id, status="draft")
        .first()
    )
    if survey is None or SurveyPublication.objects.filter(survey=survey).exists():
        raise PublicationRejected("Survey draft not eligible for first publication.")

    questions = list(survey.questions.all())
    try:
        # Reject structurally empty/duplicate question sets before publishing.
        validate_answers(questions, {q.key: (3 if q.question_type == "scale" else
            q.choices[0] if q.question_type == "choice" and q.choices else
            q.choices[:1] if q.question_type == "multi" and q.choices else
            True if q.question_type == "boolean" else "Prepublication check")
            for q in questions if q.required})
    except (SurveyAnswerValidationError, TypeError, KeyError) as exc:
        raise PublicationRejected("The instrument needs question validation.") from exc

    if not 1 <= len(questions) <= 40:
        raise PublicationRejected("A survey must contain 1 to 40 questions.")
    allowed = {"scale", "choice", "multi", "text", "boolean"}
    snapshot_questions = []
    for q in questions:
        if q.question_type not in allowed or not valid_storage_text(q.prompt) or not q.prompt.strip():
            raise PublicationRejected("Survey has unsupported questions.")
        if q.question_type in {"choice", "multi"} and not (
            isinstance(q.choices, list) and len(q.choices) >= 2
            and len(q.choices) == len(set(q.choices))
        ):
            raise PublicationRejected("Survey contains invalid choice options.")
        snapshot_questions.append({
            "key": q.key, "prompt": q.prompt,
            "question_type": q.question_type, "choices": q.choices,
            "required": q.required, "sort_order": q.sort_order,
        })

    snapshot = {
        "survey_id": str(survey.id), "school_id": str(survey.school_id),
        "purpose": survey.purpose, "version": 1,
        "collection_mode": "anonymous", "respondent_notice": notice.strip(),
        "questions": snapshot_questions,
    }
    canonical = json.dumps(snapshot, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    pub = SurveyPublication.objects.create(
        survey=survey, version=1, snapshot_json=snapshot,
        snapshot_sha256=hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
        respondent_notice=notice.strip(), collection_mode="anonymous",
        published_by_user_id=approved_by_user_id,
    )
    survey.status = "active"
    survey.anonymous_allowed = True
    survey.public_enabled = False
    survey.save(update_fields=["status", "anonymous_allowed", "public_enabled", "updated_at"])
    return pub
