#!/usr/bin/env python3
"""Verify certified AUDIT_PACK bundle integrity."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

try:
    from env_guard import validate_environment
    from certify_audit_pack import REQUIRED_FILES
except ImportError:
    from solomon_governance_c1.env_guard import validate_environment
    from solomon_governance_c1.certify_audit_pack import REQUIRED_FILES


MANIFEST_NAME = "99_BUNDLE_MANIFEST.json"
CERT_NAME = "AUDIT_PACK_CERTIFICATION.json"
SHA_NAME = "AUDIT_PACK_SHA256SUMS.txt"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def fail(message: str) -> None:
    print(f"FAILED: {message}")
    sys.exit(1)


def validated_artifact_names(hashes: object) -> list[str]:
    """Reject manifest-selected filenames outside the certified audit contract."""
    if not isinstance(hashes, dict) or set(hashes) != set(REQUIRED_FILES):
        fail("manifest artifact names must match required audit files")
    return sorted(REQUIRED_FILES)


def require_regular_file(path: Path) -> None:
    """Do not follow bundle file symlinks outside the selected audit directory."""
    if path.is_symlink() or not path.is_file():
        fail(f"missing or linked audit file: {path.name}")


def main() -> int:
    validate_environment()
    parser = argparse.ArgumentParser(description="Verify certified AUDIT_PACK bundle integrity")
    parser.add_argument("--bundle", required=True, help="Runtime or canonical audit bundle directory")
    args = parser.parse_args()

    bundle = Path(args.bundle).resolve()

    if not bundle.exists() or not bundle.is_dir():
        fail(f"bundle directory not found: {bundle}")

    manifest_path = bundle / MANIFEST_NAME
    cert_path = bundle / CERT_NAME
    sha_path = bundle / SHA_NAME

    for path in [manifest_path, cert_path, sha_path]:
        require_regular_file(path)

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    cert = json.loads(cert_path.read_text(encoding="utf-8"))

    if cert.get("result") != "PASS":
        fail("certification result is not PASS")

    manifest_hashes = manifest.get("file_sha256", {})
    cert_hashes = cert.get("file_sha256", {})

    if manifest_hashes != cert_hashes:
        fail("manifest hashes do not match certification hashes")

    for name in validated_artifact_names(manifest_hashes):
        expected_hash = manifest_hashes[name]
        path = bundle / name
        require_regular_file(path)

        actual = sha256_file(path)
        if actual != expected_hash:
            fail(f"hash mismatch for {name}")

    sha_lines = [
        line.strip()
        for line in sha_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    expected_lines = [f"{manifest_hashes[name]}  {name}" for name in sorted(manifest_hashes)]

    if sha_lines != expected_lines:
        fail("AUDIT_PACK_SHA256SUMS.txt content mismatch")

    print("AUDIT_PACK_INTEGRITY PASS")
    print(f"bundle={bundle}")
    print(f"verified_file_count={len(manifest_hashes)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
