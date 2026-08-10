"""Canonical curriculum publisher registry and normalization utilities.

Publisher recognition is metadata only. It does not imply licensed content,
SSO, roster sync, grade sync, or a vendor API integration.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List, Mapping


@dataclass(frozen=True)
class CurriculumPublisherProfile:
    canonical_name: str
    aliases: tuple[str, ...]
    integration_status: str
    content_policy: str
    notes: str = ""


PUBLISHER_PROFILES: Mapping[str, CurriculumPublisherProfile] = {
    "BJU Press": CurriculumPublisherProfile(
        canonical_name="BJU Press",
        aliases=("bju", "bju press", "bob jones university press"),
        integration_status="metadata_only",
        content_policy="licensed_content_requires_vendor_authorization",
        notes="Official-reference metadata is supported; no bulk copyrighted-content ingestion is implied.",
    ),
    "Abeka": CurriculumPublisherProfile(
        canonical_name="Abeka",
        aliases=("abeka", "a beka", "abeka academy"),
        integration_status="metadata_only",
        content_policy="licensed_content_requires_vendor_authorization",
    ),
    "Purposeful Design": CurriculumPublisherProfile(
        canonical_name="Purposeful Design",
        aliases=("purposeful design", "purposefuldesign"),
        integration_status="metadata_only",
        content_policy="licensed_content_requires_vendor_authorization",
    ),
    "Standard Publishing": CurriculumPublisherProfile(
        canonical_name="Standard Publishing",
        aliases=("standard publishing", "standard press"),
        integration_status="legacy_metadata_only",
        content_policy="ownership_and_license_must_be_verified_per_resource",
        notes=(
            "Legacy Christian curriculum references may use 'Standard Press'. "
            "Verify current rights ownership per resource."
        ),
    ),
    "Positive Action for Christ": CurriculumPublisherProfile(
        canonical_name="Positive Action for Christ",
        aliases=("positive action for christ", "positive action"),
        integration_status="metadata_only",
        content_policy="licensed_content_requires_vendor_authorization",
    ),
    "Summit Ministries": CurriculumPublisherProfile(
        canonical_name="Summit Ministries",
        aliases=("summit ministries", "summit worldview"),
        integration_status="metadata_only",
        content_policy="licensed_content_requires_vendor_authorization",
    ),
}

SUPPORTED_CURRICULUM_PUBLISHERS: Dict[str, List[str]] = {
    canonical: list(profile.aliases) for canonical, profile in PUBLISHER_PROFILES.items()
}


def _contains_alias(value: str, alias: str) -> bool:
    """Match aliases as complete normalized phrases, not arbitrary substrings."""
    pattern = rf"(?<![a-z0-9]){re.escape(alias)}(?![a-z0-9])"
    return re.search(pattern, value) is not None


def normalize_curriculum_publisher(name: str) -> str:
    value = " ".join((name or "").strip().lower().split())
    if not value:
        return ""

    for canonical, aliases in SUPPORTED_CURRICULUM_PUBLISHERS.items():
        candidates = (canonical.lower(), *aliases)
        if any(value == candidate or _contains_alias(value, candidate) for candidate in candidates):
            return canonical
    return ""


def get_curriculum_publisher_profile(name: str) -> CurriculumPublisherProfile | None:
    canonical = normalize_curriculum_publisher(name)
    return PUBLISHER_PROFILES.get(canonical) if canonical else None


def is_supported_curriculum_publisher(name: str) -> bool:
    return bool(normalize_curriculum_publisher(name))


def publisher_search_terms(query: str) -> List[str]:
    canonical = normalize_curriculum_publisher(query)
    if not canonical:
        return [query.strip()] if query.strip() else []
    return [canonical, *SUPPORTED_CURRICULUM_PUBLISHERS[canonical]]
