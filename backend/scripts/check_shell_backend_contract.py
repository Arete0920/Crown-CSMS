"""Fail when backend shell contract declaration drifts from canonical contract."""

from __future__ import annotations

import json
import importlib.util
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = REPO_ROOT / "backend"

if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))


def _load_backend_contract_module():
    module_path = BACKEND_ROOT / "crown_api" / "shell_backend_contract.py"
    spec = importlib.util.spec_from_file_location("shell_backend_contract", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load backend contract module from {module_path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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
    backend_module = _load_backend_contract_module()
    backend = _normalize(backend_module.get_shell_backend_contract())

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
