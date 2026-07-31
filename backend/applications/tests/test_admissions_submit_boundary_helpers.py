from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import UUID, uuid4

import pytest
from rest_framework.response import Response

from applications import views_admissions as views


def _request(*, headers=None, meta=None):
    return SimpleNamespace(headers=headers or {}, META=meta or {})


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (None, "other"),
        (" church ", "church_referral"),
        ("Current Family", "word_of_mouth"),
        ("friend-or-colleague", "word_of_mouth"),
        ("social media", "facebook"),
        ("search-engine", "google"),
        ("community event", "website"),
        ("unrecognized", "other"),
    ],
)
def test_normalize_source_maps_external_values(value, expected):
    assert views._normalize_source(value) == expected


def test_validation_error_includes_optional_correlation_id():
    response = views._validation_error("Invalid payload", code="invalid_payload", correlation_id="corr-1")

    assert response.status_code == 400
    assert response.data == {
        "detail": "Invalid payload",
        "message": "Invalid payload",
        "code": "invalid_payload",
        "correlation_id": "corr-1",
    }


def test_request_correlation_id_prefers_request_id_and_truncates():
    request = _request(headers={"X-Request-Id": "x" * 140, "X-Correlation-Id": "fallback"})

    assert views._request_correlation_id(request) == "x" * 128


def test_request_correlation_id_generates_uuid_without_headers():
    value = views._request_correlation_id(_request())

    assert str(UUID(value)) == value


def test_request_trace_id_uses_declared_precedence():
    request = _request(
        headers={
            "X-Trace-Id": "trace",
            "X-Request-Id": "request",
            "X-Correlation-Id": "correlation",
        }
    )

    assert views._request_trace_id(request) == "trace"


def test_request_trace_id_falls_back_to_correlation_id():
    assert views._request_trace_id(_request(headers={"X-Correlation-Id": "corr"})) == "corr"


def test_idempotency_key_prefers_standard_header_and_truncates():
    request = _request(
        headers={
            "Idempotency-Key": "k" * 300,
            "X-Idempotency-Key": "fallback",
        }
    )

    assert views._idempotency_key(request) == "k" * 256


def test_idempotency_key_uses_compatibility_header():
    assert views._idempotency_key(_request(headers={"X-Idempotency-Key": "compat"})) == "compat"


def test_cache_key_for_submit_is_tenant_and_key_specific():
    school_id = uuid4()

    assert views._cache_key_for_submit(school_id, "submission-1") == (
        f"admissions_submit:{school_id}:submission-1"
    )


def test_cache_increment_returns_one_when_bucket_is_created(monkeypatch):
    cache = MagicMock()
    cache.add.return_value = True
    monkeypatch.setattr(views, "cache", cache)

    assert views._cache_increment_with_window("bucket", 60) == 1
    cache.add.assert_called_once_with("bucket", 1, timeout=60)
    cache.incr.assert_not_called()


def test_cache_increment_uses_existing_bucket(monkeypatch):
    cache = MagicMock()
    cache.add.return_value = False
    cache.incr.return_value = 4
    monkeypatch.setattr(views, "cache", cache)

    assert views._cache_increment_with_window("bucket", 60) == 4
    cache.incr.assert_called_once_with("bucket")


def test_cache_increment_recovers_from_missing_counter(monkeypatch):
    cache = MagicMock()
    cache.add.return_value = False
    cache.incr.side_effect = ValueError
    monkeypatch.setattr(views, "cache", cache)

    assert views._cache_increment_with_window("bucket", 60) == 1
    cache.set.assert_called_once_with("bucket", 1, timeout=60)


def test_client_ip_prefers_first_forwarded_address():
    request = _request(
        headers={"X-Forwarded-For": " 203.0.113.8, 10.0.0.1 "},
        meta={"REMOTE_ADDR": "192.0.2.9"},
    )

    assert views._client_ip_address(request) == "203.0.113.8"


def test_client_ip_falls_back_to_remote_then_unknown():
    assert views._client_ip_address(_request(meta={"REMOTE_ADDR": "192.0.2.9"})) == "192.0.2.9"
    assert views._client_ip_address(_request()) == "unknown"


def test_primary_guardian_email_prefers_explicit_primary_and_normalizes():
    payload = {
        "family": {
            "guardians": [
                {"email": "first@example.org"},
                {"email": " PRIMARY@EXAMPLE.ORG ", "isPrimary": True},
            ]
        }
    }

    assert views._primary_guardian_email(payload) == "primary@example.org"


def test_primary_guardian_email_uses_first_guardian_or_legacy_email():
    assert views._primary_guardian_email(
        {"family": {"guardians": [{"email": " FIRST@EXAMPLE.ORG "}]}}
    ) == "first@example.org"
    assert views._primary_guardian_email(
        {"family": {"email": " LEGACY@EXAMPLE.ORG "}}
    ) == "legacy@example.org"


