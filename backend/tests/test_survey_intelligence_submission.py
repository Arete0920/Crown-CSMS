"""Transactional anonymous survey collection: real database and tenant-boundary tests."""
import pytest
from django.db import transaction

from core.models import School
from survey_sentiment.models import SurveyAnswer, SurveyDefinition, SurveyQuestion, SurveyResponse
from survey_sentiment.submission import SurveyUnavailable, submit_anonymous_response
from survey_sentiment.validation import SurveyAnswerValidationError

pytestmark = pytest.mark.django_db(transaction=True)


def make_survey(*, school, status="active", anonymous_allowed=True):
    survey = SurveyDefinition.objects.create(
        school=school, name="Independent Family Experience",
        purpose="parent_pulse", status=status,
        anonymous_allowed=anonymous_allowed,
    )
    SurveyQuestion.objects.create(
        survey=survey, key="satisfaction",
        question_type="scale", prompt="How satisfied are you?",
        required=True,
    )
    return survey


def test_anonymous_answer_written_with_no_identity_or_metadata():
    school = School.objects.create(name="Survey Tenant A")
    survey = make_survey(school=school)
    result = submit_anonymous_response(
        school_id=school.id, survey_id=survey.id,
        answers={"satisfaction": 4},
    )
    result.refresh_from_db()
    assert result.school_id == school.id
    assert result.anonymous is True
    assert result.household_id is None
    assert result.application_id is None
    assert result.student_id is None
    assert result.campaign_id is None
    assert result.metadata_json == {}
    assert list(SurveyAnswer.objects.filter(response=result).values_list("value_json", flat=True)) == [{"value": 4}]


def test_cross_school_survey_id_cannot_be_submitted():
    school_a = School.objects.create(name="Survey Tenant A")
    school_b = School.objects.create(name="Survey Tenant B")
    survey_b = make_survey(school=school_b)
    with pytest.raises(SurveyUnavailable):
        submit_anonymous_response(school_id=school_a.id, survey_id=survey_b.id, answers={"satisfaction": 4})
    assert SurveyResponse.objects.count() == 0


@pytest.mark.parametrize("status, anonymous", [
    ("draft", True), ("closed", True), ("archived", True), ("active", False),
])
def test_ineligible_collection_is_denied(status, anonymous):
    school = School.objects.create(name="Survey Tenant")
    survey = make_survey(school=school, status=status, anonymous_allowed=anonymous)
    with pytest.raises(SurveyUnavailable):
        submit_anonymous_response(school_id=school.id, survey_id=survey.id, answers={"satisfaction": 4})
    assert SurveyResponse.objects.count() == 0


def test_invalid_answers_do_not_leave_partial_writes():
    school = School.objects.create(name="Survey Tenant")
    survey = make_survey(school=school)
    with pytest.raises(SurveyAnswerValidationError):
        submit_anonymous_response(school_id=school.id, survey_id=survey.id, answers={"satisfaction": "4"})
    assert SurveyResponse.objects.count() == 0
    assert SurveyAnswer.objects.count() == 0


def test_unknown_answer_fields_fail_closed():
    school = School.objects.create(name="Survey Tenant")
    survey = make_survey(school=school)
    with pytest.raises(SurveyAnswerValidationError):
        submit_anonymous_response(
            school_id=school.id, survey_id=survey.id,
            answers={"satisfaction": 4, "student_id": "unsolicited"},
        )
    assert SurveyResponse.objects.count() == 0
