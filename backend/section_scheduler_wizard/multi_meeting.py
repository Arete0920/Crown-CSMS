"""Bounded deterministic multi-meeting timetabling with soft placement preferences.

This is a pure read-only solver for *supplied canonical meeting requirements*.
It never infers a school's required contact hours, writes records, or publishes.
Every successful plan is independently validated by existing CROWN hard checks.
OPTIMAL means optimal only across the explicitly supplied finite domains and
integer soft costs, never a globally optimal school timetable.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

from .preflight import CandidatePlacement, PeriodInput, RoomInput, SectionInput, validate_candidate_placements
from .planning_inputs import TeacherPlanningRule, validate_planning_inputs
from .teacher_feasibility import MAX_CYCLE_OCCURRENCES, validate_teacher_feasibility

MAX_MEETINGS = 64
MAX_CHOICES_PER_MEETING = 24
MAX_CANDIDATES = 512
MAX_NODES = 20000
DEFAULT_NODES = 2500


@dataclass(frozen=True)
class MeetingChoice:
    placement: CandidatePlacement
    preference_penalty: int = 0


@dataclass(frozen=True)
class MeetingRequirement:
    meeting_id: str
    section_id: str
    choices: tuple[MeetingChoice, ...]


@dataclass(frozen=True)
class MultiMeetingSolution:
    status: str
    placements: tuple[CandidatePlacement, ...]
    meeting_ids: tuple[str, ...]
    preference_penalty: int | None
    explored_nodes: int
    optimality_proven: bool
    diagnostics: tuple[str, ...]


def _invalid(code: str) -> MultiMeetingSolution:
    return MultiMeetingSolution("MODEL_INVALID", (), (), None, 0, False, (code,))


def optimize_multi_meeting(
    *, school_id: str, academic_year_id: str, term_code: str,
    sections: Mapping[str, SectionInput], periods: Mapping[str, PeriodInput],
    rooms: Mapping[str, RoomInput], requirements: Sequence[MeetingRequirement],
    teacher_rules: Mapping[str, TeacherPlanningRule],
    template_occurrences: Mapping[str, int], node_limit: int = DEFAULT_NODES,
) -> MultiMeetingSolution:
    """Find least-penalized verified multi-meeting plan within an explicit budget."""
    if (
        not all(isinstance(x, str) and x for x in (school_id, academic_year_id, term_code))
        or type(node_limit) is not int or not 1 <= node_limit <= MAX_NODES
        or not isinstance(requirements, (tuple, list)) or not 1 <= len(requirements) <= MAX_MEETINGS
        or not sections or len(sections) > MAX_MEETINGS or not periods or len(periods) > 1000
        or len(rooms) > 1000 or len(teacher_rules) > 1000
    ):
        return _invalid("INVALID_SCOPE_OR_BOUNDS")
    if any(
        key != section.section_id
        or (section.school_id, section.academic_year_id, section.term_code)
            != (school_id, academic_year_id, term_code)
        or section.roster_verified is not True or not section.teacher_ids
        or len(section.teacher_ids) > 16 or len(section.student_ids) > 1000
        for key, section in sections.items()
    ):
        return _invalid("UNVERIFIED_SECTION_AUTHORITY")
    if any(
        key != room.room_id or room.school_id != school_id
        or type(room.capacity) is not int or room.capacity < 1
        for key, room in rooms.items()
    ):
        return _invalid("UNVERIFIED_ROOM_AUTHORITY")
    if any(
        key != period.period_id
        or (period.school_id, period.academic_year_id) != (school_id, academic_year_id)
        or type(period.instructional) is not bool
        or type(period.start_minute) is not int or type(period.end_minute) is not int
        or not 0 <= period.start_minute < period.end_minute <= 1440
        or not period.template_id
        for key, period in periods.items()
    ):
        return _invalid("UNVERIFIED_PERIOD_AUTHORITY")
    if (
        set(template_occurrences) != {p.template_id for p in periods.values()}
        or any(type(x) is not int or not 1 <= x <= MAX_CYCLE_OCCURRENCES
               for x in template_occurrences.values())
        or sum(template_occurrences.values()) > MAX_CYCLE_OCCURRENCES
    ):
        return _invalid("INVALID_CYCLE")
    known_staff = frozenset(st for sec in sections.values() for st in sec.teacher_ids)
    if set(teacher_rules) != set(known_staff) or validate_planning_inputs(
        school_id=school_id, academic_year_id=academic_year_id,
        term_code=term_code, known_staff_ids=known_staff,
        known_student_ids=frozenset(), known_course_ids=frozenset(),
        known_period_ids=frozenset(periods), teacher_rules=teacher_rules,
        student_requests=(),
    ):
        return _invalid("INVALID_TEACHER_POLICY")
    meeting_ids: set[str] = set()
    total = 0
    domains: dict[str, tuple[MeetingChoice, ...]] = {}
    sections_covered: set[str] = set()
    for req in requirements:
        if (
            not isinstance(req, MeetingRequirement) or not isinstance(req.meeting_id, str)
            or not req.meeting_id or req.meeting_id in meeting_ids
            or not isinstance(req.section_id, str) or req.section_id not in sections
            or not isinstance(req.choices, (tuple, list))
            or not 1 <= len(req.choices) <= MAX_CHOICES_PER_MEETING
        ):
            return _invalid("INVALID_MEETING_REQUIREMENT")
        meeting_ids.add(req.meeting_id)
        sections_covered.add(req.section_id)
        unique: dict[tuple[str, str, str | None], MeetingChoice] = {}
        for choice in req.choices:
            if not isinstance(choice, MeetingChoice) or not isinstance(choice.placement, CandidatePlacement):
                return _invalid("MALFORMED_MEETING_CHOICE")
            p = choice.placement
            if (
                p.section_id != req.section_id or not isinstance(p.period_id, str)
                or not isinstance(p.room_id, str) or p.room_id not in rooms
                or p.period_id not in periods
                or type(choice.preference_penalty) is not int
                or not 0 <= choice.preference_penalty <= 1000
            ):
                return _invalid("INVALID_CHOICE_OR_COST")
            period = periods[p.period_id]
            if not period.instructional:
                return _invalid("PROTECTED_CHOICE")
            if any(
                other.template_id == period.template_id and not other.instructional
                and max(other.start_minute, period.start_minute)
                    < min(other.end_minute, period.end_minute)
                for other in periods.values()
            ):
                return _invalid("OVERLAPS_PROTECTED_TIME")
            if validate_candidate_placements(
                school_id=school_id, academic_year_id=academic_year_id,
                term_code=term_code, sections=sections, periods=periods,
                rooms=rooms, placements=(p,),
            ):
                return _invalid("CHOICE_PREFLIGHT_FAILED")
            key = (p.section_id, p.period_id, p.room_id)
            old = unique.get(key)
            if old is None or choice.preference_penalty < old.preference_penalty:
                unique[key] = choice
        total += len(unique)
        if total > MAX_CANDIDATES:
            return _invalid("CANDIDATE_LIMIT")
        domains[req.meeting_id] = tuple(sorted(
            unique.values(), key=lambda c: (
                c.preference_penalty, c.placement.period_id, c.placement.room_id or ""
            )
        ))
    if sections_covered != set(sections):
        return _invalid("UNSCHEDULED_CANONICAL_SECTION")

    ordered = tuple(sorted(requirements, key=lambda r: (len(domains[r.meeting_id]), r.meeting_id)))
    suffix_min = [0] * (len(ordered) + 1)
    for i in range(len(ordered)-1, -1, -1):
        suffix_min[i] = suffix_min[i+1] + domains[ordered[i].meeting_id][0].preference_penalty
    visited = 0
    exhausted = False
    best: tuple[tuple[CandidatePlacement, ...], tuple[str, ...], int] | None = None
    errors: set[str] = set()

    def visit(depth: int, assigned: list[CandidatePlacement], labels: list[str], cost: int) -> None:
        nonlocal visited, exhausted, best
        if exhausted:
            return
        if best is not None and cost + suffix_min[depth] >= best[2]:
            return
        if depth == len(ordered):
            failures = validate_teacher_feasibility(
                school_id=school_id, academic_year_id=academic_year_id,
                term_code=term_code, sections=sections, periods=periods,
                rooms=rooms, placements=tuple(assigned),
                teacher_rules=teacher_rules,
                template_occurrences=template_occurrences,
            )
            if failures:
                errors.update(f.code for f in failures)
            else:
                best = (tuple(assigned), tuple(labels), cost)
            return
        meeting = ordered[depth]
        for choice in domains[meeting.meeting_id]:
            if visited >= node_limit:
                exhausted = True
                return
            visited += 1
            assigned.append(choice.placement)
            labels.append(meeting.meeting_id)
            collisions = validate_candidate_placements(
                school_id=school_id, academic_year_id=academic_year_id,
                term_code=term_code, sections=sections, periods=periods,
                rooms=rooms, placements=tuple(assigned),
            )
            if collisions:
                errors.update(f.code for f in collisions)
            else:
                visit(depth+1, assigned, labels, cost + choice.preference_penalty)
            assigned.pop()
            labels.pop()
            if exhausted:
                return

    visit(0, [], [], 0)
    if best is None:
        return MultiMeetingSolution(
            "UNKNOWN" if exhausted else "INFEASIBLE", (), (), None, visited,
            False if exhausted else True,
            (("NODE_LIMIT",) if exhausted else ()) + tuple(sorted(errors))[:12]
            or (("NO_VALID_COMBINATION",) if not exhausted else ("NODE_LIMIT",)),
        )
    placements, labels, score = best
    if validate_candidate_placements(
        school_id=school_id, academic_year_id=academic_year_id,
        term_code=term_code, sections=sections, periods=periods,
        rooms=rooms, placements=placements,
    ) or validate_teacher_feasibility(
        school_id=school_id, academic_year_id=academic_year_id,
        term_code=term_code, sections=sections, periods=periods,
        rooms=rooms, placements=placements, teacher_rules=teacher_rules,
        template_occurrences=template_occurrences,
    ):
        return _invalid("FINAL_HARD_REVALIDATION_FAILED")
    return MultiMeetingSolution(
        "FEASIBLE" if exhausted else "OPTIMAL", placements, labels,
        score, visited, not exhausted, (),
    )
