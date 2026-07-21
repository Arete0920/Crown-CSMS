from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
TEMP_NAMES = {".DS_Store", "Thumbs.db", "desktop.ini"}
TEMP_SUFFIXES = (".tmp", ".temp", ".bak", ".orig", ".rej", "~")
EDITOR_PARTS = {".idea", ".vscode", "__pycache__", ".pytest_cache", ".mypy_cache"}
OVERSIZED_LOG_BYTES = 2_000_000


def classify(path: Path, size_bytes: int) -> list[str]:
    reasons: list[str] = []
    relative_parts = set(path.parts)
    if path.name in TEMP_NAMES or path.name.endswith(TEMP_SUFFIXES):
        reasons.append("temporary_or_os_artifact")
    if relative_parts & EDITOR_PARTS:
        reasons.append("editor_or_cache_artifact")
    if path.suffix.lower() == ".log" and size_bytes >= OVERSIZED_LOG_BYTES:
        reasons.append("oversized_tracked_log")
    if "docs/release/evidence/live-pack" in path.as_posix():
        reasons.append("nested_evidence_copy_requires_dedup_review")
    return sorted(set(reasons))


def build_inventory(repo_root: Path = REPO_ROOT) -> dict:
    records = []
    for path in sorted(p for p in repo_root.rglob("*") if p.is_file()):
        relative = path.relative_to(repo_root)
        if ".git" in relative.parts:
            continue
        size_bytes = path.stat().st_size
        reasons = classify(relative, size_bytes)
        if reasons:
            records.append(
                {
                    "path": relative.as_posix(),
                    "size_bytes": size_bytes,
                    "reasons": reasons,
                    "deletion_authorized": False,
                }
            )
    records.sort(key=lambda item: item["path"])
    return {
        "schema_version": 1,
        "mode": "read_only_tracked_repository_noise_inventory",
        "deletion_performed": False,
        "deletion_authorized": False,
        "record_count": len(records),
        "records": records,
    }


def main() -> int:
    print(json.dumps(build_inventory(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
