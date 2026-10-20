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

    # Revocation is permanent for this bundle ID, even when no other bundle
    # is available. A newly certified replacement must use its own identity.
    if any(
        entry.get("bundle_id") == bundle_id
        for entry in index.get("revoked_bundles", [])
    ) or any(
        entry.get("bundle_id") == bundle_id and entry.get("status") in {"revoked", "quarantined"}
        for entry in index.get("certified_bundles", [])
    ):
        print(f"ERROR: revoked bundle {bundle_id} cannot be recertified")
        return 1

    # A signed security hold blocks promotion until independently resolved.
    if index.get("security_hold", {}).get("bundle_id") == bundle_id:
        print(f"ERROR: security-held bundle {bundle_id} cannot be certified")
        return 1

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
    """Quarantine a bundle and clear any active selection without replacement.

    This records in-repository bundle governance only. It does not revoke a
    signing key, inspect external verifiers, or remediate historical Git data.
    """
    index = load_index()
    revoked_entries = index["revoked_bundles"]
    already_revoked = any(
        entry.get("bundle_id") == bundle_id for entry in revoked_entries
    )
    revoked_at = datetime.now(timezone.utc).isoformat()
    changed = False

    for certified in index["certified_bundles"]:
        if certified.get("bundle_id") != bundle_id:
            continue
        if certified.get("status") != "revoked":
            certified["status"] = "revoked"
            certified.setdefault("revoked_at_utc", revoked_at)
            certified.setdefault("revoked_reason", reason)
            changed = True

    if not already_revoked:
        revoked_entries.append({
            "bundle_id": bundle_id,
            "revoked_at_utc": revoked_at,
            "reason": reason,
        })
        changed = True

    if index.get("active_bundle") == bundle_id:
        # Requiring a replacement here would leave a known-untrusted bundle
        # selected. No active bundle is safer than keeping compromised trust.
        index["active_bundle"] = None
        changed = True
        print(f"WARN: active bundle {bundle_id} quarantined; no active bundle")

    if not changed:
        print(f"WARN: bundle {bundle_id} already revoked")
        return 0

    save_index(index)
    print("BUNDLE_MARKED_REVOKED")
    print(f"bundle_id={bundle_id}")
    print(f"reason={reason}")
    print(f"active_bundle={index['active_bundle']}")
    print(f"revoked_count={len(revoked_entries)}")
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
