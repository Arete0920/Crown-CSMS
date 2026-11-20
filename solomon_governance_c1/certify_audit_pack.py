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
import os
import stat
import re
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
RUNTIME_PACK_ROOT = SOL / "governance" / "c1" / "runtime" / "audit_pack"

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
    if (not path.is_absolute() or path.name not in {SHA_NAME, CERT_NAME}
            or path.parent != validated_certification_bundle_path(path.parent)
            or path.is_symlink() or (path.exists() and not path.is_file())):
        raise ValueError("audit certification output outside safe runtime bundle")
    flags = os.O_WRONLY | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(path, flags, 0o600)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            raise ValueError("audit certification output must be a single regular file")
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as output:
            fd = -1
            output.truncate(0)
            output.write(text.rstrip("\n") + "\n")
    finally:
        if fd >= 0:
            os.close(fd)


def write_json(path: Path, payload: dict) -> None:
    write_text(path, json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False))


def has_crlf(path: Path) -> bool:
    return b"\r\n" in path.read_bytes()


def load_manifest(bundle: Path) -> dict:
    path = bundle / MANIFEST_NAME
    if not path.exists():
        raise FileNotFoundError(f"missing manifest: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def validated_certification_bundle_path(bundle: Path) -> Path:
    """Constrain certification writes to direct runtime audit bundle folders."""
    if RUNTIME_PACK_ROOT.is_symlink():
        raise ValueError("runtime audit root cannot be a symlink")
    # ROOT is the resolved checkout. A symlink anywhere below it can redirect
    # audit certification outputs outside the checked-out runtime directory.
    if RUNTIME_PACK_ROOT.is_relative_to(ROOT):
        component = ROOT
        for part in RUNTIME_PACK_ROOT.relative_to(ROOT).parts:
            component /= part
            if component.is_symlink():
                raise ValueError("runtime audit root cannot traverse a symlink")
    root = RUNTIME_PACK_ROOT.resolve()
    if ".." in bundle.parts or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,79}", bundle.name):
        raise ValueError("invalid runtime audit bundle path")
    if bundle.is_symlink():
        raise ValueError("runtime audit bundle cannot be a symlink")
    target = bundle.resolve()
    if target.parent != root or not target.is_dir():
        raise ValueError("certification requires a direct runtime audit bundle")
    return target


def certify(bundle: Path) -> int:
    try:
        bundle = validated_certification_bundle_path(bundle)
    except ValueError as exc:
        print(f"FAILED: invalid certification bundle: {exc}")
        return 1
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
    output_paths = [bundle / SHA_NAME, bundle / CERT_NAME]
    if any(path.is_symlink() or (path.exists() and not path.is_file()) for path in output_paths):
        print("FAILED: linked or non-file certification output")
        return 1
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
