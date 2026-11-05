"""Draft replacement: optimistic revisions, immutable publication and scoped writes."""
import json
from unittest.mock import patch

import pytest
from django.db import IntegrityError
from django.test import override_settings
from rest_framework.test import APIClient

from backend.tests.test_survey_intelligence_draft_api import (
    bearer_client, payload, request, school_client,
)
from core.models import RolePermission, School, UserRole
from survey_sentiment.models import SurveyDefinition, SurveyQuestion, SurveyResponse
from survey_sentiment.publication import publish_anonymous_instrument

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def required_tenant_header(settings):
    # The global test fixture disables this boundary; exercise runtime behavior.
    settings.TENANT_HEADER_REQUIRED = True


def created_draft(school_client):
    client, school, user = school_client
    created = request(client, school, payload())
    assert created.status_code == 201
    return client, school, user, created


def replace(client, school, created, data=None, **headers):
    return client.put(
        f'/api/v1/survey-intelligence/surveys/{created.json()["id"]}/',
        data=json.dumps(payload() if data is None else data), content_type="application/json",
        HTTP_X_SCHOOL_ID=str(school.pk), **headers,
    )


def test_revision_is_consistent_across_create_list_detail(school_client):
    client, school, _, created = created_draft(school_client)
    detail = client.get(f'/api/v1/survey-intelligence/surveys/{created.json()["id"]}/', HTTP_X_SCHOOL_ID=str(school.pk))
    listed = client.get('/api/v1/survey-intelligence/surveys/', HTTP_X_SCHOOL_ID=str(school.pk))
    assert detail.json() == created.json() == listed.json()["results"][0]
    assert detail["ETag"] == created["ETag"] == f'"{detail.json()["revision"]}"'


def test_editor_replaces_questions_preserving_retained_identity_and_tags(school_client):
    client, school, user, created = created_draft(school_client)
    survey = SurveyDefinition.objects.get(pk=created.json()["id"])
    original = survey.questions.get()
    original.strategic_tags = ["server-owned"]
    original.save(update_fields=["strategic_tags"])
    removed = SurveyQuestion.objects.create(survey=survey, key="remove", prompt="Remove?", question_type="text")
    # Read after another server-side question write: old revisions cannot overwrite it.
    read = client.get(f'/api/v1/survey-intelligence/surveys/{survey.pk}/', HTTP_X_SCHOOL_ID=str(school.pk))
    changed = payload()
    changed.update(name="Updated questionnaire", purpose="custom")
    changed["questions"][0]["prompt"] = "Updated clarity?"
    changed["questions"].insert(0, {"key": "new", "prompt": "New?", "question_type": "boolean"})
    response = replace(bearer_client(user), school, created, changed, HTTP_IF_MATCH=read["ETag"])
    assert response.status_code == 200, response.content
    assert response["ETag"] != read["ETag"]
    survey.refresh_from_db()
    original.refresh_from_db()
    assert survey.name == changed["name"] and survey.purpose == "custom"
    assert original.prompt == "Updated clarity?" and original.strategic_tags == ["server-owned"]
    assert not SurveyQuestion.objects.filter(pk=removed.pk).exists()
    assert [q.key for q in survey.questions.all()] == ["new", "clarity"]
    assert survey.status == "draft" and not survey.public_enabled and not survey.anonymous_allowed
    assert replace(client, school, created, HTTP_IF_MATCH=read["ETag"]).status_code == 412


@pytest.mark.parametrize("revision,status", [(None, 428), ('*', 412), ('W/"stale"', 412), ('"stale"', 412)])
def test_missing_or_stale_revision_never_mutates(school_client, revision, status):
    client, school, _, created = created_draft(school_client)
    headers = {} if revision is None else {"HTTP_IF_MATCH": revision}
    assert replace(client, school, created, dict(payload(), name="Overwrite"), **headers).status_code == status
    assert SurveyDefinition.objects.get().name == payload()["name"]


def test_identical_save_still_invalidates_prior_revision(school_client):
    client, school, _, created = created_draft(school_client)
    response = replace(client, school, created, HTTP_IF_MATCH=created["ETag"])
    assert response.status_code == 200
    assert response["ETag"] != created["ETag"]
    assert replace(client, school, created, HTTP_IF_MATCH=created["ETag"]).status_code == 412


