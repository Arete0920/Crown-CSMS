"""Synthetic standalone Kairos interchange: no PII, DB writes or publishing."""
from dataclasses import replace
import pytest
from section_scheduler_wizard.canonical_snapshot import CanonicalPlanningSnapshot
from section_scheduler_wizard.preflight import CandidatePlacement, PeriodInput, RoomInput, SectionInput
from section_scheduler_wizard.standalone_interchange import (
    StandaloneInterchangeError, validate_standalone_csv, export_standalone_csv,
)
def sample():
    sections={
        "s1":SectionInput("s1","school","year","S1",frozenset({"teacher1"}),frozenset({"student1"}),True),
        "s2":SectionInput("s2","school","year","S1",frozenset({"teacher2"}),frozenset({"student2"}),True),
    }
    periods={
        "p1":PeriodInput("p1","school","year","A",480,540,True),
        "p2":PeriodInput("p2","school","year","A",540,600,True),
        "chapel":PeriodInput("chapel","school","year","A",600,660,False),
    }
    snapshot=CanonicalPlanningSnapshot("school","year","S1",sections,periods,
        {"r1":RoomInput("r1","school",25)},frozenset({"course"}),
        frozenset({"student1","student2"}),frozenset({"teacher1","teacher2"}),"a"*64)
    rows=(CandidatePlacement("s1","p1","r1"),CandidatePlacement("s2","p2","r1"))
    return snapshot,rows

def check(value,snap=None):
    if snap is None:snap=sample()[0]
    return validate_standalone_csv(snapshot=snap,expected_source_fingerprint=snap.source_fingerprint,content=value)

def test_deterministic_roundtrip_and_no_student_pii():
    snap,rows=sample()
    text=export_standalone_csv(snapshot=snap,expected_source_fingerprint=snap.source_fingerprint,placements=rows)
    assert text=="section_id,period_id,room_id\ns1,p1,r1\ns2,p2,r1\n"
    assert "student1" not in text and "teacher1" not in text
    assert check(text).status=="VALID_PREVIEW_ONLY"
    assert check(text).placements==rows
    assert check(text.encode("utf-8")).file_digest==check(text).file_digest
    assert check(b"\xef\xbb\xbf"+text.encode()).candidate_count==2

def test_foreign_or_stale_source_refused():
    snap,_=sample()
    with pytest.raises(StandaloneInterchangeError):
        validate_standalone_csv(snapshot=snap,expected_source_fingerprint="b"*64,content="section_id,period_id,room_id\n")

@pytest.mark.parametrize("body",[
 "section_id,period_id,room_id\ns1,p1,r1\ns1,p2,r1\n",
 "section_id,period_id,room_id\ns1,p1,r1\n",
 "section_id,period_id,room_id\ns1,p1,r1\ns2,p2,foreign\n",
 "section_id,period_id,room_id\nforeign,p1,r1\ns2,p2,r1\n",
 "section_id,period_id,room_id\ns1,p1,r1,extra\ns2,p2,r1\n",
 "section_id,room_id,period_id\ns1,r1,p1\ns2,r1,p2\n",
 "section_id,period_id,room_id\ns1,,r1\ns2,p2,r1\n",
])
def test_malformed_foreign_duplicate_and_incomplete_import_refused(body):
    with pytest.raises(StandaloneInterchangeError):
        check(body)

def test_chapel_import_returns_non_publishable_diagnostic():
    x=check("section_id,period_id,room_id\ns1,chapel,r1\ns2,p2,r1\n")
    assert x.status=="INVALID_CONSTRAINTS" and "PROTECTED_PERIOD" in x.error_codes
    assert not x.placements and x.publication_allowed is False

def test_same_time_room_collision_rejected():
    x=check("section_id,period_id,room_id\ns1,p1,r1\ns2,p1,r1\n")
    assert x.status=="INVALID_CONSTRAINTS" and "ROOM_OVERLAP" in x.error_codes

def test_oversized_input_fails_closed():
    with pytest.raises(StandaloneInterchangeError):
        check("x"*(256*1024+1))

def test_verified_roster_required():
    s,_=sample()
    s=replace(s,section_inputs={**s.section_inputs,
        "s1":replace(s.section_inputs["s1"],roster_verified=False)})
    with pytest.raises(StandaloneInterchangeError):
        check("section_id,period_id,room_id\ns1,p1,r1\ns2,p2,r1\n",s)

def test_export_requires_complete_valid_canonical_set():
    s,p=sample()
    with pytest.raises(StandaloneInterchangeError):
        export_standalone_csv(snapshot=s,expected_source_fingerprint=s.source_fingerprint,placements=p[:1])
    with pytest.raises(StandaloneInterchangeError):
        export_standalone_csv(snapshot=s,expected_source_fingerprint=s.source_fingerprint,
                              placements=(p[0],CandidatePlacement("s2","chapel","r1")))

def test_csv_formula_ids_are_rejected_even_when_supplied_in_snapshot():
    s,_=sample()
    # This intentionally models an unsafe external identifier previously
    # admitted to an authorized mapping; escaping it is not sufficient.
    unsafe=replace(s,section_inputs={
        "=IMPORT":replace(s.section_inputs["s1"],section_id="=IMPORT"),
        "s2":s.section_inputs["s2"],
    })
    with pytest.raises(StandaloneInterchangeError,match="UNSAFE_CSV_CELL"):
        check("section_id,period_id,room_id\\n=IMPORT,p1,r1\\ns2,p2,r1\\n",unsafe)
