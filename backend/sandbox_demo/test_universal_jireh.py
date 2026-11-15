"""Real Jireh application, offered-award and processor transactions; no live funds."""
from uuid import uuid4
import pytest
from django.core.management.base import CommandError
from rest_framework.test import APIClient
from aid.models import AidApplication, AidAward
from core.models import School, UserRole
from jireh_sgo.models import SGOFamilyIntake, SGOProcessorAssignment, SGOAward, SGOMembership
from sandbox_demo.test_universal_access import operator_secrets, login
from sandbox_demo.test_universal_presenter import local_runtime
from sandbox_demo.universal_demo import prepare_presenter
from sandbox_demo.universal_jireh import prepare_presenter_jireh

pytestmark = pytest.mark.django_db
BASE = "/api/v1/presenter/jireh/"


@pytest.fixture
def jireh(local_runtime, operator_secrets):
    from django.core.management import call_command
    from io import StringIO
    call_command("seed_permissions", stdout=StringIO())
    prepare_presenter(apply=True, enable_password_login=True)
    assert prepare_presenter_jireh()["mode"] == "PREFLIGHT"
    assert not SGOProcessorAssignment.objects.exists()
    return prepare_presenter_jireh(apply=True)


def test_parent_submits_canonical_aid_and_officer_commits_offered_award(jireh, operator_secrets):
    parent, _ = login("parent", operator_secrets)
    officer, _ = login("finance_director", operator_secrets)
    data = parent.get(BASE + "aid/family/").json()
    payload = {"fictional_acknowledged": True, "scenario": data["scenarios"][0]["id"],
        "household_size": 4, "academic_year_id": data["academic_years"][0]["id"],
        "student_ids": [data["students"][0]["id"]]}
    created = parent.post(BASE + "aid/family/", payload, format="json")
    assert created.status_code == 201, created.content
    application = AidApplication.objects.get(pk=created.json()["application"]["id"])
    assert application.status == AidApplication.STATUS_SUBMITTED
    assert application.financial_profile_id and application.submitted_at
    assert parent.post(BASE + "aid/family/", payload, format="json").status_code == 409
    for _ in range(2):
        assert str(parent.get(BASE + "aid/family/").json()["applications"][0]["id"]) == str(application.pk)
    overview = officer.get("/api/v1/aid/admin/overview/", {"academic_year_id": payload["academic_year_id"]})
    assert overview.status_code == 200, overview.content
    assert application.pk in [row["id"] for row in overview.json()["applications"]]
    wizard = "/api/v1/aid-wizard/sessions/"
    denied = parent.post(wizard, {}, format="json")
    assert denied.status_code == 403
    started = officer.post(wizard, {}, format="json")
    assert started.status_code == 201, started.content
    session = wizard + str(started.json()["session_id"]) + "/"
    for action, body in (("configure", {"aid_year": data["academic_years"][0]["name"]}),
        ("buckets", {"buckets": ["need"]}),
        ("awards", {"awards": [{"application_id": application.pk, "student_id": payload["student_ids"][0],
            "bucket": "need", "amount": "250.00", "rationale": "Fictional presenter case"}]}),
        ("commit", {"confirm": True})):
        response = officer.post(session + action + "/", body, format="json")
        assert response.status_code == 200, response.content
    award = AidAward.objects.get(aid_application=application)
    assert award.decision_status == AidAward.DECISION_OFFERED and award.ledger_entry_id is None
    assert award.awarded_cents == 25000
    approval = f"/api/v1/aid/admin/awards/{award.pk}/approve/"
    assert parent.post(approval, {}, format="json").status_code == 403
    for _ in range(2):
        response = officer.post(approval, {"reason": "Fictional noncash credit exercise"}, format="json")
        assert response.status_code == 200, response.content
    award.refresh_from_db()
    assert award.decision_status == AidAward.DECISION_ACCEPTED and award.ledger_entry_id
    from aid.models import AidBudgetTracker
    from core.models import LedgerEntry
    assert AidBudgetTracker.objects.get(school_id=jireh["school_id"], academic_year=application.academic_year,
        bucket=award.award_type).awarded_cents == 25000
    assert LedgerEntry.objects.filter(pk=award.ledger_entry_id, school_id=jireh["school_id"]).count() == 1
    for _ in range(2):
        result = parent.get("/api/v1/aid/family/status/", {"student_id": payload["student_ids"][0],
            "academic_year_id": payload["academic_year_id"]})
        assert result.status_code == 200, result.content
        assert str(result.json()["awards"][0]["id"]) == str(award.pk)


def test_sgo_submit_retry_processor_correction_parent_resubmit_persists(jireh, operator_secrets):
    parent, _ = login("parent", operator_secrets)
    officer, tokens = login("finance_director", operator_secrets)
    programs = parent.get(BASE + "sgo/family/programs/").json()["programs"]
    assert len(programs) == 2
    program = programs[0]
    body = {"program_id": program["id"], "grade_level": "7", "consent": True,
        "consent_version": program["consent_version"], "submission_key": str(uuid4())}
    created = parent.post(BASE + "sgo/family/submit/", body, format="json")
    assert created.status_code == 201, created.content
    assert parent.post(BASE + "sgo/family/submit/", body, format="json").status_code == 200
    app = created.json()["application"]
    queue = BASE + f'sgo/processor/programs/{program["id"]}/queue/'
    assert officer.get(queue).json()["applications"][0]["id"] == app["id"]
    assert parent.get(queue).status_code == 404
    requested = officer.post(BASE + f'sgo/processor/applications/{app["id"]}/request-correction/', {
        "expected_revision": app["revision"], "reason": "GRADE_UNVERIFIED", "request_key": str(uuid4())}, format="json")
    assert requested.status_code == 200, requested.content
    revision = requested.json()["application"]["revision"]
    corrected = parent.post(BASE + f'sgo/family/applications/{app["id"]}/correct/', {
        "expected_revision": revision, "grade_level": "8", "correction_key": str(uuid4())}, format="json")
    assert corrected.status_code == 200, corrected.content
    for _ in range(2):
        readback = parent.get(BASE + f'sgo/family/applications/{app["id"]}/').json()["application"]
        assert readback["grade_level"] == "8"
    assert SGOFamilyIntake.objects.get(application_id=app["id"]).grade_level == "8"
    assert not SGOAward.objects.exists() and not SGOMembership.objects.exists()
    foreign = School.objects.create(name="Other invented Jireh tenant")
    officer.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}", HTTP_X_SCHOOL_ID=str(foreign.pk))
    assert officer.get(queue).status_code == 404


def test_jireh_roles_runtime_and_repeat_fail_closed(jireh, operator_secrets, settings):
    parent, _ = login("parent", operator_secrets)
    teacher, _ = login("teacher", operator_secrets)
    assert teacher.get(BASE + "aid/family/").status_code == 404
    assert APIClient().get(BASE + "aid/family/", HTTP_X_SCHOOL_ID=jireh["school_id"]).status_code == 401
    assert parent.get(BASE + "aid/family/", {"family_id": str(uuid4())}).status_code == 400
    UserRole.objects.filter(school_id=jireh["school_id"], role_code="PARENT").delete()
    assert parent.get(BASE + "aid/family/").status_code == 404
    settings.CROWN_ENV = "dev"
    assert parent.get(BASE + "aid/family/").status_code == 404
    with pytest.raises(CommandError):
        prepare_presenter_jireh(apply=True)
