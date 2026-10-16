"""Synthetic immutable what-if previews, no school PII or persistence."""
from dataclasses import replace

import pytest

from section_scheduler_wizard.bounded_feasibility import FEASIBLE, FeasibilityResult, solve_section_meetings
from section_scheduler_wizard.preflight import CandidatePlacement
from section_scheduler_wizard.what_if_preview import (
    InvalidPreview, compare_what_if_previews, freeze_what_if_preview,
)
from .test_bounded_feasibility import scenario


def preview(data=None, result=None, fingerprint="a" * 64):
    data = scenario() if data is None else data
    result = solve_section_meetings(**data) if result is None else result
    return freeze_what_if_preview(
        school_id=data["school_id"],
        academic_year_id=data["academic_year_id"],
        term_code=data["term_code"],
        source_fingerprint=fingerprint,
        sections=data["sections"], periods=data["periods"], rooms=data["rooms"],
        result=result, teacher_rules=data["teacher_rules"],
        template_occurrences=data["template_occurrences"],
    )


def test_verified_preview_deterministic_and_immutable():
    a = preview()
    assert a == preview()
    assert len(a.placements) == 2
    with pytest.raises(Exception):
        a.source_fingerprint = "forged"


def test_self_comparison_has_no_moves():
    x = preview()
    diff = compare_what_if_previews(x, x)
    assert diff.total_sections == 2
    assert diff.unchanged_sections == 2
    assert diff.moved_sections == 0


def test_two_valid_solutions_can_be_compared():
    data = scenario()
    before = preview(data)
    data["candidate_domains"] = {
        "english": (CandidatePlacement("english", "p2", "r"),),
        "math": (CandidatePlacement("math", "p1", "r"),),
    }
    after = preview(data)
    diff = compare_what_if_previews(before, after)
    assert diff.moved_sections == 2
    assert diff.changed_periods == 2
    assert diff.changed_rooms == 0
    assert before.preview_digest != after.preview_digest


def test_foreign_school_and_stale_source_denied():
    x = preview()
    with pytest.raises(InvalidPreview):
        compare_what_if_previews(x, replace(x, school_id="foreign"))
    with pytest.raises(InvalidPreview):
        compare_what_if_previews(x, replace(x, source_fingerprint="b" * 64))


def test_nonfeasible_solution_never_becomes_preview():
    with pytest.raises(InvalidPreview):
        preview(result=FeasibilityResult("UNKNOWN", (), 1, ("NODE_BUDGET_EXHAUSTED",)))


def test_duplicate_or_missing_section_is_rejected():
    x = preview()
    with pytest.raises(InvalidPreview):
        compare_what_if_previews(x, replace(x, placements=x.placements[:1]))
    with pytest.raises(InvalidPreview):
        compare_what_if_previews(x, replace(x, placements=(x.placements[0], x.placements[0])))


def test_independent_teacher_revalidation_blocks_forged_solution():
    data = scenario()
    forged = FeasibilityResult(
        FEASIBLE,
        (CandidatePlacement("english", "p1", "r"),
         CandidatePlacement("math", "p1", "r")),
        1, (),
    )
    with pytest.raises(InvalidPreview):
        preview(data, forged)


def test_bad_source_fingerprint_denied():
    with pytest.raises(InvalidPreview):
        preview(fingerprint="no-current-proof")
