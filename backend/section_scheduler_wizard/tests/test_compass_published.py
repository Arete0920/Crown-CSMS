"""Published Kairos Compass synthetic hard-constraint and privacy cases."""
from dataclasses import replace
import pytest
from section_scheduler_wizard.canonical_snapshot import CanonicalPlanningSnapshot
from section_scheduler_wizard.compass_published import PublishedScheduleCard, summarize_published_kairos
from section_scheduler_wizard.preflight import PeriodInput, RoomInput, SectionInput

def fixture(n=6):
    students=frozenset(f"s{i}" for i in range(n))
    sections={
      "s1":SectionInput("s1","school","year","S1",frozenset({"t1"}),students,True),
      "s2":SectionInput("s2","school","year","S1",frozenset({"t2"}),frozenset(),True),
    }
    periods={
      "p1":PeriodInput("p1","school","year","A",480,540,True),
      "p2":PeriodInput("p2","school","year","A",540,600,True),
      "chapel":PeriodInput("chapel","school","year","A",600,660,False),
    }
    rooms={"r1":RoomInput("r1","school",20),"r2":RoomInput("r2","school",20)}
    snapshot=CanonicalPlanningSnapshot("school","year","S1",sections,periods,rooms,
      frozenset({"course"}),students,frozenset({"t1","t2"}),"a"*64)
    cards=[PublishedScheduleCard("card1","school","year","s1","p1","A","r1")]
    return snapshot,cards

def test_reports_published_card_counts_and_privacy():
    s,c=fixture()
    x=summarize_published_kairos(s,c)
    assert x.placed_sections==1 and x.unplaced_sections==1
    assert x.published_meetings==1 and x.distinct_students==6
    assert x.meeting_seat_utilization_percent==30.0
    assert x.provenance=="CANONICAL_PUBLISHED_SECTION_PLACEMENTS"

def test_small_cell_cannot_report_enrollment_or_utilization():
    s,c=fixture(4)
    x=summarize_published_kairos(s,c)
    assert x.privacy_suppressed and x.distinct_students is None
    assert x.enrolled_meeting_seats is None and x.meeting_seat_utilization_percent is None

def test_cross_tenant_or_bad_day_template_rejected():
    s,c=fixture()
    for bad in (replace(c[0],school_id="foreign"),replace(c[0],day_template_id="B")):
        with pytest.raises(ValueError):
            summarize_published_kairos(s,[bad])

def test_protected_chapel_and_stale_period_rejected():
    s,c=fixture()
    for bad in (replace(c[0],period_id="chapel"),replace(c[0],period_id="missing")):
        with pytest.raises(ValueError):
            summarize_published_kairos(s,[bad])

def test_duplicate_published_card_rejected():
    s,c=fixture()
    with pytest.raises(ValueError):
        summarize_published_kairos(s,[c[0],c[0]])

def test_overlapping_distinct_periods_same_room_rejected():
    s,c=fixture()
    s=replace(s,period_inputs={**s.period_inputs,
        "overlap":PeriodInput("overlap","school","year","A",510,570,True)})
    with pytest.raises(ValueError):
        summarize_published_kairos(s,[c[0],PublishedScheduleCard("card2","school","year","s2","overlap","A","r1")])

def test_roomless_meeting_never_claims_known_capacity():
    s,c=fixture()
    x=summarize_published_kairos(s,[replace(c[0],room_id=None)])
    assert x.capacity_meeting_seats is None and x.meeting_seat_utilization_percent is None

def test_deterministic_digest_and_read_only_source():
    s,c=fixture()
    assert summarize_published_kairos(s,c)==summarize_published_kairos(s,c)
    assert len(s.section_inputs["s1"].student_ids)==6
