"""Read-only teacher feasibility checks for proposed Kairos placements.

This is an independent deterministic hard-constraint checker, NOT a solver or
publication API. Call only on a school-authorized, fresh canonical snapshot.
The caller must supply explicit day-template occurrences in a planning cycle;
neither A/B days nor weekly staffing load may be guessed.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Mapping, Sequence

from .planning_inputs import TeacherPlanningRule, validate_planning_inputs
from .preflight import (
    CandidatePlacement, PeriodInput, RoomInput, SectionInput,
    MAX_CANDIDATE_PLACEMENTS, validate_candidate_placements,
)

MAX_FINDINGS = 1000
MAX_CYCLE_OCCURRENCES = 14


@dataclass(frozen=True)
class TeacherFeasibilityFinding:
    code: str
    placement_index: int
    message: str


def _minutes(intervals: Sequence[tuple[int, int]]) -> int:
    """Union intervals so overlapping bell blocks cannot double-count prep."""
    total = 0
    end = 0
    for start, stop in sorted(intervals):
        if start >= stop:
            continue
        if start >= end:
            total += stop - start
            end = stop
        elif stop > end:
            total += stop - end
            end = stop
    return total


def _overlap(left: tuple[int, int], right: tuple[int, int]) -> bool:
    return max(left[0], right[0]) < min(left[1], right[1])


def _free_minutes(
    instructional: Sequence[tuple[int, int]],
    blocked: Sequence[tuple[int, int]],
) -> int:
    """Find instructional minutes not blocked by teaching or unavailability."""
    covered = _minutes(instructional)
    overlaps = [
        (max(a, x), min(b, y))
        for a, b in instructional
        for x, y in blocked
        if max(a, x) < min(b, y)
    ]
    # Intersect blocked union with instructional union by splitting at endpoints.
    endpoints = sorted({v for a, b in instructional for v in (a, b)} |
                       {v for a, b in blocked for v in (a, b)})
    free = 0
    for left, right in zip(endpoints, endpoints[1:]):
        if right <= left:
            continue
        within_day = any(a <= left and right <= b for a, b in instructional)
        obstructed = any(a < right and left < b for a, b in blocked)
        if within_day and not obstructed:
            free += right - left
    assert free <= covered
    return free


def validate_teacher_feasibility(
    *,
    school_id: str,
    academic_year_id: str,
    term_code: str,
    sections: Mapping[str, SectionInput],
    periods: Mapping[str, PeriodInput],
    rooms: Mapping[str, RoomInput],
    placements: Sequence[CandidatePlacement],
    teacher_rules: Mapping[str, TeacherPlanningRule],
    template_occurrences: Mapping[str, int],
) -> tuple[TeacherFeasibilityFinding, ...]:
    """Verify teacher availability, cycle workload and preparation minima.

    A clean result applies only to the *proposed* placements, not to complete
    school scheduling, prerequisites, staffing qualifications, or publication.
    """
    if len(placements) > MAX_CANDIDATE_PLACEMENTS:
        return (TeacherFeasibilityFinding("INPUT_LIMIT", -1, "Too many placements."),)
    if not school_id or not academic_year_id or not term_code:
        return (TeacherFeasibilityFinding("MISSING_SCOPE", -1, "Planning scope required."),)

    expected = (school_id, academic_year_id)
    if any(
        key != period.period_id
        or (period.school_id, period.academic_year_id) != expected
        or type(period.instructional) is not bool
        or type(period.start_minute) is not int
        or type(period.end_minute) is not int
        or not 0 <= period.start_minute < period.end_minute <= 1440
        or not period.template_id
        for key, period in periods.items()
    ):
        return (TeacherFeasibilityFinding("INVALID_PERIODS", -1, "Period authority invalid."),)

    template_ids = {period.template_id for period in periods.values()}
    if not template_ids or set(template_occurrences) != template_ids:
        return (TeacherFeasibilityFinding("CYCLE_UNDEFINED", -1, "Every template requires an explicit cycle count."),)
    if (any(type(n) is not int or not 1 <= n <= MAX_CYCLE_OCCURRENCES
            for n in template_occurrences.values())
            or sum(template_occurrences.values()) > MAX_CYCLE_OCCURRENCES):
        return (TeacherFeasibilityFinding("INVALID_CYCLE", -1, "Planning-cycle counts must be bounded positive integers."),)

    known_staff = frozenset(staff for section in sections.values() for staff in section.teacher_ids)
    planning_findings = validate_planning_inputs(
        school_id=school_id, academic_year_id=academic_year_id, term_code=term_code,
        known_staff_ids=known_staff, known_student_ids=frozenset(),
        known_course_ids=frozenset(), known_period_ids=frozenset(periods),
        teacher_rules=teacher_rules, student_requests=(),
    )
    if planning_findings:
        return (TeacherFeasibilityFinding("INVALID_TEACHER_RULE", -1, "Teacher policies failed input validation."),)

    preflight = validate_candidate_placements(
        school_id=school_id, academic_year_id=academic_year_id, term_code=term_code,
        sections=sections, periods=periods, rooms=rooms, placements=placements,
    )
    if preflight:
        return (TeacherFeasibilityFinding("PLACEMENT_PREFLIGHT_FAILED", -1, "Candidate placements failed hard constraints."),)

    expected_staff = set().union(*(sections[p.section_id].teacher_ids for p in placements))
    if not expected_staff <= set(teacher_rules):
        return (TeacherFeasibilityFinding("MISSING_TEACHER_RULE", -1, "A scheduled teacher lacks an explicit availability rule."),)

    instructional = defaultdict(list)
    by_template_period = defaultdict(list)
    for period in periods.values():
        by_template_period[period.template_id].append(period)
        if period.instructional:
            instructional[period.template_id].append((period.start_minute, period.end_minute))

    by_staff = defaultdict(lambda: defaultdict(list))
    findings: list[TeacherFeasibilityFinding] = []
    for index, placement in enumerate(placements):
        section, period = sections[placement.section_id], periods[placement.period_id]
        interval = (period.start_minute, period.end_minute)
        for staff in section.teacher_ids:
            rule = teacher_rules[staff]
            unavailable = [
                p for p in by_template_period[period.template_id]
                if p.period_id in rule.unavailable_period_ids
            ]
            if any(_overlap(interval, (p.start_minute, p.end_minute)) for p in unavailable):
                findings.append(TeacherFeasibilityFinding(
                    "TEACHER_UNAVAILABLE", index,
                    "A teacher is unavailable during a proposed placement.",
                ))
            by_staff[staff][period.template_id].append(interval)
            if len(findings) >= MAX_FINDINGS:
                return tuple(findings[:MAX_FINDINGS]) + (
                    TeacherFeasibilityFinding("FINDINGS_TRUNCATED", -1, "Additional findings omitted."),)

    for staff in sorted(expected_staff):
        rule = teacher_rules[staff]
        work = 0
        prep = 0
        for template_id, repeat in template_occurrences.items():
            teaching = by_staff[staff][template_id]
            unavailable = [
                (p.start_minute, p.end_minute)
                for p in by_template_period[template_id]
                if p.period_id in rule.unavailable_period_ids
            ]
            work += repeat * _minutes(teaching)
            prep += repeat * _free_minutes(instructional[template_id], teaching + unavailable)
        if work > rule.max_instructional_minutes_per_cycle:
            findings.append(TeacherFeasibilityFinding(
                "TEACHER_OVERLOAD", -1, "Proposed teaching exceeds an authorized cycle limit."))
        if prep < rule.minimum_preparation_minutes_per_cycle:
            findings.append(TeacherFeasibilityFinding(
                "INSUFFICIENT_PREPARATION", -1, "Proposed schedule provides insufficient free instructional time."))
        if len(findings) >= MAX_FINDINGS:
            return tuple(findings[:MAX_FINDINGS]) + (
                TeacherFeasibilityFinding("FINDINGS_TRUNCATED", -1, "Additional findings omitted."),)
    return tuple(findings)
