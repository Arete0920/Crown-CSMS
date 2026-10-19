"""Query-bound and cursor behavior regressions for the admissions queue."""
import uuid
from datetime import timedelta

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone
from rest_framework.test import APIClient

from core.models import CrownPermission, RolePermission, School, UserAccount, UserRole
from crm_marketing.models import CampaignTouchpoint, MarketingLead


pytestmark = pytest.mark.django_db
URL = "/api/v1/crm/inquiries/"


def _school():
    return School.objects.create(name=f"Queue {uuid.uuid4()}")


def _staff(school):
    user = UserAccount.objects.create_user(
        username=f"queue-{uuid.uuid4().hex}", email=f"queue-{uuid.uuid4().hex}@example.test"
    )
    role = f"queue_{uuid.uuid4().hex[:12]}"
    UserRole.objects.create(user=user, school=school, role_code=role)
    for code in ("admissions.view", "admissions.edit"):
        permission, _ = CrownPermission.objects.get_or_create(
            code=code, defaults={"description": code},
        )
        RolePermission.objects.create(role_code=role, permission=permission)
    client = APIClient()
    client.force_authenticate(user=user)
    return client


def _create_leads(school, count, *, shared_email=False):
    now = timezone.now()
    leads = [
        MarketingLead(
            school=school, parent_name=f"Parent {index:03d}",
            email="shared@example.test" if shared_email else f"parent{index}@example.test",
            inquiry_received_at=now,
            next_follow_up_at=now + timedelta(minutes=index),
            stage="inquiry",
        ) for index in range(count)
    ]
    return MarketingLead.objects.bulk_create(leads)


def _get(client, school, query=""):
    return client.get(f"{URL}{query}", HTTP_X_SCHOOL_ID=str(school.id))


def test_queue_cursor_visits_all_records_without_duplicates_and_rejects_tampering():
    school = _school()
    other = _school()
    leads = _create_leads(school, 62)
    _create_leads(other, 12)
    client = _staff(school)
    seen = []
    cursor = None
    for _ in range(4):
        from urllib.parse import quote
        params = "?limit=20" + (f"&cursor={quote(cursor, safe='')}" if cursor else "")
        response = _get(client, school, params)
        assert response.status_code == 200, response.data
        assert response.data["count"] == 62
        assert len(response.data["results"]) <= 20
        seen.extend(item["id"] for item in response.data["results"])
        cursor = response.data["next_cursor"]
        if not cursor:
            break
    assert len(seen) == 62
    assert len(set(seen)) == 62
    assert set(seen) == {str(lead.id) for lead in leads}

    assert _get(client, school, "?limit=0").status_code == 400
    assert _get(client, school, "?limit=101").status_code == 400
    assert _get(client, school, "?cursor=invalid").status_code == 400
    first = _get(client, school, "?limit=10").data["next_cursor"]
    assert _get(client, school, f"?limit=20&cursor={first}").status_code == 400
    assert _get(client, school, f"?limit=10&stage=all&cursor={first}").status_code == 400
    assert _get(_staff(other), other, f"?limit=10&cursor={first}").status_code == 400


def test_queue_keeps_null_follow_up_last_and_ties_deterministic():
    school = _school()
    _create_leads(school, 6)
    MarketingLead.objects.create(
        school=school, email="no-due@example.test",
        inquiry_received_at=timezone.now(),
        next_follow_up_at=None, stage="inquiry",
    )
    client = _staff(school)
    first = _get(client, school, "?limit=3")
    second = _get(client, school, f"?limit=3&cursor={first.data['next_cursor']}")
    third = _get(client, school, f"?limit=3&cursor={second.data['next_cursor']}")
    all_rows = first.data["results"] + second.data["results"] + third.data["results"]
    assert len(all_rows) == 7
    assert len({row["id"] for row in all_rows}) == 7
    assert all_rows[-1]["next_follow_up_at"] is None


def test_queue_query_count_is_bounded_as_record_count_grows():
    school = _school()
    client = _staff(school)
    _create_leads(school, 2, shared_email=True)
    with CaptureQueriesContext(connection) as small_capture:
        small = _get(client, school, "?limit=50")
    assert small.status_code == 200, small.data
    _create_leads(school, 25, shared_email=True)
    with CaptureQueriesContext(connection) as large_capture:
        large = _get(client, school, "?limit=50")
    assert large.status_code == 200, large.data
    assert len(large.data["results"]) == 27
    # Bounded queries: relation queries must not grow per inquiry.
    assert len(large_capture) <= len(small_capture) + 3, (
        len(small_capture), len(large_capture),
    )
    assert len(large_capture) < 35


def test_queue_related_history_is_school_scoped_and_bounded():
    school = _school()
    other = _school()
    lead = _create_leads(school, 1)[0]
    peer = MarketingLead.objects.create(
        school=school, email=lead.email, inquiry_received_at=timezone.now(),
    )
    foreign = MarketingLead.objects.create(
        school=other, email=lead.email, inquiry_received_at=timezone.now(),
    )
    for index in range(15):
        CampaignTouchpoint.objects.create(
            school=school, lead=lead, channel="phone",
            summary=f"school touch {index}", occurred_at=timezone.now() + timedelta(minutes=index),
        )
    CampaignTouchpoint.objects.create(
        school=other, lead=lead, channel="phone",
        summary="other school private note", occurred_at=timezone.now(),
    )
    response = _get(_staff(school), school)
    assert response.status_code == 200, response.data
    row = next(item for item in response.data["results"] if item["id"] == str(lead.id))
    assert len(row["touchpoints"]) == 10
    assert {str(item["id"]) for item in row["duplicate_candidates"]} == {str(peer.id)}
    assert str(foreign.id) not in str(row)
    assert all("other school" not in item["summary"] for item in row["touchpoints"])
