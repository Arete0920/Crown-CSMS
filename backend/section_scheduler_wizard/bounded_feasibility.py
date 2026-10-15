"""Bounded deterministic *feasibility* search for one meeting per section.

Internal, read-only original Kairos prototype. This is not CP-SAT, does not
optimize student elective rankings, and cannot publish schedules. Only an
authenticated, school-authorized caller may supply canonical snapshot data.
MODEL_INVALID, FEASIBLE, INFEASIBLE and UNKNOWN are distinct outcomes.
Every returned solution is independently checked by the existing hard
placement and teacher-cycle validators. An UNKNOWN never means infeasible.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

from .planning_inputs import TeacherPlanningRule
from .preflight import (
    CandidatePlacement, PeriodInput, RoomInput, SectionInput,
    validate_candidate_placements,
)
from .teacher_feasibility import validate_teacher_feasibility

MAX_SECTIONS = 64
MAX_CHOICES_PER_SECTION = 32
MAX_TOTAL_CHOICES = 512
MAX_NODE_LIMIT = 20000
DEFAULT_NODE_LIMIT = 2500
MAX_DIAGNOSTIC_CODES = 12

FEASIBLE = "FEASIBLE"
INFEASIBLE = "INFEASIBLE"
UNKNOWN = "UNKNOWN"
MODEL_INVALID = "MODEL_INVALID"


@dataclass(frozen=True)
class FeasibilityResult:
    status: str
    placements: tuple[CandidatePlacement, ...]
    nodes_visited: int
    diagnostics: tuple[str, ...]


def _result(status: str, nodes: int = 0, *codes: str) -> FeasibilityResult:
    return FeasibilityResult(status, (), nodes, tuple(codes))


def _sort_key(p: CandidatePlacement) -> tuple[str, str, str]:
    return (str(p.section_id), str(p.period_id), str(p.room_id or ""))


def solve_section_meetings(
    *,
    school_id: str,
    academic_year_id: str,
    term_code: str,
    sections: Mapping[str, SectionInput],
    periods: Mapping[str, PeriodInput],
    rooms: Mapping[str, RoomInput],
    candidate_domains: Mapping[str, Sequence[CandidatePlacement]],
    teacher_rules: Mapping[str, TeacherPlanningRule],
    template_occurrences: Mapping[str, int],
    node_limit: int = DEFAULT_NODE_LIMIT,
) -> FeasibilityResult:
    """Assign exactly one proposed meeting per supplied canonical section.

    Caller-supplied candidate domains are required (no guessed placements).
    The bounded search neither writes records nor establishes publish
    authority. A feasible candidate still requires current-DB transactional
    revalidation before any later, independently governed publish operation.
    """
    if (type(node_limit) is not int or not 1 <= node_limit <= MAX_NODE_LIMIT
            or not school_id or not academic_year_id or not term_code):
        return _result(MODEL_INVALID, 0, "INVALID_SCOPE_OR_BUDGET")
    if not sections or len(sections) > MAX_SECTIONS or set(candidate_domains) != set(sections):
        return _result(MODEL_INVALID, 0, "INVALID_SECTION_DOMAIN")
    if any(
        key != section.section_id
        or (section.school_id, section.academic_year_id, section.term_code)
           != (school_id, academic_year_id, term_code)
        or not section.roster_verified
        or not section.teacher_ids
        for key, section in sections.items()
    ):
        return _result(MODEL_INVALID, 0, "UNVERIFIED_SECTION_SCOPE")
    if any(
        key != room.room_id or room.school_id != school_id
        or type(room.capacity) is not int or room.capacity < 1
        for key, room in rooms.items()
    ):
        return _result(MODEL_INVALID, 0, "INVALID_ROOM_SCOPE")

    domains: dict[str, tuple[CandidatePlacement, ...]] = {}
    total = 0
    for section_id in sorted(sections):
        candidates = candidate_domains[section_id]
        if not candidates or len(candidates) > MAX_CHOICES_PER_SECTION:
            return _result(MODEL_INVALID, 0, "INVALID_CANDIDATE_COUNT")
        unique = tuple(sorted(set(candidates), key=_sort_key))
        total += len(unique)
        if total > MAX_TOTAL_CHOICES:
            return _result(MODEL_INVALID, 0, "CANDIDATE_LIMIT")
        for candidate in unique:
            if candidate.section_id != section_id:
                return _result(MODEL_INVALID, 0, "FOREIGN_CANDIDATE_SECTION")
            findings = validate_candidate_placements(
                school_id=school_id, academic_year_id=academic_year_id,
                term_code=term_code, sections=sections, periods=periods,
                rooms=rooms, placements=(candidate,),
            )
            if findings:
                return _result(MODEL_INVALID, 0, *sorted({f.code for f in findings}))
        domains[section_id] = unique

    # Most-constrained-first with stable ties; no randomness or global state.
    order = tuple(sorted(sections, key=lambda section: (len(domains[section]), section)))
    nodes_visited = 0
    exhausted = False
    solution: tuple[CandidatePlacement, ...] | None = None
    failures: set[str] = set()

    def search(chosen: list[CandidatePlacement], depth: int) -> None:
        nonlocal nodes_visited, exhausted, solution
        if solution is not None or exhausted:
            return
        if depth == len(order):
            verdict = validate_teacher_feasibility(
                school_id=school_id, academic_year_id=academic_year_id,
                term_code=term_code, sections=sections, periods=periods,
                rooms=rooms, placements=tuple(chosen),
                teacher_rules=teacher_rules,
                template_occurrences=template_occurrences,
            )
            if not verdict:
                solution = tuple(sorted(chosen, key=_sort_key))
            else:
                failures.update(v.code for v in verdict)
            return
        for candidate in domains[order[depth]]:
            if nodes_visited >= node_limit:
                exhausted = True
                return
            nodes_visited += 1
            chosen.append(candidate)
            collisions = validate_candidate_placements(
                school_id=school_id, academic_year_id=academic_year_id,
                term_code=term_code, sections=sections, periods=periods,
                rooms=rooms, placements=tuple(chosen),
            )
            if not collisions:
                search(chosen, depth + 1)
            else:
                failures.update(f.code for f in collisions)
            chosen.pop()
            if solution is not None or exhausted:
                return

    search([], 0)
    if solution is not None:
        # Independent final validation even though the leaf was validated.
        final = validate_teacher_feasibility(
            school_id=school_id, academic_year_id=academic_year_id,
            term_code=term_code, sections=sections, periods=periods,
            rooms=rooms, placements=solution,
            teacher_rules=teacher_rules,
            template_occurrences=template_occurrences,
        )
        if final:
            return _result(MODEL_INVALID, nodes_visited, "FINAL_REVALIDATION_FAILED")
        return FeasibilityResult(FEASIBLE, solution, nodes_visited, ())
    diagnostics = tuple(sorted(failures))[:MAX_DIAGNOSTIC_CODES]
    if exhausted:
        return FeasibilityResult(UNKNOWN, (), nodes_visited, ("NODE_BUDGET_EXHAUSTED",) + diagnostics)
    return FeasibilityResult(INFEASIBLE, (), nodes_visited, diagnostics or ("NO_VALID_COMBINATION",))
