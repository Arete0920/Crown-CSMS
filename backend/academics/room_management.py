from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence
from uuid import UUID


@dataclass(frozen=True)
class Classroom:
    """Canonical room record used by the Module 018 proof boundary."""

    school_id: UUID
    room_id: str
    code: str
    capacity: int
    active: bool = True


@dataclass(frozen=True)
class RoomAssignment:
    """A section-to-room placement with explicit term, days, and time window."""

    school_id: UUID
    assignment_id: str
    section_id: str
    room_id: str
    term: str
    meeting_days: tuple[str, ...]
    start_minute: int
    end_minute: int
    expected_enrollment: int


VALID_DAYS = {"MO", "TU", "WE", "TH", "FR", "SA", "SU"}


def normalize_days(days: Sequence[str]) -> tuple[str, ...]:
    """Return stable upper-case meeting-day codes and reject unknown days."""

    normalized = tuple(dict.fromkeys(day.strip().upper() for day in days if day.strip()))
    invalid = [day for day in normalized if day not in VALID_DAYS]
    if invalid:
        raise ValueError(f"Invalid meeting day code(s): {', '.join(invalid)}")
    return normalized


def validate_room_assignment(assignment: RoomAssignment) -> None:
    """Validate structural assignment data before capacity or conflict checks."""

    if not assignment.section_id:
        raise ValueError("section_id is required")
    if not assignment.room_id:
        raise ValueError("room_id is required")
    if not assignment.term:
        raise ValueError("term is required")
    if assignment.start_minute < 0 or assignment.end_minute < 0:
        raise ValueError("meeting times must be non-negative")
    if assignment.start_minute >= assignment.end_minute:
        raise ValueError("start_minute must be before end_minute")
    if not assignment.meeting_days:
        raise ValueError("at least one meeting day is required")
    normalize_days(assignment.meeting_days)


def _room_index(school_id: UUID, classrooms: Iterable[Classroom]) -> dict[str, Classroom]:
    return {
        room.room_id: room
        for room in classrooms
        if room.school_id == school_id
    }


def _school_assignments(
    school_id: UUID,
    assignments: Iterable[RoomAssignment],
    *,
    term: str | None = None,
) -> list[RoomAssignment]:
    scoped = [assignment for assignment in assignments if assignment.school_id == school_id]
    if term:
        scoped = [assignment for assignment in scoped if assignment.term == term]
    return sorted(scoped, key=lambda item: (item.term, item.room_id, item.start_minute, item.assignment_id))


def room_capacity_violations(
    school_id: UUID,
    classrooms: Iterable[Classroom],
    assignments: Iterable[RoomAssignment],
    *,
    term: str | None = None,
) -> list[dict]:
    """Return tenant-scoped room capacity and room-existence violations."""

    rooms = _room_index(school_id, classrooms)
    violations: list[dict] = []

    for assignment in _school_assignments(school_id, assignments, term=term):
        validate_room_assignment(assignment)
        room = rooms.get(assignment.room_id)

        if room is None:
            violations.append(
                {
                    "assignment_id": assignment.assignment_id,
                    "section_id": assignment.section_id,
                    "room_id": assignment.room_id,
                    "violation_type": "ROOM_NOT_FOUND",
                    "expected_enrollment": assignment.expected_enrollment,
                    "capacity": None,
                }
            )
            continue

        if not room.active:
            violations.append(
                {
                    "assignment_id": assignment.assignment_id,
                    "section_id": assignment.section_id,
                    "room_id": assignment.room_id,
                    "room_code": room.code,
                    "violation_type": "ROOM_INACTIVE",
                    "expected_enrollment": assignment.expected_enrollment,
                    "capacity": room.capacity,
                }
            )

        if assignment.expected_enrollment > room.capacity:
            violations.append(
                {
                    "assignment_id": assignment.assignment_id,
                    "section_id": assignment.section_id,
                    "room_id": assignment.room_id,
                    "room_code": room.code,
                    "violation_type": "CAPACITY_EXCEEDED",
                    "expected_enrollment": assignment.expected_enrollment,
                    "capacity": room.capacity,
                }
            )

    return violations


def _overlaps(left: RoomAssignment, right: RoomAssignment) -> bool:
    if left.term != right.term:
        return False
    if left.room_id != right.room_id:
        return False
    if not set(normalize_days(left.meeting_days)).intersection(normalize_days(right.meeting_days)):
        return False
    return left.start_minute < right.end_minute and right.start_minute < left.end_minute


def room_schedule_conflicts(
    school_id: UUID,
    assignments: Iterable[RoomAssignment],
    *,
    term: str | None = None,
) -> list[dict]:
    """Return tenant-scoped conflicts where two sections occupy one room simultaneously."""

    scoped = _school_assignments(school_id, assignments, term=term)
    conflicts: list[dict] = []

    for left_index, left in enumerate(scoped):
        validate_room_assignment(left)
        for right in scoped[left_index + 1 :]:
            validate_room_assignment(right)
            if not _overlaps(left, right):
                continue

            conflicts.append(
                {
                    "room_id": left.room_id,
                    "term": left.term,
                    "meeting_days": tuple(sorted(set(left.meeting_days).intersection(right.meeting_days))),
                    "left_assignment_id": left.assignment_id,
                    "left_section_id": left.section_id,
                    "right_assignment_id": right.assignment_id,
                    "right_section_id": right.section_id,
                    "conflict_type": "ROOM_TIME_OVERLAP",
                }
            )

    return conflicts
