"""Canonical shell/backend contract parity tests."""

from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = REPO_ROOT / "backend"

if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from crown_api.shell_backend_contract import get_shell_backend_contract


CONTRACT_PATH = REPO_ROOT / "contracts" / "shell_backend_contract.json"


def _load_canonical_contract() -> dict:
    with CONTRACT_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _normalize(contract: dict) -> dict:
    return {
        "version": contract.get("version"),
        "dashboardModules": list(contract.get("dashboardModules") or []),
        "wizards": sorted(list(contract.get("wizards") or []), key=lambda row: str(row.get("moduleKey") or "")),
    }


class TestShellBackendContractParity(unittest.TestCase):
    def test_contract_file_exists(self):
        self.assertTrue(CONTRACT_PATH.exists(), f"Missing canonical contract: {CONTRACT_PATH}")

    def test_backend_rows_match_canonical_contract(self):
        self.assertEqual(_normalize(_load_canonical_contract()), _normalize(get_shell_backend_contract()))

    def test_backend_module_keys_unique(self):
        module_keys = [row.get("moduleKey") for row in get_shell_backend_contract().get("wizards", [])]
        self.assertEqual(
            len(module_keys),
            len(set(module_keys)),
            f"Duplicate backend wizard module keys found: {module_keys}",
        )


if __name__ == "__main__":
    unittest.main()
