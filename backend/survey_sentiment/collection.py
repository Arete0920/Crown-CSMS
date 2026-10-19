"""Internal adult anonymous collection. No HTTP routes or invitation delivery.

Authority is one-use and bound to a publication fingerprint. Issuance does not
approve notices, enable collection or prove respondent eligibility.
"""
import hashlib
import hmac
import json
import re
import secrets
from datetime import datetime, timedelta

from django.conf import settings
from django.db import DatabaseError, transaction
from django.db.models import F
from django.utils import timezone

from core.models import School
from core.permissions import user_has_permission
from .models import SurveyDefinition, SurveyPublication, SurveyRespondentGrant, SurveyCollectionReceipt
from .submission import SurveyUnavailable, submit_anonymous_response
from .validation import SurveyAnswerValidationError

MAX_BODY_BYTES = 65536
MAX_ATTEMPTS = 30  # lifetime bound per grant; no network identifiers retained
SECRET_PATTERN = re.compile(r"^[A-Za-z0-9_-]{32,128}$")
UNAVAILABLE = "Survey is not available."


class CollectionRejected(ValueError):
    """Safe respondent-facing failure; never include payload or token details."""


def _digest(domain, value):
    return hmac.new(settings.SECRET_KEY.encode(), (domain + ":" + value).encode(), hashlib.sha256).hexdigest()


