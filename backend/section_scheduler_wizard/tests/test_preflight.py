"""Behavioral checks for the pure Kairos candidate-placement preflight."""

from section_scheduler_wizard.preflight import (
    MAX_CANDIDATE_PLACEMENTS,
    MAX_REPORTED_FINDINGS,
    CandidatePlacement,
    PeriodInput,
    RoomInput,
    SectionInput,
    validate_candidate_placements,
)


def sample():
    sections = {
        "english": SectionInput("english", "school-a", "year-a", "S1", frozenset({"teacher-1"}), frozenset({"student-1", "student-2"}), True),
        "math": SectionInput("math", "school-a", "year-a", "S1", frozenset({"teacher-2"}), frozenset({"student-3"}), True),
    }
    periods = {
        "p1": PeriodInput("p1", "school-a", "year-a", "day-a", 480, 540, True),
        "p2": PeriodInput("p2", "school-a", "year-a", "day-a", 540, 600, True),
        "p1b": PeriodInput("p1b", "school-a", "year-a", "day-b", 480, 540, True),
        "chapel": PeriodInput("chapel", "school-a", "year-a", "day-a", 600, 660, False),
    }
    rooms = {
        "one": RoomInput("one", "school-a", 20),
        "two": RoomInput("two", "school-a", 20),
    }
    return sections, periods, rooms


def check(placements, sections=None, periods=None, rooms=None):
    base = sample()
    return validate_candidate_placements(
        school_id="school-a", academic_year_id="year-a", term_code="S1",
        sections=sections if sections is not None else base[0],
        periods=periods if periods is not None else base[1],
        rooms=rooms if rooms is not None else base[2], placements=placements,
    )


def codes(findings):
    return {finding.code for finding in findings}


def test_valid_placements_have_no_findings():
    assert check([CandidatePlacement("english", "p1", "one"), CandidatePlacement("math", "p2", "one")]) == ()


def test_different_day_templates_do_not_conflict():
    assert check([CandidatePlacement("english", "p1", "one"), CandidatePlacement("math", "p1b", "one")]) == ()


def test_overlapping_ranges_not_just_identical_period_ids_are_checked():
    sections, periods, rooms = sample()
    periods["overlap"] = PeriodInput("overlap", "school-a", "year-a", "day-a", 510, 570, True)
    sections["math"] = SectionInput("math", "school-a", "year-a", "S1", frozenset({"teacher-1"}), frozenset({"student-2"}), True)
    result = check([CandidatePlacement("english", "p1", "one"), CandidatePlacement("math", "overlap", "one")], sections, periods, rooms)
    assert codes(result) == {"ROOM_OVERLAP", "TEACHER_OVERLAP", "STUDENT_OVERLAP"}


def test_chapel_protected_and_capacity():
    sections, periods, rooms = sample()
    rooms["one"] = RoomInput("one", "school-a", 1)
    result = check([CandidatePlacement("english", "chapel", "one")], sections, periods, rooms)
    assert codes(result) == {"PROTECTED_PERIOD", "ROOM_CAPACITY"}


def test_foreign_school_and_year_records_fail_closed():
    sections, periods, rooms = sample()
    sections["math"] = SectionInput("math", "school-b", "year-a", "S1", frozenset({"teacher-2"}), frozenset(), True)
    periods["p1"] = PeriodInput("p1", "school-a", "year-b", "day-a", 480, 540, True)
    rooms["one"] = RoomInput("one", "school-b", 20)
    result = check([CandidatePlacement("math", "p1", "one")], sections, periods, rooms)
    assert codes(result) == {"INVALID_SECTION_SCOPE", "INVALID_PERIOD_SCOPE", "INVALID_ROOM_SCOPE"}


def test_unverified_roster_and_missing_teacher_fail_closed():
    sections, periods, rooms = sample()
    sections["english"] = SectionInput("english", "school-a", "year-a", "S1", frozenset(), frozenset(), False)
    result = check([CandidatePlacement("english", "p1", "one")], sections, periods, rooms)
    assert codes(result) == {"ROSTER_NOT_VERIFIED", "TEACHER_NOT_ASSIGNED"}


def test_invalid_time_and_unknown_references():
    sections, periods, rooms = sample()
    periods["p1"] = PeriodInput("p1", "school-a", "year-a", "day-a", 720, 700, True)
    result = check([CandidatePlacement("english", "p1", "one"), CandidatePlacement("invalid", "p2", "two"), CandidatePlacement("math", "missing", "two")], sections, periods, rooms)
    assert codes(result) == {"INVALID_PERIOD_TIME", "INVALID_SECTION_SCOPE", "INVALID_PERIOD_SCOPE"}


def test_same_section_same_time_rejected_even_when_room_differs():
    result = check([CandidatePlacement("english", "p1", "one"), CandidatePlacement("english", "p1", "two")])
    assert "SECTION_OVERLAP" in codes(result)


def test_placement_limit_and_missing_scope():
    assert codes(check([CandidatePlacement("english", "p1")] * (MAX_CANDIDATE_PLACEMENTS + 1))) == {"TOO_MANY_PLACEMENTS"}
    assert codes(validate_candidate_placements(school_id="", academic_year_id="year-a", term_code="S1", sections={}, periods={}, rooms={}, placements=[])) == {"MISSING_SCOPE"}


def test_does_not_modify_input_collections():
    sections, periods, rooms = sample()
    placements = [CandidatePlacement("english", "p1", "one")]
    before = (dict(sections), dict(periods), dict(rooms), list(placements))
    assert check(placements, sections, periods, rooms) == ()
    assert (sections, periods, rooms, placements) == before


def test_empty_candidate_set_is_not_mistaken_for_valid_schedule():
    assert codes(check([])) == {"NO_PLACEMENTS"}

def test_high_conflict_input_returns_bounded_findings():
    proposals = [CandidatePlacement("english", "p1", "one")] * 60
    result = check(proposals)
    assert len(result) == MAX_REPORTED_FINDINGS + 1
    assert result[-1].code == "FINDINGS_TRUNCATED"