def test_abuse_throttle_response_sets_retry_and_correlation_headers():
    response = views._abuse_throttle_response("Slow down", "corr-2", 900)

    assert response.status_code == 429
    assert response["Retry-After"] == "900"
    assert response["X-Correlation-Id"] == "corr-2"
    assert response["X-Request-Id"] == "corr-2"
    assert response.data["code"] == "rate_limited"
    assert response.data["correlation_id"] == "corr-2"


def test_attach_correlation_preserves_existing_payload_value():
    response = Response({"correlation_id": "existing", "ok": True})

    result = views._attach_correlation(response, "new")

    assert result is response
    assert response.data["correlation_id"] == "existing"
    assert response["X-Correlation-Id"] == "new"


def test_submit_abuse_controls_fail_closed_on_ip_limit(monkeypatch):
    request = _request(meta={"REMOTE_ADDR": "192.0.2.1"})
    increment = MagicMock(return_value=views.SUBMIT_IP_RATE_LIMIT + 1)
    monkeypatch.setattr(views, "_cache_increment_with_window", increment)

    response = views._enforce_submit_abuse_controls(
        request,
        uuid4(),
        {"family": {"email": "guardian@example.org"}},
        "corr-ip",
    )

    assert response.status_code == 429
    assert response.data["detail"].startswith("Too many admissions submissions from this network")
    assert increment.call_count == 1


def test_submit_abuse_controls_fail_closed_on_email_limit(monkeypatch):
    request = _request(meta={"REMOTE_ADDR": "192.0.2.1"})
    increment = MagicMock(
        side_effect=[views.SUBMIT_IP_RATE_LIMIT, views.SUBMIT_EMAIL_RATE_LIMIT + 1]
    )
    monkeypatch.setattr(views, "_cache_increment_with_window", increment)

    response = views._enforce_submit_abuse_controls(
        request,
        uuid4(),
        {"family": {"email": " GUARDIAN@EXAMPLE.ORG "}},
        "corr-email",
    )

    assert response.status_code == 429
    assert response.data["detail"].startswith("Too many admissions submissions for this email")
    assert "guardian@example.org" in increment.call_args_list[1].args[0]


def test_submit_abuse_controls_allow_request_under_limits(monkeypatch):
    increment = MagicMock(side_effect=[1, 1])
    monkeypatch.setattr(views, "_cache_increment_with_window", increment)

    response = views._enforce_submit_abuse_controls(
        _request(meta={"REMOTE_ADDR": "192.0.2.1"}),
        uuid4(),
        {"family": {"email": "guardian@example.org"}},
        "corr-ok",
    )

    assert response is None
    assert increment.call_count == 2


def test_build_legacy_guardian_requires_any_legacy_identity_value():
    assert views._build_legacy_guardian({}) is None
    assert views._build_legacy_guardian({"guardianName": "Pat Guardian"}) == {
        "relationship": "Guardian",
        "relationshipOther": "",
        "guardianName": "Pat Guardian",
        "email": "",
        "phone": "",
        "isPrimary": True,
    }


def test_extract_guardians_filters_non_dict_values_and_falls_back_to_legacy():
    explicit = {"guardians": [None, "invalid", {"guardianName": "Primary"}]}

    assert views._extract_guardians(explicit) == [{"guardianName": "Primary"}]
    assert views._extract_guardians(
        {"guardianName": "Legacy", "email": "legacy@example.org", "phone": "555-0100"}
    )[0]["isPrimary"] is True


def test_extract_students_prefers_list_and_filters_non_dict_values():
    payload = {
        "students": [None, {"firstName": "A"}, "invalid"],
        "student": {"firstName": "Legacy"},
    }

    assert views._extract_students(payload) == [{"firstName": "A"}]


def test_extract_students_supports_legacy_student_and_empty_payload():
    assert views._extract_students({"student": {"firstName": "Legacy"}}) == [
        {"firstName": "Legacy"}
    ]
    assert views._extract_students({}) == []


def test_extract_submit_data_normalizes_optional_sections_and_core_fields():
    data = views._extract_submit_data(
        {
            "inquiry": {"campus": " North ", "startTerm": " Fall 2027 "},
            "family": {
                "guardianName": "Pat Guardian",
                "email": "guardian@example.org",
                "phone": "555-0100",
            },
            "student": {"firstName": "Student"},
            "mission": "invalid",
            "documents": {"birthCertificate": True},
            "financialAidInterest": {"interested": True},
            "attestations": {"accurate": True},
            "applicationFee": {"policyAccepted": True},
        }
    )

    assert data.campus == "North"
    assert data.start_term == "Fall 2027"
    assert data.students == [{"firstName": "Student"}]
    assert data.guardians[0]["guardianName"] == "Pat Guardian"
    assert data.mission == {}
    assert data.documents == {"birthCertificate": True}
    assert data.financial_aid_interest == {"interested": True}