@pytest.mark.parametrize("state", ["active", "closed", "archived", "public", "anonymous", "published", "response"])
def test_non_draft_or_evidence_bearing_survey_is_immutable(school_client, state):
    client, school, user, created = created_draft(school_client)
    survey = SurveyDefinition.objects.get()
    if state == "published":
        pub = publish_anonymous_instrument(school_id=school.pk, survey_id=survey.pk, approved_by_user_id=user.pk, notice="Reviewed synthetic adult respondent notice for testing only.")
        SurveyDefinition.objects.filter(pk=survey.pk).update(status="draft", anonymous_allowed=False)
        before = pub.snapshot_json
    elif state == "response":
        SurveyResponse.objects.create(school=school, survey=survey)
    elif state in {"public", "anonymous"}:
        SurveyDefinition.objects.filter(pk=survey.pk).update(**{"public_enabled" if state == "public" else "anonymous_allowed": True})
    else:
        SurveyDefinition.objects.filter(pk=survey.pk).update(status=state)
    response = replace(client, school, created, dict(payload(), name="Forbidden edit"), HTTP_IF_MATCH=created["ETag"])
    assert response.status_code == 409
    assert SurveyDefinition.objects.get().name == payload()["name"]
    if state == "published":
        pub.refresh_from_db()
        assert pub.snapshot_json == before


@pytest.mark.parametrize("extra", [{"status": "active"}, {"school_id": "other"}, {"public_enabled": True}, {"questions": []}, {"name": ""}, {"questions": [{"key": "q", "prompt": "Q?", "question_type": "text", "strategic_tags": ["injected"]}]}])
def test_invalid_replacement_cannot_partially_update(school_client, extra):
    client, school, _, created = created_draft(school_client)
    response = replace(client, school, created, dict(payload(), **extra), HTTP_IF_MATCH=created["ETag"])
    assert response.status_code == 400
    assert SurveyDefinition.objects.get().name == payload()["name"]
    assert SurveyQuestion.objects.get().prompt == payload()["questions"][0]["prompt"]


def test_edit_requires_current_school_action_permission(school_client):
    client, school, user, created = created_draft(school_client)
    user.school = school
    user.save(update_fields=["school"])
    other = School.objects.create(name="Foreign draft school")
    UserRole.objects.create(user=user, school=other, role_code="survey_draft_editor_test")
    assert replace(bearer_client(user), other, created, HTTP_IF_MATCH=created["ETag"]).status_code == 404
    RolePermission.objects.filter(role_code="survey_draft_editor_test", permission__code="survey.edit").delete()
    assert replace(bearer_client(user), school, created, HTTP_IF_MATCH=created["ETag"]).status_code == 403
    assert SurveyDefinition.objects.get().name == payload()["name"]


def test_anonymous_and_cookie_session_csrf_cannot_edit(school_client):
    _, school, user, created = created_draft(school_client)
    anonymous = APIClient(enforce_csrf_checks=True)
    assert replace(anonymous, school, created, HTTP_IF_MATCH=created["ETag"]).status_code in (401, 403)
    anonymous.force_login(user)
    response = replace(anonymous, school, created, HTTP_IF_MATCH=created["ETag"])
    assert response.status_code == 403 and b"CSRF" in response.content


def test_question_write_failure_rolls_back_definition_and_deletions(school_client):
    client, school, _, created = created_draft(school_client)
    replacement = dict(payload(), name="Must roll back", questions=[{"key": "different", "prompt": "Replacement?", "question_type": "boolean"}])
    with patch.object(SurveyQuestion.objects, "update_or_create", side_effect=IntegrityError("synthetic storage failure")):
        response = replace(client, school, created, replacement, HTTP_IF_MATCH=created["ETag"])
    assert response.status_code == 500
    assert SurveyDefinition.objects.get().name == payload()["name"]
    assert SurveyQuestion.objects.get().key == "clarity"


@override_settings(CORS_ALLOWED_ORIGINS=["https://draft-editor.example.test"])
def test_browser_can_send_revision_and_read_etag(school_client):
    client, school, _, created = created_draft(school_client)
    path = f'/api/v1/survey-intelligence/surveys/{created.json()["id"]}/'
    preflight = client.options(path, HTTP_ORIGIN="https://draft-editor.example.test", HTTP_ACCESS_CONTROL_REQUEST_METHOD="PUT", HTTP_ACCESS_CONTROL_REQUEST_HEADERS="authorization,content-type,x-school-id,if-match")
    assert preflight.status_code == 200
    assert "if-match" in preflight["Access-Control-Allow-Headers"].lower()
    read = client.get(path, HTTP_ORIGIN="https://draft-editor.example.test", HTTP_X_SCHOOL_ID=str(school.pk))
    assert read.status_code == 200
    assert "etag" in read["Access-Control-Expose-Headers"].lower()
