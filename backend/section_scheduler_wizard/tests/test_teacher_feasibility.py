"""Pure Kairos teacher-cycle tests with synthetic data, no student PII."""
from dataclasses import replace

from section_scheduler_wizard.planning_inputs import TeacherPlanningRule
from section_scheduler_wizard.preflight import (
    CandidatePlacement, PeriodInput, RoomInput, SectionInput,
)
from section_scheduler_wizard.teacher_feasibility import validate_teacher_feasibility


def fixture():
    sections = {
        "english": SectionInput("english", "school", "year", "S1", frozenset({"t1"}), frozenset({"s1"}), True),
        "math": SectionInput("math", "school", "year", "S1", frozenset({"t2"}), frozenset({"s2"}), True),
    }
    periods = {
        "a1": PeriodInput("a1", "school", "year", "A", 480, 540, True),
        "a2": PeriodInput("a2", "school", "year", "A", 540, 600, True),
        "b1": PeriodInput("b1", "school", "year", "B", 480, 540, True),
        "b2": PeriodInput("b2", "school", "year", "B", 540, 600, True),
        "chapel": PeriodInput("chapel", "school", "year", "A", 600, 660, False),
    }
    rooms = {"r": RoomInput("r", "school", 24)}
    rules = {
        "t1": TeacherPlanningRule("t1", "school", "year", "S1", frozenset({"a2"}), 120, 60),
        "t2": TeacherPlanningRule("t2", "school", "year", "S1", frozenset(), 240, 0),
    }
    placements = [CandidatePlacement("english", "a1", "r"), CandidatePlacement("english", "b1", "r")]
    return {
        "school_id": "school", "academic_year_id": "year", "term_code": "S1",
        "sections": sections, "periods": periods, "rooms": rooms,
        "placements": placements, "teacher_rules": rules,
        "template_occurrences": {"A": 1, "B": 1},
    }


def findings(**changes):
    values = fixture()
    values.update(changes)
    return validate_teacher_feasibility(**values)


def codes(**changes):
    return {f.code for f in findings(**changes)}


def test_two_template_cycle_with_availability_and_prep_passes():
    assert findings() == ()


def test_unavailable_teacher_period_is_denied():
    values = fixture()
    values["teacher_rules"]["t1"] = replace(values["teacher_rules"]["t1"], unavailable_period_ids=frozenset({"a1"}))
    assert "TEACHER_UNAVAILABLE" in codes(**values)


def test_overlapping_unavailable_period_denied_even_if_id_differs():
    values = fixture()
    values["periods"]["blocked"] = PeriodInput("blocked", "school", "year", "A", 510, 570, False)
    values["teacher_rules"]["t1"] = replace(values["teacher_rules"]["t1"], unavailable_period_ids=frozenset({"blocked"}))
    assert "TEACHER_UNAVAILABLE" in codes(**values)


def test_staff_max_minutes_enforced_with_occurrence_weights():
    values = fixture()
    values["teacher_rules"]["t1"] = replace(values["teacher_rules"]["t1"], max_instructional_minutes_per_cycle=100)
    assert "TEACHER_OVERLOAD" in codes(**values)


def test_minimum_preparation_enforced_after_unavailability():
    values = fixture()
    values["teacher_rules"]["t1"] = replace(values["teacher_rules"]["t1"], minimum_preparation_minutes_per_cycle=61)
    assert "INSUFFICIENT_PREPARATION" in codes(**values)


def test_cycle_counts_cannot_be_guessed_or_boolean():
    assert codes(template_occurrences={"A": 1}) == {"CYCLE_UNDEFINED"}
    assert codes(template_occurrences={"A": 1, "B": True}) == {"INVALID_CYCLE"}
    assert codes(template_occurrences={"A": 0, "B": 1}) == {"INVALID_CYCLE"}
    assert codes(template_occurrences={"A": 12, "B": 3}) == {"INVALID_CYCLE"}


def test_two_cycle_occurrences_are_counted_explicitly():
    values = fixture()
    values["template_occurrences"] = {"A": 2, "B": 1}
    assert "TEACHER_OVERLOAD" in codes(**values)


def test_foreign_or_spoofed_period_mapping_rejected():
    values = fixture()
    values["periods"]["a1"] = replace(values["periods"]["a1"], school_id="other")
    assert codes(**values) == {"INVALID_PERIODS"}
    values = fixture()
    values["periods"]["a1"] = replace(values["periods"]["a1"], period_id="fake")
    assert codes(**values) == {"INVALID_PERIODS"}


def test_missing_teacher_policy_fails_closed():
    values = fixture()
    values["teacher_rules"].pop("t1")
    assert codes(**values) == {"MISSING_TEACHER_RULE"}


def test_foreign_teacher_policy_fails_closed():
    values = fixture()
    values["teacher_rules"]["t1"] = replace(values["teacher_rules"]["t1"], school_id="other")
    assert codes(**values) == {"INVALID_TEACHER_RULE"}


def test_base_preflight_must_pass_before_workload_scoring():
    values = fixture()
    values["placements"] = [CandidatePlacement("english", "chapel", "r")]
    assert codes(**values) == {"PLACEMENT_PREFLIGHT_FAILED"}
    values["placements"] = []
    assert codes(**values) == {"PLACEMENT_PREFLIGHT_FAILED"}


def test_no_mutations_or_inferred_staff_rules():
    values = fixture()
    before = (dict(values["sections"]), dict(values["periods"]), list(values["placements"]), dict(values["teacher_rules"]))
    assert validate_teacher_feasibility(**values) == ()
    assert before == (values["sections"], values["periods"], values["placements"], values["teacher_rules"])


def test_overlap_union_does_not_double_count_prep():
    values = fixture()
    values["periods"]["a1dup"] = PeriodInput("a1dup", "school", "year", "A", 480, 540, True)
    assert validate_teacher_feasibility(**values) == ()


def test_bounded_placements_and_scope():
    values = fixture()
    values["school_id"] = ""
    assert codes(**values) == {"MISSING_SCOPE"}
    values = fixture()
    values["placements"] *= 2001
    assert codes(**values) == {"INPUT_LIMIT"}


def test_co_teacher_requires_policy_for_each_member():
    values = fixture()
    values["sections"]["english"] = replace(values["sections"]["english"], teacher_ids=frozenset({"t1", "t2"}))
    assert findings(**values) == ()
    values["teacher_rules"].pop("t2")
    assert codes(**values) == {"MISSING_TEACHER_RULE"}
