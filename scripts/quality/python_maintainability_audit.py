#!/usr/bin/env python3
"""Inventory Python maintainability findings without changing source files.

This read-only inventory reports PEP 8 line length, missing function
annotations and docstrings, and simple loop-refactor candidates. Findings
require human review and do not assert that a rewrite preserves behavior.
"""

from __future__ import annotations

import argparse
import ast
import json
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Sequence

MAX_LINE_LENGTH = 79
EXCLUDED_DIRECTORIES = frozenset(
    {
        ".git",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".venv",
        "__pycache__",
        "archive",
        "audit-artifacts",
        "build",
        "dist",
        "migrations",
        "node_modules",
        "venv",
    }
)


@dataclass(frozen=True, order=True)
class Finding:
    """A reviewable source location and maintainability concern."""

    path: str
    line: int
    rule: str
    detail: str


@dataclass(frozen=True)
class Inventory:
    """Deterministic source-inventory results and summary counters."""

    scanned_files: int
    skipped_files: int
    findings: tuple[Finding, ...]

    @property
    def counts_by_rule(self) -> dict[str, int]:
        """Return counts by rule name, sorted for stable output."""
        counts = Counter(item.rule for item in self.findings)
        return dict(sorted(counts.items()))


class _DefinitionVisitor(ast.NodeVisitor):
    """Check functions and reviewable append-only loop shapes."""

    def __init__(self, path: str) -> None:
        """Begin with an empty qualified-name scope for one source file."""
        self.path = path
        self.scope: list[str] = []
        self.findings: list[Finding] = []

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Include the owning class in reported function names."""
        self.scope.append(node.name)
        self.generic_visit(node)
        self.scope.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Inspect a synchronous function and its nested definitions."""
        self._visit_function(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Apply identical rules to asynchronous functions."""
        self._visit_function(node)

    def _visit_function(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef
    ) -> None:
        """Record missing documentation and annotations for one function."""
        name = ".".join((*self.scope, node.name))
        if not ast.get_docstring(node):
            self.findings.append(
                Finding(self.path, node.lineno, "missing_docstring", name)
            )
        if node.returns is None:
            self.findings.append(
                Finding(self.path, node.lineno, "missing_return_type", name)
            )

        positional = [*node.args.posonlyargs, *node.args.args]
        if positional and positional[0].arg in {"self", "cls"}:
            positional = positional[1:]
        parameters = [*positional, *node.args.kwonlyargs]
        parameters.extend(
            arg for arg in (node.args.vararg, node.args.kwarg)
            if arg is not None
        )
        untyped = [arg.arg for arg in parameters if arg.annotation is None]
        if untyped:
            self.findings.append(
                Finding(
                    self.path,
                    node.lineno,
                    "missing_parameter_types",
                    f"{name}: {', '.join(untyped)}",
                )
            )

        self.scope.append(node.name)
        self.generic_visit(node)
        self.scope.pop()

    def visit_For(self, node: ast.For) -> None:
        """Flag simple append loops for review, never automatic rewriting."""
        if len(node.body) == 1 and not node.orelse:
            statement = node.body[0]
            if isinstance(statement, ast.Expr):
                call = statement.value
                if (
                    isinstance(call, ast.Call)
                    and isinstance(call.func, ast.Attribute)
                    and call.func.attr == "append"
                    and len(call.args) == 1
                    and not call.keywords
                ):
                    self.findings.append(
                        Finding(
                            self.path,
                            node.lineno,
                            "append_loop_review",
                            ".".join(self.scope) or "module",
                        )
                    )
        self.generic_visit(node)


def scan_text(path: str, text: str) -> list[Finding]:
    """Inventory one Python source file without importing or executing it."""
    # A UTF-8 BOM is an encoding marker, not a Python syntax error.
    text = text.removeprefix("\ufeff")
    findings = [
        Finding(path, index, "line_over_79", str(len(line)))
        for index, line in enumerate(text.splitlines(), start=1)
        if len(line) > MAX_LINE_LENGTH
    ]
    try:
        tree = ast.parse(text, filename=path)
    except SyntaxError as exc:
        findings.append(
            Finding(path, exc.lineno or 0, "syntax_error", "cannot parse")
        )
        return sorted(findings)

    visitor = _DefinitionVisitor(path)
    visitor.visit(tree)
    return sorted([*findings, *visitor.findings])


def scan_root(root: Path, max_file_bytes: int = 1_000_000) -> Inventory:
    """Inspect Python files, excluding generated and vendor trees."""
    root = root.resolve()
    if not root.is_dir():
        raise ValueError("root must be an existing directory")
    if max_file_bytes < 1:
        raise ValueError("max_file_bytes must be positive")

    scanned = skipped = 0
    findings: list[Finding] = []
    for path in sorted(root.rglob("*.py")):
        if EXCLUDED_DIRECTORIES.intersection(path.relative_to(root).parts):
            continue
        # Never inspect linked files outside the checkout, including secrets.
        if path.is_symlink() or not path.resolve().is_relative_to(root):
            skipped += 1
            continue
        if not path.is_file():
            continue
        relative = path.relative_to(root).as_posix()
        try:
            if path.stat().st_size > max_file_bytes:
                skipped += 1
                continue
            source = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            skipped += 1
            findings.append(Finding(relative, 0, "read_error", "unreadable"))
            continue
        scanned += 1
        findings.extend(scan_text(relative, source))
    return Inventory(scanned, skipped, tuple(sorted(findings)))


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse repository path and output options for the read-only scanner."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "root", nargs="?", type=Path, default=Path(__file__).parents[2]
    )
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--limit", type=int, default=30)
    parser.add_argument("--max-file-bytes", type=int, default=1_000_000)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    """Display a bounded report and leave all source files unchanged."""
    args = parse_args(argv)
    if args.limit < 0:
        raise ValueError("limit must not be negative")
    report = scan_root(args.root, args.max_file_bytes)
    selected = report.findings[:args.limit]
    if args.format == "json":
        print(
            json.dumps(
                {
                    "scanned_files": report.scanned_files,
                    "skipped_files": report.skipped_files,
                    "counts_by_rule": report.counts_by_rule,
                    "total_findings": len(report.findings),
                    "findings": [asdict(item) for item in selected],
                },
                indent=2,
                sort_keys=True,
            )
        )
    else:
        print(f"scanned_files={report.scanned_files}")
        print(f"skipped_files={report.skipped_files}")
        print(f"total_findings={len(report.findings)}")
        for rule, count in report.counts_by_rule.items():
            print(f"{rule}={count}")
        for item in selected:
            print(f"{item.path}:{item.line} {item.rule} {item.detail}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
