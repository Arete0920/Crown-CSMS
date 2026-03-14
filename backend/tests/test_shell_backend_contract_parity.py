"""Canonical shell/backend wizard contract parity tests."""

from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = REPO_ROOT / "backend"

if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from crown_api.shell_backend_contract import get_backend_wizard_contract_rows


CONTRACT_PATH = REPO_ROOT / "contracts" / "shell_backend_contract.json"


def _load_canonical_backend_rows() -> list[dict]:
    with CONTRACT_PATH.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)

    rows = []
    for row in payload.get("wizards", []):
        rows.append(
            {
                "slug": row.get("slug"),
                "title": row.get("title"),
                "backendUrlPrefix": row.get("backendUrlPrefix"),
                "backendModule": row.get("backendModule"),
            }
        )
    rows.sort(key=lambda item: item["slug"])
    return rows


class TestShellBackendContractParity(unittest.TestCase):
    def test_contract_file_exists(self):
        self.assertTrue(CONTRACT_PATH.exists(), f"Missing canonical contract: {CONTRACT_PATH}")

    def test_backend_rows_match_canonical_contract(self):
        self.assertEqual(_load_canonical_backend_rows(), get_backend_wizard_contract_rows())

    def test_backend_slugs_unique(self):
        slugs = [row["slug"] for row in get_backend_wizard_contract_rows()]
        self.assertEqual(len(slugs), len(set(slugs)), f"Duplicate backend wizard slugs found: {slugs}")


if __name__ == "__main__":
    unittest.main()
