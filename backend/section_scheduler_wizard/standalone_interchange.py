"""Strict read-only Kairos standalone CSV reconciliation with canonical IDs.

School-owned placement exchange only: no external SIS identifier inference,
student/teacher PII, database reads/writes, CSV-to-publication shortcut or new
masters. Import is a *preflight*, not an authorization to publish.

The caller must obtain a currently school-authorized CanonicalPlanningSnapshot
using build_canonical_planning_snapshot and must revalidate freshness and
publish permission independently before any future state change.
"""
from __future__ import annotations

import csv
from dataclasses import dataclass
from hashlib import sha256
from io import StringIO
from typing import Sequence

from .canonical_snapshot import CanonicalPlanningSnapshot
from .preflight import CandidatePlacement, validate_candidate_placements

CSV_COLUMNS = ("section_id", "period_id", "room_id")
MAX_BYTES = 256 * 1024
MAX_ROWS = 2000
MAX_DIAGNOSTICS = 100
NO_ROOM = ""


@dataclass(frozen=True)
class StandalonePreflight:
    status: str
    school_id: str
    academic_year_id: str
    term_code: str
    source_fingerprint: str
    file_digest: str
    candidate_count: int
    placements: tuple[CandidatePlacement, ...]
    error_codes: tuple[str, ...]
    publication_allowed: bool = False


class StandaloneInterchangeError(ValueError):
    """An interchange is invalid or not based on proven canonical authority."""


def _validated_scope(snapshot: CanonicalPlanningSnapshot, expected_fingerprint: str) -> None:
    if not isinstance(snapshot, CanonicalPlanningSnapshot):
        raise StandaloneInterchangeError("SCHOOL_SCOPE_REQUIRED")
    if (
        not snapshot.school_id or not snapshot.academic_year_id or not snapshot.term_code
        or not isinstance(snapshot.source_fingerprint, str)
        or len(snapshot.source_fingerprint) != 64
        or any(c not in "0123456789abcdef" for c in snapshot.source_fingerprint)
        or expected_fingerprint != snapshot.source_fingerprint
    ):
        raise StandaloneInterchangeError("STALE_OR_INVALID_SOURCE")
    if not snapshot.section_inputs or len(snapshot.section_inputs) > MAX_ROWS:
        raise StandaloneInterchangeError("SECTION_SCOPE_OUT_OF_BOUNDS")
    if any(
        sid != item.section_id
        or (item.school_id, item.academic_year_id, item.term_code)
        != (snapshot.school_id, snapshot.academic_year_id, snapshot.term_code)
        or item.roster_verified is not True
        or not item.student_ids <= snapshot.verified_student_ids
        or not item.teacher_ids <= snapshot.assigned_staff_ids
        for sid, item in snapshot.section_inputs.items()
    ):
        raise StandaloneInterchangeError("SECTION_IDENTITY_NOT_VERIFIED")


