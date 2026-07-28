#!/usr/bin/env python3
"""Fail closed when tracked files contain private-key artifacts.

This guard is intentionally independent of .gitignore because force-added files
bypass ignore rules. It inspects the Git index, not the working tree.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GUARD_PATH = Path("tools/verify_no_tracked_private_keys.py")
PLACEHOLDER_PATH = Path(
    "solomon_governance_c1/governance/c1/runtime/audit_pack/"
    "20260515T185051Z/crypto_attestation/ed25519_private_key_DO_NOT_SHARE.pem"
)
PLACEHOLDER_TEXT = (
    "REDACTED_ARTIFACT_PLACEHOLDER\n"
    "The original private key material was intentionally removed from version control.\n"
    "Regenerate keys in CI/runtime as ephemeral secrets only.\n"
)
BINARY_SECRET_SUFFIXES = {".pfx", ".p12", ".jks", ".keystore", ".kdbx"}
RISKY_NAME_PARTS = (
    "private_key",
    "private-key",
    "privatekey",
    "do_not_share",
    "do-not-share",
)
PRIVATE_KEY_BLOCK = re.compile(
    rb"-----BEGIN (?P<kind>(?:RSA |EC |DSA |OPENSSH )?)PRIVATE KEY-----"
    rb"\r?\n(?:[A-Za-z0-9+/=]{16,}\r?\n)+"
    rb"-----END (?P=kind)PRIVATE KEY-----"
)


def tracked_files() -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    return [Path(p.decode("utf-8")) for p in result.stdout.split(b"\0") if p]


def main() -> int:
    violations: list[str] = []
    for rel in tracked_files():
        path = ROOT / rel
        if not path.is_file():
            continue

        if rel == GUARD_PATH:
            continue

        if rel == PLACEHOLDER_PATH:
            actual = path.read_text(encoding="utf-8", errors="strict")
            if actual != PLACEHOLDER_TEXT:
                violations.append(f"{rel}: redacted placeholder content changed")
            continue

        lower_name = rel.name.lower()
        risky_name = rel.suffix.lower() in BINARY_SECRET_SUFFIXES or any(
            part in lower_name for part in RISKY_NAME_PARTS
        )
        if risky_name:
            violations.append(f"{rel}: prohibited tracked key/secret filename")
            continue

        if path.stat().st_size > 2_000_000:
            continue
        data = path.read_bytes()
        if PRIVATE_KEY_BLOCK.search(data):
            violations.append(f"{rel}: contains a complete private-key PEM block")

    if violations:
        print("Tracked private-key guard: FAIL")
        for violation in sorted(violations):
            print(f"- {violation}")
        return 1

    print("Tracked private-key guard: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
