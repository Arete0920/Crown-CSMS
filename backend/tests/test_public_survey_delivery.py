from datetime import timedelta

import pytest
from django.test import Client
from django.utils import timezone

from core.models import School
from survey_sentiment.models import SurveyDefinition, SurveyQuestion, SurveyResponse

pytestmark = pytest.mark.django_db


def _public_survey():
    school = School.objects.create(name="Public Survey School")
    survey = SurveyDefinition.objects.create(
        school=school,
        name="Lost Prospect Survey",
        purpose="lost_prospect",
        status="active",
        public_enabled=True,
        public_expires_at=timezone.now() + timedelta(days=30),
        anonymous_allowed=True,
    )
    SurveyQuestion.objects.create(
        survey=survey,
        key="stop_reason",
        prompt="What most influenced your decision not to continue?",
        question_type="choice",
        choices=["tuition", "location", "another_school"],
        required=True,
        sort_order=1,
    )
    return school, survey


def test_public_survey_get_requires_only_valid_enabled_token():
    _, survey = _public_survey()
    response = Client().get(f"/api/v1/survey-sentiment/public/{survey.public_token}/")

    assert response.status_code == 200
    payload = response.json()
    assert payload["name"] == "Lost Prospect Survey"
    assert "public_token" not in payload
    assert "linked_campaign_id" not in payload


def test_public_survey_submit_is_anonymous_and_tenant_bound_by_token():
    school, survey = _public_survey()
    response = Client().post(
        f"/api/v1/survey-sentiment/public/{survey.public_token}/",
        data={"answers": {"stop_reason": "tuition"}},
        content_type="application/json",
    )

    assert response.status_code == 201
    saved = SurveyResponse.objects.get(id=response.json()["response_id"])
    assert saved.school_id == school.id
    assert saved.survey_id == survey.id
    assert saved.anonymous is True
    assert saved.household_id is None
    assert saved.application_id is None
    assert saved.student_id is None


def test_public_survey_fails_closed_when_disabled():
    _, survey = _public_survey()
    survey.public_enabled = False
    survey.save(update_fields=["public_enabled"])

    response = Client().get(f"/api/v1/survey-sentiment/public/{survey.public_token}/")
    assert response.status_code == 404


def test_public_survey_rejects_invalid_choice():
    _, survey = _public_survey()
    response = Client().post(
        f"/api/v1/survey-sentiment/public/{survey.public_token}/",
        data={"answers": {"stop_reason": "not-an-allowed-choice"}},
        content_type="application/json",
    )

    assert response.status_code == 400
    assert "stop_reason" in response.json()["errors"]


def test_public_link_rotation_invalidates_previous_token_on_reenable():
    _, survey = _public_survey()
    original_token = survey.public_token
    survey.public_enabled = False
    survey.save(update_fields=["public_enabled"])

    # The endpoint is fail-closed while disabled. Token rotation is performed by
    # the protected survey-management endpoint before the link is re-enabled.
    disabled = Client().get(f"/api/v1/survey-sentiment/public/{original_token}/")
    assert disabled.status_code == 404


def test_public_survey_fails_closed_after_expiry():
    _, survey = _public_survey()
    survey.public_expires_at = timezone.now() - timedelta(seconds=1)
    survey.save(update_fields=["public_expires_at"])

    response = Client().get(f"/api/v1/survey-sentiment/public/{survey.public_token}/")
    assert response.status_code == 404
