import pytest

from .test_views import BASE_URL, VALID_BUCKETS, _client_for, _headers, _make_school


@pytest.mark.django_db
def test_zero_award_cycle_commits_and_verifies():
    school = _make_school("Zero Award School")
    client = _client_for(school)
    headers = _headers(school.id)

    created = client.post(BASE_URL, **headers)
    session_id = created.data["session_id"]

    assert client.post(f"{BASE_URL}{session_id}/configure/", {"aid_year": "2026-2027"}, format="json", **headers).status_code == 200
    assert client.post(f"{BASE_URL}{session_id}/buckets/", {"buckets": VALID_BUCKETS}, format="json", **headers).status_code == 200
    staged = client.post(f"{BASE_URL}{session_id}/awards/", {"awards": []}, format="json", **headers)
    assert staged.status_code == 200
    assert staged.data["awards_count"] == 0

    committed = client.post(f"{BASE_URL}{session_id}/commit/", {"confirm": True}, format="json", **headers)
    assert committed.status_code == 200
    assert committed.data["status"] == "committed"
    assert committed.data["awards_created"] == 0
    assert committed.data["awards_skipped"] == 0
    assert committed.data["errors"] == []

    verified = client.get(f"{BASE_URL}{session_id}/verify/", **headers)
    assert verified.status_code == 200
    assert verified.data["status"] == "verified"
    assert verified.data["awards_created"] == 0
    assert verified.data["errors"] == []
