"""Validate generated schema inventory file targets before rewriting source files."""

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
