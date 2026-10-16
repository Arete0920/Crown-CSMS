"""Synthetic Compass scheduling metrics: scoped, deterministic, privacy protected."""
from dataclasses import replace
import pytest
from section_scheduler_wizard.canonical_snapshot import CanonicalPlanningSnapshot
from section_scheduler_wizard.compass_scheduling import build_compass_scheduling_summary
from section_scheduler_wizard.preflight import CandidatePlacement, PeriodInput, RoomInput, SectionInput

def fixture(n=6):
    students=frozenset(f"s{i}" for i in range(n))
    sections={"english":SectionInput("english","school","year","S1",frozenset({"staff1"}),students,True)}
    periods={"p1":PeriodInput("p1","school","year","A",480,540,True)}
    rooms={"r1":RoomInput("r1","school",20)}
    snapshot=CanonicalPlanningSnapshot("school","year","S1",sections,periods,rooms,
        frozenset({"course1"}),students,frozenset({"staff1"}),"a"*64)
    return snapshot,[CandidatePlacement("english","p1","r1")]

def summarize(n=6,**kwargs):
    snapshot,placements=fixture(n)
    return build_compass_scheduling_summary(snapshot=snapshot,placements=placements,
        expected_source_fingerprint=snapshot.source_fingerprint,**kwargs)

def test_synthetic_school_scope_provenance_and_counts():
    x=summarize()
    assert x.school_id=="school" and x.publication_allowed is False
    assert x.distinct_student_count==6 and x.scheduled_roster_seats==6
    assert x.known_room_capacity==20 and x.utilization_percent==30
    assert x.placed_sections==1 and x.unplaced_sections==0
    assert x.provenance=="CANONICAL_KAIROS_READ_ONLY_PROJECTION"

def test_small_cell_suppresses_studental_and_utilization():
    x=summarize(4)
    assert x.privacy_suppressed
    assert x.distinct_student_count is None
    assert x.scheduled_roster_seats is None
    assert x.known_room_capacity is None
    assert x.utilization_percent is None
    assert "SMALL_CELL_SUPPRESSED" in x.limitations

def test_source_fingerprint_mismatch_fails_closed():
    s,p=fixture()
    with pytest.raises(ValueError):
        build_compass_scheduling_summary(snapshot=s,placements=p,expected_source_fingerprint="b"*64)

def test_foreign_school_placement_fails_closed():
    s,p=fixture()
    s=replace(s,section_inputs={"english":replace(s.section_inputs["english"],school_id="foreign")})
    with pytest.raises(ValueError):
        build_compass_scheduling_summary(snapshot=s,placements=p,expected_source_fingerprint=s.source_fingerprint)

def test_unverified_student_identity_fails_closed():
    s,p=fixture()
    s=replace(s,verified_student_ids=frozenset())
    with pytest.raises(ValueError):
        build_compass_scheduling_summary(snapshot=s,placements=p,expected_source_fingerprint=s.source_fingerprint)

def test_duplicate_or_unknown_placement_fails_closed():
    s,p=fixture()
    for bad in ([p[0],p[0]],[CandidatePlacement("missing","p1","r1")]):
        with pytest.raises(ValueError):
            build_compass_scheduling_summary(snapshot=s,placements=bad,expected_source_fingerprint=s.source_fingerprint)

def test_empty_placement_has_no_false_utilization_denominator():
    s,p=fixture()
    x=build_compass_scheduling_summary(snapshot=s,placements=[],expected_source_fingerprint=s.source_fingerprint)
    assert x.placed_sections==0 and x.unplaced_sections==1
    assert x.utilization_percent is None and x.known_room_capacity is None

def test_same_inputs_yield_stable_digest_and_no_mutation():
    s,p=fixture()
    original=s.section_inputs["english"].student_ids
    one=build_compass_scheduling_summary(snapshot=s,placements=p,expected_source_fingerprint=s.source_fingerprint)
    two=build_compass_scheduling_summary(snapshot=s,placements=p,expected_source_fingerprint=s.source_fingerprint)
    assert one==two
    assert s.section_inputs["english"].student_ids==original


def test_provisional_metric_rejects_chapel_overlap_on_distinct_period_ids():
    s, placements = fixture()
    from section_scheduler_wizard.preflight import PeriodInput
    s = replace(s, period_inputs={
        **s.period_inputs,
        "chapel": PeriodInput("chapel", "school", "year", "A", 510, 570, False),
    })
    with pytest.raises(ValueError, match="protected scheduling block"):
        build_compass_scheduling_summary(
            snapshot=s, placements=placements,
            expected_source_fingerprint=s.source_fingerprint,
        )
