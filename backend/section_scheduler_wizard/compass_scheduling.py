"""Privacy-bounded, read-only Kairos scheduling metrics for Compass consumers.

Consumes an already authorized canonical planning snapshot and independently
validated placements. It never queries, mutates or publishes school records.
Counts derived from fewer than five distinct students are suppressed.
No financial or teacher-policy assumptions are invented.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from json import dumps
from typing import Sequence

from .canonical_snapshot import CanonicalPlanningSnapshot
from .preflight import CandidatePlacement, validate_candidate_placements

MIN_REPORTABLE_STUDENTS = 5
MAX_METRIC_SECTIONS = 2000


@dataclass(frozen=True)
class CompassSchedulingSummary:
    school_id: str
    academic_year_id: str
    term_code: str
    source_fingerprint: str
    placement_fingerprint: str
    provenance: str
    freshness: str
    source_authority: str
    publication_allowed: bool
    total_sections: int
    placed_sections: int
    unplaced_sections: int
    active_room_count: int
    distinct_student_count: int | None
    assigned_teacher_count: int | None
    scheduled_roster_seats: int | None
    known_room_capacity: int | None
    utilization_percent: float | None
    privacy_suppressed: bool
    limitations: tuple[str, ...]


def build_compass_scheduling_summary(
    *,
    snapshot: CanonicalPlanningSnapshot,
    placements: Sequence[CandidatePlacement],
    expected_source_fingerprint: str,
) -> CompassSchedulingSummary:
    """Produce a truthful provisional summary from verified canonical input.

    The caller must have obtained the snapshot through the school's existing
    scheduling.view authority. In particular, this does not grant access to
    persons who have not independently been authorized to read that school.
    """
    if not isinstance(snapshot, CanonicalPlanningSnapshot):
        raise ValueError("An authorized canonical planning snapshot is required.")
    if (
        not expected_source_fingerprint
        or expected_source_fingerprint != snapshot.source_fingerprint
        or len(snapshot.source_fingerprint) != 64
        or any(c not in "0123456789abcdef" for c in snapshot.source_fingerprint)
    ):
        raise ValueError("Source authority is stale or invalid.")
    if not snapshot.school_id or not snapshot.academic_year_id or not snapshot.term_code:
        raise ValueError("An explicit scoped school and academic term are required.")
    sections = snapshot.section_inputs
    periods = snapshot.period_inputs
    rooms = snapshot.room_inputs
    if not sections or len(sections) > MAX_METRIC_SECTIONS:
        raise ValueError("Section scope is empty or exceeds the report limit.")
    if any(
        key != section.section_id
        or (section.school_id, section.academic_year_id, section.term_code)
           != (snapshot.school_id, snapshot.academic_year_id, snapshot.term_code)
        or section.roster_verified is not True
        or not section.student_ids <= snapshot.verified_student_ids
        or not section.teacher_ids <= snapshot.assigned_staff_ids
        for key, section in sections.items()
    ):
        raise ValueError("The school-scoped section roster or teacher authority is invalid.")
    if not isinstance(placements, (tuple, list)) or len(placements) > len(sections):
        raise ValueError("Placement collection is malformed or unbounded.")
    if any(not isinstance(p, CandidatePlacement) for p in placements):
        raise ValueError("Placement items must be verified candidate objects.")
    chosen_ids = [p.section_id for p in placements]
    if len(chosen_ids) != len(set(chosen_ids)) or not set(chosen_ids) <= set(sections):
        raise ValueError("A section must have at most one planned placement.")
    if placements and validate_candidate_placements(
        school_id=snapshot.school_id,
        academic_year_id=snapshot.academic_year_id,
        term_code=snapshot.term_code,
        sections=sections,
        periods=periods,
        rooms=rooms,
        placements=placements,
    ):
        raise ValueError("A proposed placement violates a hard scheduling constraint.")

    ordered = tuple(sorted(placements, key=lambda p: (p.section_id, p.period_id, p.room_id or "")))
    digest = sha256(dumps(
        {
            "scope": [snapshot.school_id, snapshot.academic_year_id,
                      snapshot.term_code, snapshot.source_fingerprint],
            "placements": [[p.section_id, p.period_id, p.room_id] for p in ordered],
        },
        sort_keys=True, separators=(",", ":"),
    ).encode("utf-8")).hexdigest()

    all_students = frozenset(student for s in sections.values() for student in s.student_ids)
    all_staff = frozenset(staff for s in sections.values() for staff in s.teacher_ids)
    occupied = sum(len(sections[p.section_id].student_ids) for p in placements)
    placed_students = frozenset(student for p in placements
                               for student in sections[p.section_id].student_ids)
    room_ids = frozenset(p.room_id for p in placements if p.room_id is not None)
    # A roomless placement does not have verified capacity; never manufacture
    # a denominator or imply a complete utilization figure.
    capacity_proven = len(room_ids) > 0 and all(p.room_id is not None for p in placements)
    capacity = sum(rooms[p.room_id].capacity for p in placements) if capacity_proven else None
    # Only report enrollment and load when at least five *distinct* students
    # make up the cell; otherwise suppress all derived occupancy values.
    count_allowed = len(all_students) >= MIN_REPORTABLE_STUDENTS
    occupancy_allowed = count_allowed and len(placed_students) >= MIN_REPORTABLE_STUDENTS
    reported_capacity = capacity if capacity_proven and occupancy_allowed else None
    utilization = round(100 * occupied / capacity, 2) if (
        reported_capacity is not None and capacity > 0
    ) else None
    limits = (
        "SOURCE_REVALIDATION_REQUIRED_BEFORE_USE",
        "PROVISIONAL_NOT_PUBLISHED",
        "NO_APPROVED_TEACHER_POLICY_ATTESTATION",
        "NO_FINANCIAL_COST_ESTIMATE",
    )
    if not count_allowed or not occupancy_allowed:
        limits += ("SMALL_CELL_SUPPRESSED",)
    if capacity is None:
        limits += ("CAPACITY_UNVERIFIED",)

    return CompassSchedulingSummary(
        school_id=snapshot.school_id,
        academic_year_id=snapshot.academic_year_id,
        term_code=snapshot.term_code,
        source_fingerprint=snapshot.source_fingerprint,
        placement_fingerprint=digest,
        provenance="CANONICAL_KAIROS_READ_ONLY_PROJECTION",
        freshness="SOURCE_FINGERPRINT_MATCHED_AT_PROJECTION",
        source_authority="SCHOOL_SCHEDULING_VIEW_REQUIRED",
        publication_allowed=False,
        total_sections=len(sections),
        placed_sections=len(placements),
        unplaced_sections=len(sections) - len(placements),
        active_room_count=len(room_ids),
        distinct_student_count=len(all_students) if count_allowed else None,
        assigned_teacher_count=len(all_staff) if count_allowed else None,
        scheduled_roster_seats=occupied if occupancy_allowed else None,
        known_room_capacity=reported_capacity,
        utilization_percent=utilization,
        privacy_suppressed=not count_allowed or not occupancy_allowed,
        limitations=limits,
    )
