"""Immutable, read-only Kairos what-if planning previews.

No DB tables, writes, publication or authorization API. A caller must first
construct a school-authorized canonical snapshot and explicitly establish the
candidate-domain cycle. Previews must be revalidated against current canonical
records before any future governed publication. This module is a pure comparison
primitive, NOT persisted version history or approved-baseline attestation.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from json import dumps
from typing import Mapping, Sequence

from .bounded_feasibility import FEASIBLE, FeasibilityResult
from .planning_inputs import TeacherPlanningRule
from .preflight import (
    CandidatePlacement, PeriodInput, RoomInput, SectionInput,
    validate_candidate_placements,
)
from .teacher_feasibility import validate_teacher_feasibility

MAX_PREVIEW_SECTIONS = 64


class InvalidPreview(ValueError):
    """Preview cannot be certified from this input."""


@dataclass(frozen=True)
class FrozenWhatIfPreview:
    school_id: str
    academic_year_id: str
    term_code: str
    source_fingerprint: str
    preview_digest: str
    placements: tuple[CandidatePlacement, ...]


@dataclass(frozen=True)
class WhatIfComparison:
    school_id: str
    academic_year_id: str
    term_code: str
    source_fingerprint: str
    before_digest: str
    after_digest: str
    total_sections: int
    unchanged_sections: int
    moved_sections: int
    changed_rooms: int
    changed_periods: int
    changed_section_ids: tuple[str, ...]


def _placement_key(p: CandidatePlacement) -> tuple[str, str, str]:
    return p.section_id, p.period_id, p.room_id or ""


def _valid_fingerprint(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(c in "0123456789abcdef" for c in value)
    )


def freeze_what_if_preview(
    *,
    school_id: str,
    academic_year_id: str,
    term_code: str,
    source_fingerprint: str,
    sections: Mapping[str, SectionInput],
    periods: Mapping[str, PeriodInput],
    rooms: Mapping[str, RoomInput],
    result: FeasibilityResult,
    teacher_rules: Mapping[str, TeacherPlanningRule],
    template_occurrences: Mapping[str, int],
) -> FrozenWhatIfPreview:
    """Freeze an independently rechecked FEASIBLE proposal without writes."""
    if not all((school_id, academic_year_id, term_code)) or not _valid_fingerprint(source_fingerprint):
        raise InvalidPreview("Valid explicit scope and canonical source fingerprint are required.")
    if not isinstance(result, FeasibilityResult) or result.status != FEASIBLE:
        raise InvalidPreview("Only FEASIBLE solutions may become previews.")
    if not sections or len(sections) > MAX_PREVIEW_SECTIONS:
        raise InvalidPreview("Preview section count is outside bounded limits.")
    placements = result.placements
    if len(placements) != len(sections) or len({p.section_id for p in placements}) != len(sections):
        raise InvalidPreview("One placement per canonical section is required.")
    if set(p.section_id for p in placements) != set(sections):
        raise InvalidPreview("All and only authorized sections must be present.")
    if result.diagnostics:
        raise InvalidPreview("A successful proposal cannot carry unresolved diagnostics.")

    basic = validate_candidate_placements(
        school_id=school_id, academic_year_id=academic_year_id, term_code=term_code,
        sections=sections, periods=periods, rooms=rooms, placements=placements,
    )
    if basic:
        raise InvalidPreview("Candidate placement hard constraints must pass independently.")
    teacher = validate_teacher_feasibility(
        school_id=school_id, academic_year_id=academic_year_id,
        term_code=term_code, sections=sections, periods=periods, rooms=rooms,
        placements=placements, teacher_rules=teacher_rules,
        template_occurrences=template_occurrences,
    )
    if teacher:
        raise InvalidPreview("Teacher and protected-time constraints must pass independently.")
    canonical = tuple(sorted(placements, key=_placement_key))
    payload = {
        "version": 1,
        "scope": [school_id, academic_year_id, term_code, source_fingerprint],
        "placements": [[p.section_id, p.period_id, p.room_id] for p in canonical],
    }
    digest = sha256(dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    return FrozenWhatIfPreview(
        school_id, academic_year_id, term_code, source_fingerprint,
        digest, canonical,
    )


def compare_what_if_previews(
    before: FrozenWhatIfPreview, after: FrozenWhatIfPreview,
) -> WhatIfComparison:
    """Compare only matching, immutable canonical source revisions.

    Cross-school, stale-source and incomplete section comparisons are rejected.
    This counts slot/room movement, not tuition, staffing costs or academic merit.
    """
    if not isinstance(before, FrozenWhatIfPreview) or not isinstance(after, FrozenWhatIfPreview):
        raise InvalidPreview("Both comparison inputs must be certified previews.")
    if (
        before.school_id != after.school_id
        or before.academic_year_id != after.academic_year_id
        or before.term_code != after.term_code
        or before.source_fingerprint != after.source_fingerprint
    ):
        raise InvalidPreview("Cross-school or stale-source comparison is forbidden.")
    if not _valid_fingerprint(before.source_fingerprint):
        raise InvalidPreview("Invalid canonical source fingerprint.")
    a = {p.section_id: p for p in before.placements}
    b = {p.section_id: p for p in after.placements}
    if (
        not a or len(a) != len(before.placements)
        or len(b) != len(after.placements)
        or set(a) != set(b)
    ):
        raise InvalidPreview("A complete identical section set is required.")
    changed = tuple(sorted(k for k in a if a[k] != b[k]))
    room_changes = sum(a[k].room_id != b[k].room_id for k in a)
    period_changes = sum(a[k].period_id != b[k].period_id for k in a)
    return WhatIfComparison(
        before.school_id, before.academic_year_id, before.term_code,
        before.source_fingerprint, before.preview_digest, after.preview_digest,
        len(a), len(a) - len(changed), len(changed),
        room_changes, period_changes, changed,
    )
