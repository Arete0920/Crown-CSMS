"""Session-local snapshot of the repository's Python source used by module-sentinel tests.

The historical checks independently read the whole source tree for each case.
Caching the same inclusive *.py snapshot preserves their existing predicates
while avoiding repeated filesystem reads during a static-source test run.
"""

from functools import lru_cache
from pathlib import Path


@lru_cache(maxsize=4)
def repository_python_files(project_root: Path) -> tuple[Path, ...]:
    """Return the same inclusive Python path inventory as Path.rglob('*.py')."""
    return tuple(project_root.rglob("*.py"))


@lru_cache(maxsize=4)
def repository_python_source(project_root: Path) -> str:
    """Concatenate the source text in discovery order, tolerating unreadable files."""
    parts: list[str] = []
    for source_path in repository_python_files(project_root):
        try:
            parts.append(source_path.read_text(encoding="utf-8", errors="ignore"))
        except Exception:
            # Preserve the historical sentinel tests' read-failure behavior.
            continue
    return "".join(parts)
