from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCAN_ROOTS = ("backend", "frontend", "scripts", "tools")
TEXT_SUFFIXES = {".py", ".js", ".jsx", ".ts", ".tsx", ".ps1", ".md"}
EXCLUDED_PARTS = {"node_modules", ".venv", "venv", "dist", "build", "coverage", "audit-artifacts", "__pycache__"}

PATTERNS = {
    "canonical_core": re.compile(
        r"(?:from\s+core\.models\s+import[^\n]*(?:Family|Guardian|Student)|"
        r"core\.(?:Family|Guardian|Student)|"
        r"\b(?:Family|Guardian|Student)\.objects\b)"
    ),
    "households_compatibility": re.compile(
        r"(?:from\s+households\.models\s+import[^\n]*(?:Household|Guardian|Student)|"
        r"households\.(?:Household|Guardian|Student)|"
        r"households\.models)"
    ),
    "crown_api_compatibility": re.compile(
        r"(?:crown_api\.models_households|"
        r"from\s+crown_api\.models_households\s+import|"
        r"HouseholdMember)"
    ),
    "guardian_wizard": re.compile(r"GuardianHouseholdWizardSession|guardian_household_wizard"),
    "household_family_bridge": re.compile(r"HouseholdFamilyLink|household_family_link"),
}

PATH_FAMILIES = {
    "backend/core/models.py": {"canonical_core"},
    "backend/households/models.py": {"households_compatibility"},
    "backend/crown_api/models_households.py": {"crown_api_compatibility"},
}

KNOWN_ANCHORS = {
    "canonical_core": {
        "backend/core/models.py",
        "backend/guardian_household_wizard/containment_views.py",
        "backend/crown_api/views_students.py",
    },
    "households_compatibility": {
        "backend/households/models.py",
        "backend/applications/views_admissions.py",
    },
    "crown_api_compatibility": {"backend/crown_api/models_households.py"},
}


def iter_source_files(repo_root: Path):
    for root_name in SCAN_ROOTS:
        root = repo_root / root_name
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
                continue
            relative = path.relative_to(repo_root)
            if any(part in EXCLUDED_PARTS for part in relative.parts):
                continue
            if relative.as_posix() == "tools/generate_identity_consumer_inventory.py":
                continue
            yield path, relative.as_posix()


def classify_role(path: str, text: str) -> str:
    lowered = path.lower()
    if "/migrations/" in lowered:
        return "migration"
    if "/tests/" in lowered or lowered.endswith("_test.py") or lowered.startswith("backend/tests/"):
        return "test"
    if "seed" in lowered or "/fixtures/" in lowered:
        return "seed"
    if "serializer" in lowered:
        return "serializer"
    if "view" in lowered or "/api/" in lowered:
        return "endpoint_or_api"
    if "task" in lowered or "signal" in lowered:
        return "background_or_signal"
    if lowered.startswith("frontend/"):
        return "frontend_contract"
    if "model" in lowered or "models.Model" in text:
        return "model"
    if lowered.startswith("scripts/") or lowered.startswith("tools/"):
        return "tooling"
    return "consumer"


def build_inventory(repo_root: Path) -> dict:
    records = []
    for path, relative in iter_source_files(repo_root):
        text = path.read_text(encoding="utf-8", errors="replace")
        matched = {name for name, pattern in PATTERNS.items() if pattern.search(text)}
        matched.update(PATH_FAMILIES.get(relative, set()))
        if not matched:
            continue
        records.append({"path": relative, "role": classify_role(relative, text), "families": sorted(matched)})

    records.sort(key=lambda record: record["path"])
    family_counts = Counter()
    role_counts = Counter()
    for record in records:
        role_counts[record["role"]] += 1
        family_counts.update(record["families"])

    observed = {record["path"]: set(record["families"]) for record in records}
    missing_anchors = {
        family: sorted(path for path in paths if family not in observed.get(path, set()))
        for family, paths in KNOWN_ANCHORS.items()
    }
    missing_anchors = {family: paths for family, paths in missing_anchors.items() if paths}

    return {
        "schema_version": 1,
        "mode": "read_only_static_inventory",
        "scope": list(SCAN_ROOTS),
        "record_count": len(records),
        "family_counts": dict(sorted(family_counts.items())),
        "role_counts": dict(sorted(role_counts.items())),
        "missing_known_anchors": missing_anchors,
        "records": records,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a deterministic, read-only inventory of identity-model consumers.")
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    inventory = build_inventory(repo_root)
    rendered = json.dumps(inventory, indent=2, sort_keys=True) + "\n"

    if args.output:
        output = args.output if args.output.is_absolute() else repo_root / args.output
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")

    return 1 if inventory["missing_known_anchors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
