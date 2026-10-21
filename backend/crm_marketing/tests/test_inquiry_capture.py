import json
import uuid
from datetime import timedelta

import pytest
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.db import connection, transaction
from django.db.migrations.loader import MigrationLoader
from django.utils import timezone
from rest_framework.test import APIClient

from applications.models import Application, Applicant
from core.models import CrownPermission, RolePermission, School, UserAccount, UserRole
from crm_marketing.models import CampaignTouchpoint, MarketingCampaign, MarketingLead
from households.models import Household


pytestmark = pytest.mark.django_db
URL = "/api/v1/crm/inquiries/"


@pytest.fixture(autouse=True)
def protected_tenant_runtime(settings):
    settings.TENANT_HEADER_REQUIRED = True
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def school():
    return School.objects.create(name=f"Inquiry School {uuid.uuid4().hex[:8]}")


def _staff(school, *, edit=True):
    user = UserAccount.objects.create_user(username=f"staff-{uuid.uuid4().hex}", email="staff@example.test")
    role = f"inquiry_{uuid.uuid4().hex[:12]}"
    UserRole.objects.create(user=user, school=school, role_code=role)
    for code in ["admissions.view"] + (["admissions.edit"] if edit else []):
        permission, _ = CrownPermission.objects.get_or_create(code=code, defaults={"description": code})
        RolePermission.objects.create(role_code=role, permission=permission)
    return user


def _payload(school, **changes):
    return {
        "school_id": str(school.id), "campus": school.name,
        "parent_name": "Jordan Example", "email": "jordan@example.test",
        "phone": "+15550101000", "grade_interest": "5", "entry_year": "2027-2028",
        "request_type": "tour", "contact_preference": "email", "response_consent": True,
        "source": "instagram", "utm": {"utm_source": "instagram", "utm_campaign": "fall-open-house"},
        **changes,
    }


def _capture(school, *, client=None, request_key=None, **changes):
    return (client or APIClient()).post(
        URL, _payload(school, **changes), format="json",
        HTTP_IDEMPOTENCY_KEY=request_key or str(uuid.uuid4()),
    )


def _application_payload(school, receipt):
    return {
        "inquiry_id": receipt["inquiry_id"], "continuation_token": receipt["continuation_token"],
        "inquiry": {"campus": school.name, "startTerm": "2027-2028", "heardAbout": "website"},
        "family": {"guardians": [{"guardianName": "Jordan Example", "email": "jordan@example.test", "phone": "+15550101000", "relationship": "Parent", "isPrimary": True}]},
        "students": [{"firstName": name, "lastName": "Example", "gradeApplyingFor": "5", "currentSchool": "Homeschool"} for name in ["Alex", "Casey"]],
        "applicationFee": {"waiverRequested": True},
    }


def test_pre_inquiry_model_can_insert_after_inquiry_migration(school):
    historical_apps = MigrationLoader(connection).project_state([
        ("crm_marketing", "0001_initial"),
    ]).apps
    historical_lead = historical_apps.get_model("crm_marketing", "MarketingLead")
    expected_defaults = {
        "attribution_json": {}, "submission_receipt": {},
        "family_follow_up_enabled": False, "follow_up_consent": False,
        "response_consent": False,
        "campus": "", "contact_preference": "", "email": "", "entry_year": "",
        "grade_interest": "", "intake_payload_digest": "", "parent_name": "",
        "phone": "", "request_type": "",
    }
    assert set(expected_defaults).isdisjoint(
        field.name for field in historical_lead._meta.concrete_fields
    )

    # The previous API does not know these columns and cannot supply their defaults.
    legacy = historical_lead.objects.create(
        school_id=school.id, stage="application_submitted", first_source="legacy",
    )
    current = MarketingLead.objects.get(pk=legacy.pk)
    assert {name: getattr(current, name) for name in expected_defaults} == expected_defaults
    assert current.school_id == school.id
    assert current.stage == "application_submitted" and current.first_source == "legacy"
    assert current.inquiry_received_at is None
    assert not current.applications.exists()


