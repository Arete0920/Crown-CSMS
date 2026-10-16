"""Deterministic multi-meeting checks against a separate exhaustive oracle.

All data are invented for testing; no database, student PII, or published
schedule writes. Full school optimization certification remains separate.
"""
from itertools import product
from random import Random

from section_scheduler_wizard.multi_meeting import (
    MeetingChoice, MeetingRequirement, optimize_multi_meeting,
)
from section_scheduler_wizard.planning_inputs import TeacherPlanningRule
from section_scheduler_wizard.preflight import (
    CandidatePlacement, PeriodInput, RoomInput, SectionInput, validate_candidate_placements,
)
from section_scheduler_wizard.teacher_feasibility import validate_teacher_feasibility


def _valid(data, placements):
    return (
        not validate_candidate_placements(
            school_id=data["school_id"], academic_year_id=data["academic_year_id"],
            term_code=data["term_code"], sections=data["sections"], periods=data["periods"],
            rooms=data["rooms"], placements=placements,
        )
        and not validate_teacher_feasibility(
            school_id=data["school_id"], academic_year_id=data["academic_year_id"],
            term_code=data["term_code"], sections=data["sections"], periods=data["periods"],
            rooms=data["rooms"], placements=placements,
            teacher_rules=data["teacher_rules"],
            template_occurrences=data["template_occurrences"],
        )
    )


def test_randomized_small_school_results_match_independent_exhaustive_oracle():
    random = Random(83712)
    for meeting_count in range(1, 6):
        for _case in range(60):
            sections = {
                "sec": SectionInput("sec", "school", "year", "S1",
                                    frozenset({"teacher"}), frozenset({"student"}), True),
            }
            periods = {
                f"p{i}": PeriodInput(f"p{i}", "school", "year", "A",
                                      480 + 45*i, 525 + 45*i, True)
                for i in range(5)
            }
            rooms = {"room": RoomInput("room", "school", 10)}
            rules = {
                "teacher": TeacherPlanningRule(
                    "teacher", "school", "year", "S1", frozenset(), 270, 0),
            }
            requirements = tuple(
                MeetingRequirement(
                    f"meeting-{k}", "sec",
                    tuple(MeetingChoice(CandidatePlacement("sec", f"p{i}", "room"),
                                        random.randrange(0, 8))
                          for i in sorted(random.sample(range(5),
                                                        random.randrange(1, 5)))),
                )
                for k in range(meeting_count)
            )
            inputs = dict(
                school_id="school", academic_year_id="year", term_code="S1",
                sections=sections, periods=periods, rooms=rooms,
                requirements=requirements, teacher_rules=rules,
                template_occurrences={"A": 1},
            )
            actual = optimize_multi_meeting(**inputs, node_limit=20000)
            scores = []
            for choice_set in product(*(r.choices for r in requirements)):
                placements = tuple(choice.placement for choice in choice_set)
                if _valid(inputs, placements):
                    scores.append(sum(choice.preference_penalty for choice in choice_set))
            if scores:
                assert actual.status == "OPTIMAL", (inputs, actual)
                assert actual.optimality_proven
                assert actual.preference_penalty == min(scores)
                assert _valid(inputs, actual.placements)
            else:
                assert actual.status == "INFEASIBLE", (inputs, actual)


def test_250_synthetic_students_20_sections_two_meetings_per_section():
    school, year, term = "school", "year", "S1"
    periods = {
        f"{day}{slot}": PeriodInput(
            f"{day}{slot}", school, year, day, 480+60*slot, 540+60*slot, True)
        for day in ("A", "B") for slot in range(10)
    }
    rooms = {f"room-{j}": RoomInput(f"room-{j}", school, 25) for j in range(2)}
    sections = {
        f"section-{i}": SectionInput(
            f"section-{i}", school, year, term,
            frozenset({f"teacher-{i%5}"}),
            frozenset(f"student-{j}" for j in range(i, 250, 20)), True,
        )
        for i in range(20)
    }
    requirements = tuple(
        MeetingRequirement(
            f"section-{i}/{day}", f"section-{i}",
            (MeetingChoice(CandidatePlacement(
                f"section-{i}", f"{day}{(i//2+(0 if day=='A' else 1))%10}",
                f"room-{i%2}"), 0),),
        )
        for i in range(20) for day in ("A", "B")
    )
    rules = {
        f"teacher-{i}": TeacherPlanningRule(
            f"teacher-{i}", school, year, term, frozenset(), 600, 0)
        for i in range(5)
    }
    result = optimize_multi_meeting(
        school_id=school, academic_year_id=year, term_code=term,
        sections=sections, periods=periods, rooms=rooms, requirements=requirements,
        teacher_rules=rules, template_occurrences={"A": 1, "B": 1},
        node_limit=100,
    )
    assert result.status == "OPTIMAL"
    assert result.optimality_proven
    assert result.explored_nodes == 40
    assert result.preference_penalty == 0
    assert len(result.placements) == 40
    distinct_students = set().union(*(s.student_ids for s in sections.values()))
    assert len(distinct_students) == 250
    assert _valid({
        "school_id": school, "academic_year_id": year, "term_code": term,
        "sections": sections, "periods": periods, "rooms": rooms,
        "teacher_rules": rules, "template_occurrences": {"A": 1, "B": 1},
    }, result.placements)
