"""School-scoped internal survey response persistence.

No endpoint calls this service yet. A future caller MUST separately enforce user
authorization, collection mode, consent, published instrument immutability,
public-token security, idempotency, and rate limits before enabling traffic.
"""
from django.db import transaction

from .models import SurveyAnswer, SurveyDefinition, SurveyResponse
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

    questions = list(survey.questions.all())
    normalized = validate_answers(questions, answers)
    response = SurveyResponse.objects.create(
        school_id=survey.school_id,
        survey=survey,
        anonymous=True,
        household_id=None,
        application_id=None,
        student_id=None,
        campaign_id=None,
        metadata_json={},
    )
    lookup = {question.key: question for question in questions}
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
