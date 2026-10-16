"""Synthetic 250-student / 20-section Kairos bounded-search acceptance.

Pure algorithm evidence only: not equivalent to a full school timetable,
canonical school-data authorization, ranked elective fulfillment or deployment.
"""
from collections import Counter

from section_scheduler_wizard.bounded_feasibility import FEASIBLE, solve_section_meetings
from section_scheduler_wizard.planning_inputs import TeacherPlanningRule
from section_scheduler_wizard.preflight import (
    CandidatePlacement, PeriodInput, RoomInput, SectionInput,
    validate_candidate_placements,
)
from section_scheduler_wizard.teacher_feasibility import validate_teacher_feasibility


def synthetic_school_250():
    school, year, term = "synthetic-school", "2026-2027", "S1"
    student_ids = tuple(f"student-{i:03d}" for i in range(250))
    sections = {}
    periods = {}
    candidate_domains = {}
    for day in ("A", "B"):
        for slot in range(10):
            period_id = f"{day}-{slot}"
            start = 480 + slot * 60
            periods[period_id] = PeriodInput(
                period_id, school, year, day, start, start + 60, True,
            )
    for i in range(20):
        sec_id = f"section-{i:02d}"
        staff_id = f"teacher-{i % 5}"
        enrolled = frozenset(student_ids[j] for j in range(i, 250, 20))
        sections[sec_id] = SectionInput(
            sec_id, school, year, term, frozenset({staff_id}), enrolled, True,
        )
        template = "A" if i < 10 else "B"
        slot = i if i < 10 else i - 10
        candidate_domains[sec_id] = (
            CandidatePlacement(sec_id, f"{template}-{slot}", "room-101"),
        )
    policies = {
        f"teacher-{i}": TeacherPlanningRule(
            f"teacher-{i}", school, year, term, frozenset(), 240, 0,
        )
        for i in range(5)
    }
    return {
        "school_id": school, "academic_year_id": year, "term_code": term,
        "sections": sections, "periods": periods,
        "rooms": {"room-101": RoomInput("room-101", school, 25)},
        "candidate_domains": candidate_domains,
        "teacher_rules": policies,
        "template_occurrences": {"A": 1, "B": 1},
        "node_limit": 2500,
    }


def test_250_synthetic_students_unique_rosters_feasible_and_deterministic():
    data = synthetic_school_250()
    all_students = [student for section in data["sections"].values()
                    for student in section.student_ids]
    assert len(all_students) == 250
    assert len(set(all_students)) == 250
    assert len(data["sections"]) == 20
    assert len(data["teacher_rules"]) == 5
    assert max(map(len, (s.student_ids for s in data["sections"].values()))) <= 25
    first = solve_section_meetings(**data)
    second = solve_section_meetings(**data)
    assert first.status == FEASIBLE, first.diagnostics
    assert first == second
    assert len(first.placements) == 20
    assert not validate_candidate_placements(
        school_id=data["school_id"], academic_year_id=data["academic_year_id"],
        term_code=data["term_code"], sections=data["sections"],
        periods=data["periods"], rooms=data["rooms"], placements=first.placements,
    )
    assert not validate_teacher_feasibility(
        school_id=data["school_id"], academic_year_id=data["academic_year_id"],
        term_code=data["term_code"], sections=data["sections"],
        periods=data["periods"], rooms=data["rooms"], placements=first.placements,
        teacher_rules=data["teacher_rules"],
        template_occurrences=data["template_occurrences"],
    )
    counts = Counter(p.section_id for p in first.placements)
    assert set(counts.values()) == {1}
