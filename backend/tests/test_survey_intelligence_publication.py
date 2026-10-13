"""Publication approval evidence and first-party instrument freezing."""
from uuid import uuid4

import pytest

from core.models import School
from survey_sentiment.models import SurveyDefinition, SurveyQuestion, SurveyPublication
from survey_sentiment.publication import PublicationRejected, publish_anonymous_instrument

pytestmark = pytest.mark.django_db

NOTICE = "Responses are anonymous and will be reviewed only as authorized, aggregated school feedback."


def seed():
    school = School.objects.create(name="First-party Survey School")
    survey = SurveyDefinition.objects.create(
        school=school, name="Parent feedback", purpose="parent_pulse",
    )
    SurveyQuestion.objects.create(survey=survey, key="experience", prompt="How was your experience?",
                                  question_type="scale", required=True)
    return school, survey


def test_publication_freezes_version_and_leaves_public_access_disabled():
    school, survey = seed()
    approved_by = uuid4()
    publication = publish_anonymous_instrument(
        school_id=school.id, survey_id=survey.id,
        approved_by_user_id=approved_by, notice=NOTICE,
    )
    survey.refresh_from_db()
    assert survey.status == "active"
    assert survey.anonymous_allowed
    assert survey.public_enabled is False
    assert publication.version == 1
    assert publication.published_by_user_id == approved_by
    assert len(publication.snapshot_sha256) == 64
    assert publication.snapshot_json["questions"][0]["key"] == "experience"
    assert publication.snapshot_json["respondent_notice"] == NOTICE


def test_published_snapshot_remains_stable_when_original_questions_change():
    school, survey = seed()
    publication = publish_anonymous_instrument(
        school_id=school.id, survey_id=survey.id, approved_by_user_id=uuid4(), notice=NOTICE,
    )
    question = survey.questions.first()
    question.prompt = "Updated source draft text"
    question.save(update_fields=["prompt"])
    publication.refresh_from_db()
    assert publication.snapshot_json["questions"][0]["prompt"] == "How was your experience?"


def test_republication_is_denied():
    school, survey = seed()
    publish_anonymous_instrument(
        school_id=school.id, survey_id=survey.id, approved_by_user_id=uuid4(), notice=NOTICE,
    )
    with pytest.raises(PublicationRejected):
        publish_anonymous_instrument(
            school_id=school.id, survey_id=survey.id, approved_by_user_id=uuid4(), notice=NOTICE,
        )
    assert SurveyPublication.objects.filter(survey=survey).count() == 1


def test_cross_tenant_publication_is_denied():
    school, survey = seed()
    other = School.objects.create(name="Different School")
    with pytest.raises(PublicationRejected):
        publish_anonymous_instrument(
            school_id=other.id, survey_id=survey.id, approved_by_user_id=uuid4(), notice=NOTICE,
        )
    assert not SurveyPublication.objects.exists()


def test_short_notice_is_denied_without_state_transition():
    school, survey = seed()
    with pytest.raises(PublicationRejected):
        publish_anonymous_instrument(
            school_id=school.id, survey_id=survey.id, approved_by_user_id=uuid4(), notice="Too short",
        )
    survey.refresh_from_db()
    assert survey.status == "draft"
    assert not SurveyPublication.objects.exists()


@pytest.mark.parametrize("choices", [
    ["one", 2], [["one"], ["two"]], ["one", " "], ["one", "two", "one"],
])
def test_invalid_optional_choices_cannot_be_published(choices):
    school, survey = seed()
    SurveyQuestion.objects.create(
        survey=survey, key="optional", prompt="Optional source?",
        question_type="choice", required=False, choices=choices,
    )
    with pytest.raises(PublicationRejected):
        publish_anonymous_instrument(
            school_id=school.pk, survey_id=survey.pk, approved_by_user_id=uuid4(), notice=NOTICE,
        )
    survey.refresh_from_db()
    assert survey.status == "draft"
    assert not SurveyPublication.objects.filter(survey=survey).exists()
