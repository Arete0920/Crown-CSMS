"""Internal respondent authority, replay, privacy and concurrency contracts."""
import json
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from unittest.mock import patch

import pytest
from django.db import DatabaseError, close_old_connections
from django.utils import timezone

from core.models import CrownPermission, RolePermission, School, UserAccount, UserRole
from survey_sentiment.collection import CollectionRejected, collect_response, issue_respondent_grant, revoke_respondent_grant, MAX_ATTEMPTS
from survey_sentiment.models import SurveyCollectionReceipt, SurveyRespondentGrant, SurveyResponse, SurveyPublication
from backend.tests.test_survey_intelligence_submission import make_survey

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.fixture
def collection():
    school = School.objects.create(name="Collection School")
    user = UserAccount.objects.create_user(username="collector", email="collector@example.com")
    UserRole.objects.create(user=user, school=school, role_code="collection_editor")
    perm, _ = CrownPermission.objects.get_or_create(code="survey.edit")
    RolePermission.objects.get_or_create(role_code="collection_editor", permission=perm)
    survey = make_survey(school=school)
    pub = survey.publications.get()
    token = issue_respondent_grant(school_id=school.pk, publication_id=pub.pk, issuer=user, expires_at=timezone.now() + timedelta(days=1))
    # Test-only collection switch: issuance and production routes never enable it.
    survey.public_enabled = True
    survey.save(update_fields=["public_enabled"])
    payload = {"answers": {"satisfaction": 4}, "notice_sha256": pub.snapshot_sha256, "retry_key": "r" * 32}
    return school, user, survey, pub, token, payload


def send(c, payload=None):
    return collect_response(token=c[4], body=json.dumps(payload if payload is not None else c[5]).encode())


def test_safe_retry_and_private_receipt(collection, caplog):
    receipt = send(collection)
    assert send(collection) == receipt
    response = SurveyResponse.objects.get()
    assert response.publication_id == collection[3].pk and response.school_id == collection[0].pk
    assert response.anonymous and response.metadata_json == {}
    assert all(getattr(response, field) is None for field in ("household_id", "student_id", "application_id", "campaign_id"))
    stored = SurveyCollectionReceipt.objects.get()
    assert receipt == str(stored.pk) and receipt != str(response.pk)
    grant = SurveyRespondentGrant.objects.get()
    assert collection[4] not in str(grant.__dict__) and collection[5]["retry_key"] not in str(stored.__dict__)
    assert caplog.text == ""


@pytest.mark.parametrize("field,value", [("answers", {"satisfaction": 5}), ("retry_key", "x" * 32)])
def test_one_use_grant_rejects_changed_replay(collection, field, value):
    send(collection)
    payload = dict(collection[5], **{field: value})
    with pytest.raises(CollectionRejected, match="conflicts"):
        send(collection, payload)
    assert SurveyResponse.objects.count() == SurveyCollectionReceipt.objects.count() == 1


