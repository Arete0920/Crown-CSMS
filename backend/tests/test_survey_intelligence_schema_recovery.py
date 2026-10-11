"""Focused schema tests for the recovered, deliberately unexposed survey domain.

Historical generic health/keyword tests are NOT used as implementation proof.
"""
import uuid

import pytest
from django.db import IntegrityError, transaction

from core.models import School
from survey_sentiment.models import SurveyDefinition, SurveyQuestion, SurveyResponse, SurveyAnswer

pytestmark = pytest.mark.django_db


def test_survey_domain_persists_scoped_definition_question_response_and_answer():
    school = School.objects.create(name="Survey Foundation A")
    survey = SurveyDefinition.objects.create(school=school, name="Family Experience", purpose="parent_pulse")
    question = SurveyQuestion.objects.create(
        survey=survey, key="experience", prompt="How was your experience?",
        question_type="scale", required=True,
    )
    response = SurveyResponse.objects.create(school=school, survey=survey, anonymous=True)
    answer = SurveyAnswer.objects.create(response=response, question=question, value_json={"value": 4})
    assert survey.status == "draft"
    assert not survey.public_enabled
    assert not survey.anonymous_allowed
    assert response.school_id == school.id
    assert answer.question.survey_id == response.survey_id
    assert answer.value_json == {"value": 4}


def test_duplicate_question_keys_are_database_rejected():
    school = School.objects.create(name="Survey Foundation B")
    survey = SurveyDefinition.objects.create(school=school, name="Family Experience", purpose="parent_pulse")
    fields = {"survey": survey, "key": "experience", "prompt": "First?", "question_type": "choice"}
    SurveyQuestion.objects.create(**fields)
    with pytest.raises(IntegrityError), transaction.atomic():
        SurveyQuestion.objects.create(**fields)


def test_duplicate_answer_for_same_question_response_is_rejected():
    school = School.objects.create(name="Survey Foundation C")
    survey = SurveyDefinition.objects.create(school=school, name="Family Experience", purpose="parent_pulse")
    question = SurveyQuestion.objects.create(survey=survey, key="experience", prompt="Experience?", question_type="scale")
    response = SurveyResponse.objects.create(school=school, survey=survey, anonymous=True)
    SurveyAnswer.objects.create(response=response, question=question, value_json={"value": 3})
    with pytest.raises(IntegrityError), transaction.atomic():
        SurveyAnswer.objects.create(response=response, question=question, value_json={"value": 5})


def test_school_surveys_use_independent_public_tokens():
    school_a = School.objects.create(name="Survey Foundation D")
    school_b = School.objects.create(name="Survey Foundation E")
    a = SurveyDefinition.objects.create(school=school_a, name="A", purpose="custom")
    b = SurveyDefinition.objects.create(school=school_b, name="B", purpose="custom")
    assert isinstance(a.public_token, uuid.UUID)
    assert a.public_token != b.public_token
    assert not a.public_enabled and not b.public_enabled
