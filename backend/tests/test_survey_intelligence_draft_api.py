"""Survey draft routes: action permissions, tenant isolation and invalid-payload proof."""
import json

import pytest

from core.models import CrownPermission, RolePermission, School, UserAccount, UserRole
from survey_sentiment.models import SurveyDefinition, SurveyQuestion

pytestmark = pytest.mark.django_db


@pytest.fixture
def school_client(client):
    school = School.objects.create(name="Survey Draft School")
    user = UserAccount.objects.create_user(username="draft-admin", email="draft-admin@example.com")
    UserRole.objects.create(user=user, school=school, role_code="survey_draft_editor_test")
    for code in ("survey.view", "survey.edit"):
        perm, _ = CrownPermission.objects.get_or_create(code=code)
        RolePermission.objects.get_or_create(role_code="survey_draft_editor_test", permission=perm)
    client.force_login(user)
    return client, school, user


def request(client, school, data):
    return client.post(
        "/api/v1/survey-intelligence/surveys/",
        data=json.dumps(data), content_type="application/json",
        HTTP_X_SCHOOL_ID=str(school.pk),
    )


def payload():
    return {
        "name": "Parent Communication", "purpose": "parent_pulse",
        "questions": [
            {"key": "clarity", "prompt": "How clear were school updates?",
             "question_type": "scale", "required": True},
        ],
    }


def test_authorized_admin_can_create_and_read_scoped_draft(school_client):
    client, school, user = school_client
    created = request(client, school, payload())
    assert created.status_code == 201, created.content
    detail = created.json()
    assert detail["status"] == "draft"
    assert len(detail["questions"]) == 1
    survey = SurveyDefinition.objects.get(pk=detail["id"])
    assert survey.school_id == school.id
    assert not survey.public_enabled and not survey.anonymous_allowed
    listed = client.get("/api/v1/survey-intelligence/surveys/", HTTP_X_SCHOOL_ID=str(school.pk))
    assert listed.status_code == 200
    assert len(listed.json()["results"]) == 1
    read = client.get(f"/api/v1/survey-intelligence/surveys/{survey.pk}/", HTTP_X_SCHOOL_ID=str(school.pk))
    assert read.status_code == 200
    assert "public_token" not in read.json()


def test_other_school_cannot_read_draft(school_client):
    client, school, _ = school_client
    created = request(client, school, payload())
    survey_id = created.json()["id"]
    another = School.objects.create(name="Other Survey School")
    client.force_login(UserAccount.objects.create_user(username="outsider", email="outsider@example.com"))
    forbidden = client.get(f"/api/v1/survey-intelligence/surveys/{survey_id}/", HTTP_X_SCHOOL_ID=str(another.pk))
    assert forbidden.status_code in (403, 404)


def test_non_editor_cannot_create(school_client):
    client, school, user = school_client
    RolePermission.objects.filter(role_code="survey_draft_editor_test", permission__code="survey.edit").delete()
    forbidden = request(client, school, payload())
    assert forbidden.status_code == 403
    assert not SurveyDefinition.objects.exists()


def bearer_client(user):
    from rest_framework.test import APIClient
    from rest_framework_simplejwt.tokens import RefreshToken

    authenticated = APIClient(enforce_csrf_checks=True)
    authenticated.credentials(
        HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(user).access_token}"
    )
    return authenticated


def test_bearer_editor_can_create_list_and_read_an_inactive_draft(school_client):
    _, school, user = school_client
    authenticated = bearer_client(user)
    created = request(authenticated, school, payload())
    assert created.status_code == 201, created.content
    survey = SurveyDefinition.objects.get(pk=created.json()["id"])
    assert not survey.public_enabled and not survey.anonymous_allowed
    listed = authenticated.get("/api/v1/survey-intelligence/surveys/", HTTP_X_SCHOOL_ID=str(school.pk))
    assert listed.status_code == 200, listed.content
    assert [row["id"] for row in listed.json()["results"]] == [str(survey.pk)]
    detail = authenticated.get(f"/api/v1/survey-intelligence/surveys/{survey.pk}/", HTTP_X_SCHOOL_ID=str(school.pk))
    assert detail.status_code == 200, detail.content
    assert detail.json()["id"] == str(survey.pk)