def test_public_capture_creates_owned_inquiry_before_application(school):
    owner = _staff(school)
    response = _capture(school)
    assert response.status_code == 201, response.data
    lead = MarketingLead.objects.get(id=response.data["inquiry_id"])
    assert lead.parent_name == "Jordan Example"
    assert lead.email == "jordan@example.test"
    assert lead.stage == "inquiry" and lead.application_id is None
    assert lead.assigned_to_user_id == owner.id
    assert lead.next_follow_up_at > lead.inquiry_received_at
    assert lead.response_consent and lead.consent_at
    assert not lead.follow_up_consent and not lead.family_follow_up_enabled
    assert lead.first_source == "instagram"
    assert lead.attribution_json["utm_campaign"] == "fall-open-house"
    assert response.data["school_id"] == str(school.id)
    assert response["Cache-Control"] == "no-store"
    assert Application.objects.count() == Household.objects.count() == 0


def test_retries_are_persistent_and_contact_matches_do_not_grant_access(school):
    key = str(uuid.uuid4())
    first = _capture(school, request_key=key)
    cache.clear()
    replay = _capture(school, request_key=key)
    assert replay.status_code == 200 and replay.data["replayed"]
    assert replay.data["inquiry_id"] == first.data["inquiry_id"]
    changed = _capture(school, request_key=key, parent_name="Different Person")
    assert changed.status_code == 400
    another = _capture(school)
    assert another.status_code == 201
    assert another.data["inquiry_id"] != first.data["inquiry_id"]
    assert "duplicate_candidates" not in another.data and "email" not in another.data
    assert MarketingLead.objects.count() == 2


@pytest.mark.parametrize("changes", [
    {"response_consent": False}, {"response_consent": "true"}, {"email": "invalid"},
    {"parent_name": "x" * 161}, {"request_type": []}, {"contact_preference": "sms", "phone": ""},
    {"contact_preference": "sms", "phone": "(302) 555-0100"},
    {"follow_up_consent": "true"}, {"website": "https://bot.example"},
    {"utm": {"unsupported": "x"}}, {"parent_name": "Unsafe\nHeader"},
])
def test_invalid_or_unconsented_capture_creates_no_records(school, changes):
    assert _capture(school, **changes).status_code == 400
    assert MarketingLead.objects.count() == 0


@pytest.mark.parametrize("surrogate", ["\ud800", "\udfff"], ids=["high-surrogate", "low-surrogate"])
def test_public_capture_rejects_escaped_surrogate_utm_before_persistence(school, surrogate):
    response = APIClient().post(
        URL, json.dumps(_payload(school, utm={"utm_campaign": surrogate}), ensure_ascii=True),
        content_type="application/json", HTTP_IDEMPOTENCY_KEY=str(uuid.uuid4()),
    )
    assert response.status_code == 400, response.content
    assert response.json()["detail"] == "utm_campaign contains unsupported Unicode characters."
    assert not MarketingLead.objects.exists()
    assert not CampaignTouchpoint.objects.exists()


def test_public_capture_preserves_unicode_through_staff_queue_serialization(school):
    parent_name = "Zoë 李 🌱"
    attribution = {"utm_campaign": "École 🏫"}
    client = APIClient()
    response = client.post(
        URL, json.dumps(_payload(school, parent_name=parent_name, utm=attribution), ensure_ascii=True),
        content_type="application/json", HTTP_IDEMPOTENCY_KEY=str(uuid.uuid4()),
    )
    assert response.status_code == 201, response.content
    lead = MarketingLead.objects.get(id=response.json()["inquiry_id"])
    assert lead.parent_name == parent_name
    assert lead.attribution_json == attribution
    client.force_authenticate(user=_staff(school, edit=False))
    queue = client.get(URL, HTTP_X_SCHOOL_ID=str(school.id))
    assert queue.status_code == 200, queue.content
    row = queue.json()["results"][0]
    assert row["parent_name"] == parent_name
    assert row["utm"] == attribution


