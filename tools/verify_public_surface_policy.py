#!/usr/bin/env python3
from __future__ import annotations

import json
import pathlib
import re
import sys
from typing import Iterable

ROOT = pathlib.Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
PUBLIC_POLICY = ROOT / "docs" / "security" / "public_endpoint_policy_matrix.json"
CSRF_POLICY = ROOT / "docs" / "security" / "csrf_exception_policy_matrix.json"

ALLOW_ANY_RE = re.compile(r"@permission_classes\(\[AllowAny\]\)|permission_classes\s*=\s*\[AllowAny\]")
CSRF_RE = re.compile(r"@csrf_exempt|@method_decorator\(\s*csrf_exempt")
SYMBOL_RE = re.compile(r"\s*(def|class)\s+([A-Za-z_]\w*)")


class PolicyError(RuntimeError):
    pass


def _discover() -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    allow_any: list[dict[str, str]] = []
    csrf_exempt: list[dict[str, str]] = []

    for path in BACKEND.rglob("*.py"):
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        rel = path.relative_to(ROOT).as_posix()

        for idx, line in enumerate(lines):
            if ALLOW_ANY_RE.search(line):
                allow_any.append(
                    {
                        "path": rel,
                        "symbol": _symbol_after(lines, idx),
                    }
                )
            if CSRF_RE.search(line):
                csrf_exempt.append(
                    {
                        "path": rel,
                        "symbol": _symbol_after(lines, idx),
                    }
                )

    allow_any = _dedupe_sorted(allow_any)
    csrf_exempt = _dedupe_sorted(csrf_exempt)
    return allow_any, csrf_exempt


def _symbol_after(lines: list[str], index: int) -> str:
    for j in range(index + 1, min(index + 12, len(lines))):
        m = SYMBOL_RE.match(lines[j])
        if m:
            return m.group(2)
    return "<unknown>"


def _dedupe_sorted(items: list[dict[str, str]]) -> list[dict[str, str]]:
    seen = set()
    out: list[dict[str, str]] = []
    for item in sorted(items, key=lambda x: (x["path"], x["symbol"])):
        key = (item["path"], item["symbol"])
        if key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out


def _load_policy(path: pathlib.Path, required_type: str) -> list[dict[str, object]]:
    if not path.exists():
        raise PolicyError(f"Missing policy file: {path.relative_to(ROOT)}")

    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise PolicyError(f"Invalid policy format (object expected): {path.relative_to(ROOT)}")

    entries = raw.get("entries")
    if not isinstance(entries, list):
        raise PolicyError(f"Invalid policy format (entries list expected): {path.relative_to(ROOT)}")

    for entry in entries:
        _validate_policy_entry(path, required_type, entry)

    return entries


def _validate_policy_entry(path: pathlib.Path, required_type: str, entry: object) -> None:
    rel = path.relative_to(ROOT)
    if not isinstance(entry, dict):
        raise PolicyError(f"Invalid policy entry in {rel}: {entry!r}")

    _require_keys(rel, entry, ("path", "symbol", "status", "owner", "rationale", "controls"))

    if entry.get("type") != required_type:
        raise PolicyError(
            f"Policy entry type mismatch in {rel}: expected {required_type}, got {entry.get('type')}"
        )

    if entry["status"] not in {"approved", "temporary"}:
        raise PolicyError(
            f"Policy status must be 'approved' or 'temporary' in {rel} for {entry['path']}::{entry['symbol']}"
        )

    if not isinstance(entry["controls"], list) or not entry["controls"]:
        raise PolicyError(
            f"Policy controls must be non-empty list in {rel} for {entry['path']}::{entry['symbol']}"
        )


def _require_keys(rel: pathlib.Path, entry: dict[str, object], keys: tuple[str, ...]) -> None:
    for key in keys:
        if key not in entry:
            raise PolicyError(f"Missing key '{key}' in {rel} entry: {entry}")


def _to_key(items: Iterable[dict[str, object]]) -> set[tuple[str, str]]:
    keys: set[tuple[str, str]] = set()
    for item in items:
        keys.add((str(item["path"]), str(item["symbol"])))
    return keys


def _report_diff(label: str, discovered: set[tuple[str, str]], policy: set[tuple[str, str]]) -> list[str]:
    errors: list[str] = []

    missing = sorted(discovered - policy)
    stale = sorted(policy - discovered)

    if missing:
        errors.append(f"{label}: unmanaged entries detected ({len(missing)}):")
        errors.extend([f"  - {p}::{s}" for p, s in missing])

    if stale:
        errors.append(f"{label}: stale policy entries detected ({len(stale)}):")
        errors.extend([f"  - {p}::{s}" for p, s in stale])

    return errors


def main() -> int:
    allow_any_discovered, csrf_discovered = _discover()

    try:
        allow_policy_entries = _load_policy(PUBLIC_POLICY, "allow_any")
        csrf_policy_entries = _load_policy(CSRF_POLICY, "csrf_exempt")
    except PolicyError as exc:
        print(f"Public surface policy gate FAILED: {exc}")
        return 1

    errors: list[str] = []
    errors.extend(_report_diff("AllowAny", _to_key(allow_any_discovered), _to_key(allow_policy_entries)))
    errors.extend(_report_diff("csrf_exempt", _to_key(csrf_discovered), _to_key(csrf_policy_entries)))

    if errors:
        print("Public surface policy gate FAILED")
        for line in errors:
            print(line)
        return 1

    print("Public surface policy gate PASSED")
    print(f"AllowAny entries tracked: {len(allow_any_discovered)}")
    print(f"csrf_exempt entries tracked: {len(csrf_discovered)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
