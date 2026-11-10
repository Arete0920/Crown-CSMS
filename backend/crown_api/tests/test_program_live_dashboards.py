"""Synthetic database proof for read-only program summaries and disclosure gates."""
from datetime import date, datetime, timedelta, timezone as dt_timezone
from decimal import Decimal
from unittest.mock import Mock

import pytest
from django.db import DatabaseError
from django.urls import reverse
from rest_framework.test import APIClient, APIRequestFactory, force_authenticate

from aftercare.models import AftercareAttendance, AftercareEnrollment, AftercareProgramConfig
from core.models import CrownPermission, RolePermission, School, UserAccount, UserRole
from crown_api.dashboards import program_live_payloads as live, views
from crown_api.dashboards.models import DashboardSnapshot
from crown_api.dashboards.payload_contract import build_dashboard_payload, validate_dashboard_payload
from crown_api.jwt_utils import build_access_token
from households.models import Household, Student
from ledger.models import Charge, LedgerAccount, Payment
from summer_camp.models import (
    SummerCampAttendance, SummerCampBillingLedgerLink, SummerCampEnrollment,
    SummerCampIncident, SummerCampProgram, SummerCampProgramConfig, SummerCampSession,
)

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def program_settings(settings):
    settings.TENANT_HEADER_REQUIRED = True
    settings.CROWN_ENV = "production"
    settings.CROWN_DEV_OPEN_API = False
NOW = datetime(2026, 11, 1, 3, 30, tzinfo=dt_timezone.utc)  # Oct 31 in New York
KEYS = list(live.PROGRAM_PERMISSIONS)


def url(key):
    return f"/api/v1/dashboards/{key}/summary"


def client(user=None):
    result = APIClient(SERVER_PORT="443", **{"wsgi.url_scheme": "https"})
    if user:
        result.force_login(user)
    return result


def bearer_client(user, school_claim):
    token = build_access_token(user_id=str(user.id), email=user.email,
        role="PROGRAM_READER_TEST", school_id=school_claim)
    api = client()
    api.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    return api


def actor(school, *, grants=True, **flags):
    name = f"operator-{UserAccount.objects.count()}"
    user = UserAccount.objects.create_user(username=name, email=f"{name}@example.invalid", school=school, **flags)
    if grants:
        UserRole.objects.create(user=user, school=school, role_code="PROGRAM_READER_TEST")
    return user


def child(school, suffix="A"):
    household = Household.objects.create(school_id=school.id, name=f"Synthetic private household {suffix}")
    return Student.objects.create(school_id=school.id, household=household,
                                  first_name=f"Synthetic private child {suffix}", last_name="Fixture")


@pytest.fixture
def school(monkeypatch):
    monkeypatch.setattr(live.timezone, "now", lambda: NOW)
    school = School.objects.create(name="Synthetic program school", timezone="America/New_York")
    SummerCampProgramConfig.objects.create(school=school)
    AftercareProgramConfig.objects.create(school_fk=school)
    for code in live.PROGRAM_PERMISSIONS.values():
        grant, _ = CrownPermission.objects.get_or_create(code=code)
        RolePermission.objects.get_or_create(role_code="PROGRAM_READER_TEST", permission=grant)
    return school


def get(school, key, user=None):
    return client(user or actor(school)).get(url(key), HTTP_X_SCHOOL_ID=str(school.id))


def metrics(response):
    assert response.status_code == 200, response.content
    payload = response.json()
    assert validate_dashboard_payload(payload)
    return {row["label"]: row["value"] for row in payload["metrics"]}


def session(school, suffix="A"):
    program, _ = SummerCampProgram.objects.get_or_create(school=school, name="Synthetic Camp")
    return SummerCampSession.objects.create(school=school, program=program, name=suffix,
        start_date=date(2026, 10, 1), end_date=date(2026, 11, 30), start_time="08:00", end_time="15:00")


def camp_enrollment(school, student, camp_session=None, **kwargs):
    return SummerCampEnrollment.objects.create(school=school, student=student,
        session=camp_session or session(school), **kwargs)


def care_enrollment(school, student, care_session, **kwargs):
    return AftercareEnrollment.objects.create(school_fk=school, student_fk=student,
        care_session=care_session, start_date=date(2026, 10, 1), billing_model="FLAT_MONTHLY", **kwargs)


