"""Validate generated schema inventory file targets before rewriting source files."""

import json
from pathlib import Path


def inventory_target(item: object, root: Path) -> Path | None:
    """Fail closed for paths outside real backend Python files."""
    if not isinstance(item, dict) or not isinstance(item.get("file"), str):
        raise ValueError("invalid schema inventory entry")
    name = item["file"]
    if name == "unknown":
        return None
    relative = Path(name)
    if (
        "\\" in name
        or not relative.parts
        or relative.parts[0] != "backend"
        or ".." in relative.parts
        or relative.is_absolute()
        or relative.suffix != ".py"
    ):
        raise ValueError("schema inventory path must be a backend Python file")
    target = root / relative
    if not target.exists():
        return None
    if target.resolve() != target or not target.is_file():
        raise ValueError("schema inventory path must be a regular in-repository file")
    return target


def inventory_targets(inventory: Path, root: Path) -> list[Path]:
    """Return only validated targets from a bounded schema inventory."""
    if not inventory.exists():
        return []
    items = json.loads(inventory.read_text(encoding="utf-8"))
    if not isinstance(items, list):
        raise ValueError("schema inventory must be a list")
    targets: list[Path] = []
    for item in items[:30]:
        path = inventory_target(item, root)
        if path is not None:
            targets.append(path)
    return targets


def ensure_imports(text: str) -> str:
    """Preserve the existing schema decorator import insertion behavior."""
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
    return "\\n".join(lines) + "\\n"