def test_bearer_authority_stays_school_and_action_scoped(school_client):
    _, school, user = school_client
    authenticated = bearer_client(user)
    other = School.objects.create(name="Foreign Survey School")
    # Matching token identity is insufficient to authorize another school.
    foreign = request(authenticated, other, payload())
    assert foreign.status_code in (403, 404), foreign.content
    assert not SurveyDefinition.objects.exists()
    # Read authority cannot create drafts or enable public collection.
    RolePermission.objects.filter(role_code="survey_draft_editor_test", permission__code="survey.edit").delete()
    denied = request(authenticated, school, payload())
    assert denied.status_code == 403, denied.content
    assert not SurveyDefinition.objects.exists()
    listed = authenticated.get("/api/v1/survey-intelligence/surveys/", HTTP_X_SCHOOL_ID=str(school.pk))
    assert listed.status_code == 200, listed.content


def test_bearer_editor_cannot_create_for_inactive_school(school_client):
    _, school, user = school_client
    school.is_active = False
    school.save(update_fields=["is_active"])
    denied = request(bearer_client(user), school, payload())
    # Inactive tenants are deliberately indistinguishable from unknown tenants.
    # The shared school resolver denies them before the survey draft handler.
    assert denied.status_code == 404, denied.content
    assert not SurveyDefinition.objects.exists()


def test_session_editor_still_needs_csrf_for_draft_writes(school_client):
    from rest_framework.test import APIClient

    _, school, user = school_client
    session = APIClient(enforce_csrf_checks=True)
    session.force_login(user)
    denied = request(session, school, payload())
    assert denied.status_code == 403, denied.content
    assert b"CSRF" in denied.content
    assert not SurveyDefinition.objects.exists()


@pytest.mark.parametrize("patch", [
    {"name": ""}, {"purpose": "unsupported"},
    {"purpose": []}, {"purpose": {}},
    {"questions": [{"key": "q1", "prompt": "Q?", "question_type": []}]},
    {"questions": [{"key": "q1", "prompt": "Q?", "question_type": {}}]},
    {"questions": []}, {"status": "active"},
    {"public_enabled": True},
    {"questions": [{"key": "invalid!", "prompt": "Q?", "question_type": "scale"}]},
    {"questions": [{"key": "q1", "prompt": "Q?", "question_type": "choice", "choices": ["one"]}]},
    {"questions": [{"key": "q1", "prompt": "Q?", "question_type": "scale", "required": "true"}]},
])
def test_invalid_draft_does_not_create_any_rows(school_client, patch):
    client, school, _ = school_client
    data = payload()
    data.update(patch)
    response = request(client, school, data)
    assert response.status_code == 400, response.content
    assert not SurveyDefinition.objects.exists()
    assert not SurveyQuestion.objects.exists()


def test_unauthenticated_cannot_list_or_create(client):
    school = School.objects.create(name="Unprivileged")
    response = client.get("/api/v1/survey-intelligence/surveys/", HTTP_X_SCHOOL_ID=str(school.pk))
    assert response.status_code in (401, 403)
    assert request(client, school, payload()).status_code in (401, 403)


@pytest.mark.parametrize("duplicate_field", ["name", "key"])
def test_duplicate_json_members_fail_closed(school_client, duplicate_field):
    client, school, _ = school_client
    body = json.dumps(payload())
    if duplicate_field == "name":
        body = body.replace(
            '"name": "Parent Communication"',
            '"name": "Parent Communication", "name": "Ambiguous override"',
        )
    else:
        body = body.replace(
            '"key": "clarity"',
            '"key": "clarity", "key": "ambiguous_override"',
        )
    response = client.post(
        "/api/v1/survey-intelligence/surveys/",
        data=body,
        content_type="application/json",
        HTTP_X_SCHOOL_ID=str(school.pk),
    )
    assert response.status_code == 400, response.content
    assert not SurveyDefinition.objects.exists()
    assert not SurveyQuestion.objects.exists()

@pytest.mark.parametrize("bad_choice", [
    ["First", " first "], ["yes", "YES"], ["café", "cafe\u0301"],
    ["valid", "bad\x00value"], ["valid", "\ud800"],
])
def test_ambiguous_and_unsafe_draft_choices_denied(school_client, bad_choice):
    client, school, _ = school_client
    data = payload()
    data["questions"] = [{"key": "source", "prompt": "Source?", "question_type": "choice", "choices": bad_choice}]
    result = request(client, school, data)
    assert result.status_code == 400
    assert not SurveyDefinition.objects.exists()


def test_excessively_nested_json_returns_validation_error(school_client):
    client, school, _ = school_client
    body = '{"name":"Parent Communication","purpose":"parent_pulse","questions":' + "[" * 1500 + "0" + "]" * 1500 + "}"
    response = client.post(
        "/api/v1/survey-intelligence/surveys/",
        data=body, content_type="application/json",
        HTTP_X_SCHOOL_ID=str(school.pk),
    )
    assert response.status_code == 400
    assert not SurveyDefinition.objects.exists()
    assert not SurveyQuestion.objects.exists()
