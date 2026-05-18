#!/usr/bin/env python3
"""Manage runtime bundle lifecycle with append-only governance.

This script maintains the SUPERSESSION_INDEX.json that tracks:
- active_bundle: currently in-use bundle
- certified_bundles: bundles that have passed certification
- superseded_bundles: older bundles replaced by newer ones
- revoked_bundles: bundles with detected issues

Rules:
- Never delete historical bundles
- Mark as superseded when replaced by new certified bundle
- Mark as revoked if tampering or integrity failures detected
- Preserve complete audit lineage
"""

from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

try:
    from env_guard import validate_environment
except ImportError:
    from solomon_governance_c1.env_guard import validate_environment


ROOT = Path(__file__).resolve().parent.parent
SOL = ROOT / "solomon_governance_c1"
RUNTIME_PACK = SOL / "governance" / "c1" / "runtime" / "audit_pack"
INDEX_NAME = "SUPERSESSION_INDEX.json"


def run_cmd(args: list[str]) -> tuple[int, str, str]:
    proc = subprocess.run(
        args,
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()


def load_index() -> dict:
    """Load or initialize supersession index."""
    index_path = RUNTIME_PACK / INDEX_NAME
    if index_path.exists():
        return json.loads(index_path.read_text(encoding="utf-8"))

    return {
        "index_version": "1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "last_updated_utc": datetime.now(timezone.utc).isoformat(),
        "active_bundle": None,
        "certified_bundles": [],
        "superseded_bundles": [],
        "revoked_bundles": [],
        "governance_notes": "Append-only bundle retention. Never delete. Mark as superseded or revoked instead.",
    }


def save_index(index: dict) -> None:
    """Write supersession index to disk."""
    index["last_updated_utc"] = datetime.now(timezone.utc).isoformat()
    index_path = RUNTIME_PACK / INDEX_NAME
    index_path.write_text(json.dumps(index, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def mark_certified(bundle_id: str, reason: str = "bundle certified") -> int:
    """Mark bundle as certified and active."""
    index = load_index()

    # Check if already certified
    for cert in index["certified_bundles"]:
        if cert["bundle_id"] == bundle_id:
            print(f"WARN: bundle {bundle_id} already certified")
            return 0

    # If there's an active bundle, supersede it
    if index["active_bundle"] and index["active_bundle"] != bundle_id:
        old_active = index["active_bundle"]

        # Find in certified_bundles and mark as superseded
        for cert in index["certified_bundles"]:
            if cert["bundle_id"] == old_active:
                cert["status"] = "superseded"
                cert["superseded_at_utc"] = datetime.now(timezone.utc).isoformat()
                cert["superseded_by"] = bundle_id
                break

        # Also track in superseded_bundles list
        index["superseded_bundles"].append({
            "bundle_id": old_active,
            "superseded_at_utc": datetime.now(timezone.utc).isoformat(),
            "superseded_by": bundle_id,
            "reason": "replaced by newer certified bundle"
        })

    # Add new certified bundle as active
    index["certified_bundles"].append({
        "bundle_id": bundle_id,
        "certified_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "active",
        "reason": reason
    })

    index["active_bundle"] = bundle_id
    save_index(index)

    print(f"BUNDLE_MARKED_CERTIFIED")
    print(f"bundle_id={bundle_id}")
    print(f"active_bundle={index['active_bundle']}")
    print(f"certified_count={len(index['certified_bundles'])}")
    print(f"superseded_count={len(index['superseded_bundles'])}")
    return 0


def mark_revoked(bundle_id: str, reason: str = "integrity failure") -> int:
    """Mark bundle as revoked (integrity/tampering issue detected)."""
    index = load_index()

    # Check if already revoked
    for revoked in index["revoked_bundles"]:
        if revoked["bundle_id"] == bundle_id:
            print(f"WARN: bundle {bundle_id} already revoked")
            return 0

    # Mark in certified_bundles if present
    for cert in index["certified_bundles"]:
        if cert["bundle_id"] == bundle_id:
            cert["status"] = "revoked"
            cert["revoked_at_utc"] = datetime.now(timezone.utc).isoformat()
            cert["revoked_reason"] = reason
            break

    # Add to revoked_bundles
    index["revoked_bundles"].append({
        "bundle_id": bundle_id,
        "revoked_at_utc": datetime.now(timezone.utc).isoformat(),
        "reason": reason
    })

    # If this was active, it must be replaced
    if index["active_bundle"] == bundle_id:
        print(f"ERROR: active bundle {bundle_id} cannot be revoked without replacement")
        print(f"Governance action required: promote alternative certified bundle to active")
        return 1

    save_index(index)

    print(f"BUNDLE_MARKED_REVOKED")
    print(f"bundle_id={bundle_id}")
    print(f"reason={reason}")
    print(f"revoked_count={len(index['revoked_bundles'])}")
    return 0


def show_status() -> int:
    """Display current bundle lifecycle status."""
    index = load_index()

    print("BUNDLE_LIFECYCLE_STATUS")
    print(f"index_version={index['index_version']}")
    print(f"active_bundle={index['active_bundle']}")
    print(f"certified_count={len(index['certified_bundles'])}")
    print(f"superseded_count={len(index['superseded_bundles'])}")
    print(f"revoked_count={len(index['revoked_bundles'])}")
    print()
    print("Certified bundles:")
    for cert in index["certified_bundles"]:
        status = cert.get("status", "unknown")
        bundle_id = cert["bundle_id"]
        print(f"  {bundle_id}: {status}")

    if index["superseded_bundles"]:
        print()
        print("Superseded bundles:")
        for sup in index["superseded_bundles"]:
            print(f"  {sup['bundle_id']} → {sup['superseded_by']}")

    if index["revoked_bundles"]:
        print()
        print("Revoked bundles:")
        for rev in index["revoked_bundles"]:
            reason = rev.get("reason", "unknown")
            print(f"  {rev['bundle_id']}: {reason}")

    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage runtime bundle lifecycle")
    sub = parser.add_subparsers(dest="command", required=True)

    cert = sub.add_parser("certified", help="Mark bundle as certified and active")
    cert.add_argument("--bundle", required=True, help="Bundle ID")
    cert.add_argument("--reason", default="bundle certified", help="Certification reason")

    revoke = sub.add_parser("revoked", help="Mark bundle as revoked")
    revoke.add_argument("--bundle", required=True, help="Bundle ID")
    revoke.add_argument("--reason", default="integrity failure", help="Revocation reason")

    sub.add_parser("status", help="Show bundle lifecycle status")

    return parser


def main() -> int:
    validate_environment()
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "certified":
        return mark_certified(args.bundle, args.reason)
    elif args.command == "revoked":
        return mark_revoked(args.bundle, args.reason)
    elif args.command == "status":
        return show_status()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