@pytest.mark.parametrize("key", KEYS)
def test_authorized_empty_configured_database_is_real_zero_with_complete_provenance(school, key):
    response = get(school, key)
    values = metrics(response)
    meta = response.json()["meta"]
    assert meta["served_from"] == "live_db"
    assert meta["school_id"] == str(school.id)
    assert datetime.fromisoformat(meta["observed_at"]).utcoffset() is not None
    assert "local-day=[2026-10-31T00:00:00-04:00,2026-11-01T00:00:00-04:00)" in meta["aggregation_window"]
    assert "live_certified" not in meta
    assert values["Registered Campers" if key == "summer-camp" else "Enrolled Students"] == "0"
    assert values["Settled Camp Receipts" if key == "summer-camp" else "Settled Care Receipts"] == "Not available"
    assert response.json()["queue"] == response.json()["alerts"] == []


@pytest.mark.parametrize("key", KEYS)
def test_legacy_alias_uses_the_same_permission_and_live_contract(school, key):
    alias = reverse("dashboard-summary", kwargs={"dashboard_key": key})
    allowed = client(actor(school)).get(alias, HTTP_X_SCHOOL_ID=str(school.id))
    assert allowed.status_code == 200
    assert allowed.json()["meta"]["served_from"] == "live_db"
    denied = client(actor(school, grants=False)).get(alias, HTTP_X_SCHOOL_ID=str(school.id))
    assert denied.status_code == 403


@pytest.mark.parametrize("key", KEYS)
def test_dev_open_and_sample_flags_do_not_bypass_program_grants(school, key, settings):
    settings.CROWN_ENV = "development"
    settings.CROWN_DEV_OPEN_API = True
    settings.CROWN_ALLOW_SAMPLE_DASHBOARD_PAYLOADS = True
    assert client().get(url(key), HTTP_X_SCHOOL_ID=str(school.id)).status_code == 401
    assert get(school, key, actor(school, grants=False)).status_code == 403
    assert get(school, key).json()["meta"]["served_from"] == "live_db"


@pytest.mark.parametrize("key", KEYS)
@pytest.mark.parametrize("flags", [{}, {"is_staff": True}, {"is_staff": True, "is_superuser": True}])
def test_ungranted_users_staff_and_superusers_cannot_query_program_or_snapshot(school, key, flags, monkeypatch):
    builder = Mock(side_effect=AssertionError("Program data must not be queried"))
    monkeypatch.setattr(views, "build_program_live_payload", builder)
    response = get(school, key, actor(school, grants=False, **flags))
    assert response.status_code == 403
    builder.assert_not_called()


@pytest.mark.parametrize("key", KEYS)
def test_anonymous_inactive_and_wrong_program_grants_are_denied(school, key):
    assert client().get(url(key), HTTP_X_SCHOOL_ID=str(school.id)).status_code in (401, 403)
    inactive = actor(school, is_active=False)
    assert get(school, key, inactive).status_code in (401, 403)
    user = actor(school, grants=False)
    UserRole.objects.create(user=user, school=school, role_code="OTHER_PROGRAM_TEST")
    other_code = live.PROGRAM_PERMISSIONS[KEYS[1 - KEYS.index(key)]]
    RolePermission.objects.create(role_code="OTHER_PROGRAM_TEST", permission=CrownPermission.objects.get(code=other_code))
    assert get(school, key, user).status_code == 403


@pytest.mark.parametrize("key", KEYS)
@pytest.mark.parametrize("superuser", [False, True])
def test_foreign_school_even_with_target_grant_and_override_bit_is_rejected(school, key, superuser):
    foreign = School.objects.create(name="Synthetic foreign")
    user = actor(foreign, is_staff=superuser, is_superuser=superuser)
    UserRole.objects.create(user=user, school=school, role_code="PROGRAM_READER_TEST")
    assert get(school, key, user).status_code in (403, 404)


@pytest.mark.parametrize("key", KEYS)
def test_unambiguous_canonical_role_membership_can_bind_operator_without_direct_school(school, key):
    user = UserAccount.objects.create_user(username="role-bound", school=None)
    UserRole.objects.create(user=user, school=school, role_code="PROGRAM_READER_TEST")
    assert get(school, key, user).status_code == 200


@pytest.mark.parametrize("key", KEYS)
def test_ambiguous_role_membership_cannot_use_superuser_override_for_program_data(school, key):
    user = UserAccount.objects.create_user(username="ambiguous-operator", school=None,
                                          is_staff=True, is_superuser=True)
    foreign = School.objects.create(name="Synthetic ambiguous role school")
    for membership in (school, foreign):
        UserRole.objects.create(user=user, school=membership, role_code="PROGRAM_READER_TEST")
    assert get(school, key, user).status_code in (403, 404)


