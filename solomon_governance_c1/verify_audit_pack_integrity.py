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
except ImportError:
    from solomon_governance_c1.env_guard import validate_environment


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
        if not path.exists():
            fail(f"missing integrity file: {path.name}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    cert = json.loads(cert_path.read_text(encoding="utf-8"))

    if cert.get("result") != "PASS":
        fail("certification result is not PASS")

    manifest_hashes = manifest.get("file_sha256", {})
    cert_hashes = cert.get("file_sha256", {})

    if manifest_hashes != cert_hashes:
        fail("manifest hashes do not match certification hashes")

    for name, expected_hash in sorted(manifest_hashes.items()):
        path = bundle / name
        if not path.exists():
            fail(f"missing certified artifact: {name}")

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
