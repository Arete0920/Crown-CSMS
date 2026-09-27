#!/usr/bin/env python3
"""Fail when named competitors appear in committed first-party repository content."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

EXCLUDED_PARTS = {
    ".git", ".venv", "venv", "node_modules", "dist", "build", "coverage",
    "__pycache__", ".pytest_cache", "audit-artifacts",
}

TEXT_EXTENSIONS = {
    ".md", ".txt", ".py", ".js", ".jsx", ".ts", ".tsx", ".json", ".yml", ".yaml",
    ".csv", ".ps1", ".sh", ".html", ".css", ".toml", ".ini", ".cfg",
}

# Keep this list generic in policy docs; this mechanical gate is the only committed
# location where detection terms are centralized.
TERMS = [
    "gr" + "adelink",
    "f" + "acts management",
    "ren" + "web",
    "black" + "baud",
    "power" + "school",
    "ver" + "across",
    "redi" + "ker",
    "nel" + "net",
    "my" + "schoolworx",
    "my" + "schoolworks",
    "final" + "site",
    "school" + "admin",
    "quick" + "schools",
    "school" + "cues",
    "school" + "speak",
    "open" + "sis",
    "dream" + "class",
    "classe" + "365",
    "fe" + "dena",
    "ed" + "sembli",
    "spark" + "rock",
    "school" + "mint",
    "rav" + "enna",
    "senior " + "systems",
    "sky" + "ward",
    "infinite " + "campus",
    "t" + "ads",
    "f" + "aria",
    "curriculum " + "trak",
    "curriculum " + "track",
    "praxi" + "school",
]

PATTERNS = [
    (term, re.compile(r"(?i)(?<![A-Za-z0-9])" + re.escape(term) + r"(?![A-Za-z0-9])"))
    for term in TERMS
]


def first_party_text_files():
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(ROOT)
        if any(part in EXCLUDED_PARTS for part in rel.parts):
            continue
        if path.suffix.lower() not in TEXT_EXTENSIONS:
            continue
        yield rel, path


def main() -> int:
    findings: list[tuple[str, int, str]] = []
    self_rel = Path(__file__).resolve().relative_to(ROOT)

    for rel, path in first_party_text_files():
        if rel == self_rel:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for lineno, line in enumerate(text.splitlines(), start=1):
            for term, pattern in PATTERNS:
                if pattern.search(line):
                    findings.append((rel.as_posix(), lineno, term))
                    break

    if findings:
        print("Named competitor references found in first-party repository content:")
        for rel, lineno, _ in findings:
            print(f"- {rel}:{lineno}")
        return 1

    print("Competitor-name hygiene: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