@pytest.mark.parametrize("key", KEYS)
@pytest.mark.parametrize("role_only", [False, True])
def test_native_bearer_accepts_current_persisted_operator_binding(school, key, role_only):
    if role_only:
        user = UserAccount.objects.create_user(username="bearer-role-bound", school=None)
        UserRole.objects.create(user=user, school=school, role_code="PROGRAM_READER_TEST")
    else:
        user = actor(school)
    api = bearer_client(user, None if role_only else str(school.id))
    response = api.get(url(key), HTTP_X_SCHOOL_ID=str(school.id))
    assert response.status_code == 200
    assert response.json()["meta"]["served_from"] == "live_db"


@pytest.mark.parametrize("key", KEYS)
@pytest.mark.parametrize("binding", ["foreign", "ambiguous", "revoked_grant"])
def test_native_bearer_school_and_role_claims_cannot_replace_persisted_authority(school, key, binding, monkeypatch):
    foreign = School.objects.create(name="Synthetic persisted token boundary")
    if binding == "foreign":
        user = actor(foreign, is_staff=True, is_superuser=True)
        UserRole.objects.create(user=user, school=school, role_code="PROGRAM_READER_TEST")
    elif binding == "ambiguous":
        user = UserAccount.objects.create_user(username="bearer-ambiguous", school=None,
                                               is_staff=True, is_superuser=True)
        for membership in (school, foreign):
            UserRole.objects.create(user=user, school=membership, role_code="PROGRAM_READER_TEST")
    else:
        user = actor(school, grants=False)
    builder = Mock(side_effect=AssertionError("Unpermitted bearer must not read program data"))
    monkeypatch.setattr(views, "build_program_live_payload", builder)
    api = bearer_client(user, str(school.id))
    assert api.get(url(key), HTTP_X_SCHOOL_ID=str(school.id)).status_code in (403, 404)
    builder.assert_not_called()


@pytest.mark.parametrize("key", KEYS)
def test_missing_invalid_conflicting_and_inactive_tenant_context(school, key):
    user = actor(school)
    api = client(user)
    assert api.get(url(key)).status_code == 400
    assert api.get(url(key), HTTP_X_SCHOOL_ID="invalid").status_code == 400
    foreign = School.objects.create(name="Synthetic conflicting school")
    assert api.get(url(key), HTTP_X_SCHOOL_ID=str(school.id), HTTP_X_CROWN_SCHOOL_ID=str(foreign.id)).status_code in (400, 404)
    # Direct view proof covers pre-bound context even without tenant middleware.
    request = APIRequestFactory().get(url(key), HTTP_X_SCHOOL_ID=str(school.id))
    force_authenticate(request, user=user)
    request.school = foreign
    assert views.DashboardSummaryView.as_view()(request, dashboard_key=key).status_code == 404
    school.is_active = False
    school.save(update_fields=["is_active"])
    assert api.get(url(key), HTTP_X_SCHOOL_ID=str(school.id)).status_code == 404


def test_camp_unique_children_registration_rows_and_actual_arrivals_are_distinct(school):
    student = child(school)
    camp_session = session(school)
    for _ in range(2):
        camp_enrollment(school, student, camp_session)  # historical duplicate
    second = session(school, "B")
    camp_enrollment(school, student, second)
    camp_enrollment(school, child(school, "waitlisted"), camp_session, status="WAITLISTED")
    for item in (camp_session, second):
        SummerCampAttendance.objects.create(school=school, session=item, student=student,
            date=date(2026, 10, 31), checkin_time=NOW - timedelta(hours=1))
    # Foreign records and future observations must not inflate this school's count.
    foreign = School.objects.create(name="Synthetic excluded foreign")
    camp_enrollment(foreign, child(foreign), session(foreign))
    response = get(school, "summer-camp")
    values = metrics(response)
    assert values["Registered Campers"] == "1"
    assert values["Registration Records"] == "3"
    assert values["Waitlisted Children"] == "1"
    assert values["Children Arrived Today"] == "1"
    assert values["Staffed Sessions"] == values["Transport Confirmed"] == "Not available"
    assert "Synthetic private" not in response.content.decode()


