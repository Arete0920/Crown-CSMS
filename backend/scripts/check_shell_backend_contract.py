"""Fail when backend wizard declarations drift from contracts/shell_backend_contract.json."""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = REPO_ROOT / "backend"

if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from crown_api.shell_backend_contract import get_backend_wizard_contract_rows  # noqa: E402


def _canonical_backend_rows() -> list[dict]:
    contract_path = REPO_ROOT / "contracts" / "shell_backend_contract.json"
    with contract_path.open("r", encoding="utf-8") as handle:
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


def main() -> int:
    canonical_rows = _canonical_backend_rows()
    backend_rows = get_backend_wizard_contract_rows()

    if canonical_rows != backend_rows:
        print("FAIL: backend contract parity mismatch detected.")

        canonical_by_slug = {row["slug"]: row for row in canonical_rows}
        backend_by_slug = {row["slug"]: row for row in backend_rows}

        missing_in_contract = sorted(set(backend_by_slug) - set(canonical_by_slug))
        missing_in_backend = sorted(set(canonical_by_slug) - set(backend_by_slug))
        mismatched = [
            slug
            for slug in sorted(set(canonical_by_slug) & set(backend_by_slug))
            if canonical_by_slug[slug] != backend_by_slug[slug]
        ]

        if missing_in_contract:
            print(f"Canonical contract missing backend slugs: {', '.join(missing_in_contract)}")
        if missing_in_backend:
            print(f"Backend registry missing canonical slugs: {', '.join(missing_in_backend)}")
        if mismatched:
            print(f"Rows with field mismatches: {', '.join(mismatched)}")

        return 1

    print(f"PASS: backend contract parity verified ({len(backend_rows)} wizard entries).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
