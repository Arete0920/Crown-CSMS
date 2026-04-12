from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VERIFY_DIR = ROOT / "audit-artifacts" / "release-verify"
VERIFY_DIR.mkdir(parents=True, exist_ok=True)

INVENTORY = VERIFY_DIR / "schema_w002_inventory.json"
REPORT = VERIFY_DIR / "schema_apiview_patch_report.json"

CLASS_RE = re.compile(
    r"^(?P<indent>\s*)class\s+\w+\((?P<bases>[^)]*(APIView|GenericAPIView|ViewSet|ModelViewSet|ReadOnlyModelViewSet)[^)]*)\):"
)
METHOD_RE = re.compile(
    r"^(?P<indent>\s+)def\s+(?P<name>get|post|put|patch|delete|list|retrieve|create|update|destroy)\("
)


def ensure_imports(text: str) -> str:
    inserts = []
    if "from drf_spectacular.utils import extend_schema" not in text:
        inserts.append("from drf_spectacular.utils import extend_schema")
    if "from drf_spectacular.types import OpenApiTypes" not in text:
        inserts.append("from drf_spectacular.types import OpenApiTypes")
    if not inserts:
        return text

    lines = text.splitlines()
    insert_at = 0
    for i, line in enumerate(lines):
        if line.startswith("from ") or line.startswith("import "):
            insert_at = i + 1
    lines[insert_at:insert_at] = inserts
    return "\n".join(lines) + "\n"


def target_files() -> list[Path]:
    files: list[Path] = []
    if INVENTORY.exists():
        items = json.loads(INVENTORY.read_text(encoding="utf-8"))
        for item in items[:30]:
            path = ROOT / item["file"]
            if path.exists():
                files.append(path)
    return files


def patch_file(path: Path) -> dict:
    original = path.read_text(encoding="utf-8", errors="ignore")
    text = ensure_imports(original)

    lines = text.splitlines()
    out = []
    added = 0
    class_stack: list[int] = []

    for line in lines:
        class_match = CLASS_RE.match(line)
        if class_match:
            class_stack = [len(class_match.group("indent"))]
            out.append(line)
            continue

        if class_stack:
            current_indent = len(line) - len(line.lstrip(" "))
            if line.strip() and current_indent <= class_stack[-1]:
                class_stack = []

        method_match = METHOD_RE.match(line)
        if class_stack and method_match:
            prev_nonempty = ""
            for j in range(len(out) - 1, -1, -1):
                if out[j].strip():
                    prev_nonempty = out[j].strip()
                    break
            if "@extend_schema" not in prev_nonempty:
                out.append(f"{method_match.group('indent')}@extend_schema(responses=OpenApiTypes.OBJECT)")
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