def test_public_school_resolution_is_exact_and_header_cannot_conflict(school):
    body = _payload(school)
    body.pop("school_id")
    client = APIClient()
    exact = client.post(URL, body, format="json", HTTP_IDEMPOTENCY_KEY=str(uuid.uuid4()))
    assert exact.status_code == 201
    body["campus"] = school.name[:5]
    assert client.post(URL, body, format="json", HTTP_IDEMPOTENCY_KEY=str(uuid.uuid4())).status_code == 400
    other = School.objects.create(name="Other inquiry school")
    assert client.post(URL, _payload(school), format="json", HTTP_IDEMPOTENCY_KEY=str(uuid.uuid4()), HTTP_X_SCHOOL_ID=str(other.id)).status_code == 400
    assert client.post(URL, _payload(school), format="json", HTTP_IDEMPOTENCY_KEY=str(uuid.uuid4()), HTTP_X_SCHOOL_ID="invalid").status_code == 400
    defaulted = _capture(school, campus="")
    assert defaulted.status_code == 201
    assert MarketingLead.objects.get(id=defaulted.data["inquiry_id"]).campus == school.name


def test_sms_requires_country_code_while_phone_calls_accept_human_format(school):
    assert _capture(school, contact_preference="sms", phone="+13025550100").status_code == 201
    assert _capture(school, contact_preference="phone", phone="(302) 555-0100").status_code == 201


def test_campaign_scope_and_submission_throttles(school):
    other = School.objects.create(name="Campaign School")
    campaign = MarketingCampaign.objects.create(school=other, name="Other campaign", status="active")
    assert _capture(school, campaign_id=str(campaign.id)).status_code == 400
    cache.clear()
    for _ in range(6):
        assert _capture(school).status_code == 201
    limited = _capture(school)
    assert limited.status_code == 429 and limited["Retry-After"]
    assert MarketingLead.objects.count() == 6


def test_capability_start_is_idempotent_and_rejects_other_school_nonce_and_expiry(school):
    receipt = _capture(school).data
    lead = MarketingLead.objects.get(id=receipt["inquiry_id"])
    client = APIClient()
    url = f"{URL}{lead.id}/start/"
    body = {"school_id": str(school.id), "continuation_token": receipt["continuation_token"]}
    assert client.post(url, body, format="json").status_code == 200
    assert client.post(url, body, format="json").status_code == 200
    assert lead.touchpoints.filter(outcome="application_started").count() == 1
    other = School.objects.create(name="Other continuation school")
    assert client.post(url, {**body, "school_id": str(other.id)}, format="json").status_code == 404
    assert client.post(url, {**body, "continuation_token": "invalid"}, format="json").status_code == 404
    original_nonce = lead.continuation_nonce
    lead.continuation_nonce = uuid.uuid4()
    lead.save(update_fields=["continuation_nonce"])
    assert client.post(url, body, format="json").status_code == 404
    # Prove the original capability is valid again before checking expiry alone.
    lead.continuation_nonce = original_nonce
    lead.save(update_fields=["continuation_nonce"])
    assert client.post(url, body, format="json").status_code == 200
    lead.continuation_expires_at = timezone.now() - timedelta(seconds=1)
    lead.save(update_fields=["continuation_expires_at"])
    assert client.post(url, body, format="json").status_code == 404


def test_inquiry_to_multichild_application_preserves_source_and_real_times(school):
    campaign = MarketingCampaign.objects.create(school=school, name="Fall visits", status="active")
    receipt = _capture(school, campaign_id=str(campaign.id)).data
    lead = MarketingLead.objects.get(id=receipt["inquiry_id"])
    lead.inquiry_received_at = timezone.now() - timedelta(days=3)
    lead.save(update_fields=["inquiry_received_at"])
    client = APIClient()
    assert client.post(f"{URL}{lead.id}/start/", {"school_id": str(school.id), "continuation_token": receipt["continuation_token"]}, format="json").status_code == 200
    lead.refresh_from_db()
    first = client.post("/api/v1/admissions/submit/", _application_payload(school, receipt), format="json", HTTP_X_SCHOOL_ID=str(school.id))
    assert first.status_code == 201, first.data
    cache.clear()
    replay = client.post("/api/v1/admissions/submit/", _application_payload(school, receipt), format="json", HTTP_X_SCHOOL_ID=str(school.id), HTTP_IDEMPOTENCY_KEY=str(uuid.uuid4()))
    assert replay.status_code == 200 and replay["X-Idempotent-Replay"] == "true"
    assert replay.data["application_ids"] == first.data["application_ids"]
    assert Household.objects.count() == 1 and MarketingLead.objects.count() == 1
    assert Application.objects.count() == Applicant.objects.count() == 2
    lead.refresh_from_db()
    assert lead.applications.count() == 2 and lead.campaign == campaign
    assert lead.stage == "application_submitted" and lead.first_source == "instagram"
    for app in lead.applications.all():
        assert app.applicants.get().source == "instagram"
        assert app.applicants.get().flags["source_attribution"]["utm_campaign"] == "fall-open-house"
        assert app.events.get(event_type="inquiry_created").created_at == lead.inquiry_received_at
        assert app.events.get(event_type="application_started").created_at == lead.application_started_at
    assert "family" not in lead.submission_receipt and "reviewer_summary" not in lead.submission_receipt


