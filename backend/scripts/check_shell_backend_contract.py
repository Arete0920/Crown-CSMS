"""Fail when backend shell contract declaration drifts from canonical contract."""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = REPO_ROOT / "backend"

if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from crown_api.shell_backend_contract import get_shell_backend_contract  # noqa: E402


def _load_canonical_contract() -> dict:
    contract_path = REPO_ROOT / "contracts" / "shell_backend_contract.json"
    with contract_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _normalize(contract: dict) -> dict:
    normalized = {
        "version": contract.get("version"),
        "dashboardModules": list(contract.get("dashboardModules") or []),
        "wizards": sorted(list(contract.get("wizards") or []), key=lambda row: str(row.get("moduleKey") or "")),
    }
    return normalized


def main() -> int:
    canonical = _normalize(_load_canonical_contract())
    backend = _normalize(get_shell_backend_contract())

    if canonical != backend:
        print("FAIL: backend contract parity mismatch detected.")
        print("=== Canonical (normalized) ===")
        print(json.dumps(canonical, indent=2, sort_keys=True))
        print("=== Backend (normalized) ===")
        print(json.dumps(backend, indent=2, sort_keys=True))
        return 1

    print(f"PASS: backend contract parity verified ({len(backend['wizards'])} wizard entries).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