@pytest.mark.parametrize("sessions", [("AM",), ("PM",), ("AM", "PM")])
def test_care_enrollment_deduplicates_combined_children_without_fabricating_attendance(school, sessions):
    student = child(school)
    for care_session in sessions:
        care_enrollment(school, student, care_session)
    care_enrollment(school, student, sessions[0])  # duplicate enrollment is not a second child
    foreign = School.objects.create(name="Synthetic excluded care school")
    care_enrollment(foreign, child(foreign), "PM")
    values = metrics(get(school, "extended-care"))
    assert values["Enrolled Students"] == "1"
    assert values["AM Enrolled Students"] == str(int("AM" in sessions))
    assert values["PM Enrolled Students"] == str(int("PM" in sessions))
    assert values["Attendance Today"] == "0"  # enrollment is not attendance


def test_care_actual_am_pm_attendance_local_day_and_month_boundaries(school):
    student = child(school)
    for care_session in ("AM", "PM"):
        care_enrollment(school, student, care_session)
        AftercareAttendance.objects.create(school_fk=school, student_fk=student,
            care_session=care_session, date=date(2026, 10, 31), checkin_time=NOW - timedelta(hours=2))
    for stamp in (datetime(2026, 10, 1, 3, 59, tzinfo=dt_timezone.utc),
                  datetime(2026, 10, 1, 4, 0, tzinfo=dt_timezone.utc)):
        AftercareAttendance.objects.create(school_fk=school, student_fk=student, care_session="AM",
            date=stamp.astimezone(live.ZoneInfo(school.timezone)).date(), checkin_time=stamp)
    values = metrics(get(school, "extended-care"))
    assert values["Attendance Today"] == "1"
    assert values["AM Children Arrived Today"] == values["PM Children Arrived Today"] == "1"
    assert values["AM Attendance Sessions MTD"] == "2"
    assert values["PM Attendance Sessions MTD"] == "1"


def test_camp_incidents_use_local_month_and_exclude_future_records(school):
    camp_session = session(school)
    for stamp in (datetime(2026, 10, 1, 3, 59, tzinfo=dt_timezone.utc),
                  datetime(2026, 10, 1, 4, 0, tzinfo=dt_timezone.utc), NOW,
                  NOW + timedelta(minutes=1)):
        SummerCampIncident.objects.create(school=school, session=camp_session,
            created_at=stamp, description="Synthetic private incident")
    assert metrics(get(school, "summer-camp"))["Incidents MTD"] == "2"


@pytest.mark.parametrize("amount", [12500])
def test_assessed_obligations_are_verified_deduplicated_and_never_called_receipts(school, amount):
    student = child(school)
    enrollment = camp_enrollment(school, student, payment_status="PAID_IN_FULL")
    account = LedgerAccount.objects.create(school_id=school.id, household=student.household)
    charge = Charge.objects.create(school_id=school.id, account=account, amount=Decimal(amount) / 100, description="Synthetic Camp assessment")
    for _ in range(2):
        SummerCampBillingLedgerLink.objects.create(school=school, enrollment=enrollment,
            charge_id=str(charge.id), amount_cents=amount)
    Payment.objects.create(school_id=school.id, account=account, amount=Decimal("99"))
    values = metrics(get(school, "summer-camp"))
    assert values["Assessed Camp Charges"] == f"${Decimal(amount) / 100:,.2f}"
    assert values["Settled Camp Receipts"] == "Not available"


@pytest.mark.parametrize("charge_id,amount", [("", 0), ("not-a-charge", 0), ("", -1)])
def test_unverified_or_invalid_charge_values_never_become_zero(school, charge_id, amount):
    enrollment = camp_enrollment(school, child(school))
    SummerCampBillingLedgerLink.objects.create(school=school, enrollment=enrollment, charge_id=charge_id, amount_cents=amount)
    assert metrics(get(school, "summer-camp"))["Assessed Camp Charges"] == "Not available"


