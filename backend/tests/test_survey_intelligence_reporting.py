"""Conservative aggregate reporting tests using real survey records."""
import pytest

from core.models import School
from survey_sentiment.models import SurveyAnswer, SurveyDefinition, SurveyQuestion, SurveyResponse
from survey_sentiment.reporting import summarized_survey

pytestmark = pytest.mark.django_db


def survey(school):
    definition = SurveyDefinition.objects.create(
        school=school, name="Survey", purpose="parent_pulse", status="active",
    )
    question = SurveyQuestion.objects.create(
        survey=definition, key="score", question_type="scale",
        prompt="School communication satisfaction?",
    )
    return definition, question


def seed(school, definition, question, values):
    for value in values:
        response = SurveyResponse.objects.create(school=school, survey=definition, anonymous=True)
        SurveyAnswer.objects.create(
            response=response, question=question, value_json={"value": value},
        )


def test_no_school_or_cross_tenant_report_exists():
    school = School.objects.create(name="Survey A")
    other = School.objects.create(name="Survey B")
    definition, question = survey(school)
    seed(school, definition, question, [4] * 10)
    assert summarized_survey(school_id=other.id, survey_id=definition.id) is None


def test_small_sample_is_entirely_suppressed():
    school = School.objects.create(name="Survey A")
    definition, question = survey(school)
    seed(school, definition, question, [4] * 9)
    report = summarized_survey(school_id=school.id, survey_id=definition.id)
    assert report["response_count"] is None
    assert report["suppressed"] is True
    assert report["questions"] == []


def test_safe_distributions_require_at_least_five_in_each_used_bucket():
    school = School.objects.create(name="Survey A")
    definition, question = survey(school)
    seed(school, definition, question, [4] * 5 + [5] * 5)
    report = summarized_survey(school_id=school.id, survey_id=definition.id)
    assert not report["suppressed"]
    assert report["response_count"] == 10
    assert report["questions"][0]["distribution"] == {"4": 5, "5": 5}


def test_single_small_bucket_suppresses_entire_question():
    school = School.objects.create(name="Survey A")
    definition, question = survey(school)
    seed(school, definition, question, [4] * 9 + [5])
    report = summarized_survey(school_id=school.id, survey_id=definition.id)
    assert report["questions"][0]["distribution"] is None
    assert report["questions"][0]["answered_count"] is None
    assert report["questions"][0]["suppressed"] is True


def test_report_never_includes_text_comments_or_individual_answers():
    school = School.objects.create(name="Survey A")
    definition, q = survey(school)
    free_text = SurveyQuestion.objects.create(
        survey=definition, key="comments", question_type="text",
        prompt="What would you change?",
    )
    for _ in range(10):
        response = SurveyResponse.objects.create(school=school, survey=definition, anonymous=True)
        SurveyAnswer.objects.create(response=response, question=q, value_json={"value": 4})
        SurveyAnswer.objects.create(response=response, question=free_text, value_json={"value": "private feedback"})
    report = summarized_survey(school_id=school.id, survey_id=definition.id)
    assert "private feedback" not in str(report)
    assert not any(row["question_key"] == "comments" for row in report["questions"])
