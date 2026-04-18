"""Utilities for canonical curriculum publisher normalization and filtering."""

from __future__ import annotations

from typing import Dict, List

SUPPORTED_CURRICULUM_PUBLISHERS: Dict[str, List[str]] = {
    "BJU Press": ["bju", "bju press", "bob jones university press"],
    "Abeka": ["abeka", "a beka", "abeka academy"],
    "Purposeful Design": ["purposeful design", "purposefuldesign"],
    "Positive Action for Christ": ["positive action for christ", "positive action", "pac"],
    "Summit Ministries": ["summit ministries", "summit", "summit worldview"],
}


def normalize_curriculum_publisher(name: str) -> str:
    value = (name or "").strip().lower()
    if not value:
        return ""

    for canonical, aliases in SUPPORTED_CURRICULUM_PUBLISHERS.items():
        if value == canonical.lower() or value in aliases:
            return canonical
        if any(alias in value for alias in aliases):
            return canonical
    return ""


def is_supported_curriculum_publisher(name: str) -> bool:
    return bool(normalize_curriculum_publisher(name))


def publisher_search_terms(query: str) -> List[str]:
    canonical = normalize_curriculum_publisher(query)
    if not canonical:
        return [query.strip()] if query.strip() else []
    return [canonical, *SUPPORTED_CURRICULUM_PUBLISHERS[canonical]]