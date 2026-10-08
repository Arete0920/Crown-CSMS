"""Governed BJU Press scope-and-sequence source registry.

This module intentionally stores source metadata only. It does not embed,
mirror, scrape, or bulk-ingest publisher-owned curriculum text. Curriculum
mapping and lesson-planning features may use these records to identify the
authoritative publisher source and edition while preserving the publisher
rights boundary.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class BJUScopeSequenceSource:
    academic_year: int
    scope_kind: str
    sku: str
    title: str
    official_url: str
    grade_band: str
    mapping_mode: str = "official_reference_only"
    objective_ingestion_authorized: bool = False


BJU_SCOPE_SEQUENCE_SOURCES: tuple[BJUScopeSequenceSource, ...] = (
    BJUScopeSequenceSource(
        academic_year=2026,
        scope_kind="academic",
        sku="563213",
        title="2026 Christian School Scope & Sequence",
        official_url="https://www.bjupress.com/2026-christian-school-scope-sequence/5637752826.p",
        grade_band="Early Childhood-12",
    ),
    BJUScopeSequenceSource(
        academic_year=2027,
        scope_kind="academic",
        sku="577536",
        title="2027 Christian School Scope & Sequence",
        official_url="https://www.bjupress.com/category/supplies/5637160371.c",
        grade_band="Elementary-Secondary",
    ),
    BJUScopeSequenceSource(
        academic_year=2026,
        scope_kind="biblical_worldview",
        sku="563049",
        title="2026 Biblical Worldview Scope & Sequence",
        official_url="https://www.bjupress.com/2026-biblical-worldview-scope-sequence/5637746826.p",
        grade_band="K-12",
    ),
    BJUScopeSequenceSource(
        academic_year=2027,
        scope_kind="biblical_worldview",
        sku="575555",
        title="2027 Biblical Worldview Scope & Sequence",
        official_url="https://www.bjupress.com/2027-biblical-worldview-scope-sequence/5637887827.p",
        grade_band="K-12",
    ),
)


BJU_2026_SUBJECT_LANES: tuple[str, ...] = (
    "Early Childhood",
    "Reading/Literature",
    "Writing & Grammar",
    "Spelling",
    "Handwriting",
    "Vocabulary",
    "Math",
    "Science",
    "Heritage Studies",
    "Bible",
    "Spanish",
)


def get_bju_scope_sequence_sources(
    *,
    academic_year: int | None = None,
    scope_kind: str | None = None,
) -> list[BJUScopeSequenceSource]:
    """Return approved BJU source metadata for curriculum planning surfaces."""

    sources: Iterable[BJUScopeSequenceSource] = BJU_SCOPE_SEQUENCE_SOURCES
    if academic_year is not None:
        sources = (source for source in sources if source.academic_year == academic_year)
    if scope_kind is not None:
        sources = (source for source in sources if source.scope_kind == scope_kind)
    return list(sources)


def bju_objective_ingestion_ready() -> bool:
    """Fail closed until publisher authorization exists for objective ingestion."""

    return all(source.objective_ingestion_authorized for source in BJU_SCOPE_SEQUENCE_SOURCES)
