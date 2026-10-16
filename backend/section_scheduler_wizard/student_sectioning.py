"""Deterministic, read-only student sectioning from verified CROWN identities.

An internal bounded constructive planner, not an optimal solver, a publication
API or a new student/section master. It never changes canonical enrollments.
PARTIAL means *unfulfilled by this heuristic*, not proven impossible.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

from .planning_inputs import StudentCourseRequest, validate_planning_inputs
from .preflight import (
    CandidatePlacement, PeriodInput, RoomInput, SectionInput,
    validate_candidate_placements,
)

MAX_SECTIONING_STUDENTS = 500
MAX_SECTIONING_SECTIONS = 64
MAX_REQUIRED_COURSES = 16
MAX_ELECTIVE_SLOTS = 4
MAX_REPORTED_UNMET = 1000

COMPLETE = "COMPLETE"
PARTIAL = "PARTIAL"
MODEL_INVALID = "MODEL_INVALID"


@dataclass(frozen=True)
class StudentSectionAssignment:
    student_id: str
    course_id: str
    section_id: str
    required: bool
    elective_rank: int | None = None


@dataclass(frozen=True)
class StudentSectioningResult:
    status: str
    additions: tuple[StudentSectionAssignment, ...]
    student_count: int
    required_fulfilled: int
    required_unfulfilled: int
    elective_fulfilled: int
    elective_unfulfilled: int
    diagnostics: tuple[str, ...]


def _invalid(code: str) -> StudentSectioningResult:
    return StudentSectioningResult(MODEL_INVALID, (), 0, 0, 0, 0, 0, (code,))


def _overlaps(a: PeriodInput, b: PeriodInput) -> bool:
    return (
        a.template_id == b.template_id
        and a.start_minute < b.end_minute and b.start_minute < a.end_minute
    )


def construct_student_sectioning(
    *,
    school_id: str,
    academic_year_id: str,
    term_code: str,
    sections: Mapping[str, SectionInput],
    periods: Mapping[str, PeriodInput],
    rooms: Mapping[str, RoomInput],
    placements: Sequence[CandidatePlacement],
    section_course_ids: Mapping[str, str],
    verified_student_ids: frozenset[str],
    catalog_course_ids: frozenset[str],
    requests: Sequence[StudentCourseRequest],
    elective_slots: Mapping[str, int],
) -> StudentSectioningResult:
    """Allocate explicit required courses then ranked elective choices.

    The caller must derive section/course IDs and student identities from
    authorized canonical records. Existing verified rosters consume capacity;
    proposed assignments only appear in the returned immutable plan.
    """
    if not school_id or not academic_year_id or not term_code:
        return _invalid("MISSING_SCOPE")
    if (
        not sections or len(sections) > MAX_SECTIONING_SECTIONS
        or len(requests) > MAX_SECTIONING_STUDENTS
        or len(placements) != len(sections)
        or set(section_course_ids) != set(sections)
    ):
        return _invalid("INVALID_SECTIONING_SIZE")
    if not isinstance(verified_student_ids, frozenset) or not isinstance(catalog_course_ids, frozenset):
        return _invalid("UNVERIFIED_IDENTITY_CONTRACT")
    if any(
        section_id != section.section_id
        or (section.school_id, section.academic_year_id, section.term_code)
           != (school_id, academic_year_id, term_code)
        or section.roster_verified is not True
        or not section.student_ids <= verified_student_ids
        or section_course_ids[section_id] not in catalog_course_ids
        for section_id, section in sections.items()
    ):
        return _invalid("UNVERIFIED_SECTION_OR_COURSE")
    if any(
        not isinstance(placement, CandidatePlacement)
        or placement.section_id not in sections
        or placement.period_id not in periods
        or (placement.room_id is not None and placement.room_id not in rooms)
        for placement in placements
    ):
        return _invalid("INVALID_PLACEMENT")
    placement_by_section = {p.section_id: p for p in placements}
    if len(placement_by_section) != len(sections):
        return _invalid("DUPLICATE_OR_MISSING_PLACEMENT")
    # The generic placement preflight intentionally permits a roomless meeting,
    # but student sectioning must prove occupancy against an actual room limit.
    # Never index rooms[None] or assume unlimited capacity for roomless cards.
    if any(placement.room_id is None for placement in placements):
        return _invalid("ROOM_CAPACITY_UNVERIFIED")
    if validate_candidate_placements(
        school_id=school_id, academic_year_id=academic_year_id,
        term_code=term_code, sections=sections, periods=periods,
        rooms=rooms, placements=placements,
    ):
        return _invalid("FAILED_HARD_PLACEMENT_CONSTRAINTS")
    if any(
        not isinstance(request, StudentCourseRequest)
        or len(request.required_course_ids) > MAX_REQUIRED_COURSES
        for request in requests
    ):
        return _invalid("INVALID_COURSE_REQUEST")
    request_ids = [request.student_id for request in requests]
    if set(elective_slots) != set(request_ids) or len(set(request_ids)) != len(request_ids):
        return _invalid("MISSING_OR_DUPLICATE_STUDENT_SLOTS")
    if any(
        type(slot_count) is not int or not 0 <= slot_count <= MAX_ELECTIVE_SLOTS
        for slot_count in elective_slots.values()
    ):
        return _invalid("INVALID_ELECTIVE_SLOT_COUNT")
    findings = validate_planning_inputs(
        school_id=school_id, academic_year_id=academic_year_id,
        term_code=term_code, known_staff_ids=frozenset(),
        known_student_ids=verified_student_ids,
        known_course_ids=catalog_course_ids,
        known_period_ids=frozenset(periods),
        teacher_rules={}, student_requests=requests,
    )
    if findings:
        return _invalid("UNVERIFIED_STUDENT_REQUESTS")

    # Each section already contains canonical enrolled students. Never
    # subtract capacity or mutate source rosters when adding proposals.
    occupants = {section_id: set(section.student_ids)
                 for section_id, section in sections.items()}
    by_course: dict[str, list[str]] = {}
    for section_id, course_id in section_course_ids.items():
        by_course.setdefault(course_id, []).append(section_id)
    for choices in by_course.values():
        choices.sort()

    additions: list[StudentSectionAssignment] = []
    required_fulfilled = required_unfulfilled = 0
    elective_fulfilled = elective_unfulfilled = 0
    unmet_codes: set[str] = set()

    def enrolled_sections(student_id: str) -> set[str]:
        return {key for key, students in occupants.items() if student_id in students}

    def choose(student_id: str, course_id: str, required: bool,
               rank: int | None = None) -> bool:
        held = enrolled_sections(student_id)
        # A verified existing assignment satisfies a request without
        # producing an extraneous or duplicate write proposal.
        if any(section_course_ids[key] == course_id for key in held):
            return True
        options = by_course.get(course_id, ())
        # Prefer least-filled classes, then stable canonical section ID.
        for key in sorted(options, key=lambda key: (len(occupants[key]), key)):
            room_id = placement_by_section[key].room_id
            if len(occupants[key]) >= rooms[room_id].capacity:
                continue
            period = periods[placement_by_section[key].period_id]
            if any(_overlaps(period, periods[placement_by_section[other].period_id])
                   for other in held):
                continue
            occupants[key].add(student_id)
            additions.append(StudentSectionAssignment(
                student_id, course_id, key, required, rank))
            return True
        return False

    # Stable order matters because this is a constructive approximation;
    # do not represent the result as a globally optimal enrollment.
    for req in sorted(requests, key=lambda req: req.student_id):
        for course_id in sorted(req.required_course_ids):
            if choose(req.student_id, course_id, True):
                required_fulfilled += 1
            else:
                required_unfulfilled += 1
                unmet_codes.add("REQUIRED_UNFILLED")
        slots = elective_slots[req.student_id]
        matched = 0
        for choice in sorted(req.elective_choices, key=lambda c: c.rank):
            if matched >= slots:
                break
            if choose(req.student_id, choice.course_id, False, choice.rank):
                matched += 1
                elective_fulfilled += 1
        if matched < slots:
            elective_unfulfilled += slots - matched
            unmet_codes.add("ELECTIVE_UNFILLED")

    # Final independent capacity and per-student timetable verification.
    for section_id, students in occupants.items():
        room = rooms[placement_by_section[section_id].room_id]
        if len(students) > room.capacity:
            return _invalid("FINAL_CAPACITY_FAILURE")
    for student_id in verified_student_ids:
        held = sorted(key for key, roster in occupants.items() if student_id in roster)
        for i, left in enumerate(held):
            for right in held[i+1:]:
                if _overlaps(periods[placement_by_section[left].period_id],
                             periods[placement_by_section[right].period_id]):
                    return _invalid("FINAL_STUDENT_COLLISION")
    status = PARTIAL if required_unfulfilled or elective_unfulfilled else COMPLETE
    return StudentSectioningResult(
        status, tuple(additions), len(requests), required_fulfilled,
        required_unfulfilled, elective_fulfilled, elective_unfulfilled,
        tuple(sorted(unmet_codes))[:MAX_REPORTED_UNMET],
    )
