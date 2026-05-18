#!/usr/bin/env python3
"""Certify deterministic AUDIT_PACK runtime bundles.

This script validates a generated runtime audit bundle before canonical promotion.

Rules:
- Does not mutate AUDIT_PACK.
- Does not mutate governance baselines.
- Reads one runtime bundle.
- Verifies required files.
- Verifies manifest hashes.
- Verifies LF normalization.
- Captures repo branch/head and generator hash.
- Emits certification JSON inside the runtime bundle only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    from env_guard import validate_environment
except ImportError:
    from solomon_governance_c1.env_guard import validate_environment


ROOT = Path(__file__).resolve().parent.parent
SOL = ROOT / "solomon_governance_c1"
GENERATOR = SOL / "generate_audit_pack.py"

MANIFEST_NAME = "99_BUNDLE_MANIFEST.json"
CERT_NAME = "AUDIT_PACK_CERTIFICATION.json"
SHA_NAME = "AUDIT_PACK_SHA256SUMS.txt"

REQUIRED_FILES = [
    "00_OVERVIEW.txt",
    "01_TREE.txt",
    "02_WORKFLOWS_INDEX.txt",
    "03_WORKFLOWS_TRIGGERS.txt",
    "04_JOB_LEVEL_IF.txt",
    "05_BRANCH_PROTECTION_MAIN.json",
    "06_BACKEND_URLS.txt",
    "07_MIGRATIONS.txt",
    "08_PY_DEPS.txt",
    "09_NODE_DEPS.txt",
    "10_SECRET_SCAN_FINDINGS.txt",
    "11_TRACKED_BINARIES.txt",
    "12_UNTRACKED_ARTIFACTS.txt",
    "13_HEALTH_PROBE.txt",
    "14_DEPLOY_PROD_RECENT.txt",
]


def run_cmd(args: list[str]) -> tuple[int, str, str]:
    proc = subprocess.run(
        args,
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def write_text(path: Path, text: str) -> None:
    path.write_text(text.rstrip("\n") + "\n", encoding="utf-8", newline="\n")


def write_json(path: Path, payload: dict) -> None:
    write_text(path, json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False))


def has_crlf(path: Path) -> bool:
    return b"\r\n" in path.read_bytes()


def load_manifest(bundle: Path) -> dict:
    path = bundle / MANIFEST_NAME
    if not path.exists():
        raise FileNotFoundError(f"missing manifest: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def certify(bundle: Path) -> int:
    bundle = bundle.resolve()
    failures: list[str] = []
    warnings: list[str] = []

    if not bundle.exists() or not bundle.is_dir():
        print(f"FAILED: bundle directory not found: {bundle}")
        return 1

    try:
        manifest = load_manifest(bundle)
    except Exception as exc:
        print(f"FAILED: cannot load manifest: {exc}")
        return 1

    expected = sorted(REQUIRED_FILES)
    manifest_required = sorted(manifest.get("required_files", []))
    if manifest_required != expected:
        failures.append("manifest required_files does not match expected required file list")

    manifest_hashes = manifest.get("file_sha256", {})
    if sorted(manifest_hashes.keys()) != expected:
        failures.append("manifest file_sha256 keys do not match expected required file list")

    computed_hashes: dict[str, str] = {}

    for name in expected:
        path = bundle / name
        if not path.exists():
            failures.append(f"missing required file: {name}")
            continue

        computed = sha256_file(path)
        computed_hashes[name] = computed

        expected_hash = manifest_hashes.get(name)
        if expected_hash != computed:
            failures.append(f"hash mismatch: {name}")

        if has_crlf(path):
            failures.append(f"CRLF detected: {name}")

    if has_crlf(bundle / MANIFEST_NAME):
        failures.append(f"CRLF detected: {MANIFEST_NAME}")

    rc_branch, branch, _ = run_cmd(["git", "branch", "--show-current"])
    rc_head, head, _ = run_cmd(["git", "rev-parse", "HEAD"])
    rc_status, status, _ = run_cmd(["git", "status", "--short", "--branch"])

    generator_hash = sha256_file(GENERATOR) if GENERATOR.exists() else "MISSING"

    certification = {
        "certified_at_utc": datetime.now(timezone.utc).isoformat(),
        "result": "PASS" if not failures else "FAIL",
        "bundle_path": str(bundle),
        "bundle_id": manifest.get("bundle_id"),
        "generator": str(GENERATOR.relative_to(ROOT)),
        "generator_sha256": generator_hash,
        "git_branch": branch if rc_branch == 0 else "UNKNOWN",
        "git_head": head if rc_head == 0 else "UNKNOWN",
        "git_status_short_branch": status if rc_status == 0 else "UNKNOWN",
        "required_file_count": len(expected),
        "verified_file_count": len(computed_hashes),
        "manifest_name": MANIFEST_NAME,
        "sha256s_name": SHA_NAME,
        "failures": failures,
        "warnings": warnings,
        "file_sha256": computed_hashes,
    }

    sha_lines = [f"{computed_hashes[name]}  {name}" for name in sorted(computed_hashes)]
    write_text(bundle / SHA_NAME, "\n".join(sha_lines))
    write_json(bundle / CERT_NAME, certification)

    print(f"AUDIT_PACK_CERTIFICATION {certification['result']}")
    print(f"bundle_id={certification['bundle_id']}")
    print(f"verified_file_count={certification['verified_file_count']}")
    print(f"certification={bundle / CERT_NAME}")
    print(f"sha256s={bundle / SHA_NAME}")

    if failures:
        print("failures:")
        for failure in failures:
            print(f"- {failure}")

    return 0 if not failures else 1


def main() -> int:
    validate_environment()
    parser = argparse.ArgumentParser(description="Certify a runtime AUDIT_PACK bundle")
    parser.add_argument("--bundle", required=True, help="Runtime bundle directory")
    args = parser.parse_args()
    return certify(Path(args.bundle))


if __name__ == "__main__":
    raise SystemExit(main())
