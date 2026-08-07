#!/usr/bin/env python3
"""Fail when CROWN's current-facing release authority contradicts itself."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STATUS = ROOT / "docs/CURRENT_RELEASE_STATUS.md"

FIELD_REQUIREMENTS = {
    "README.md": ("sha", "tag"),
    "docs/CURRENT_RELEASE_STATUS.md": ("sha", "tag", "run"),
    "docs/ownership/OWNER_HANDOFF.md": ("sha", "tag"),
    "docs/operations/README.md": ("sha", "tag", "run"),
    "docs/canonical/DILIGENCE_EVIDENCE_INDEX.md": ("sha", "tag"),
    "docs/KNOWN_LIMITATIONS.md": ("sha", "tag"),
    "docs/compliance/PRIVACY_COMPLIANCE_EVIDENCE_STATUS.md": ("sha",),
    "docs/RELEASE_NOTES.md": ("sha", "tag", "run"),
    "docs/RELEASE_TAG_POLICY.md": ("sha", "tag", "run"),
}

STALE_CURRENT_CLAIMS = (
    "not production-authorized",
    "production: **not approved",
    "future immutable release candidate",
    "immutable release candidate: **not yet selected",
    "founder/product owner final authorization has not occurred",
    "protected-history remediation: **not verified complete",
)

STATUS_PATTERNS = {
    "sha": r"(?m)^\*\*Certified release source:\*\*\s*`?([0-9a-f]{40})`?\s*$",
    "tag": r"(?m)^\*\*Immutable production tag:\*\*\s*`?([A-Za-z0-9._-]+)`?\s*$",
    "run": r"(?m)^\*\*Production deployment run:\*\*\s*`?([0-9]+)`?\s*$",
}


def fail(message: str, failures: list[str]) -> None:
    failures.append(message)


def main() -> int:
    failures: list[str] = []
    if not STATUS.is_file():
        print("ERROR: docs/CURRENT_RELEASE_STATUS.md is missing", file=sys.stderr)
        return 1

    try:
        status_text = STATUS.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        print(f"ERROR: cannot read docs/CURRENT_RELEASE_STATUS.md: {exc}", file=sys.stderr)
        return 1
    authority: dict[str, str] = {}
    for key, pattern in STATUS_PATTERNS.items():
        match = re.search(pattern, status_text)
        if not match:
            fail(f"CURRENT_RELEASE_STATUS.md does not declare a parseable {key}", failures)
        else:
            authority[key] = match.group(1)

    for rel_path, required_fields in FIELD_REQUIREMENTS.items():
        path = ROOT / rel_path
        if not path.is_file():
            fail(f"missing current-facing authority document: {rel_path}", failures)
            continue

        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            fail(f"cannot read current-facing authority document {rel_path}: {exc}", failures)
            continue
        lowered = text.lower()

        for key in required_fields:
            value = authority.get(key)
            if value and value not in text:
                fail(f"{rel_path} does not cite current {key} {value}", failures)

        for stale_claim in STALE_CURRENT_CLAIMS:
            if stale_claim in lowered:
                fail(f"{rel_path} contains stale current-state claim: {stale_claim!r}", failures)

    authority_documents = {}
    for rel_path in ("docs/RELEASE_NOTES.md", "docs/RELEASE_TAG_POLICY.md"):
        path = ROOT / rel_path
        if path.is_file():
            try:
                authority_documents[rel_path] = path.read_text(encoding="utf-8")
            except (OSError, UnicodeError) as exc:
                fail(f"cannot read authority document {rel_path}: {exc}", failures)

    for rel_path, text in authority_documents.items():
        for key in ("sha", "tag", "run"):
            value = authority.get(key)
            if value and value not in text:
                fail(f"{rel_path} does not cite current {key} {value}", failures)

    notes = authority_documents.get("docs/RELEASE_NOTES.md", "")
    policy = authority_documents.get("docs/RELEASE_TAG_POLICY.md", "")
    registry_path = ROOT / "docs/RELEASE_TAGS.json"
    if not registry_path.is_file():
        fail("missing canonical historical tag registry: docs/RELEASE_TAGS.json", failures)
    else:
        try:
            historical_tags = json.loads(registry_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            fail(f"docs/RELEASE_TAGS.json is not a readable tag registry: {exc}", failures)
            historical_tags = {}

        if not isinstance(historical_tags, dict):
            fail("docs/RELEASE_TAGS.json must contain a JSON object of tag-to-SHA mappings", failures)
            historical_tags = {}

        historical_sections = {}
        for rel_path, text, heading in (
            ("docs/RELEASE_NOTES.md", notes, "Historical releases"),
            ("docs/RELEASE_TAG_POLICY.md", policy, "Historical tags"),
        ):
            match = re.search(
                rf"(?ms)^## {re.escape(heading)}\s*$(.*?)(?=^## |\Z)",
                text,
            )
            if not match:
                fail(f"{rel_path} is missing its {heading!r} section", failures)
                historical_sections[rel_path] = ""
            else:
                historical_sections[rel_path] = match.group(1)

        for tag_name, tag_sha in historical_tags.items():
            if not re.fullmatch(r"[0-9a-f]{40}", str(tag_sha)):
                fail(f"docs/RELEASE_TAGS.json has invalid SHA for {tag_name}", failures)
                continue
            for rel_path, section in historical_sections.items():
                if tag_name not in section or tag_sha not in section:
                    fail(
                        f"{rel_path} historical section does not match registry entry "
                        f"{tag_name}={tag_sha}",
                        failures,
                    )

    if failures:
        print("Repository freshness verification FAILED:", file=sys.stderr)
        for item in failures:
            print(f" - {item}", file=sys.stderr)
        return 1

    print(
        "Repository freshness verification passed: "
        f"certified_sha={authority['sha']} tag={authority['tag']} run={authority['run']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
