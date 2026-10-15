"""Synthetic bounded feasibility tests. No Django, database or PII."""
from section_scheduler_wizard.bounded_feasibility import (
    FEASIBLE, INFEASIBLE, MODEL_INVALID, UNKNOWN, solve_section_meetings,
)
from section_scheduler_wizard.planning_inputs import TeacherPlanningRule
from section_scheduler_wizard.preflight import (
    CandidatePlacement, PeriodInput, RoomInput, SectionInput,
)


def scenario():
    sections = {
        "english": SectionInput("english", "school", "year", "S1", frozenset({"t1"}), frozenset({"s1"}), True),
        "math": SectionInput("math", "school", "year", "S1", frozenset({"t1"}), frozenset({"s2"}), True),
    }
    periods = {
        "p1": PeriodInput("p1", "school", "year", "A", 480, 540, True),
        "p2": PeriodInput("p2", "school", "year", "A", 540, 600, True),
        "chapel": PeriodInput("chapel", "school", "year", "A", 600, 660, False),
    }
    return dict(
        school_id="school", academic_year_id="year", term_code="S1",
        sections=sections, periods=periods, rooms={"r": RoomInput("r", "school", 30)},
        teacher_rules={"t1": TeacherPlanningRule("t1", "school", "year", "S1", frozenset(), 120, 0)},
        template_occurrences={"A": 1},
        candidate_domains={
            "english": (CandidatePlacement("english", "p1", "r"), CandidatePlacement("english", "p2", "r")),
            "math": (CandidatePlacement("math", "p1", "r"), CandidatePlacement("math", "p2", "r")),
        },
    )


def solve(**changes):
    data = scenario()
    data.update(changes)
    return solve_section_meetings(**data)


def test_finds_conflict_free_schedule_and_is_deterministic():
    one = solve()
    two = solve()
    assert one == two
    assert one.status == FEASIBLE
    assert {p.section_id for p in one.placements} == {"english", "math"}
    assert len({p.period_id for p in one.placements}) == 2


def test_single_slot_for_shared_teacher_is_infeasible():
    x = scenario()
    x["candidate_domains"] = {
        "english": (CandidatePlacement("english", "p1", "r"),),
        "math": (CandidatePlacement("math", "p1", "r"),),
    }
    result = solve(**x)
    assert result.status == INFEASIBLE and result.placements == ()


def test_explicit_budget_limit_returns_unknown_not_infeasible():
    result = solve(node_limit=1)
    assert result.status == UNKNOWN and not result.placements
    assert "NODE_BUDGET_EXHAUSTED" in result.diagnostics


def test_invalid_or_unverified_scope_is_model_invalid():
    assert solve(school_id="other").status == MODEL_INVALID
    x = scenario()
    from dataclasses import replace
    x["sections"]["english"] = replace(x["sections"]["english"], roster_verified=False)
    assert solve(**x).status == MODEL_INVALID


def test_foreign_room_rejected():
    x = scenario()
    x["rooms"]["r"] = RoomInput("r", "foreign", 30)
    assert solve(**x).status == MODEL_INVALID


def test_protected_chapel_domain_is_rejected():
    x = scenario()
    x["candidate_domains"]["english"] = (CandidatePlacement("english", "chapel", "r"),)
    assert solve(**x).status == MODEL_INVALID


def test_unknown_period_rejected():
    x = scenario()
    x["candidate_domains"]["english"] = (CandidatePlacement("english", "missing", "r"),)
    assert solve(**x).status == MODEL_INVALID


def test_no_domain_or_missing_section_is_invalid():
    assert solve(candidate_domains={}).status == MODEL_INVALID
    x = scenario()
    x["candidate_domains"]["english"] = ()
    assert solve(**x).status == MODEL_INVALID


def test_teacher_cycle_limits_enforced_as_infeasible():
    x = scenario()
    from dataclasses import replace
    x["teacher_rules"]["t1"] = replace(x["teacher_rules"]["t1"], max_instructional_minutes_per_cycle=60)
    assert solve(**x).status == INFEASIBLE


def test_explicit_unavailability_enforced():
    x = scenario()
    from dataclasses import replace
    x["teacher_rules"]["t1"] = replace(x["teacher_rules"]["t1"], unavailable_period_ids=frozenset({"p1"}))
    assert solve(**x).status == INFEASIBLE


