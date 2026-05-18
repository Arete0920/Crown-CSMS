#!/usr/bin/env python3
"""
SOLOMON C1 Deterministic Promotion Pipeline

Governed transition: runtime artifact -> reviewed -> certified -> promoted to canonical baseline.

Usage:
  --dry-run       Validate runtime artifacts exist and are structurally sound.
                  Does NOT require a clean repo. Does NOT modify anything.
  (no --dry-run)  Actual promotion: requires clean repo + explicit confirm token,
                  captures SHA-256 hashes, copies to canonical dirs, writes promotion log.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

CONFIRM_TOKEN = "SOLOMON-C1-PROMOTE-RUNTIME"

# All paths relative to solomon_governance_c1/ (cwd when script runs)
RUNTIME_DIR = Path("governance/c1/runtime")
PROMOTION_LOG_DIR = Path("governance/c1/promotions")

# runtime sub-dir -> canonical target dir
RUNTIME_TARGETS: list[tuple[Path, Path]] = [
    (RUNTIME_DIR / "dry_run_ingestion", Path("governance/c1/dry_run_ingestion")),
    (RUNTIME_DIR / "rollback",          Path("governance/c1/rollback")),
]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(65536), b""):
            h.update(block)
    return h.hexdigest()


def collect_runtime_files() -> list[Path]:
    """Return sorted list of all files under RUNTIME_DIR."""
    if not RUNTIME_DIR.exists():
        print(f"FAIL: Runtime directory does not exist: {RUNTIME_DIR}")
        sys.exit(1)
    files = sorted(p for p in RUNTIME_DIR.rglob("*") if p.is_file())
    if not files:
        print(f"FAIL: No runtime artifacts found under {RUNTIME_DIR}")
        sys.exit(1)
    return files


def validate_artifacts(files: list[Path]) -> dict[Path, str]:
    """Validate each file is non-empty and return path->sha256 map."""
    hashes: dict[Path, str] = {}
    errors: list[str] = []
    for f in files:
        if f.stat().st_size == 0:
            errors.append(f"empty file: {f}")
            continue
        hashes[f] = sha256_file(f)
    if errors:
        for e in errors:
            print(f"FAIL: {e}")
        sys.exit(1)
    return hashes


def validate_repo_clean() -> None:
    """Abort promotion if the repo has uncommitted tracked changes outside runtime/."""
    result = subprocess.run(
        ["git", "-C", str(Path.cwd().parent), "status", "--short"],
        capture_output=True, text=True,
    )
    dirty = [
        line for line in result.stdout.splitlines()
        if line and "solomon_governance_c1/governance/c1/runtime" not in line
    ]
    if dirty:
        print("FAIL: Repository has uncommitted changes outside runtime/. Commit before promoting.")
        for line in dirty:
            print(f"  {line}")
        sys.exit(1)


def write_promotion_log(hashes: dict[Path, str]) -> Path:
    """Write a deterministic promotion log entry; return log path."""
    PROMOTION_LOG_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    log_path = PROMOTION_LOG_DIR / f"promotion_{ts}.json"
    entries = [
        {
            "runtime_artifact": str(path.as_posix()),
            "sha256": digest,
            "promoted_at": ts,
        }
        for path, digest in sorted(hashes.items(), key=lambda kv: str(kv[0]))
    ]
    log_path.write_text(
        json.dumps({"promotion": entries}, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return log_path


def promote(hashes: dict[Path, str]) -> None:
    """Copy runtime artifacts to their canonical target directories."""
    for runtime_sub, target_dir in RUNTIME_TARGETS:
        if not runtime_sub.exists():
            continue
        target_dir.mkdir(parents=True, exist_ok=True)
        for src in sorted(runtime_sub.rglob("*")):
            if not src.is_file():
                continue
            rel = src.relative_to(runtime_sub)
            dst = target_dir / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            print(f"  promoted: {src} -> {dst}")


def main() -> None:
    parser = argparse.ArgumentParser(description="SOLOMON C1 Deterministic Promotion Pipeline")
    parser.add_argument("--confirm-token", required=True)
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Validate only; do not copy artifacts or write promotion logs.",
    )
    args = parser.parse_args()

    if args.confirm_token != CONFIRM_TOKEN:
        print("FAIL: Invalid confirm token.")
        sys.exit(1)

    files = collect_runtime_files()
    hashes = validate_artifacts(files)

    if args.dry_run:
        print("DRY-RUN VALIDATION PASS")
        print(f"  Runtime directory : {RUNTIME_DIR}")
        print(f"  Artifacts found   : {len(files)}")
        for path, digest in sorted(hashes.items(), key=lambda kv: str(kv[0])):
            print(f"  {digest[:16]}...  {path}")
        return

    # Actual promotion -- require clean repo
    validate_repo_clean()
    promote(hashes)
    log_path = write_promotion_log(hashes)
    print("PROMOTION COMPLETE")
    print(f"  Log: {log_path}")


if __name__ == "__main__":
    main()
