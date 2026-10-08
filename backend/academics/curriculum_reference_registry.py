"""Publisher-neutral curriculum reference registry for Solomon/CROWN.

The registry is intentionally rights-safe. Publicly accessible publisher
materials may be indexed as official references, but structured objective
ingestion remains disabled unless an explicit authorization decision is
recorded for that source.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .bju_scope_sequence import BJU_SCOPE_SEQUENCE_SOURCES
from .curriculum_publishers import normalize_curriculum_publisher


@dataclass(frozen=True)
class CurriculumReferenceSource:
    publisher: str
    title: str
    official_url: str
    grade_band: str
    subject: str
    edition: str
    source_kind: str
    rights_mode: str = "public_reference_only"
    objective_ingestion_authorized: bool = False
    lesson_content_ingestion_authorized: bool = False
    mapping_resource_level: str = "reference"
    authority_tier: str = "publisher_direct"
    runtime_dependency: str = "none"
    lesson_planning_level: str = "reference_only"
    licensed_teacher_materials_available: bool = False


def _bju_sources() -> tuple[CurriculumReferenceSource, ...]:
    return tuple(
        CurriculumReferenceSource(
            publisher="BJU Press",
            title=source.title,
            official_url=source.official_url,
            grade_band=source.grade_band,
            subject="Multiple",
            edition=str(source.academic_year),
            source_kind=source.scope_kind,
            rights_mode="public_reference_only",
            objective_ingestion_authorized=source.objective_ingestion_authorized,
        )
        for source in BJU_SCOPE_SEQUENCE_SOURCES
    )


NON_BJU_REFERENCE_SOURCES: tuple[CurriculumReferenceSource, ...] = (
    CurriculumReferenceSource(
        publisher="BJU Press",
        title="Curriculum Guides / Curriculum Maps",
        official_url="https://www.bjupress.com/resources/curriculum-guides",
        grade_band="K-12",
        subject="Multiple",
        edition="Current",
        source_kind="curriculum_map_index",
        mapping_resource_level="publisher_map",
        authority_tier="publisher_direct",
        lesson_planning_level="public_scaffold",
        licensed_teacher_materials_available=True,
    ),
    CurriculumReferenceSource(
        publisher="BJU Press",
        title="Lesson Plan Overviews",
        official_url="https://www.bjupress.com/resources/lesson-plan-overviews/",
        grade_band="Preschool-12",
        subject="Multiple",
        edition="Current",
        source_kind="lesson_plan_overview_index",
        mapping_resource_level="lesson_plan_overview",
        authority_tier="publisher_direct",
        lesson_planning_level="public_scaffold",
        licensed_teacher_materials_available=True,
    ),
    CurriculumReferenceSource(
        publisher="Abeka",
        title="2026 School Scope & Sequence",
        official_url="https://static.abeka.com/ABeka/InteractivePDF/ScopeSequence/SchoolSS/2026/2026Scope-and-Sequence.pdf",
        grade_band="Preschool-12",
        subject="Multiple",
        edition="2026",
        source_kind="scope_sequence",
        mapping_resource_level="scope_sequence",
        lesson_planning_level="public_scaffold",
        licensed_teacher_materials_available=True,
    ),
    CurriculumReferenceSource(
        publisher="Abeka",
        title="Curriculum Lesson Plans product family",
        official_url="https://www.abeka.com/abekaonline/bookdescription.aspx?sbn=414999",
        grade_band="K-12",
        subject="Multiple",
        edition="Current",
        source_kind="lesson_plan_product_evidence",
        mapping_resource_level="lesson_plan_overview",
        authority_tier="publisher_direct",
        lesson_planning_level="licensed_full",
        licensed_teacher_materials_available=True,
    ),
    CurriculumReferenceSource(
        publisher="Purposeful Design",
        title="Purposeful Design Elementary Bible Scope and Sequence",
        official_url="https://s3.amazonaws.com/acsipdp/NewWebstore2018/Doc_Downloads/10062_Scope_Sequence.pdf",
        grade_band="Preschool-6",
        subject="Bible",
        edition="Current",
        source_kind="scope_sequence",
        mapping_resource_level="scope_sequence",
        lesson_planning_level="public_scaffold",
        licensed_teacher_materials_available=True,
    ),
    CurriculumReferenceSource(
        publisher="Purposeful Design",
        title="Third-party starter maps (K-4 referenced by ACSI)",
        official_url="https://www.acsi.org/purposeful-design-publications/news-update/fall-2022",
        grade_band="K-4",
        subject="Multiple",
        edition="Current",
        source_kind="curriculum_map_registry",
        mapping_resource_level="publisher_map",
        authority_tier="publisher_authorized_partner",
        runtime_dependency="reference_only",
        lesson_planning_level="public_scaffold",
        licensed_teacher_materials_available=True,
    ),
    CurriculumReferenceSource(
        publisher="Positive Action for Christ",
        title="Elementary Scope & Sequence",
        official_url="https://www.positiveaction.org/media/scopesequence/elementary_scope_and_sequence.pdf",
        grade_band="Pre-K-6",
        subject="Bible",
        edition="Current",
        source_kind="scope_sequence",
        mapping_resource_level="scope_sequence",
        lesson_planning_level="public_scaffold",
        licensed_teacher_materials_available=True,
    ),
    CurriculumReferenceSource(
        publisher="Positive Action for Christ",
        title="Third-party curriculum maps",
        official_url="https://positiveaction.org/",
        grade_band="K4-12",
        subject="Bible",
        edition="Current",
        source_kind="curriculum_map_registry",
        mapping_resource_level="publisher_map",
        authority_tier="publisher_authorized_partner",
        runtime_dependency="reference_only",
        lesson_planning_level="public_scaffold",
        licensed_teacher_materials_available=True,
    ),
    CurriculumReferenceSource(
        publisher="Positive Action for Christ",
        title="Secondary Scope & Sequence",
        official_url="https://positiveaction.org/blog/homeschooling-with-positive-action-choosing-a-grade-level/",
        grade_band="7-12",
        subject="Bible",
        edition="Current",
        source_kind="scope_sequence_index",
        lesson_planning_level="public_scaffold",
        licensed_teacher_materials_available=True,
    ),
    CurriculumReferenceSource(
        publisher="Positive Action for Christ",
        title="Secondary Teacher Manual planning structure",
        official_url="https://positiveaction.org/documents/864/Secondary_Scope_and_Sequence_2025.pdf",
        grade_band="6-12",
        subject="Bible",
        edition="2025",
        source_kind="teacher_manual_structure",
        mapping_resource_level="lesson_plan_overview",
        authority_tier="publisher_direct",
        lesson_planning_level="licensed_full",
        licensed_teacher_materials_available=True,
    ),
    CurriculumReferenceSource(
        publisher="Summit Ministries",
        title="Christian School Curriculum",
        official_url="https://www.summit.org/promotions/christian-school-curriculum/",
        grade_band="K-12",
        subject="Bible/Biblical Worldview",
        edition="Current",
        source_kind="curriculum_overview",
        mapping_resource_level="overview",
        lesson_planning_level="public_scaffold",
        licensed_teacher_materials_available=True,
    ),
    CurriculumReferenceSource(
        publisher="Summit Ministries",
        title="Summit Curriculum Catalog",
        official_url="https://www.summit.org/educators/christian-school/summit-curriculum-catalog/",
        grade_band="K-12",
        subject="Bible/Biblical Worldview",
        edition="Current",
        source_kind="catalog",
        mapping_resource_level="overview",
        lesson_planning_level="public_scaffold",
        licensed_teacher_materials_available=True,
    ),
)


CURRICULUM_REFERENCE_SOURCES: tuple[CurriculumReferenceSource, ...] = (
    *_bju_sources(),
    *NON_BJU_REFERENCE_SOURCES,
)


def get_curriculum_reference_sources(
    *,
    publisher: str | None = None,
    grade_band: str | None = None,
    subject: str | None = None,
    edition: str | None = None,
) -> list[CurriculumReferenceSource]:
    """Return rights-safe publisher references for planning and mapping."""

    sources: Iterable[CurriculumReferenceSource] = CURRICULUM_REFERENCE_SOURCES

    if publisher:
        canonical = normalize_curriculum_publisher(publisher)
        if not canonical:
            return []
        sources = (source for source in sources if source.publisher == canonical)

    if grade_band:
        needle = grade_band.strip().lower()
        sources = (
            source for source in sources if needle in source.grade_band.lower()
        )

    if subject:
        needle = subject.strip().lower()
        sources = (
            source for source in sources if needle in source.subject.lower()
        )

    if edition:
        normalized = edition.strip().lower()
        sources = (
            source for source in sources if source.edition.lower() == normalized
        )

    return list(sources)


def structured_publisher_ingestion_ready(publisher: str) -> bool:
    """Fail closed unless every indexed source for a publisher is authorized."""

    sources = get_curriculum_reference_sources(publisher=publisher)
    return bool(sources) and all(
        source.objective_ingestion_authorized
        and source.lesson_content_ingestion_authorized
        for source in sources
    )


def supported_reference_publishers() -> tuple[str, ...]:
    return tuple(sorted({source.publisher for source in CURRICULUM_REFERENCE_SOURCES}))


AUTHORITY_TIER_PRIORITY = {
    "publisher_direct": 0,
    "publisher_authorized_partner": 1,
    "association_reference": 2,
    "school_public_map": 3,
    "discovery_only": 4,
}


def preferred_curriculum_references(publisher: str) -> list[CurriculumReferenceSource]:
    """Return publisher references ordered by source authority, without paid runtime dependencies."""

    sources = get_curriculum_reference_sources(publisher=publisher)
    eligible = [
        source
        for source in sources
        if source.runtime_dependency in {"none", "reference_only"}
    ]
    return sorted(
        eligible,
        key=lambda source: (
            AUTHORITY_TIER_PRIORITY.get(source.authority_tier, 99),
            source.title.lower(),
        ),
    )


def has_paid_runtime_dependency() -> bool:
    """CROWN curriculum mapping must remain independently operable."""

    return any(
        source.runtime_dependency == "paid_platform"
        for source in CURRICULUM_REFERENCE_SOURCES
    )


LESSON_PLANNING_PRIORITY = {
    "licensed_full": 3,
    "public_scaffold": 2,
    "reference_only": 1,
}


def publisher_lesson_planning_readiness(publisher: str) -> dict:
    """Summarize how much publisher material can support teacher planning.

    public_scaffold means Praeceptum can prefill a school-authored planning
    structure from public factual/reference material without reproducing
    protected lesson text. licensed_full means the publisher offers deeper
    teacher planning materials, but those materials remain subject to the
    school's license and are not part of the shared Solomon corpus.
    """

    sources = get_curriculum_reference_sources(publisher=publisher)
    if not sources:
        return {
            "publisher": publisher,
            "level": "unsupported",
            "public_scaffold_available": False,
            "licensed_teacher_materials_available": False,
        }

    best = max(
        sources,
        key=lambda source: LESSON_PLANNING_PRIORITY.get(source.lesson_planning_level, 0),
    )
    return {
        "publisher": best.publisher,
        "level": best.lesson_planning_level,
        "public_scaffold_available": any(
            source.lesson_planning_level in {"public_scaffold", "licensed_full"}
            for source in sources
        ),
        "licensed_teacher_materials_available": any(
            source.licensed_teacher_materials_available for source in sources
        ),
    }