def test_invalid_node_limits_never_start_search():
    assert solve(node_limit=0).status == MODEL_INVALID
    assert solve(node_limit=True).status == MODEL_INVALID


def test_domain_limit_rejected():
    x = scenario()
    x["candidate_domains"]["english"] = tuple(
        CandidatePlacement("english", "p1", "r") for _ in range(33)
    )
    assert solve(**x).status == MODEL_INVALID


def test_pure_no_mutation():
    data = scenario()
    prior = {key: tuple(value) for key, value in data["candidate_domains"].items()}
    result = solve_section_meetings(**data)
    assert result.status == FEASIBLE
    assert prior == {key: tuple(value) for key, value in data["candidate_domains"].items()}


def test_missing_teacher_policy_is_invalid_model_not_infeasibility():
    x = scenario()
    x["teacher_rules"] = {}
    result = solve(**x)
    assert result.status == MODEL_INVALID
    assert "MISSING_TEACHER_POLICY" in result.diagnostics


def test_invalid_cycle_count_is_invalid_model_not_unknown():
    x = scenario()
    x["template_occurrences"] = {"A": True}
    result = solve(**x)
    assert result.status == MODEL_INVALID
    assert "INVALID_CYCLE_CONTRACT" in result.diagnostics


def test_foreign_teacher_policy_cannot_produce_infeasibility_claim():
    from dataclasses import replace
    x = scenario()
    x["teacher_rules"]["t1"] = replace(x["teacher_rules"]["t1"], school_id="foreign")
    assert solve(**x).status == MODEL_INVALID


def test_spoofed_period_mapping_is_invalid_model():
    from dataclasses import replace
    x = scenario()
    x["periods"]["p1"] = replace(x["periods"]["p1"], period_id="forged")
    assert solve(**x).status == MODEL_INVALID


def test_oversized_room_catalog_rejected_before_search():
    x = scenario()
    x["rooms"] = {str(i): RoomInput(str(i), "school", 20) for i in range(1001)}
    assert solve(**x).status == MODEL_INVALID


def test_oversized_roster_rejected_before_search():
    from dataclasses import replace
    x = scenario()
    x["sections"]["english"] = replace(
        x["sections"]["english"], student_ids=frozenset(str(i) for i in range(1001))
    )
    assert solve(**x).status == MODEL_INVALID


def test_unverified_truthy_roster_flag_rejected():
    from dataclasses import replace
    x = scenario()
    x["sections"]["english"] = replace(x["sections"]["english"], roster_verified=1)
    assert solve(**x).status == MODEL_INVALID


def test_student_conflict_cannot_be_returned_as_feasible():
    from dataclasses import replace
    x = scenario()
    x["sections"]["math"] = replace(
        x["sections"]["math"], student_ids=frozenset({"s1"})
    )
    x["candidate_domains"] = {
        "english": (CandidatePlacement("english", "p1", "r"),),
        "math": (CandidatePlacement("math", "p1", "r"),),
    }
    assert solve(**x).status == INFEASIBLE


def test_room_capacity_violation_is_invalid_candidate_input():
    x = scenario()
    x["rooms"]["r"] = RoomInput("r", "school", 0)
    assert solve(**x).status == MODEL_INVALID


def test_separate_day_templates_are_independent_if_cycles_valid():
    from dataclasses import replace
    x = scenario()
    x["periods"]["bp1"] = PeriodInput("bp1", "school", "year", "B", 480, 540, True)
    x["candidate_domains"] = {
        "english": (CandidatePlacement("english", "p1", "r"),),
        "math": (CandidatePlacement("math", "bp1", "r"),),
    }
    x["template_occurrences"] = {"A": 1, "B": 1}
    assert solve(**x).status == FEASIBLE


def test_overlapping_chapel_blocks_disallow_candidate():
    x = scenario()
    x["periods"]["chapel"] = PeriodInput(
        "chapel", "school", "year", "A", 510, 570, False
    )
    assert solve(**x).status == INFEASIBLE


def test_malformed_candidate_is_invalid_not_server_error():
    x = scenario()
    x["candidate_domains"]["english"] = ({"section_id": "english"},)
    assert solve(**x).status == MODEL_INVALID


def test_unhashable_candidate_field_is_denied():
    x = scenario()
    x["candidate_domains"]["english"] = (
        CandidatePlacement("english", ["p1"], "r"),
    )
    assert solve(**x).status == MODEL_INVALID
