from __future__ import annotations

import json
import re
from pathlib import Path

try:
    from scripts.release.schema_patch_path_guard import ensure_imports, inventory_targets
except ModuleNotFoundError:
    from schema_patch_path_guard import ensure_imports, inventory_targets

ROOT = Path(__file__).resolve().parents[2]
VERIFY_DIR = ROOT / "audit-artifacts" / "release-verify"
VERIFY_DIR.mkdir(parents=True, exist_ok=True)

INVENTORY = VERIFY_DIR / "schema_w002_inventory.json"
REPORT = VERIFY_DIR / "schema_function_patch_report.json"

API_VIEW_RE = re.compile(r"^(?P<indent>\s*)@api_view\(")


def target_files() -> list[Path]:
    files = inventory_targets(INVENTORY, ROOT)

    for path in ROOT.glob("backend/*_wizard/views.py"):
        if path not in files:
            files.append(path)

    fixed = [
        ROOT / "backend" / "ledger" / "api.py",
        ROOT / "backend" / "advancement" / "api.py",
        ROOT / "backend" / "core" / "auth" / "views.py",
        ROOT / "backend" / "aftercare" / "api.py",
        ROOT / "backend" / "aid" / "api_views.py",
        ROOT / "backend" / "billing" / "api.py",
        ROOT / "backend" / "comms" / "api" / "views.py",
        ROOT / "backend" / "hr" / "api.py",
        ROOT / "backend" / "safety" / "api.py",
    ]
    for path in fixed:
        if path.exists() and path not in files:
            files.append(path)

    return files


def patch_file(path: Path) -> dict:
    original = path.read_text(encoding="utf-8", errors="ignore")
    text = ensure_imports(original)

    lines = text.splitlines()
    out = []
    added = 0

    for i, line in enumerate(lines):
        match = API_VIEW_RE.match(line)
        if match:
            prev_nonempty = ""
            for j in range(len(out) - 1, -1, -1):
                if out[j].strip():
                    prev_nonempty = out[j].strip()
                    break
            if "@extend_schema" not in prev_nonempty:
                out.append(f"{match.group('indent')}@extend_schema(responses=OpenApiTypes.OBJECT)")
                added += 1
        out.append(line)

    new_text = "\n".join(out).rstrip() + "\n"
    if new_text != original:
        path.write_text(new_text, encoding="utf-8")

    return {
        "file": str(path.relative_to(ROOT)).replace("\\", "/"),
        "decorators_added": added,
        "changed": new_text != original,
    }


def main() -> None:
    results = [patch_file(path) for path in target_files()]
    REPORT.write_text(json.dumps(results, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()