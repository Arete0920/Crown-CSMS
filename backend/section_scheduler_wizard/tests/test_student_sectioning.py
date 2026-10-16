"""Synthetic, pure student-sectioning acceptance without enrollment writes."""
from dataclasses import replace
from section_scheduler_wizard.planning_inputs import StudentCourseRequest, CourseChoice
from section_scheduler_wizard.preflight import CandidatePlacement, PeriodInput, RoomInput, SectionInput
from section_scheduler_wizard.student_sectioning import (
    COMPLETE, PARTIAL, MODEL_INVALID, construct_student_sectioning,
)

def scenario():
    sections = {
        "math-a": SectionInput("math-a","school","year","S1",frozenset({"t1"}),frozenset(),True),
        "science-a": SectionInput("science-a","school","year","S1",frozenset({"t2"}),frozenset(),True),
        "art-a": SectionInput("art-a","school","year","S1",frozenset({"t3"}),frozenset(),True),
    }
    periods = {
        "p1": PeriodInput("p1","school","year","A",480,540,True),
        "p2": PeriodInput("p2","school","year","A",540,600,True),
        "p3": PeriodInput("p3","school","year","A",600,660,True),
    }
    return dict(
        school_id="school",academic_year_id="year",term_code="S1",
        sections=sections, periods=periods,
        rooms={"r1":RoomInput("r1","school",2),"r2":RoomInput("r2","school",2),"r3":RoomInput("r3","school",2)},
        placements=(CandidatePlacement("math-a","p1","r1"),CandidatePlacement("science-a","p2","r2"),CandidatePlacement("art-a","p3","r3")),
        section_course_ids={"math-a":"math","science-a":"science","art-a":"art"},
        catalog_course_ids=frozenset({"math","science","art"}),
        verified_student_ids=frozenset({"s1","s2","s3"}),
        requests=(StudentCourseRequest("s1","school","year","S1",True,frozenset({"math","science"}),(CourseChoice("art",1),)),),
        elective_slots={"s1":1},
    )

def solve(**overrides):
    data=scenario()
    data.update(overrides)
    return construct_student_sectioning(**data)

def test_required_and_ranked_elective_allocations_are_deterministic():
    first=solve()
    assert first==solve()
    assert first.status==COMPLETE
    assert first.required_fulfilled==2 and first.elective_fulfilled==1
    assert len(first.additions)==3

def test_capacity_shortfall_is_partial_not_false_infeasible():
    x=scenario()
    x["sections"]["math-a"]=replace(x["sections"]["math-a"],student_ids=frozenset({"s2","s3"}))
    result=solve(**x)
    assert result.status==PARTIAL
    assert result.required_unfulfilled==1
    assert "REQUIRED_UNFILLED" in result.diagnostics

def test_foreign_student_identity_and_course_are_rejected():
    x=scenario()
    x["verified_student_ids"]=frozenset({"s2","s3"})
    assert solve(**x).status==MODEL_INVALID
    x=scenario()
    x["section_course_ids"]["math-a"]="foreign"
    assert solve(**x).status==MODEL_INVALID

def test_duplicate_student_request_rejected():
    x=scenario()
    x["requests"]=(x["requests"][0], x["requests"][0])
    assert solve(**x).status==MODEL_INVALID

def test_existing_enrollment_satisfies_request_without_duplicate_addition():
    x=scenario()
    x["sections"]["math-a"]=replace(x["sections"]["math-a"],student_ids=frozenset({"s1"}))
    result=solve(**x)
    assert result.status==COMPLETE
    assert not any(a.course_id=="math" for a in result.additions)

def test_conflicting_required_sections_cannot_overlap():
    x=scenario()
    x["periods"]["p2"]=PeriodInput("p2","school","year","A",510,570,True)
    result = solve(**x)
    # The empty input rosters are valid. The heuristic must leave one
    # conflicting request unmet rather than propose an overlapping enrollment.
    assert result.status == PARTIAL
    assert result.required_fulfilled == 1
    assert result.required_unfulfilled == 1
    assert "REQUIRED_UNFILLED" in result.diagnostics
    required = [a for a in result.additions if a.required]
    assert len(required) == 1

def test_existing_conflicting_enrollments_are_invalid():
    x = scenario()
    x["periods"]["p2"] = PeriodInput("p2", "school", "year", "A", 510, 570, True)
    for key in ("math-a", "science-a"):
        x["sections"][key] = replace(x["sections"][key], student_ids=frozenset({"s1"}))
    result = solve(**x)
    assert result.status == MODEL_INVALID
    assert result.additions == ()

def test_elective_slots_must_be_bounded():
    x=scenario()
    x["elective_slots"]={"s1":True}
    assert solve(**x).status==MODEL_INVALID

def test_unknown_section_or_room_rejected():
    x=scenario()
    x["placements"]=(CandidatePlacement("math-a","p1","missing"),)+x["placements"][1:]
    assert solve(**x).status==MODEL_INVALID

def test_read_only_no_roster_mutation():
    x=scenario()
    before={k:v.student_ids for k,v in x["sections"].items()}
    solve(**x)
    assert before=={k:v.student_ids for k,v in x["sections"].items()}

def test_roomless_placement_fails_closed_without_capacity_proof():
    x = scenario()
    x["placements"] = (CandidatePlacement("math-a", "p1", None),) + x["placements"][1:]
    result = solve(**x)
    assert result.status == MODEL_INVALID
    assert result.additions == ()
    assert result.diagnostics[0] in {"ROOM_CAPACITY_UNVERIFIED", "INVALID_PLACEMENT"}