def validate_standalone_csv(
    *, snapshot: CanonicalPlanningSnapshot, expected_source_fingerprint: str,
    content: str | bytes,
) -> StandalonePreflight:
    """Preflight explicit canonical IDs; reject ambiguity, duplicates and collisions."""
    _validated_scope(snapshot, expected_source_fingerprint)
    if isinstance(content, bytes):
        if len(content) > MAX_BYTES:
            raise StandaloneInterchangeError("IMPORT_BYTES_LIMIT")
        try:
            source = content.decode("utf-8-sig", errors="strict")
        except UnicodeDecodeError as exc:
            raise StandaloneInterchangeError("IMPORT_UTF8_REQUIRED") from exc
    elif isinstance(content, str):
        if len(content.encode("utf-8")) > MAX_BYTES:
            raise StandaloneInterchangeError("IMPORT_BYTES_LIMIT")
        source = content.removeprefix("\ufeff")
    else:
        raise StandaloneInterchangeError("CSV_TEXT_REQUIRED")
    if "\x00" in source:
        raise StandaloneInterchangeError("INVALID_CSV_CONTROL_CHARACTER")
    if not source:
        raise StandaloneInterchangeError("EMPTY_IMPORT")

    try:
        reader = csv.DictReader(StringIO(source, newline=""), restkey="_EXTRA_",
                                restval=None, strict=True)
        if reader.fieldnames != list(CSV_COLUMNS):
            raise StandaloneInterchangeError("CSV_HEADER_MUST_MATCH_CANONICAL_SCHEMA")
        placements = []
        sections_seen = set()
        for row in reader:
            if len(placements) >= MAX_ROWS:
                raise StandaloneInterchangeError("ROW_LIMIT_EXCEEDED")
            if "_EXTRA_" in row or any(not isinstance(row[k], str) for k in CSV_COLUMNS):
                raise StandaloneInterchangeError("CSV_ROW_FIELD_COUNT")
            section_id, period_id, room_id = (row[k].strip() for k in CSV_COLUMNS)
            # Empty room is explicitly permitted in core preflight, but capacity
            # is unverified; consumers of this export must never infer it.
            if not section_id or not period_id:
                raise StandaloneInterchangeError("EMPTY_CANONICAL_IDENTIFIER")
            if section_id in sections_seen:
                raise StandaloneInterchangeError("DUPLICATE_SECTION_ROW")
            sections_seen.add(section_id)
            if section_id not in snapshot.section_inputs:
                raise StandaloneInterchangeError("UNKNOWN_OR_FOREIGN_SECTION")
            if period_id not in snapshot.period_inputs:
                raise StandaloneInterchangeError("UNKNOWN_OR_FOREIGN_PERIOD")
            if room_id and room_id not in snapshot.room_inputs:
                raise StandaloneInterchangeError("UNKNOWN_OR_FOREIGN_ROOM")
            placements.append(CandidatePlacement(section_id, period_id, room_id or None))
    except (csv.Error, UnicodeError) as exc:
        raise StandaloneInterchangeError("MALFORMED_CSV") from exc

    if not placements or set(sections_seen) != set(snapshot.section_inputs):
        raise StandaloneInterchangeError("INCOMPLETE_CANONICAL_SECTION_SET")

    validation = validate_candidate_placements(
        school_id=snapshot.school_id, academic_year_id=snapshot.academic_year_id,
        term_code=snapshot.term_code, sections=snapshot.section_inputs,
        periods=snapshot.period_inputs, rooms=snapshot.room_inputs,
        placements=placements,
    )
    codes = tuple(sorted({v.code for v in validation}))[:MAX_DIAGNOSTICS]
    data = source.encode("utf-8")
    return StandalonePreflight(
        status="VALID_PREVIEW_ONLY" if not codes else "INVALID_CONSTRAINTS",
        school_id=snapshot.school_id,
        academic_year_id=snapshot.academic_year_id,
        term_code=snapshot.term_code,
        source_fingerprint=snapshot.source_fingerprint,
        file_digest=sha256(data).hexdigest(),
        candidate_count=len(placements),
        placements=tuple(sorted(placements, key=lambda p:p.section_id)) if not codes else (),
        error_codes=codes,
    )


def export_standalone_csv(
    *, snapshot: CanonicalPlanningSnapshot, expected_source_fingerprint: str,
    placements: Sequence[CandidatePlacement],
) -> str:
    """Deterministic canonical-ID-only export. No student/teacher PII fields."""
    _validated_scope(snapshot, expected_source_fingerprint)
    if not isinstance(placements, (list, tuple)) or not 0 < len(placements) <= MAX_ROWS:
        raise StandaloneInterchangeError("EXPORT_ROWS_OUT_OF_BOUNDS")
    if any(not isinstance(p, CandidatePlacement) for p in placements):
        raise StandaloneInterchangeError("EXPORT_PLACEMENTS_NOT_VERIFIED")
    if set(p.section_id for p in placements) != set(snapshot.section_inputs) or len(placements) != len(snapshot.section_inputs):
        raise StandaloneInterchangeError("EXPORT_SECTION_SET_MISMATCH")
    if validate_candidate_placements(
        school_id=snapshot.school_id, academic_year_id=snapshot.academic_year_id,
        term_code=snapshot.term_code, sections=snapshot.section_inputs,
        periods=snapshot.period_inputs, rooms=snapshot.room_inputs,
        placements=placements,
    ):
        raise StandaloneInterchangeError("EXPORT_HARD_CONSTRAINT_FAILED")
    text = StringIO(newline="")
    writer = csv.writer(text, lineterminator="\n")
    writer.writerow(CSV_COLUMNS)
    for p in sorted(placements, key=lambda p:p.section_id):
        # Keys originate in a verified snapshot. Never silently export CSV
        # formula cells even if malformed fixtures bypass that origin.
        row = (p.section_id, p.period_id, p.room_id or NO_ROOM)
        if any(not isinstance(v,str) or (v and v[0] in "=+@-\t\r") for v in row):
            raise StandaloneInterchangeError("UNSAFE_CSV_CELL")
        writer.writerow(row)
    rendered = text.getvalue()
    if len(rendered.encode("utf-8")) > MAX_BYTES:
        raise StandaloneInterchangeError("EXPORT_BYTES_LIMIT")
    return rendered