def _publication(survey, publication_id, fingerprint=None):
    pub = SurveyPublication.objects.select_for_update().filter(survey=survey).order_by("-version").first()
    if pub is None or pub.pk != publication_id or pub.collection_mode != "anonymous":
        raise CollectionRejected(UNAVAILABLE)
    snapshot = pub.snapshot_json
    canonical = json.dumps(snapshot, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
    if (not isinstance(snapshot, dict)
        or snapshot.get("school_id") != str(survey.school_id)
        or snapshot.get("survey_id") != str(survey.pk)
        or snapshot.get("version") != pub.version
        or snapshot.get("collection_mode") != "anonymous"
        or not pub.respondent_notice.strip()
        or snapshot.get("respondent_notice") != pub.respondent_notice
        or hashlib.sha256(canonical.encode()).hexdigest() != pub.snapshot_sha256
        or (fingerprint is not None and not hmac.compare_digest(fingerprint, pub.snapshot_sha256))):
        raise CollectionRejected(UNAVAILABLE)
    rows = snapshot.get("questions")
    current = [{"key": q.key, "prompt": q.prompt, "question_type": q.question_type,
                "choices": q.choices, "required": q.required, "sort_order": q.sort_order}
               for q in survey.questions.select_for_update().all()]
    if not rows or rows != current:
        raise CollectionRejected(UNAVAILABLE)
    return pub


@transaction.atomic
def issue_respondent_grant(*, school_id, publication_id, issuer, expires_at):
    """Trusted school editor only. Return secret once; never enable/distribute it.

    Caller must separately record school/legal/privacy approval for adult notice
    and instrument. The existing survey.edit permission authorizes this internal
    preparatory operation, not a production rollout.
    """
    now = timezone.now()
    if (not isinstance(expires_at, datetime)
        or not timezone.is_aware(expires_at)
        or not now < expires_at <= now + timedelta(days=30)):
        raise CollectionRejected(UNAVAILABLE)
    school = School.objects.select_for_update().filter(pk=school_id, is_active=True).first()
    if school is None or not user_has_permission(issuer, "survey.edit", school=school):
        raise CollectionRejected(UNAVAILABLE)
    pub = SurveyPublication.objects.filter(pk=publication_id, survey__school=school).first()
    if pub is None:
        raise CollectionRejected(UNAVAILABLE)
    survey = SurveyDefinition.objects.select_for_update().get(pk=pub.survey_id)
    if survey.status != "active" or not survey.anonymous_allowed:
        raise CollectionRejected(UNAVAILABLE)
    pub = _publication(survey, pub.pk)
    secret = secrets.token_urlsafe(32)
    SurveyRespondentGrant.objects.create(
        publication=pub, publication_sha256=pub.snapshot_sha256,
        token_digest=_digest("grant", secret), expires_at=expires_at,
        issued_by_user_id=issuer.pk,
    )
    return secret


def revoke_respondent_grant(*, school_id, grant_id, issuer):
    school = School.objects.filter(pk=school_id, is_active=True).first()
    if school is None or not user_has_permission(issuer, "survey.edit", school=school):
        raise CollectionRejected(UNAVAILABLE)
    # An UPDATE serializes against collection's grant UPDATE/row lock.
    if not SurveyRespondentGrant.objects.filter(pk=grant_id, publication__survey__school=school).update(revoked_at=timezone.now()):
        raise CollectionRejected(UNAVAILABLE)


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON key")
        result[key] = value
    return result


def collect_response(*, token, body):
    """Return only an opaque receipt UUID. Reject all client identity/scope fields.

    Body: answers, notice_sha256 (of the exact publication), retry_key. No raw
    errors are propagated/logged. DB abuse-budget failure is fail closed.
    Must be called with autocommit enabled, outside any enclosing transaction;
    otherwise a caller could roll back the durable attempt budget.
    """
    try:
        if not isinstance(token, str) or not SECRET_PATTERN.fullmatch(token):
            raise CollectionRejected(UNAVAILABLE)
        if not isinstance(body, bytes) or len(body) > MAX_BODY_BYTES:
            raise CollectionRejected("Invalid submission.")
        payload = json.loads(body.decode("utf-8"), object_pairs_hook=_unique_object,
                             parse_constant=lambda value: (_ for _ in ()).throw(ValueError()))
        if not isinstance(payload, dict) or set(payload) != {"answers", "notice_sha256", "retry_key"}:
            raise CollectionRejected("Invalid submission.")
        retry_key = payload["retry_key"]
        if not isinstance(retry_key, str) or not SECRET_PATTERN.fullmatch(retry_key):
            raise CollectionRejected("Invalid submission.")
        if not isinstance(payload["answers"], dict) or len(payload["answers"]) > 40:
            raise CollectionRejected("Invalid submission.")
        if not transaction.get_autocommit():
            # Collection owns the durable attempt write and atomic response.
            # Reject ATOMIC_REQUESTS/enclosing atomic/manual transactions before
            # any write; their rollback could otherwise erase abuse attempts.
            raise CollectionRejected(UNAVAILABLE)
        digest = _digest("grant", token)
        # Persist a bounded budget even when answer/notice validation later fails.
        if not SurveyRespondentGrant.objects.filter(token_digest=digest, attempts__lt=MAX_ATTEMPTS).update(attempts=F("attempts") + 1):
            raise CollectionRejected(UNAVAILABLE)
        return _collect(digest, payload)
    except CollectionRejected:
        raise
    except (ValueError, TypeError, RecursionError, DatabaseError, SurveyUnavailable, SurveyAnswerValidationError):
        raise CollectionRejected("Invalid or unavailable submission.") from None


@transaction.atomic
def _collect(digest, payload):
    # First write serializes competing collectors even on SQLite (whose SELECT
    # FOR UPDATE is a no-op). Never read acceptance state before obtaining it.
    SurveyRespondentGrant.objects.filter(token_digest=digest).update(attempts=F("attempts"))
    grant = SurveyRespondentGrant.objects.select_for_update().get(token_digest=digest)
    school = School.objects.select_for_update().filter(pk=grant.publication.survey.school_id, is_active=True).first()
    survey = SurveyDefinition.objects.select_for_update().get(pk=grant.publication.survey_id)
    if (school is None or grant.revoked_at is not None or grant.expires_at <= timezone.now()
        or survey.status != "active" or not survey.anonymous_allowed or not survey.public_enabled
        or (survey.public_expires_at is not None and survey.public_expires_at <= timezone.now())):
        raise CollectionRejected(UNAVAILABLE)
    pub = _publication(survey, grant.publication_id, grant.publication_sha256)
    if payload["notice_sha256"] != grant.publication_sha256:
        raise CollectionRejected("Notice acknowledgement required.")
    canonical = json.dumps(payload["answers"], sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
    payload_digest = _digest("payload:" + str(grant.pk), canonical)
    retry_digest = _digest("retry:" + str(grant.pk), payload["retry_key"])
    receipt = SurveyCollectionReceipt.objects.filter(grant=grant).first()
    if receipt is not None:
        if not hmac.compare_digest(receipt.retry_digest, retry_digest) or not hmac.compare_digest(receipt.payload_digest, payload_digest):
            raise CollectionRejected("Submission conflicts with an accepted response.")
        return str(receipt.pk)
    response = submit_anonymous_response(school_id=school.pk, survey_id=survey.pk, answers=payload["answers"])
    receipt = SurveyCollectionReceipt.objects.create(
        grant=grant, response=response, retry_digest=retry_digest, payload_digest=payload_digest,
    )
    return str(receipt.pk)
