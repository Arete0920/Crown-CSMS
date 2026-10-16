"""Synthetic pure multi-meeting solver acceptance; no database or publishing."""
from dataclasses import replace
from section_scheduler_wizard.multi_meeting import (
    MeetingRequirement, MeetingChoice, optimize_multi_meeting,
)
from section_scheduler_wizard.preflight import (
    CandidatePlacement, PeriodInput, RoomInput, SectionInput,
)
from section_scheduler_wizard.planning_inputs import TeacherPlanningRule


def scenario():
    sections={"science": SectionInput("science","school","year","S1",frozenset({"teacher"}),frozenset({"a","b"}),True)}
    periods={f"p{i}":PeriodInput(f"p{i}","school","year","A",480+60*i,540+60*i,True) for i in range(4)}
    rooms={"r":RoomInput("r","school",25)}
    def choice(p,c): return MeetingChoice(CandidatePlacement("science",p,"r"),c)
    meetings=(
        MeetingRequirement("meeting1","science",(choice("p0",3),choice("p1",0))),
        MeetingRequirement("meeting2","science",(choice("p1",5),choice("p2",1))),
    )
    rule=TeacherPlanningRule("teacher","school","year","S1",frozenset(),240,0)
    return dict(school_id="school",academic_year_id="year",term_code="S1",
        sections=sections,periods=periods,rooms=rooms,requirements=meetings,
        teacher_rules={"teacher":rule},template_occurrences={"A":1})


def test_two_meetings_optimal_deterministic():
    data=scenario()
    result=optimize_multi_meeting(**data)
    assert result==optimize_multi_meeting(**data)
    assert result.status=="OPTIMAL" and result.optimality_proven
    assert result.preference_penalty==1
    assert {p.period_id for p in result.placements}=={"p1","p2"}


def test_shared_teacher_forced_collision_is_infeasible():
    data=scenario()
    a,b=data["requirements"]
    data["requirements"]=(replace(a,choices=(a.choices[1],)),replace(b,choices=(b.choices[0],)))
    assert optimize_multi_meeting(**data).status=="INFEASIBLE"


def test_budget_exhaustion_does_not_claim_infeasible_or_optimal():
    result=optimize_multi_meeting(**scenario(),node_limit=1)
    assert result.status=="UNKNOWN" and not result.optimality_proven


def test_foreign_scope_and_invalid_cost_denied():
    data=scenario()
    assert optimize_multi_meeting(**{**data,"school_id":"foreign"}).status=="MODEL_INVALID"
    a,b=data["requirements"]
    data["requirements"]=(replace(a,choices=(replace(a.choices[0],preference_penalty=-1),)),b)
    assert optimize_multi_meeting(**data).status=="MODEL_INVALID"


def test_chapel_overlaps_rejected():
    data=scenario()
    data["periods"]["chapel"]=PeriodInput("chapel","school","year","A",510,570,False)
    assert optimize_multi_meeting(**data).status=="MODEL_INVALID"


def test_required_teacher_policy_not_guessed():
    data=scenario()
    data["teacher_rules"]={}
    assert optimize_multi_meeting(**data).status=="MODEL_INVALID"


def test_no_mutation_of_inputs():
    data=scenario()
    before=data["requirements"]
    optimize_multi_meeting(**data)
    assert data["requirements"]==before


def test_single_valid_domains_prove_optimality():
    data=scenario()
    a,b=data["requirements"]
    data["requirements"]=(replace(a,choices=(a.choices[0],)),replace(b,choices=(b.choices[0],)))
    assert optimize_multi_meeting(**data).status=="OPTIMAL"


def test_missing_canonical_section_cannot_be_skipped():
    data=scenario()
    data["requirements"]=()
    assert optimize_multi_meeting(**data).status=="MODEL_INVALID"
