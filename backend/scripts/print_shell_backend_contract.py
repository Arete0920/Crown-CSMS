"""Print backend wizard contract rows for parity debugging."""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = REPO_ROOT / "backend"

if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from crown_api.shell_backend_contract import get_backend_wizard_contract_rows  # noqa: E402


if __name__ == "__main__":
    print(
        json.dumps(
            {
                "scope": "wizard_registry_parity",
                "wizardCount": len(get_backend_wizard_contract_rows()),
                "wizards": get_backend_wizard_contract_rows(),
            },
            indent=2,
        )
    )