def test_bad_application_capability_never_falls_back_to_new_household(school):
    receipt = _capture(school).data
    payload = _application_payload(school, receipt)
    payload["continuation_token"] = "invalid"
    response = APIClient().post("/api/v1/admissions/submit/", payload, format="json", HTTP_X_SCHOOL_ID=str(school.id))
    assert response.status_code == 404
    assert Application.objects.count() == Household.objects.count() == 0


def test_staff_queue_requires_scope_and_records_real_follow_up(school):
    receipt = _capture(school).data
    lead = MarketingLead.objects.get(id=receipt["inquiry_id"])
    assert lead.assigned_to_user_id is None
    client = APIClient()
    assert client.get(URL).status_code == 400  # Protected tenant middleware still applies.
    assert client.get(URL, HTTP_X_SCHOOL_ID=str(school.id)).status_code == 403
    reader = _staff(school, edit=False)
    client.force_authenticate(user=reader)
    queue = client.get(URL, HTTP_X_SCHOOL_ID=str(school.id))
    assert queue.status_code == 200 and not queue.data["can_edit"]
    assert "continuation_nonce" not in queue.data["results"][0]
    assert "submission_receipt" not in queue.data["results"][0]
    update_url = f"{URL}{lead.id}/"
    assert client.patch(update_url, {"stage": "tour_scheduled"}, format="json", HTTP_X_SCHOOL_ID=str(school.id)).status_code == 403
    editor = _staff(school)
    client.force_authenticate(user=editor)
    due = (timezone.now() + timedelta(days=2)).isoformat()
    response = client.patch(update_url, {"assigned_to_user_id": str(editor.id), "next_follow_up_at": due, "stage": "tour_scheduled", "touchpoint": {"channel": "phone", "summary": "Family selected a campus visit date."}}, format="json", HTTP_X_SCHOOL_ID=str(school.id))
    assert response.status_code == 200, response.data
    lead.refresh_from_db()
    assert lead.stage == "tour_scheduled" and lead.last_touch_at
    assert lead.assigned_to_user_id == editor.id
    assert lead.touchpoints.filter(channel="phone").count() == 1
    assert client.patch(update_url, {"stage": "enrolled"}, format="json", HTTP_X_SCHOOL_ID=str(school.id)).status_code == 400
    assert client.patch(update_url, {"family_follow_up_enabled": True}, format="json", HTTP_X_SCHOOL_ID=str(school.id)).status_code == 400
    other = School.objects.create(name="Other staff school")
    other_editor = _staff(other)
    assert client.patch(update_url, {"assigned_to_user_id": str(other_editor.id)}, format="json", HTTP_X_SCHOOL_ID=str(school.id)).status_code == 400
    assert client.get(URL, HTTP_X_SCHOOL_ID=str(other.id)).status_code in (403, 404)


