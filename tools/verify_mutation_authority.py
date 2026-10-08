#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
WRITE_METHODS = {"post", "put", "patch", "delete"}


def _is_is_authenticated(node: ast.AST) -> bool:
    if isinstance(node, ast.Name):
        return node.id == "IsAuthenticated"
    if isinstance(node, ast.Attribute):
        return (
            node.attr == "IsAuthenticated"
            and isinstance(node.value, ast.Name)
            and node.value.id in {"permissions", "drf_permissions"}
        )
    return False


def _class_has_auth_only_permissions(node: ast.ClassDef) -> bool:
    for stmt in node.body:
        if not isinstance(stmt, ast.Assign):
            continue
        if not any(isinstance(t, ast.Name) and t.id == "permission_classes" for t in stmt.targets):
            continue
        value = stmt.value
        return (
            isinstance(value, (ast.List, ast.Tuple))
            and len(value.elts) == 1
            and _is_is_authenticated(value.elts[0])
        )
    return False


def _find_auth_only_mutations(source: str, path: str) -> set[str]:
    try:
        tree = ast.parse(source, filename=path)
    except SyntaxError:
        return set()

    findings: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef) or not _class_has_auth_only_permissions(node):
            continue
        methods = {
            child.name
            for child in node.body
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
            and child.name in WRITE_METHODS
        }
        if methods:
            findings.add(f"{path}:{node.name}:{','.join(sorted(methods))}")
    return findings


def _current_python_files() -> list[pathlib.Path]:
    return sorted((ROOT / "backend").rglob("*.py"))


def _base_python_paths(base_ref: str) -> list[str]:
    proc = subprocess.run(
        ["git", "ls-tree", "-r", "--name-only", base_ref, "--", "backend"],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    return sorted(
        line.strip()
        for line in proc.stdout.splitlines()
        if line.strip().endswith(".py")
    )


def _git_show(base_ref: str, path: str) -> str | None:
    proc = subprocess.run(
        ["git", "show", f"{base_ref}:{path}"],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    if proc.returncode != 0:
        return None
    return proc.stdout


def _scan_current() -> set[str]:
    findings: set[str] = set()
    for path in _current_python_files():
        rel = path.relative_to(ROOT).as_posix()
        findings |= _find_auth_only_mutations(
            path.read_text(encoding="utf-8", errors="replace"), rel
        )
    return findings


def _scan_base(base_ref: str) -> set[str]:
    findings: set[str] = set()
    for rel in _base_python_paths(base_ref):
        source = _git_show(base_ref, rel)
        if source is not None:
            findings |= _find_auth_only_mutations(source, rel)
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Reject newly introduced DRF mutation classes protected only by IsAuthenticated."
    )
    parser.add_argument(
        "--base-ref",
        required=True,
        help="Base commit/ref used to distinguish historical inventory from newly introduced debt.",
    )
    args = parser.parse_args()

    current = _scan_current()
    base = _scan_base(args.base_ref)
    introduced = sorted(current - base)

    if introduced:
        print("Mutation authority policy FAILED: new authentication-only mutation surfaces detected.")
        print("Tenant scope and successful authentication are not mutation authority.")
        for finding in introduced:
            print(f" - {finding}")
        print(
            "Use an explicit role/action/object permission, or implement and test an intentional "
            "self-service ownership boundary before merging."
        )
        return 1

    removed = sorted(base - current)
    print(
        f"Mutation authority policy PASSED: {len(current)} historical auth-only mutation "
        "surface(s) remain; no new surface was introduced."
    )
    if removed:
        print(f"This change removed or hardened {len(removed)} historical surface(s).")
        for finding in removed:
            print(f" - hardened: {finding}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
