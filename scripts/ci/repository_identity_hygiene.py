#!/usr/bin/env python3
"""Guard current repository identity and naming conventions."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

EXCLUDED_PARTS = {
    ".git", ".venv", "venv", "node_modules", "dist", "build", "coverage",
    "__pycache__", ".pytest_cache", "audit-artifacts",
}

HISTORICAL_PREFIXES = (
    "archive/",
    "docs/archive/",
    "docs/release/",
    "docs/demo-proof/",
    "docs/instruction-ledger/",
    "solomon_governance_c1/governance/c1/runtime/audit_pack/",
)

HISTORICAL_EXACT = {
    "docs/PROOF_LOG_2026-02-24.md",
    "docs/PROOF_DEPLOY_INTEGRITY_2026-02-21.md",
}

TEXT_EXTENSIONS = {
    ".md", ".txt", ".py", ".js", ".jsx", ".ts", ".tsx", ".json", ".yml", ".yaml",
    ".csv", ".ps1", ".sh", ".html", ".css", ".toml", ".ini", ".cfg", ".cmd",
}

FORBIDDEN = {
    "tcmegahan/Crown2026": "obsolete predecessor repository URL",
    "Arete-Advisory-Group/Crown-CSMS": "obsolete repository owner path",
    "Crown2026!": "retired hard-coded demo password",
    "AGENTS.md": "retired repository instruction file",
    "Little Lambs Daycare": "retired daycare display name",
}


def first_party_text_files():
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(ROOT)
        if any(part in EXCLUDED_PARTS for part in rel.parts):
            continue
        rel_text = rel.as_posix()
        if rel_text in HISTORICAL_EXACT or rel_text.startswith(HISTORICAL_PREFIXES):
            continue
        if "/migrations/" in f"/{rel_text}/":
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
            for token, reason in FORBIDDEN.items():
                if token in line:
                    findings.append((rel.as_posix(), lineno, reason))

    if findings:
        print("Repository identity/naming hygiene violations:")
        for rel, lineno, reason in findings:
            print(f"- {rel}:{lineno} ({reason})")
        return 1

    print("Repository identity/naming hygiene: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