def test_staff_duplicates_are_school_scoped_and_malformed_links_are_hidden(school):
    first, second = _capture(school).data, _capture(school).data
    lead = MarketingLead.objects.get(id=first["inquiry_id"])
    other = School.objects.create(name="Other duplicates school")
    foreign = _capture(other).data
    household = Household.objects.create(school_id=other.id, name="Other family")
    app = Application.objects.create(school_id=other.id, household=household)
    with pytest.raises(ValidationError), transaction.atomic():
        lead.applications.add(app)
    # Simulate a preexisting corrupt row to verify the serializer's separate read guard.
    through = lead.applications.through
    table = connection.ops.quote_name(through._meta.db_table)
    with connection.cursor() as cursor:
        cursor.execute(f"INSERT INTO {table} (marketinglead_id, application_id) VALUES (%s, %s)", [
            through._meta.get_field(name).target_field.get_db_prep_value(value, connection)
            for name, value in (("marketinglead", lead.id), ("application", app.id))
        ])
    CampaignTouchpoint.objects.create(school=other, lead=lead, channel="phone", summary="Other school private note", occurred_at=timezone.now())
    client = APIClient()
    client.force_authenticate(user=_staff(school))
    response = client.get(URL, HTTP_X_SCHOOL_ID=str(school.id))
    row = next(row for row in response.data["results"] if row["id"] == str(lead.id))
    assert "duplicate_candidates" not in row
    assert "application_ids" not in row
    assert "notification_status" not in row
    assert "touchpoints" not in row
    detail = client.get(f"{URL}{lead.id}/", HTTP_X_SCHOOL_ID=str(school.id))
    assert detail.status_code == 200
    detail_row = detail.data
    assert {str(item["id"]) for item in detail_row["duplicate_candidates"]} == {second["inquiry_id"]}
    assert foreign["inquiry_id"] not in str(detail_row)
    assert detail_row["application_ids"] == []
    assert all(item["summary"] != "Other school private note" for item in detail_row["touchpoints"])
    other_detail = client.get(f"{URL}{foreign['inquiry_id']}/", HTTP_X_SCHOOL_ID=str(school.id))
    assert other_detail.status_code == 404


@pytest.mark.parametrize("source", ["social_media", "search_engine", "community_event", "instagram", "direct_mail_qr", "current_family", "friend_or_colleague"])
def test_source_category_does_not_invent_a_specific_channel(source):
    from applications.views_admissions import _normalize_source
    assert _normalize_source(source) == source


def test_staff_inquiry_list_database_queries_do_not_scale_per_family(school):
    from django.test.utils import CaptureQueriesContext

    reader = _staff(school, edit=False)
    client = APIClient()
    client.force_authenticate(user=reader)
    MarketingLead.objects.create(
        school=school, parent_name="Initial Family", email="initial@example.invalid",
        inquiry_received_at=timezone.now(),
    )
    with CaptureQueriesContext(connection) as small_queries:
        small = client.get(URL, HTTP_X_SCHOOL_ID=str(school.id))
    assert small.status_code == 200 and small.data["count"] == 1

    MarketingLead.objects.bulk_create([
        MarketingLead(school=school, parent_name=f"Additional Family {i}",
                      email=f"family-{i}@example.invalid", inquiry_received_at=timezone.now())
        for i in range(15)
    ])
    with CaptureQueriesContext(connection) as large_queries:
        large = client.get(URL, HTTP_X_SCHOOL_ID=str(school.id))
    assert large.status_code == 200 and large.data["count"] == 16
    assert len(large.data["results"]) == 16
    assert all("notification_status" not in lead and "touchpoints" not in lead
               and "duplicate_candidates" not in lead for lead in large.data["results"])
    assert len(large_queries) <= len(small_queries) + 2


def test_staff_inquiry_cursor_pages_reach_older_records_and_scope_school(school):
    client = APIClient()
    client.force_authenticate(user=_staff(school, edit=False))
    other = School.objects.create(name="Unrelated paging school")
    MarketingLead.objects.bulk_create([
        MarketingLead(school=school, parent_name=f"Inquiry Family {i:03d}",
                      email=f"page-{i}@example.invalid",
                      inquiry_received_at=timezone.now(), stage="inquiry")
        for i in range(102)
    ])
    MarketingLead.objects.create(school=other, parent_name="Private inquiry",
                                 email="private@example.invalid",
                                 inquiry_received_at=timezone.now(), stage="inquiry")
    first = client.get(URL, {"stage": "all"}, HTTP_X_SCHOOL_ID=str(school.id))
    assert first.status_code == 200 and len(first.data["results"]) == 100
    assert first.data["page_size"] == 100 and first.data["count"] == 102
    token = first.data["next_cursor"]
    assert token
    second = client.get(URL, {"stage": "all", "cursor": token},
                        HTTP_X_SCHOOL_ID=str(school.id))
    assert second.status_code == 200 and len(second.data["results"]) == 2
    assert second.data["next_cursor"] is None
    rows = first.data["results"] + second.data["results"]
    assert len({row["id"] for row in rows}) == 102
    assert all(row["parent_name"] != "Private inquiry" for row in rows)
    for params in (
        {"stage": "all", "cursor": token + "forged"},
        {"stage": "inquiry", "cursor": token},
        {"stage": "all", "limit": "0"},
        {"stage": "all", "limit": "101"},
        {"stage": "all", "limit": "not-a-number"},
    ):
        assert client.get(URL, params, HTTP_X_SCHOOL_ID=str(school.id)).status_code == 400
    foreign = APIClient()
    foreign.force_authenticate(user=_staff(other, edit=False))
    assert foreign.get(URL, {"stage": "all", "cursor": token},
                       HTTP_X_SCHOOL_ID=str(other.id)).status_code == 400


