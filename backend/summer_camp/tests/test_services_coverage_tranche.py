from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from summer_camp import services


pytestmark = pytest.mark.django_db


def test_config_program_and_session_services(monkeypatch):
    config = object()
    config_manager = MagicMock()
    config_manager.get_or_create.return_value = (config, True)
    monkeypatch.setattr(services.SummerCampProgramConfig, "objects", config_manager)
    assert services.ensure_config("school-1") is config

    program_manager = MagicMock()
    created_program = object()
    program_manager.create.return_value = created_program
    program = SimpleNamespace(name="Old", save=MagicMock())
    program_manager.get.return_value = program
    monkeypatch.setattr(services.SummerCampProgram, "objects", program_manager)
    assert services.create_program("school-1", {"name": "Camp"}) is created_program
    assert services.update_program("school-1", "program-1", {"name": "New"}) is program
    assert program.name == "New"
    program.save.assert_called_once_with()

    session_manager = MagicMock()
    created_session = object()
    session_manager.create.return_value = created_session
    session = SimpleNamespace(capacity=10, save=MagicMock())
    session_manager.get.return_value = session
    monkeypatch.setattr(services.SummerCampSession, "objects", session_manager)
    assert services.create_session("school-1", {"capacity": 20}) is created_session
    assert services.update_session("school-1", "session-1", {"capacity": 25}) is session
    assert session.capacity == 25


def test_capacity_and_waitlist_position(monkeypatch):
    monkeypatch.setattr(
        services.SummerCampSession,
        "objects",
        SimpleNamespace(get=lambda **kwargs: SimpleNamespace(capacity=3)),
    )
    chain = MagicMock()
    chain.values.return_value.annotate.return_value = [
        {"status": "REGISTERED", "total": 2},
        {"status": "WAITLISTED", "total": 4},
    ]
    manager = MagicMock()
    manager.filter.return_value = chain
    monkeypatch.setattr(services.SummerCampEnrollment, "objects", manager)
    assert services.compute_session_capacity("school-1", "session-1") == services.CapacityState(2, 4, True)

    aggregate = MagicMock()
    aggregate.aggregate.return_value = {"max_pos": 7}
    manager.filter.return_value = aggregate
    assert services._next_waitlist_position("school-1", "session-1") == 8


def test_enroll_camper_registers_and_waitlists(monkeypatch):
    manager = MagicMock()
    enrollment = SimpleNamespace(id="enrollment-1")
    manager.create.return_value = enrollment
    monkeypatch.setattr(services.SummerCampEnrollment, "objects", manager)
    readiness = MagicMock()
    monkeypatch.setattr(services, "compute_camper_readiness", readiness)

    monkeypatch.setattr(
        services,
        "compute_session_capacity",
        lambda school_id, session_id: services.CapacityState(1, 0, True),
    )
    assert services.enroll_camper("school-1", "student-1", "session-1", {}) is enrollment
    assert manager.create.call_args.kwargs["status"] == "REGISTERED"
    assert manager.create.call_args.kwargs["waitlist_position"] is None

    monkeypatch.setattr(
        services,
        "compute_session_capacity",
        lambda school_id, session_id: services.CapacityState(10, 2, False),
    )
    monkeypatch.setattr(services, "_next_waitlist_position", lambda school_id, session_id: 3)
    services.enroll_camper("school-1", "student-1", "session-1", {})
    assert manager.create.call_args.kwargs["status"] == "WAITLISTED"
    assert manager.create.call_args.kwargs["waitlist_position"] == 3


def test_cancel_and_promote_waitlist(monkeypatch):
    enrollment = SimpleNamespace(
        status="REGISTERED",
        readiness_status="READY",
        readiness_blockers=[],
        session_id="session-1",
        save=MagicMock(),
    )
    manager = MagicMock()
    manager.select_for_update.return_value.get.return_value = enrollment
    monkeypatch.setattr(services.SummerCampEnrollment, "objects", manager)
    real_move_waitlist = services.move_waitlist_if_capacity_available
    move = MagicMock()
    monkeypatch.setattr(services, "move_waitlist_if_capacity_available", move)
    assert services.cancel_enrollment("school-1", "enrollment-1", "parent request") is enrollment
    assert enrollment.readiness_blockers == ["CANCELLED", "REASON:parent request"]
    move.assert_called_once_with("school-1", "session-1")
    monkeypatch.setattr(services, "move_waitlist_if_capacity_available", real_move_waitlist)

    promoted = SimpleNamespace(id="enrollment-2", status="WAITLISTED", waitlist_position=1, save=MagicMock())
    ordered = MagicMock()
    ordered.first.return_value = promoted
    filtered = MagicMock()
    filtered.order_by.return_value = ordered
    manager.select_for_update.return_value.filter.return_value = filtered
    monkeypatch.setattr(
        services,
        "compute_session_capacity",
        lambda school_id, session_id: services.CapacityState(9, 1, True),
    )
    readiness = MagicMock()
    monkeypatch.setattr(services, "compute_camper_readiness", readiness)
    assert services.move_waitlist_if_capacity_available("school-1", "session-1") is promoted
    assert promoted.status == "REGISTERED"
    assert promoted.waitlist_position is None


