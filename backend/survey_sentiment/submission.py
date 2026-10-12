"""School-scoped internal survey response persistence.

No endpoint calls this service yet. A future caller MUST separately enforce user
authorization, collection mode, consent, published instrument immutability,
public-token security, idempotency, and rate limits before enabling traffic.
"""
from django.db import transaction
import hashlib
import json
from types import SimpleNamespace

from .models import SurveyAnswer, SurveyDefinition, SurveyResponse, SurveyPublication
from .validation import validate_answers


class SurveyUnavailable(ValueError):
    """The survey is not eligible for this tenant and collection mode."""


@transaction.atomic
def submit_anonymous_response(*, school_id, survey_id, answers):
    """Persist only genuinely unlinked responses, scoped to a verified school.

    The caller's school_id must originate from CROWN's trusted tenant context,
    never from untrusted request JSON. No identifiers, arbitrary metadata, or
    linked campaign identifiers are copied from the respondent payload.
    """
    if school_id is None or survey_id is None:
        raise SurveyUnavailable("Survey is not available.")

    survey = (
        SurveyDefinition.objects.select_for_update()
        .filter(
            pk=survey_id,
            school_id=school_id,
            status="active",
            anonymous_allowed=True,
        )
        .first()
    )
    if survey is None:
        raise SurveyUnavailable("Survey is not available.")

    publication = (
        SurveyPublication.objects.filter(survey=survey)
        .order_by("-version")
        .first()
    )
    if publication is None or publication.collection_mode != "anonymous":
        raise SurveyUnavailable("Survey has no approved anonymous instrument version.")

    snapshot = publication.snapshot_json
    if not isinstance(snapshot, dict) or snapshot.get("survey_id") != str(survey.id) or snapshot.get("school_id") != str(survey.school_id) or snapshot.get("version") != publication.version:
        raise SurveyUnavailable("Survey publication provenance is invalid.")
    canonical = json.dumps(snapshot, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    if hashlib.sha256(canonical.encode("utf-8")).hexdigest() != publication.snapshot_sha256:
        raise SurveyUnavailable("Survey publication fingerprint is invalid.")
    rows = snapshot.get("questions")
    if not isinstance(rows, list) or not rows:
        raise SurveyUnavailable("Survey publication contains no approved questions.")
    questions = [SimpleNamespace(**row) for row in rows if isinstance(row, dict)]
    if len(questions) != len(rows):
        raise SurveyUnavailable("Survey publication questions are invalid.")
    normalized = validate_answers(questions, answers)
    existing = {q.key: q for q in survey.questions.all()}
    # Even optional/skipped answers must map to exactly the published question
    # set. Reject changes to prompts, choices, required flags or display order,
    # not only key and type. Direct ORM edits still require a separate guard.
    published = {row.key: row for row in questions}
    if len(existing) != len(questions) or set(existing) != set(published):
        raise SurveyUnavailable("Published question set has changed.")
    for key, row in published.items():
        original = existing[key]
        if (
            original.prompt != row.prompt
            or original.question_type != row.question_type
            or original.choices != row.choices
            or original.required != row.required
            or original.sort_order != row.sort_order
        ):
            raise SurveyUnavailable("Published question content has changed.")
    response = SurveyResponse.objects.create(
        school_id=survey.school_id,
        survey=survey,
        publication=publication,
        anonymous=True,
        household_id=None,
        application_id=None,
        student_id=None,
        campaign_id=None,
        metadata_json={},
    )
    lookup = existing
    SurveyAnswer.objects.bulk_create(
        [
            SurveyAnswer(
                response=response,
                question=lookup[key],
                value_json={"value": value},
            )
            for key, value in normalized.items()
        ]
    )
    return response
