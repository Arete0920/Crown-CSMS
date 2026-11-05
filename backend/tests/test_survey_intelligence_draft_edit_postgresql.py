"""Real lock ordering for draft replacement against another editor/publication."""
from concurrent.futures import ThreadPoolExecutor
from threading import Event
from unittest.mock import patch

import pytest
from django.db import connection

from backend.tests.test_survey_collection_postgresql import parallel, wait_for_lock, worker
from backend.tests.test_survey_intelligence_draft_api import bearer_client, payload, request, school_client
from backend.tests.test_survey_intelligence_draft_edit import replace, required_tenant_header
from survey_sentiment.models import SurveyDefinition, SurveyPublication, SurveyQuestion
from survey_sentiment.publication import publish_anonymous_instrument

pytestmark = [
    pytest.mark.django_db(transaction=True),
    pytest.mark.skipif(connection.vendor != "postgresql", reason="PostgreSQL lock contract; required in survey-postgresql CI"),
]


def setup_draft(school_client):
    client, school, user = school_client
    created = request(client, school, payload())
    assert created.status_code == 201
    return school, user, created


def publish(school, user, created):
    return publish_anonymous_instrument(
        school_id=school.pk, survey_id=created.json()["id"], approved_by_user_id=user.pk,
        notice="Reviewed synthetic adult respondent notice for lock contract testing.",
    )


def test_two_editors_with_same_revision_accept_exactly_one(school_client):
    school, user, created = setup_draft(school_client)
    def save(name):
        return replace(bearer_client(user), school, created, dict(payload(), name=name), HTTP_IF_MATCH=created["ETag"]).status_code
    statuses = parallel(lambda: save("Editor one"), lambda: save("Editor two"))
    assert sorted(statuses) == [200, 412]
    assert SurveyDefinition.objects.get().name in {"Editor one", "Editor two"}
    assert SurveyQuestion.objects.count() == 1


@pytest.mark.parametrize("first", ["edit", "publish"])
def test_edit_and_publication_serialize_on_same_survey_lock(school_client, first):
    school, user, created = setup_draft(school_client)
    held, release, waiting = Event(), Event(), Event()
    waiting_pid = []
    replacement = dict(payload(), name="Edited before publication")
    replacement["questions"][0]["prompt"] = "Edited prompt?"

    def edit():
        return replace(bearer_client(user), school, created, replacement, HTTP_IF_MATCH=created["ETag"])

    def waiting_operation():
        with connection.cursor() as cursor:
            cursor.execute("SELECT pg_backend_pid()")
            waiting_pid.append(cursor.fetchone()[0])
        waiting.set()
        return publish(school, user, created) if first == "edit" else edit()

    manager = SurveyQuestion.objects if first == "edit" else SurveyPublication.objects
    method = "update_or_create" if first == "edit" else "create"
    original = getattr(manager, method)

    def pause_write(*args, **kwargs):
        held.set()
        assert release.wait(timeout=10)
        return original(*args, **kwargs)

    with patch.object(manager, method, side_effect=pause_write):
        with ThreadPoolExecutor(max_workers=2) as executor:
            leader = executor.submit(worker, edit if first == "edit" else lambda: publish(school, user, created))
            try:
                assert held.wait(timeout=10)
                follower = executor.submit(worker, waiting_operation)
                assert waiting.wait(timeout=10)
                wait_for_lock(waiting_pid[0])
            finally:
                release.set()
            leading_result = leader.result(timeout=25)
            following_result = follower.result(timeout=25)
    publication = SurveyPublication.objects.get()
    survey = SurveyDefinition.objects.get()
    assert survey.status == "active"
    if first == "edit":
        assert leading_result.status_code == 200
        assert publication.snapshot_json["questions"][0]["prompt"] == "Edited prompt?"
        assert survey.name == "Edited before publication"
    else:
        assert following_result.status_code == 409
        assert publication.snapshot_json["questions"][0]["prompt"] == payload()["questions"][0]["prompt"]
        assert survey.name == payload()["name"]
