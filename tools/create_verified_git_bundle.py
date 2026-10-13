#!/usr/bin/env python3
"""Block known exposed history before creating an ordinary archive bundle.

This is a path/history guard, not key-retirement or all-secret-scan authority.
Unremediated preservation copies require the separate controlled runbook.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import subprocess
import sys
import tempfile

VERIFIER = Path(__file__).with_name("verify_remediated_git_bundle.sh")
FORBIDDEN_PATH = (
    "solomon_governance_c1/governance/c1/runtime/audit_pack/"
    "20260515T185051Z/crypto_attestation/ed25519_private_key_DO_NOT_SHARE.pem"
)


def create_bundle(repo: Path, output: Path) -> None:
    repo = repo.resolve(strict=True)
    output = output.absolute()
    if output.exists() or output.is_symlink():
        raise FileExistsError("Archive output already exists; refusing replacement")
    # Verify before creating output directories or history-bearing artifacts.
    subprocess.run(
        ["bash", str(VERIFIER), "--repo", str(repo),
         "--forbidden-path", FORBIDDEN_PATH], check=True,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="verified-bundle-", dir=output.parent) as tmp:
        staged = Path(tmp) / "archive.bundle"
        subprocess.run(
            ["git", "-C", str(repo), "bundle", "create", str(staged), "--all"],
            check=True,
        )
        # Revalidate the exact restored artifact, including any ref drift that
        # introduced forbidden history between source verification and capture.
        subprocess.run(
            ["bash", str(VERIFIER), "--bundle", str(staged),
             "--forbidden-path", FORBIDDEN_PATH], check=True,
        )
        # Same-volume publication without overwriting a concurrently created file.
        os.link(staged, output)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        create_bundle(args.repo, args.output)
    except (OSError, subprocess.CalledProcessError) as exc:
        print(f"Archive creation blocked: {exc}", file=sys.stderr)
        return 1
    print("Archive path/history verification passed; operational retirement and all-ref secret scanning remain separately required.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