def test_staff_cursor_paging_is_deterministic_on_tied_due_dates(school):
    client = APIClient()
    client.force_authenticate(user=_staff(school, edit=False))
    for i in range(7):
        MarketingLead.objects.create(school=school, parent_name=f"Family {i}",
                                     email=f"family-{i}@example.invalid",
                                     inquiry_received_at=timezone.now(), stage="inquiry")
    seen = []
    token = None
    for _ in range(4):
        params = {"stage": "all", "limit": "2"}
        if token:
            params["cursor"] = token
        response = client.get(URL, params, HTTP_X_SCHOOL_ID=str(school.id))
        assert response.status_code == 200
        seen.extend(row["id"] for row in response.data["results"])
        token = response.data["next_cursor"]
        if not token:
            break
    assert len(seen) == len(set(seen)) == 7


def test_inquiry_detail_requires_school_view_authority_without_mutation(school):
    lead = MarketingLead.objects.create(
        school=school, parent_name="Authorized Family", email="authorized@example.invalid",
        inquiry_received_at=timezone.now(), stage="inquiry",
    )
    other_school = School.objects.create(name="Other details school")
    foreign = MarketingLead.objects.create(
        school=other_school, parent_name="Private Family", email="private@example.invalid",
        inquiry_received_at=timezone.now(), stage="inquiry",
    )
    client = APIClient()
    client.force_authenticate(user=_staff(school, edit=False))
    before = CampaignTouchpoint.objects.filter(school=school, lead=lead).count()
    detail = client.get(f"{URL}{lead.id}/", HTTP_X_SCHOOL_ID=str(school.id))
    assert detail.status_code == 200
    assert detail["Cache-Control"] == "no-store"
    assert detail.data["id"] == str(lead.id)
    assert {"application_ids", "duplicate_candidates", "touchpoints", "notification_status"} <= set(detail.data)
    assert client.patch(
        f"{URL}{lead.id}/", {"stage": "lost"}, format="json",
        HTTP_X_SCHOOL_ID=str(school.id),
    ).status_code == 403
    assert client.get(f"{URL}{foreign.id}/", HTTP_X_SCHOOL_ID=str(school.id)).status_code == 404
    assert CampaignTouchpoint.objects.filter(school=school, lead=lead).count() == before
    lead.refresh_from_db()
    assert lead.stage == "inquiry"

    client.force_authenticate(user=_staff(other_school, edit=False))
    assert client.get(f"{URL}{lead.id}/", HTTP_X_SCHOOL_ID=str(school.id)).status_code == 403


def test_inquiry_cursor_preserves_due_date_and_null_last_order(school):
    client = APIClient()
    client.force_authenticate(user=_staff(school, edit=False))
    base_due = timezone.now() + timedelta(days=1)
    leads = {}
    for name, due in (
        ("no_due", None),
        ("third", base_due + timedelta(days=3)),
        ("first", base_due + timedelta(days=1)),
        ("second", base_due + timedelta(days=2)),
    ):
        leads[name] = MarketingLead.objects.create(
            school=school, parent_name=name, email=f"{name}@example.invalid",
            inquiry_received_at=timezone.now(), stage="inquiry",
            next_follow_up_at=due,
        )
    seen = []
    cursor = None
    for _ in range(3):
        params = {"stage": "all", "limit": "2"}
        if cursor:
            params["cursor"] = cursor
        response = client.get(URL, params, HTTP_X_SCHOOL_ID=str(school.id))
        assert response.status_code == 200, response.data
        seen.extend(row["id"] for row in response.data["results"])
        cursor = response.data["next_cursor"]
        if not cursor:
            break
    assert seen == [str(leads[name].id) for name in ("first", "second", "third", "no_due")]