@pytest.mark.parametrize("mutation", ["expired", "revoked", "closed", "disabled", "inactive", "public_expired", "fingerprint", "notice", "questions", "new_version", "rehash"])
def test_unavailable_authority_fails_before_replay(collection, mutation):
    school, user, survey, pub, token, _ = collection
    send(collection)
    grant = SurveyRespondentGrant.objects.get()
    if mutation == "expired":
        grant.expires_at = timezone.now(); grant.save()
    elif mutation == "revoked":
        revoke_respondent_grant(school_id=school.pk, grant_id=grant.pk, issuer=user)
    elif mutation == "closed":
        survey.status = "closed"; survey.save()
    elif mutation == "disabled":
        survey.public_enabled = False; survey.save()
    elif mutation == "inactive":
        school.is_active = False; school.save()
    elif mutation == "public_expired":
        survey.public_expires_at = timezone.now(); survey.save()
    elif mutation == "fingerprint":
        pub.snapshot_sha256 = "0" * 64; pub.save()
    elif mutation == "notice":
        pub.respondent_notice = ""; pub.save()
    elif mutation == "questions":
        q = survey.questions.get(); q.prompt = "Changed"; q.save()
    elif mutation == "new_version":
        SurveyPublication.objects.create(survey=survey, version=2, snapshot_json=pub.snapshot_json, snapshot_sha256=pub.snapshot_sha256, respondent_notice=pub.respondent_notice, published_by_user_id=user.pk)
    else:
        import hashlib
        pub.snapshot_json["respondent_notice"] = pub.respondent_notice = "Changed notice with recomputed fingerprint"
        pub.snapshot_sha256 = hashlib.sha256(json.dumps(pub.snapshot_json, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest(); pub.save()
    with pytest.raises(CollectionRejected):
        send(collection)
    assert SurveyResponse.objects.count() == 1


def test_cross_school_issuance_revocation_and_payload_denied(collection):
    school, user, survey, pub, token, payload = collection
    other = School.objects.create(name="Other School")
    with pytest.raises(CollectionRejected):
        issue_respondent_grant(school_id=other.pk, publication_id=pub.pk, issuer=user, expires_at=timezone.now() + timedelta(days=1))
    with pytest.raises(CollectionRejected):
        revoke_respondent_grant(school_id=other.pk, grant_id=SurveyRespondentGrant.objects.get().pk, issuer=user)
    for field in ("school_id", "publication_id", "student_id", "household_id", "metadata", "ip", "campaign_id"):
        with pytest.raises(CollectionRejected):
            send(collection, dict(payload, **{field: str(other.pk)}))
    assert not SurveyResponse.objects.exists()


@pytest.mark.parametrize("body", [b"{}", b"[]", b"{", b"\xff", b"x" * 65537, b'{"answers":{},"answers":{}}', b'{"answers":{"x":NaN}}'])
def test_malformed_body_creates_no_rows(collection, body):
    with pytest.raises(CollectionRejected):
        collect_response(token=collection[4], body=body)
    assert not SurveyResponse.objects.exists() and not SurveyCollectionReceipt.objects.exists()


@pytest.mark.parametrize("changes", [{"notice_sha256": None}, {"retry_key": "short"}, {"answers": {"satisfaction": "4"}}, {"answers": {"satisfaction": 4, "student_id": "secret-sensitive-marker"}}])
def test_validation_errors_are_safe_and_atomic(collection, changes, caplog):
    with pytest.raises(CollectionRejected) as exc:
        send(collection, dict(collection[5], **changes))
    assert "secret-sensitive-marker" not in str(exc.value)
    assert collection[4] not in str(exc.value) and caplog.text == ""
    assert not SurveyResponse.objects.exists() and not SurveyCollectionReceipt.objects.exists()


def test_abuse_budget_and_storage_failure_fail_closed(collection):
    SurveyRespondentGrant.objects.update(attempts=MAX_ATTEMPTS)
    with pytest.raises(CollectionRejected):
        send(collection)
    SurveyRespondentGrant.objects.update(attempts=0)
    with patch("django.db.models.query.QuerySet.update", side_effect=DatabaseError("secret database details")):
        with pytest.raises(CollectionRejected) as exc:
            send(collection)
    assert "secret" not in str(exc.value) and not SurveyResponse.objects.exists()


def test_bad_answers_consume_budget(collection):
    with pytest.raises(CollectionRejected):
        send(collection, dict(collection[5], answers={"satisfaction": "4"}))
    assert SurveyRespondentGrant.objects.get().attempts == 1


def test_grant_issue_does_not_enable_collection(collection):
    collection[2].public_enabled = False; collection[2].save()
    with pytest.raises(CollectionRejected):
        send(collection)
    assert not SurveyResponse.objects.exists()


def test_concurrent_requests_create_one_response_and_retry_receipt(collection):
    from threading import Barrier
    start = Barrier(2)
    def worker():
        close_old_connections()
        try:
            start.wait(timeout=10)
            try:
                return send(collection)
            except CollectionRejected:
                # SQLite may reject a busy writer; safe client retry is mandatory.
                return None
        finally:
            close_old_connections()
    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(lambda _: worker(), range(2)))
    receipt = send(collection)
    assert all(result is None or result == receipt for result in results)
    assert SurveyResponse.objects.count() == SurveyCollectionReceipt.objects.count() == 1


def test_unauthorized_editor_cannot_issue_or_revoke(collection):
    school, user, _, pub, _, _ = collection
    RolePermission.objects.filter(role_code="collection_editor", permission__code="survey.edit").delete()
    with pytest.raises(CollectionRejected):
        issue_respondent_grant(school_id=school.pk, publication_id=pub.pk, issuer=user, expires_at=timezone.now() + timedelta(days=1))
    with pytest.raises(CollectionRejected):
        revoke_respondent_grant(school_id=school.pk, grant_id=SurveyRespondentGrant.objects.get().pk, issuer=user)


@pytest.mark.parametrize("days", [0, -1, 31])
def test_issue_rejects_invalid_expiration(collection, days):
    school, user, _, pub, _, _ = collection
    with pytest.raises(CollectionRejected):
        issue_respondent_grant(school_id=school.pk, publication_id=pub.pk, issuer=user, expires_at=timezone.now() + timedelta(days=days))
    assert SurveyRespondentGrant.objects.count() == 1


def test_legacy_uuid_is_not_authority(collection):
    with pytest.raises(CollectionRejected):
        collect_response(token=str(collection[2].public_token), body=json.dumps(collection[5]).encode())
    assert not SurveyResponse.objects.exists()


def test_receipt_failure_rolls_back_response(collection):
    with patch.object(SurveyCollectionReceipt.objects, "create", side_effect=DatabaseError("sensitive-details")):
        with pytest.raises(CollectionRejected):
            send(collection)
    assert not SurveyResponse.objects.exists() and not SurveyCollectionReceipt.objects.exists()
    assert SurveyRespondentGrant.objects.get().attempts == 1