def test_form_and_staff_ratio_status(monkeypatch):
    enrollment = SimpleNamespace(session_id="session-1", form_status="IN_PROGRESS")
    enrollment_manager = MagicMock()
    enrollment_manager.get.return_value = enrollment
    enrollment_manager.filter.return_value.count.return_value = 11
    monkeypatch.setattr(services.SummerCampEnrollment, "objects", enrollment_manager)

    form_manager = MagicMock()
    form_manager.filter.return_value.count.return_value = 0
    monkeypatch.setattr(services.SummerCampFormRequirement, "objects", form_manager)
    assert services.compute_form_status("school-1", "enrollment-1") == "COMPLETE"
    form_manager.filter.return_value.count.return_value = 2
    assert services.compute_form_status("school-1", "enrollment-1") == "IN_PROGRESS"

    monkeypatch.setattr(
        services.SummerCampSession,
        "objects",
        SimpleNamespace(get=lambda **kwargs: SimpleNamespace(id="session-1")),
    )
    monkeypatch.setattr(services, "ensure_config", lambda school_id: SimpleNamespace(default_staff_ratio=5))
    staff_manager = MagicMock()
    staff_manager.filter.return_value.count.return_value = 2
    monkeypatch.setattr(services.SummerCampStaffAssignment, "objects", staff_manager)
    result = services.compute_staff_ratio_status("school-1", "session-1")
    assert result["required_staff"] == 3
    assert result["coverage_status"] == "GAP"


def test_readiness_blockers_and_ready_state(monkeypatch):
    enrollment = SimpleNamespace(
        id="enrollment-1",
        session_id="session-1",
        status="WAITLISTED",
        balance_due_cents=100,
        payment_required_before_attendance=True,
        health_status="NEEDS_REVIEW",
        readiness_status="",
        readiness_blockers=[],
        save=MagicMock(),
    )
    manager = MagicMock()
    manager.get.return_value = enrollment
    monkeypatch.setattr(services.SummerCampEnrollment, "objects", manager)
    monkeypatch.setattr(services, "compute_form_status", lambda school_id, enrollment_id: "MISSING")
    pickup_manager = MagicMock()
    pickup_manager.filter.return_value.exists.return_value = False
    monkeypatch.setattr(services.SummerCampPickupContact, "objects", pickup_manager)
    monkeypatch.setattr(services, "compute_staff_ratio_status", lambda school_id, session_id: {"coverage_status": "GAP"})
    result = services.compute_camper_readiness("school-1", "enrollment-1")
    assert result["status"] == "BLOCKED"
    assert result["blockers"] == [
        "WAITLISTED",
        "MISSING_PAYMENT",
        "MISSING_FORMS",
        "HEALTH_REVIEW_REQUIRED",
        "PICKUP_CONTACT_MISSING",
        "STAFF_REVIEW_REQUIRED",
    ]

    enrollment.status = "REGISTERED"
    enrollment.balance_due_cents = 0
    enrollment.health_status = "APPROVED"
    monkeypatch.setattr(services, "compute_form_status", lambda school_id, enrollment_id: "COMPLETE")
    pickup_manager.filter.return_value.exists.return_value = True
    monkeypatch.setattr(services, "compute_staff_ratio_status", lambda school_id, session_id: {"coverage_status": "OK"})
    assert services.compute_camper_readiness("school-1", "enrollment-1") == {"status": "READY", "blockers": []}


def test_parent_student_summary(monkeypatch):
    enrollment = SimpleNamespace(
        id="enrollment-1",
        session_id="session-1",
        session=SimpleNamespace(name="STEM Camp"),
        status="REGISTERED",
        form_status="COMPLETE",
        payment_status="PAID",
        health_status="APPROVED",
        pickup_status="VERIFIED",
        readiness_status="READY",
        waitlist_position=None,
        balance_due_cents=0,
    )
    queryset = MagicMock()
    queryset.select_related.return_value = [enrollment]
    manager = MagicMock()
    manager.filter.return_value = queryset
    monkeypatch.setattr(services.SummerCampEnrollment, "objects", manager)
    result = services.parent_student_summary("school-1", "student-1")
    assert result[0]["session_name"] == "STEM Camp"
    assert result[0]["readiness_status"] == "READY"