@pytest.mark.parametrize("key", KEYS)
@pytest.mark.parametrize("failure", ["query", "missing_config", "invalid_timezone", "missing_provenance", "missing_window", "foreign_scope", "naive_observation", "false_certification", "sample", "snapshot"])
def test_failure_never_falls_back_to_stored_or_sample_payload(school, key, failure, monkeypatch):
    DashboardSnapshot.objects.create(school_id=str(school.id), dashboard_key=key,
        payload=build_dashboard_payload(key, [{"label": "Private stale value", "value": "999"}], [], [], {}))
    if failure == "query":
        model = SummerCampProgramConfig if key == "summer-camp" else AftercareProgramConfig
        monkeypatch.setattr(model.objects, "filter", Mock(side_effect=DatabaseError("private query failure")))
    elif failure == "missing_config":
        (SummerCampProgramConfig.objects.filter(school=school) if key == "summer-camp"
         else AftercareProgramConfig.objects.filter(school_fk=school)).delete()
    elif failure == "invalid_timezone":
        school.timezone = "Invalid/School"
        school.save(update_fields=["timezone"])
    else:
        payload = live.build_program_live_payload(key, school)
        if failure == "missing_provenance":
            del payload["meta"]["observed_at"]
        elif failure == "missing_window":
            payload["meta"]["aggregation_window"] = " "
        elif failure == "foreign_scope":
            payload["meta"]["school_id"] = "foreign"
        elif failure == "naive_observation":
            payload["meta"]["observed_at"] = "2026-10-31T12:00:00"
        elif failure == "false_certification":
            payload["meta"]["live_certified"] = True
        else:
            payload["meta"]["served_from"] = failure
        monkeypatch.setattr(views, "build_program_live_payload", lambda *_args: payload)
    response = get(school, key)
    assert response.status_code == 503
    assert response.json()["code"] == "program_dashboard_unavailable"
    assert "999" not in response.content.decode()
    assert "private query" not in response.content.decode()


@pytest.mark.parametrize("key", KEYS)
def test_cross_school_child_links_fail_closed(school, key):
    foreign = School.objects.create(name="Synthetic corrupt child owner")
    student = child(foreign)
    if key == "summer-camp":
        camp_enrollment(school, student)
    else:
        care_enrollment(school, student, "AM")
    assert get(school, key).status_code == 503


@pytest.mark.parametrize("key", KEYS)
@pytest.mark.parametrize("minute", [59, 60])
def test_school_local_midnight_changes_the_actual_attendance_day(school, key, minute, monkeypatch):
    student = child(school)
    stamp = datetime(2026, 11, 1, 3, 0, tzinfo=dt_timezone.utc) + timedelta(minutes=minute)
    monkeypatch.setattr(live.timezone, "now", lambda: stamp)
    for day, arrival in ((date(2026, 10, 31), datetime(2026, 11, 1, 3, 59, tzinfo=dt_timezone.utc)),
                         (date(2026, 11, 1), datetime(2026, 11, 1, 4, 0, tzinfo=dt_timezone.utc))):
        if key == "summer-camp":
            # A scheduled registration alone never counts as an arrival.
            program_session = SummerCampSession.objects.filter(school=school).first() or session(school)
            SummerCampAttendance.objects.create(school=school, session=program_session,
                student=student, date=day, checkin_time=arrival)
        else:
            AftercareAttendance.objects.create(school_fk=school, student_fk=student,
                care_session="AM", date=day, checkin_time=arrival)
    response = get(school, key)
    assert metrics(response)["Children Arrived Today" if key == "summer-camp" else "Attendance Today"] == "1"
    assert f"local-day=[2026-{'10-31' if minute == 59 else '11-01'}T00:00:00-04:00" in response.json()["meta"]["aggregation_window"]


@pytest.mark.parametrize("corruption", ["negative", "mismatched_amount", "foreign_charge", "void_charge", "missing_charge", "wrong_household"])
def test_corrupt_ledger_link_never_becomes_a_verified_financial_zero(school, corruption):
    student = child(school)
    enrollment = camp_enrollment(school, student)
    owner = School.objects.create(name="Synthetic foreign finance") if corruption == "foreign_charge" else school
    household = child(owner, "finance").household if corruption in ("foreign_charge", "wrong_household") else student.household
    account = LedgerAccount.objects.create(school_id=owner.id, household=household)
    # A wrong household also fails even when its school matches.
    charge = Charge.objects.create(school_id=owner.id, account=account, amount=Decimal("10"),
        description="Synthetic charge", is_void=corruption == "void_charge")
    SummerCampBillingLedgerLink.objects.create(school=school, enrollment=enrollment,
        charge_id=str(charge.id) if corruption != "missing_charge" else str(student.id),
        amount_cents=-1 if corruption == "negative" else (999 if corruption == "mismatched_amount" else 1000))
    assert metrics(get(school, "summer-camp"))["Assessed Camp Charges"] == "Not available"
