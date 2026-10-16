"""Fail-closed aggregates of *published* CROWN schedule cards for Compass.

This is a read-only consumer of existing canonical placement records. It does
not make planning proposals authoritative and does not create another student,
teacher, room or section master. Small student cohorts are suppressed.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from json import dumps
from typing import Sequence

from .canonical_snapshot import CanonicalPlanningSnapshot

MIN_COHORT = 5
MAX_MEETINGS = 4000


@dataclass(frozen=True)
class PublishedScheduleCard:
    placement_id: str
    school_id: str
    academic_year_id: str
    section_id: str
    period_id: str
    day_template_id: str
    room_id: str | None


@dataclass(frozen=True)
class PublishedCompassSummary:
    school_id: str
    academic_year_id: str
    term_code: str
    canonical_fingerprint: str
    publication_fingerprint: str
    provenance: str
    freshness: str
    total_sections: int
    placed_sections: int
    unplaced_sections: int
    published_meetings: int
    occupied_rooms: int
    distinct_students: int | None
    enrolled_meeting_seats: int | None
    capacity_meeting_seats: int | None
    meeting_seat_utilization_percent: float | None
    privacy_suppressed: bool
    limitations: tuple[str, ...]


def summarize_published_kairos(
    snapshot: CanonicalPlanningSnapshot,
    cards: Sequence[PublishedScheduleCard],
) -> PublishedCompassSummary:
    if not isinstance(snapshot, CanonicalPlanningSnapshot):
        raise ValueError("An authorized school-scoped canonical snapshot is required.")
    if not isinstance(cards, (tuple, list)) or len(cards) > MAX_MEETINGS:
        raise ValueError("Published cards are not a bounded collection.")
    if not snapshot.section_inputs or not snapshot.school_id or not snapshot.academic_year_id:
        raise ValueError("Verified school and year scope required.")

    sections = snapshot.section_inputs
    periods = snapshot.period_inputs
    rooms = snapshot.room_inputs
    seen_ids: set[str] = set()
    normalized: list[PublishedScheduleCard] = []
    intervals: list[tuple[PublishedScheduleCard, int, int, frozenset[str], frozenset[str]]] = []
    placed_sections: set[str] = set()
    placed_students: set[str] = set()
    used_rooms: set[str] = set()
    missing_capacity = False
    occupied_seats = 0
    capacity_seats = 0
    for card in cards:
        if not isinstance(card, PublishedScheduleCard):
            raise ValueError("Unverified published card type.")
        if not card.placement_id or card.placement_id in seen_ids:
            raise ValueError("Missing or duplicated published record identity.")
        seen_ids.add(card.placement_id)
        if (card.school_id, card.academic_year_id) != (snapshot.school_id, snapshot.academic_year_id):
            raise ValueError("Published record crosses the school or academic year.")
        section = sections.get(card.section_id)
        period = periods.get(card.period_id)
        if section is None or period is None or card.day_template_id != period.template_id:
            raise ValueError("Published record refers to a missing canonical section or period.")
        if not period.instructional or not 0 <= period.start_minute < period.end_minute <= 1440:
            raise ValueError("Published record uses a protected or invalid period.")
        if (section.school_id, section.academic_year_id, section.term_code) != (
            snapshot.school_id, snapshot.academic_year_id, snapshot.term_code
        ) or section.roster_verified is not True:
            raise ValueError("Section has no verified canonical scope.")
        if not section.student_ids <= snapshot.verified_student_ids:
            raise ValueError("Published record contains unverified student identities.")
        if not section.teacher_ids <= snapshot.assigned_staff_ids:
            raise ValueError("Published record contains unverified teaching staff.")
        # Validate chapel/protected intervals, including ones not selected as
        # the period itself, before counting any occupied seat.
        for other in periods.values():
            if (other.template_id == period.template_id and not other.instructional
                    and max(other.start_minute, period.start_minute)
                    < min(other.end_minute, period.end_minute)):
                raise ValueError("Published class overlaps protected scheduling time.")
        if card.room_id is None:
            missing_capacity = True
        else:
            room = rooms.get(card.room_id)
            if room is None or room.school_id != snapshot.school_id or type(room.capacity) is not int or room.capacity < 1:
                raise ValueError("Published room capacity or tenant cannot be verified.")
            if len(section.student_ids) > room.capacity:
                raise ValueError("Published class exceeds the verified room capacity.")
            used_rooms.add(card.room_id)
            capacity_seats += room.capacity
        occupied_seats += len(section.student_ids)
        placed_students.update(section.student_ids)
        placed_sections.add(card.section_id)
        normalized.append(card)
        intervals.append((card, period.start_minute, period.end_minute,
                          section.teacher_ids, section.student_ids))

    # Different meeting cards on the same day-template may not collide for a
    # room, teacher or student, even if their canonical period IDs differ.
    for i, (left, lstart, lend, lteachers, lstudents) in enumerate(intervals):
        for right, rstart, rend, rteachers, rstudents in intervals[i+1:]:
            if left.day_template_id != right.day_template_id or max(lstart, rstart) >= min(lend, rend):
                continue
            if left.section_id == right.section_id:
                raise ValueError("Duplicate overlapping meetings for one section.")
            if left.room_id is not None and left.room_id == right.room_id:
                raise ValueError("Published room double-booking.")
            if lteachers & rteachers or lstudents & rstudents:
                raise ValueError("Published teacher or student double-booking.")

    published_digest = sha256(dumps({
        "scope": [snapshot.school_id, snapshot.academic_year_id,
                  snapshot.term_code, snapshot.source_fingerprint],
        "cards": [
            [c.placement_id, c.section_id, c.period_id, c.day_template_id, c.room_id]
            for c in sorted(normalized, key=lambda c: c.placement_id)
        ],
    }, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    report_students = len(placed_students) >= MIN_COHORT
    report_capacity = report_students and not missing_capacity and bool(normalized)
    limits = ["READ_ONLY_PUBLISHED_RECORDS", "NO_APPROVED_FINANCIAL_INPUTS",
              "SOURCE_FRESHNESS_REQUIRES_NEW_REQUEST"]
    if not report_students:
        limits.append("SMALL_CELL_SUPPRESSED")
    if missing_capacity:
        limits.append("UNVERIFIED_ROOM_CAPACITY")
    return PublishedCompassSummary(
        school_id=snapshot.school_id,
        academic_year_id=snapshot.academic_year_id,
        term_code=snapshot.term_code,
        canonical_fingerprint=snapshot.source_fingerprint,
        publication_fingerprint=published_digest,
        provenance="CANONICAL_PUBLISHED_SECTION_PLACEMENTS",
        freshness="READ_AT_REQUEST_TIME_NOT_TRANSACTIONALLY_ATTESTED",
        total_sections=len(sections),
        placed_sections=len(placed_sections),
        unplaced_sections=len(sections) - len(placed_sections),
        published_meetings=len(normalized),
        occupied_rooms=len(used_rooms),
        distinct_students=len(placed_students) if report_students else None,
        enrolled_meeting_seats=occupied_seats if report_students else None,
        capacity_meeting_seats=capacity_seats if report_capacity else None,
        meeting_seat_utilization_percent=round(100 * occupied_seats / capacity_seats, 2)
            if report_capacity and capacity_seats else None,
        privacy_suppressed=not report_students,
        limitations=tuple(limits),
    )
