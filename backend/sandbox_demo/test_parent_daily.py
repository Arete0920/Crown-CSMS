from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from uuid import uuid4

import pytest
from django.db import close_old_connections, connection
from django.test.utils import CaptureQueriesContext
from rest_framework.test import APIClient

from core.models import Student, StudentIdentityLink, UserAccount
from crown_api.models import AttendanceRecord, GradeRecord
from sandbox_demo.parent_daily import SandboxParentDailyError, parent_daily_state
from sandbox_demo.services import seed_heritage_flagship


pytestmark = pytest.mark.django_db(transaction=True)


def _user(email):
    return UserAccount.objects.get(username=email)


def test_parent_daily_work_returns_child_attendance_progress_comms_and_billing(settings):
    settings.CROWN_SANDBOX_ALLOW_OPEN_SESSION = True
    seed_heritage_flagship(reset=True)
    parent = _user("parent.reed@heritage.example.org")

    state = parent_daily_state(parent)
    assert state["child"]["name"] == "Jordan Reed"
    assert state["attendance"]
    attendance_row = state["attendance"][0]
    assert attendance_row["status"] == AttendanceRecord.STATUS_PRESENT
    assert attendance_row["section_id"]

    record = AttendanceRecord.objects.get(student_id=state["child"]["id"], date="2026-08-10")
    assert record.section_id is not None
    assert record.status == AttendanceRecord.STATUS_PRESENT
    assert not AttendanceRecord.objects.filter(
        student_id=state["child"]["id"],
        date="2026-08-10",
        section__isnull=True,
    ).exists()
    link = StudentIdentityLink.objects.get(core_student_id=state["child"]["id"])
    assert link.verification_status == StudentIdentityLink.STATUS_VERIFIED
    assert link.evidence_reference
    assert str(link.school_id) == str(parent.school_id)
    assert str(link.compatibility_student.school_id) == str(parent.school_id)

    assert state["progress"]
    assert state["progress"][0]["letter_grade"] == "A"
    assert state["communications"]
    assert state["billing"]["balance_cents"] > 0
    assert state["billing"]["external_payment_provider_enabled"] is False
    assert all(value is False for value in state["staff_controls"].values())

    with CaptureQueriesContext(connection) as captured:
        replay = parent_daily_state(parent)
    writes = [
        query["sql"].lstrip().split()[0].upper()
        for query in captured.captured_queries
        if query["sql"].lstrip().split()[0].upper()
        in {"INSERT", "UPDATE", "DELETE", "REPLACE"}
    ]
    assert writes == [], "An unchanged parent-state read must not rewrite fixtures"
    assert replay["child"]["id"] == state["child"]["id"]
    assert replay["attendance"] == state["attendance"]
    assert replay["billing"]["balance_cents"] == state["billing"]["balance_cents"]
    assert AttendanceRecord.objects.filter(
        student_id=state["child"]["id"],
        date="2026-08-10",
        section_id=record.section_id,
    ).count() == 1

    # Existing initialization/repair behavior must survive the read-only fast path.
    GradeRecord.objects.filter(student_id=state["child"]["id"]).update(score=0)
    StudentIdentityLink.objects.filter(core_student_id=state["child"]["id"]).update(
        verification_status=StudentIdentityLink.STATUS_PENDING,
    )
    repaired = parent_daily_state(parent)
    assert repaired["progress"][0]["score"] == "19.00"
    link.refresh_from_db()
    assert link.verification_status == StudentIdentityLink.STATUS_VERIFIED


def test_non_parent_persona_cannot_use_parent_daily_state(settings):
    settings.CROWN_SANDBOX_ALLOW_OPEN_SESSION = True
    seed_heritage_flagship(reset=True)
    teacher = _user("teacher.lower@heritage.example.org")
    with pytest.raises(SandboxParentDailyError, match="heritage_parent_required"):
        parent_daily_state(teacher)


def test_concurrent_warm_parent_requests_succeed_on_sqlite(settings):
    if connection.vendor != "sqlite":
        pytest.skip("SQLite local-demo read/write lock regression")
    settings.CROWN_SANDBOX_ALLOW_OPEN_SESSION = True
    seed_heritage_flagship(reset=True)
    parent = _user("parent.reed@heritage.example.org")
    expected_id = parent_daily_state(parent)["child"]["id"]
    gate = Barrier(2)
    table = Student._meta.db_table

    def read():
        close_old_connections()
        synchronized = False
        try:
            actor = UserAccount.objects.get(pk=parent.pk)

            def overlap_reads(execute, sql, params, many, context):
                nonlocal synchronized
                result = execute(sql, params, many, context)
                if (
                    not synchronized
                    and sql.lstrip().upper().startswith("SELECT")
                    and table in sql
                ):
                    synchronized = True
                    gate.wait(timeout=10)
                return result

            client = APIClient()
            client.force_authenticate(user=actor)
            with connection.execute_wrapper(overlap_reads):
                response = client.get("/api/v1/sandbox/parent/daily/")
            assert synchronized, "Both requests must overlap the student lookup"
            assert response.status_code == 200, response.content
            return response.json()["child"]["id"]
        finally:
            connection.close()

    with ThreadPoolExecutor(max_workers=2) as pool:
        requests = [pool.submit(read), pool.submit(read)]
        assert [request.result(timeout=20) for request in requests] == [expected_id, expected_id]


@pytest.mark.parametrize("boundary", ["closed_session", "foreign_school"])
def test_parent_daily_access_boundary(settings, boundary):
    settings.CROWN_SANDBOX_ALLOW_OPEN_SESSION = True
    seed_heritage_flagship(reset=True)
    parent = _user("parent.reed@heritage.example.org")
    if boundary == "closed_session":
        settings.CROWN_SANDBOX_ALLOW_OPEN_SESSION = False
        detail = "sandbox_open_session_required"
    else:
        parent.school_id = uuid4()
        detail = "heritage_school_required"
    with pytest.raises(SandboxParentDailyError, match=detail):
        parent_daily_state(parent)


def test_parent_daily_api_requires_authentication(settings):
    settings.CROWN_SANDBOX_ALLOW_OPEN_SESSION = True
    assert APIClient().get("/api/v1/sandbox/parent/daily/").status_code in {401, 403}
