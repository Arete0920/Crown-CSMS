from datetime import date

import pytest

from core.models import AcademicYear, Enrollment, Family, GradeLevel, School, Student
from enrollment_period_wizard.models import GradeCapacity
from market_intelligence.services import build_internal_school_context, validate_market_inputs
from survey_sentiment.models import SurveyAnswer, SurveyDefinition, SurveyQuestion, SurveyResponse
from survey_sentiment.services import STANDARD_TEMPLATES, survey_insights

pytestmark = pytest.mark.django_db


def _year(school):
    return AcademicYear.objects.create(
        school=school,
        name="2027-2028",
        start_date=date(2027, 8, 15),
        end_date=date(2028, 6, 5),
        is_current=True,
    )


def test_standard_survey_templates_cover_growth_and_retention():
    expected = {
        "inquiry",
        "post_tour",
        "new_family",
        "parent_pulse",
        "reenrollment_intent",
        "lost_prospect",
        "exit",
    }
    assert expected.issubset(STANDARD_TEMPLATES.keys())


def test_survey_insights_flag_retention_attention_for_low_intent_and_tuition_pressure():
    school = School.objects.create(name="Survey Insight School")
    survey = SurveyDefinition.objects.create(
        school=school,
        name="Parent Pulse",
        purpose="parent_pulse",
        status="active",
    )
    q1 = SurveyQuestion.objects.create(
        survey=survey,
        key="reenroll_likelihood",
        prompt="How likely are you to re-enroll?",
        question_type="scale",
        required=True,
        sort_order=1,
    )
    q2 = SurveyQuestion.objects.create(
        survey=survey,
        key="tuition_pressure",
        prompt="How much is tuition pressure affecting your decision?",
        question_type="scale",
        required=True,
        sort_order=2,
    )
    response = SurveyResponse.objects.create(school=school, survey=survey)
    SurveyAnswer.objects.create(response=response, question=q1, value_json={"value": 2})
    SurveyAnswer.objects.create(response=response, question=q2, value_json={"value": 5})

    insights = survey_insights(school_id=school.id, purpose="parent_pulse")

    assert insights["response_count"] == 1
    assert insights["scale_averages"]["reenroll_likelihood"] == 2.0
    assert insights["scale_averages"]["tuition_pressure"] == 5.0
    assert insights["retention_attention_recommended"] is True


def test_market_context_connects_capacity_enrollment_and_survey_intelligence():
    school = School.objects.create(name="Market Strategy School")
    year = _year(school)
    grade = GradeLevel.objects.create(school=school, code="6", label="Grade 6", sort_order=6)
    GradeCapacity.objects.create(
        school=school,
        academic_year=year,
        grade_code="6",
        target_seats=40,
        new_students_allowed=True,
    )
    family = Family.objects.create(school=school, family_name="Current Family")
    student = Student.objects.create(
        school=school,
        family=family,
        student_number="S-1",
        first_name="Avery",
        last_name="Student",
        dob=date(2015, 1, 1),
        status="ACTIVE",
        current_grade_level=grade,
    )
    Enrollment.objects.create(
        school=school,
        student=student,
        academic_year=year,
        grade_level=grade,
        start_date=year.start_date,
        status="ENROLLED",
    )

    survey = SurveyDefinition.objects.create(
        school=school,
        name="Re-enrollment Intent",
        purpose="reenrollment_intent",
        status="active",
    )
    question = SurveyQuestion.objects.create(
        survey=survey,
        key="intent",
        prompt="What is your current re-enrollment intention?",
        question_type="choice",
        required=True,
        sort_order=1,
    )
    response = SurveyResponse.objects.create(school=school, survey=survey)
    SurveyAnswer.objects.create(
        response=response,
        question=question,
        value_json={"value": "unsure"},
    )

    context = build_internal_school_context(school_id=school.id, academic_year=year)

    assert context["current_enrollment"] == 1
    assert context["grade_capacity"][0]["target_seats"] == 40
    assert context["grade_capacity"][0]["empty_seats"] == 39
    assert context["survey_intelligence"]["reenrollment_intent"]["response_count"] == 1


def test_market_study_requires_all_strategic_sections_before_commit():
    data = {
        "school_profile": {},
        "geography": {},
        "economics": {},
        "student_market": {},
        "competition": {},
        "faith_community": {},
        "enrollment_performance": {},
        "financial_profile": {},
        "program_capacity": {},
        "strategic_objectives": {},
    }
    assert validate_market_inputs(data) == []

    del data["financial_profile"]
    assert validate_market_inputs(data) == ["financial_profile"]
