"""Pure, side-effect-free validation of proposed recurring section placements.

This is a solver/input building block, NOT a publishing or authorization API.
Callers must obtain school-scoped, verified canonical data before construction.
No database queries, third-party optimizer, or student PII are used here.
"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import Mapping, Sequence


MAX_CANDIDATE_PLACEMENTS = 2000


@dataclass(frozen=True)
class SectionInput:
    section_id: str
    school_id: str
    academic_year_id: str
    term_code: str
    teacher_ids: frozenset[str]
    student_ids: frozenset[str]
    roster_verified: bool


@dataclass(frozen=True)
class PeriodInput:
    period_id: str
    school_id: str
    academic_year_id: str
    template_id: str
    start_minute: int
    end_minute: int
    instructional: bool


@dataclass(frozen=True)
class RoomInput:
    room_id: str
    school_id: str
    capacity: int


@dataclass(frozen=True)
class CandidatePlacement:
    section_id: str
    period_id: str
    room_id: str | None = None


@dataclass(frozen=True)
class Finding:
    code: str
    placement_index: int
    message: str


def validate_candidate_placements(
    *,
    school_id: str,
    academic_year_id: str,
    term_code: str,
    sections: Mapping[str, SectionInput],
    periods: Mapping[str, PeriodInput],
    rooms: Mapping[str, RoomInput],
    placements: Sequence[CandidatePlacement],
) -> tuple[Finding, ...]:
    """Check bounded proposed placements without changing existing schedules.

    An empty finding list means *only* that the supplied proposal satisfied
    these checks. It does not certify complete course fulfillment, live roster
    freshness, staffing qualifications, teacher availability or publication.
    """
    if len(placements) > MAX_CANDIDATE_PLACEMENTS:
        return (Finding("TOO_MANY_PLACEMENTS", -1, "Placement count exceeds the preflight limit."),)
    if not school_id or not academic_year_id or not term_code:
        return (Finding("MISSING_SCOPE", -1, "School, academic year and term are required."),)
    if not placements:
        return (Finding("NO_PLACEMENTS", -1, "At least one candidate placement is required."),)

    findings: list[Finding] = []
    valid: list[tuple[int, CandidatePlacement, SectionInput, PeriodInput]] = []
    for index, placement in enumerate(placements):
        section = sections.get(placement.section_id)
        period = periods.get(placement.period_id)
        room = rooms.get(placement.room_id) if placement.room_id is not None else None
        invalid = False
        if section is None or (section.school_id, section.academic_year_id, section.term_code) != (school_id, academic_year_id, term_code):
            findings.append(Finding("INVALID_SECTION_SCOPE", index, "Section is missing or outside the selected school, year or term."))
            invalid = True
        if period is None or (period.school_id, period.academic_year_id) != (school_id, academic_year_id):
            findings.append(Finding("INVALID_PERIOD_SCOPE", index, "Period is missing or outside the selected school or year."))
            invalid = True
        elif not (isinstance(period.start_minute, int) and isinstance(period.end_minute, int)
                  and 0 <= period.start_minute < period.end_minute <= 1440):
            findings.append(Finding("INVALID_PERIOD_TIME", index, "Period must have a valid nonempty same-day time range."))
            invalid = True
        if placement.room_id is not None and (room is None or room.school_id != school_id):
            findings.append(Finding("INVALID_ROOM_SCOPE", index, "Room is missing or belongs to another school."))
            invalid = True
        if invalid:
            continue
        if not section.roster_verified:
            findings.append(Finding("ROSTER_NOT_VERIFIED", index, "Section roster identity evidence is required."))
        if not section.teacher_ids:
            findings.append(Finding("TEACHER_NOT_ASSIGNED", index, "A section requires a verified teaching assignment."))
        if not period.instructional:
            findings.append(Finding("PROTECTED_PERIOD", index, "Instruction may not occupy a protected period."))
        if room is not None and (room.capacity < 1 or len(section.student_ids) > room.capacity):
            findings.append(Finding("ROOM_CAPACITY", index, "Room capacity is invalid or smaller than the verified roster."))
        valid.append((index, placement, section, period))

    # Different day templates are independent recurring days. Time overlap is
    # calculated from minute ranges, not merely from equal period identifiers.
    for left, right in combinations(valid, 2):
        li, lp, ls, lt = left
        ri, rp, rs, rt = right
        if lt.template_id != rt.template_id or max(lt.start_minute, rt.start_minute) >= min(lt.end_minute, rt.end_minute):
            continue
        if lp.section_id == rp.section_id:
            findings.append(Finding("SECTION_OVERLAP", ri, f"Section overlaps another placement at index {li}."))
        if lp.room_id is not None and lp.room_id == rp.room_id:
            findings.append(Finding("ROOM_OVERLAP", ri, f"Room overlaps another placement at index {li}."))
        if ls.teacher_ids & rs.teacher_ids:
            findings.append(Finding("TEACHER_OVERLAP", ri, f"Teacher overlaps another placement at index {li}."))
        if ls.student_ids & rs.student_ids:
            findings.append(Finding("STUDENT_OVERLAP", ri, f"Student overlaps another placement at index {li}."))
    return tuple(findings)
