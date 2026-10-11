"""Kingdom Path and Compass never consume respondent-level survey evidence."""
import pytest

from core.models import School
from survey_sentiment.consumers import strategic_survey_summary
from survey_sentiment.models import SurveyAnswer, SurveyDefinition, SurveyQuestion, SurveyResponse

pytestmark = pytest.mark.django_db


def make_survey(school, *, purpose="parent_pulse", count=10):
    survey = SurveyDefinition.objects.create(school=school, name="Original Research", purpose=purpose)
    question = SurveyQuestion.objects.create(
        survey=survey, key="communication", question_type="scale",
        prompt="How effective is communication?",
    )
    for _ in range(count):
        response = SurveyResponse.objects.create(school=school, survey=survey, anonymous=True)
        SurveyAnswer.objects.create(response=response, question=question, value_json={"value": 4})
    return survey


@pytest.mark.parametrize("consumer", ["kingdom_path", "crown_compass"])
def test_both_consumers_receive_only_aggregates(consumer):
    school = School.objects.create(name="Original Research School")
    survey = make_survey(school)
    value = strategic_survey_summary(school_id=school.pk, survey_id=survey.pk, consumer=consumer)
    assert value["source"] == "survey_intelligence"
    assert value["report"]["response_count"] == 10
    assert value["report"]["questions"][0]["distribution"] == {"4": 10}
    assert not any(key in str(value) for key in ("household_id", "student_id", "value_json", "response_id"))


def test_nonreportable_small_sample_stays_suppressed():
    school = School.objects.create(name="Small School")
    survey = make_survey(school, count=3)
    value = strategic_survey_summary(school_id=school.pk, survey_id=survey.pk, consumer="kingdom_path")
    assert value["report"]["suppressed"]
    assert value["report"]["response_count"] is None


def test_cross_school_id_never_receives_data():
    school = School.objects.create(name="School One")
    other = School.objects.create(name="School Two")
    survey = make_survey(school)
    assert strategic_survey_summary(school_id=other.pk, survey_id=survey.pk, consumer="kingdom_path") is None


def test_compass_does_not_receive_specific_reenrollment_survey():
    school = School.objects.create(name="School")
    survey = make_survey(school, purpose="reenrollment_intent")
    assert strategic_survey_summary(school_id=school.pk, survey_id=survey.pk, consumer="crown_compass") is None


def test_unknown_consumer_is_rejected():
    school = School.objects.create(name="School")
    survey = make_survey(school)
    with pytest.raises(ValueError):
        strategic_survey_summary(school_id=school.pk, survey_id=survey.pk, consumer="external")
