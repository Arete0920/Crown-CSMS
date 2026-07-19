#!/usr/bin/env python3
"""Deterministically inventory maintainability patterns without inferring authorship."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Sequence

SEVERITY_ORDER = {"none": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}
EXTENSIONS = {".py", ".ps1", ".cmd", ".sh", ".js", ".jsx", ".ts", ".tsx", ".yml", ".yaml"}
EXCLUDED_DIRS = {
    ".git", ".venv", "__pycache__", ".pytest_cache", ".mypy_cache",
    "node_modules", "vendor", "dist", "build", "coverage", "htmlcov",
    "audit-artifacts",
}
SUPPRESSION = re.compile(r"ai-audit:\s*allow\s+(?P<rule>AP-\d{2}|all)", re.I)
URGENCY_NAME = re.compile(
    r"(?:^|[_\-.])(?:tmp|temp|autopilot|finish[_-]?now|final[_-]?final|"
    r"fix[_-]?everything|one[_-]?click|gauntlet)(?:$|[_\-.])", re.I
)
ABSOLUTE_PATHS = (
    re.compile(r"\b[A-Za-z]:\\(?:Users|w|work|workspace|repos?|projects?)\\", re.I),
    re.compile(r"/(?:home|Users)/[A-Za-z0-9._-]+/"),
)
SYNTHETIC_STATUS = re.compile(
    r"\b(?:classification|decision_tag|maturity_tag|pass_state|proof_freshness|"
    r"production_backed|verification_status|verdict|status)\b\s*[:=]\s*"
    r"[\"'](?:PASS|SAFE|FIXED|KEEP|PARTIAL|CURRENT|PRODUCTION[- ]READY|"
    r"COMPLETE|COMPLETED|VERIFIED|YES|NO|UNKNOWN)[\"']", re.I
)
BROAD_EXCEPTION = re.compile(r"^\s*except(?:\s+Exception(?:\s+as\s+\w+)?)?\s*:\s*(?:#.*)?$")
PLACEHOLDER = re.compile(r"\b(?:TODO|FIXME|HACK|placeholder|not implemented|coming soon)\b", re.I)
SEPARATOR = re.compile(r"^\s*(?:#|//|;|<!--)\s*[=*_-]{12,}(?:\s*-->)?\s*$")


@dataclass(frozen=True, order=True)
class Finding:
    path: str
    line: int
    rule: str
    severity: str
    message: str
    excerpt: str


@dataclass(frozen=True)
class AuditResult:
    root: str
    scanned_files: int
    skipped_large_files: int
    findings: tuple[Finding, ...]

    @property
    def counts_by_severity(self) -> dict[str, int]:
        counts = Counter(item.severity for item in self.findings)
        return {level: counts.get(level, 0) for level in ("critical", "high", "medium", "low")}

    @property
    def counts_by_rule(self) -> dict[str, int]:
        return dict(sorted(Counter(item.rule for item in self.findings).items()))


def _suppressed(line: str, rule: str) -> bool:
    rules = {match.group("rule").upper() for match in SUPPRESSION.finditer(line)}
    return "ALL" in rules or rule.upper() in rules


def _excerpt(line: str, limit: int = 180) -> str:
    value = " ".join(line.strip().split())
    return value if len(value) <= limit else value[: limit - 3] + "..."


def _add(findings: list[Finding], path: str, number: int, line: str, rule: str, severity: str, message: str) -> None:
    if not _suppressed(line, rule):
        findings.append(Finding(path, number, rule, severity, message, _excerpt(line)))


def scan_text(relative_path: str, text: str) -> list[Finding]:
    findings: list[Finding] = []
    lines = text.splitlines()
    filename = Path(relative_path).name
    if URGENCY_NAME.search(filename):
        findings.append(Finding(relative_path, 0, "AP-01", "high", "temporary, urgency, or outcome-claiming filename", filename))

    for number, line in enumerate(lines, 1):
        if any(pattern.search(line) for pattern in ABSOLUTE_PATHS):
            _add(findings, relative_path, number, line, "AP-02", "high", "machine-specific absolute path")
        if SYNTHETIC_STATUS.search(line):
            _add(findings, relative_path, number, line, "AP-03", "high", "literal verdict or classification requires current evidence")
        if relative_path.endswith(".py") and BROAD_EXCEPTION.search(line):
            _add(findings, relative_path, number, line, "AP-04", "medium", "broad Python exception handler")
        if PLACEHOLDER.search(line):
            _add(findings, relative_path, number, line, "AP-07", "medium", "placeholder or unfinished-work marker")
        if SEPARATOR.search(line):
            _add(findings, relative_path, number, line, "AP-06", "low", "decorative separator comment")

    count = len(lines)
    if count > 1200:
        findings.append(Finding(relative_path, 0, "AP-09", "high", f"oversized source file ({count} lines)", "size is a review trigger, not proof of a defect"))
    elif count > 700:
        findings.append(Finding(relative_path, 0, "AP-09", "medium", f"large source file ({count} lines)", "size is a review trigger, not proof of a defect"))
    return findings


def _excluded(path: Path, root: Path, explicit: set[Path]) -> bool:
    resolved = path.resolve()
    if any(resolved == item or item in resolved.parents for item in explicit):
        return True
    try:
        relative = resolved.relative_to(root)
    except ValueError:
        return True
    return any(part in EXCLUDED_DIRS for part in relative.parts)


def _iter_files(root: Path, explicit: set[Path]) -> Iterable[Path]:
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.suffix.lower() in EXTENSIONS and not _excluded(path, root, explicit):
            yield path


def run_audit(root: Path, *, exclusions: Iterable[str] = (), max_file_bytes: int = 1_000_000) -> AuditResult:
    root = root.resolve()
    if not root.is_dir():
        raise ValueError(f"audit root is not a directory: {root}")
    if max_file_bytes < 1:
        raise ValueError("max_file_bytes must be positive")
    explicit = {(root / item).resolve() if not Path(item).is_absolute() else Path(item).resolve() for item in exclusions}
    findings: list[Finding] = []
    scanned = 0
    skipped = 0
    for path in _iter_files(root, explicit):
        relative = path.relative_to(root).as_posix()
        try:
            if path.stat().st_size > max_file_bytes:
                skipped += 1
                continue
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            findings.append(Finding(relative, 0, "AP-10", "medium", f"unable to read source file: {exc}", ""))
            continue
        scanned += 1
        findings.extend(scan_text(relative, text))
    return AuditResult(str(root), scanned, skipped, tuple(sorted(findings)))


def result_as_dict(result: AuditResult) -> dict[str, object]:
    return {
        "root": result.root,
        "scanned_files": result.scanned_files,
        "skipped_large_files": result.skipped_large_files,
        "counts_by_severity": result.counts_by_severity,
        "counts_by_rule": result.counts_by_rule,
        "findings": [asdict(item) for item in result.findings],
    }


def render_result(result: AuditResult, output_format: str) -> str:
    if output_format == "json":
        return json.dumps(result_as_dict(result), indent=2, sort_keys=True) + "\n"
    if output_format == "markdown":
        lines = [
            "# AI-Pattern Audit", "",
            "> Findings identify maintainability and provenance risks; they do not prove authorship.", "",
            f"- Scanned files: {result.scanned_files}",
            f"- Skipped large files: {result.skipped_large_files}",
            f"- Findings: {len(result.findings)}", "",
            "| Severity | Rule | Location | Finding |", "|---|---|---|---|",
        ]
        for item in result.findings:
            location = item.path if item.line == 0 else f"{item.path}:{item.line}"
            lines.append(f"| {item.severity} | {item.rule} | `{location}` | {item.message} |")
        return "\n".join(lines) + "\n"
    lines = [
        f"root={result.root}", f"scanned_files={result.scanned_files}",
        f"skipped_large_files={result.skipped_large_files}", f"findings={len(result.findings)}",
    ]
    for severity, count in result.counts_by_severity.items():
        lines.append(f"{severity}={count}")
    for item in result.findings:
        location = item.path if item.line == 0 else f"{item.path}:{item.line}"
        lines.append(f"{item.severity.upper()} {item.rule} {location} - {item.message} | {item.excerpt}")
    return "\n".join(lines) + "\n"


def threshold_reached(result: AuditResult, threshold: str) -> bool:
    if threshold == "none":
        return False
    floor = SEVERITY_ORDER[threshold]
    return any(SEVERITY_ORDER[item.severity] >= floor for item in result.findings)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--format", choices=("text", "json", "markdown"), default="text", dest="output_format")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--exclude", action="append", default=[])
    parser.add_argument("--max-file-bytes", type=int, default=1_000_000)
    parser.add_argument("--fail-on", choices=tuple(SEVERITY_ORDER), default="none")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    result = run_audit(args.root, exclusions=args.exclude, max_file_bytes=args.max_file_bytes)
    output = render_result(result, args.output_format)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output, encoding="utf-8")
    else:
        sys.stdout.write(output)
    return 1 if threshold_reached(result, args.fail_on) else 0


if __name__ == "__main__":
    raise SystemExit(main())
