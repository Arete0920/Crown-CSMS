"""Module 018 - Classroom & Room Management evidence.

This proof covers the current Module 018 production boundary:

1. Room assignments are tenant-scoped by school.
2. Room capacity validation detects over-capacity placements.
3. Missing and inactive rooms are not silently accepted.
4. Room time conflicts are detected by term, room, day, and time overlap.
5. Non-overlapping assignments, separate rooms, and cross-tenant assignments are ignored.
"""

from uuid import uuid4

import pytest

from academics.room_management import (
    Classroom,
    RoomAssignment,
    normalize_days,
    room_capacity_violations,
    room_schedule_conflicts,
    validate_room_assignment,
)


MODULE_ID = 18
MODULE_NAME = "Classroom & Room Management"


def _room(school_id, room_id="room-a", code="A-101", capacity=24, active=True):
    return Classroom(
        school_id=school_id,
        room_id=room_id,
        code=code,
        capacity=capacity,
        active=active,
    )


def _assignment(
    school_id,
    assignment_id="assign-a",
    section_id="section-a",
    room_id="room-a",
    term="2026-FALL",
    days=("MO", "WE"),
    start=480,
    end=530,
    enrollment=20,
):
    return RoomAssignment(
        school_id=school_id,
        assignment_id=assignment_id,
        section_id=section_id,
        room_id=room_id,
        term=term,
        meeting_days=days,
        start_minute=start,
        end_minute=end,
        expected_enrollment=enrollment,
    )


def test_module_metadata_is_present():
    assert MODULE_ID == 18
    assert MODULE_NAME == "Classroom & Room Management"


def test_normalize_days_deduplicates_and_rejects_invalid_codes():
    assert normalize_days(("mo", "MO", "we")) == ("MO", "WE")

    with pytest.raises(ValueError, match="Invalid meeting day"):
        normalize_days(("MO", "XX"))


def test_room_capacity_violations_detect_capacity_missing_and_inactive_rooms():
    school_id = uuid4()
    rooms = [
        _room(school_id, room_id="room-small", code="S-101", capacity=18),
        _room(school_id, room_id="room-inactive", code="I-101", capacity=30, active=False),
    ]
    assignments = [
        _assignment(
            school_id,
            assignment_id="capacity-over",
            section_id="section-over",
            room_id="room-small",
            enrollment=22,
        ),
        _assignment(
            school_id,
            assignment_id="missing-room",
            section_id="section-missing",
            room_id="room-missing",
            enrollment=12,
        ),
        _assignment(
            school_id,
            assignment_id="inactive-room",
            section_id="section-inactive",
            room_id="room-inactive",
            enrollment=12,
        ),
    ]

    violations = room_capacity_violations(school_id, rooms, assignments, term="2026-FALL")
    by_assignment = {row["assignment_id"]: row for row in violations}

    assert by_assignment["capacity-over"]["violation_type"] == "CAPACITY_EXCEEDED"
    assert by_assignment["capacity-over"]["expected_enrollment"] == 22
    assert by_assignment["capacity-over"]["capacity"] == 18

    assert by_assignment["missing-room"]["violation_type"] == "ROOM_NOT_FOUND"
    assert by_assignment["missing-room"]["capacity"] is None

    assert by_assignment["inactive-room"]["violation_type"] == "ROOM_INACTIVE"


def test_room_capacity_violations_are_tenant_scoped():
    school_a = uuid4()
    school_b = uuid4()
    rooms = [
        _room(school_a, room_id="shared-code", code="A-101", capacity=10),
        _room(school_b, room_id="shared-code", code="B-101", capacity=40),
    ]
    assignments = [
        _assignment(school_a, assignment_id="tenant-a", room_id="shared-code", enrollment=12),
        _assignment(school_b, assignment_id="tenant-b", room_id="shared-code", enrollment=35),
    ]

    violations = room_capacity_violations(school_a, rooms, assignments)

    assert [row["assignment_id"] for row in violations] == ["tenant-a"]
    assert violations[0]["room_code"] == "A-101"


def test_room_schedule_conflicts_detect_same_room_day_time_overlap():
    school_id = uuid4()
    assignments = [
        _assignment(
            school_id,
            assignment_id="left",
            section_id="biology-1",
            room_id="lab-1",
            days=("MO", "WE"),
            start=540,
            end=600,
        ),
        _assignment(
            school_id,
            assignment_id="right",
            section_id="chemistry-1",
            room_id="lab-1",
            days=("WE", "FR"),
            start=570,
            end=630,
        ),
    ]

    conflicts = room_schedule_conflicts(school_id, assignments, term="2026-FALL")

    assert conflicts == [
        {
            "room_id": "lab-1",
            "term": "2026-FALL",
            "meeting_days": ("WE",),
            "left_assignment_id": "left",
            "left_section_id": "biology-1",
            "right_assignment_id": "right",
            "right_section_id": "chemistry-1",
            "conflict_type": "ROOM_TIME_OVERLAP",
        }
    ]


def test_room_schedule_conflicts_ignore_cross_tenant_other_rooms_and_non_overlaps():
    school_a = uuid4()
    school_b = uuid4()
    assignments = [
        _assignment(school_a, assignment_id="base", room_id="room-a", days=("MO",), start=480, end=540),
        _assignment(school_a, assignment_id="different-room", room_id="room-b", days=("MO",), start=500, end=530),
        _assignment(school_a, assignment_id="different-day", room_id="room-a", days=("TU",), start=500, end=530),
        _assignment(school_a, assignment_id="after", room_id="room-a", days=("MO",), start=540, end=600),
        _assignment(school_b, assignment_id="other-tenant", room_id="room-a", days=("MO",), start=500, end=530),
    ]

    assert room_schedule_conflicts(school_a, assignments) == []


def test_validate_room_assignment_rejects_invalid_assignment_contract():
    school_id = uuid4()
    assignment = _assignment(school_id, start=600, end=600)

    with pytest.raises(ValueError, match="start_minute must be before end_minute"):
        validate_room_assignment(assignment)
