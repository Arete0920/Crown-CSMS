# tools/verify_demo_contract_freeze.py
# Phase 6 Move #4: Demo Proof Contract Freeze Gate (Tier-1)
#
# Contract: tools/rc_endpoint_probes.json
# Lock:     tools/demo_contract_t1.lock   (SHA256 over normalized Tier-1 probe list)
#
# CI behavior: FAIL if Tier-1 contract changes without updating the lock.
# Local: run with --update-lock to intentionally re-freeze after a deliberate Tier-1 change.
#
# Usage:
#   python tools/verify_demo_contract_freeze.py               # verify (CI)
#   python tools/verify_demo_contract_freeze.py --update-lock # re-freeze (local only)

import argparse
import hashlib
import json
import os
import sys
from typing import Any, Dict, List, Tuple

CONTRACT_PATH_DEFAULT = os.path.join("tools", "rc_endpoint_probes.json")
LOCK_PATH_DEFAULT = os.path.join("tools", "demo_contract_t1.lock")

VALID_METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"}
VALID_TIERS = {"T1", "T2"}
MIN_T1_PROBES = 5


def die(msg: str) -> None:
    print(f"\nDEMO CONTRACT FREEZE FAILED: {msg}", file=sys.stderr)
    sys.exit(1)


def load_json(path: str) -> Any:
    if not os.path.exists(path):
        die(f"missing file: {path}")
    with open(path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError as e:
            die(f"invalid JSON in {path}: {e}")


def normalize_method(m: str) -> str:
    return (m or "").strip().upper()


def ensure_probe_shape(p: Dict[str, Any], idx: int) -> None:
    required_keys = ["name", "method", "path", "expect", "requiresAuth", "requiresSchoolId", "tier"]
    missing = [k for k in required_keys if k not in p]
    if missing:
        die(f"probe[{idx}] ({p.get('name', '?')!r}) missing keys: {missing}")

    name = p["name"]
    if not isinstance(name, str) or not name.strip():
        die(f"probe[{idx}] invalid name: {name!r}")

    path = p["path"]
    if not isinstance(path, str) or not path.strip().startswith("/"):
        die(f"probe[{idx}] ({name!r}) invalid path (must start with /): {path!r}")

    method = normalize_method(p["method"])
    if method not in VALID_METHODS:
        die(f"probe[{idx}] ({name!r}) invalid method: {p.get('method')!r}")

    expect = p["expect"]
    if not isinstance(expect, list) or len(expect) == 0:
        die(f"probe[{idx}] ({name!r}) expect must be a non-empty list: {expect!r}")
    if not all(isinstance(x, int) for x in expect):
        die(f"probe[{idx}] ({name!r}) expect must be list[int]: {expect!r}")

    for bool_key in ("requiresAuth", "requiresSchoolId"):
        if not isinstance(p[bool_key], bool):
            die(f"probe[{idx}] ({name!r}) {bool_key} must be boolean, got {p[bool_key]!r}")

    tier = str(p["tier"]).strip().upper()
    if tier not in VALID_TIERS:
        die(f"probe[{idx}] ({name!r}) tier must be T1 or T2, got {p.get('tier')!r}")


def extract_tier1(probes: List[Dict[str, Any]]) -> List[Tuple]:
    t1 = []
    for p in probes:
        tier = str(p.get("tier", "")).strip().upper()
        if tier != "T1":
            continue
        t1.append((
            p["name"].strip(),
            normalize_method(p["method"]),
            p["path"].strip(),
            tuple(sorted(int(x) for x in p["expect"])),
            bool(p["requiresAuth"]),
            bool(p["requiresSchoolId"]),
        ))
    # Deterministic ordering: method → path → name
    t1.sort(key=lambda x: (x[1], x[2], x[0]))
    return t1


def fingerprint_tier1(t1: List[Tuple]) -> str:
    normalized = [
        {
            "name": name,
            "method": method,
            "path": path,
            "expect": list(expect),
            "requiresAuth": req_auth,
            "requiresSchoolId": req_school,
        }
        for (name, method, path, expect, req_auth, req_school) in t1
    ]
    blob = json.dumps(normalized, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def read_lock(lock_path: str) -> str:
    if not os.path.exists(lock_path):
        return ""
    with open(lock_path, "r", encoding="utf-8") as f:
        return f.read().strip()


def write_lock(lock_path: str, fp: str) -> None:
    lock_dir = os.path.dirname(lock_path)
    if lock_dir:
        os.makedirs(lock_dir, exist_ok=True)
    with open(lock_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(fp + "\n")


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Verify (or update) the Tier-1 demo probe contract hash lock."
    )
    ap.add_argument("--contract", default=CONTRACT_PATH_DEFAULT,
                    help=f"Path to probe contract JSON (default: {CONTRACT_PATH_DEFAULT})")
    ap.add_argument("--lock", default=LOCK_PATH_DEFAULT,
                    help=f"Path to lock file (default: {LOCK_PATH_DEFAULT})")
    ap.add_argument("--update-lock", action="store_true",
                    help="Compute current Tier-1 fingerprint and write it to the lock file")
    args = ap.parse_args()

    # --- Load + validate contract schema ---
    doc = load_json(args.contract)
    if not isinstance(doc, dict):
        die("contract JSON root must be an object")
    if "version" not in doc:
        die("contract missing top-level 'version'")
    if "probes" not in doc or not isinstance(doc["probes"], list):
        die("contract missing top-level 'probes' list")

    probes = doc["probes"]
    if len(probes) == 0:
        die("contract probes list is empty")

    for i, p in enumerate(probes):
        if not isinstance(p, dict):
            die(f"probe[{i}] must be an object")
        ensure_probe_shape(p, i)

    print(f"Schema OK  ({len(probes)} probes validated)")

    # --- Tier-1 extraction + fingerprint ---
    t1 = extract_tier1(probes)
    t2_count = len(probes) - len(t1)

    if len(t1) < MIN_T1_PROBES:
        die(f"Too few Tier-1 probes ({len(t1)}). Minimum required: {MIN_T1_PROBES}.")

    fp = fingerprint_tier1(t1)
    print(f"Tier-1 probes: {len(t1)}   Tier-2 probes: {t2_count}")
    print(f"Fingerprint:   {fp}")

    # --- Update mode ---
    if args.update_lock:
        write_lock(args.lock, fp)
        print(f"\nDEMO CONTRACT FREEZE: lock updated -> {args.lock}")
        return

    # --- Verify mode ---
    lock = read_lock(args.lock)
    if not lock:
        die(
            f"Lock file missing: {args.lock}\n"
            "  Run once (locally): python tools/verify_demo_contract_freeze.py --update-lock\n"
            "  Then commit tools/demo_contract_t1.lock"
        )

    if lock != fp:
        print(f"\n  lock file : {lock}", file=sys.stderr)
        print(f"  current   : {fp}", file=sys.stderr)
        die(
            "Tier-1 contract changed without updating lock.\n"
            "  If intentional: python tools/verify_demo_contract_freeze.py --update-lock  then commit the lock.\n"
            "  If accidental: revert your change to tools/rc_endpoint_probes.json."
        )

    print(f"\nDEMO CONTRACT FREEZE PASSED  Tier-1={len(t1)}  fingerprint={fp}")


if __name__ == "__main__":
    main()
