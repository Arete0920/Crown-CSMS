# tools/verify_backend_gate.py
# Phase 5 Backend Gate (static/runtime checks)
# Enforces:
# 1) Python bytecode compile of backend/ (compileall)
# 2) Django system checks (manage.py check)
# 3) Migration drift check (makemigrations --check --dry-run)
# 4) Tenant tripwire: all get_object_or_404(Section, ...) calls include school_id= (AST, multi-line-safe)
# 5) Tenant tripwire: get_request_school_id(..., required=False) only in approved files (AST)
#
# Designed to be deterministic in CI by setting safe env defaults.
# No DB connection required for these checks.
#
# Usage:
#   python tools/verify_backend_gate.py                  # run all checks
#   python tools/verify_backend_gate.py --tenant-checks-only  # run only checks 4+5

import ast
import os
import sys
import subprocess
from pathlib import Path

def run(cmd: list[str], cwd: Path, env: dict[str, str]) -> None:
    print(f"\n$ {' '.join(cmd)}")
    p = subprocess.run(cmd, cwd=str(cwd), env=env)
    if p.returncode != 0:
        raise SystemExit(p.returncode)

def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    backend = repo_root / "backend"
    manage_py = backend / "manage.py"

    if not backend.exists():
        print("Backend Gate FAILED: missing backend/ directory")
        return 1
    if not manage_py.exists():
        print("Backend Gate FAILED: missing backend/manage.py")
        return 1

    env = os.environ.copy()

    # Deterministic CI defaults (safe for check/compile/migrations)
    env.setdefault("DJANGO_SETTINGS_MODULE", "crown_api.settings")
    env.setdefault("SECRET_KEY", "ci-not-secret")
    env.setdefault("DEBUG", "0")
    env.setdefault("ALLOWED_HOSTS", "localhost,127.0.0.1")
    # If the project uses dj-database-url, this prevents accidental external DB dependency.
    env.setdefault("DATABASE_URL", "sqlite:///./ci.sqlite3")

    py = sys.executable

    # 1) Compile all Python under backend/
    run([py, "-m", "compileall", "-q", "backend"], cwd=repo_root, env=env)

    # 2) Django system checks (non-deploy; keep deterministic)
    run([py, "manage.py", "check"], cwd=backend, env=env)

    # 3) Migration drift check (fails if model changes not captured in migrations)
    run([py, "manage.py", "makemigrations", "--check", "--dry-run"], cwd=backend, env=env)

    # 4+5) Tenant tripwires (AST, multi-line-safe)
    if run_tenant_checks(backend) != 0:
        raise SystemExit(1)

    print("\nBackend Gate PASSED")
    return 0


# ---------------------------------------------------------------------------
# Tenant tripwires — AST-based, multi-line-safe
# ---------------------------------------------------------------------------

def _is_name(node: ast.expr, name: str) -> bool:
    return isinstance(node, ast.Name) and node.id == name


def _call_func_name(node: ast.Call) -> str:
    """Return a best-effort string name for a Call node's function."""
    if isinstance(node.func, ast.Name):
        return node.func.id
    if isinstance(node.func, ast.Attribute):
        return node.func.attr
    return ""


def _kwarg_names(node: ast.Call) -> set[str]:
    return {kw.arg for kw in node.keywords if kw.arg is not None}


def _kwarg_value_is_false(node: ast.Call, kwarg: str) -> bool:
    for kw in node.keywords:
        if kw.arg == kwarg:
            return isinstance(kw.value, ast.Constant) and kw.value.value is False
    return False


def check_tenant_tripwires(backend: Path) -> list[str]:
    """
    Check 4: Every get_object_or_404(Section, ...) call must include school_id= keyword.
    Check 5: get_request_school_id(..., required=False) must only appear in approved files.

    Returns a list of violation strings (empty = pass).
    """
    # Files where required=False is explicitly approved
    ALLOWED_REQUIRED_FALSE = {
        "households/scoping.py",
        "crown_api/tenant_guards.py",
    }

    violations: list[str] = []

    for py_file in sorted(backend.rglob("*.py")):
        try:
            source = py_file.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(py_file))
        except SyntaxError:
            # compileall (check 1) will have already caught this
            continue

        rel = py_file.relative_to(backend)
        rel_str = rel.as_posix()

        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue

            name = _call_func_name(node)

            # Check 4: get_object_or_404(Section, ...) must have school_id=
            if name == "get_object_or_404" and node.args:
                first_arg = node.args[0]
                if _is_name(first_arg, "Section"):
                    if "school_id" not in _kwarg_names(node):
                        violations.append(
                            f"  [check 4] {rel_str}:{node.lineno}: "
                            f"get_object_or_404(Section, ...) missing school_id= — "
                            f"cross-tenant Section fetch"
                        )

            # Check 5: get_request_school_id(..., required=False) only in approved files
            if name == "get_request_school_id":
                if _kwarg_value_is_false(node, "required"):
                    # Normalise path separators for comparison
                    norm = rel_str.replace("\\", "/")
                    if not any(norm.endswith(allowed) for allowed in ALLOWED_REQUIRED_FALSE):
                        violations.append(
                            f"  [check 5] {rel_str}:{node.lineno}: "
                            f"get_request_school_id(required=False) outside approved files — "
                            f"tenant bypass risk"
                        )

    return violations


def run_tenant_checks(backend: Path) -> int:
    print("\n$ tenant tripwires (AST structural check)")
    violations = check_tenant_tripwires(backend)
    if violations:
        print("FAIL: Tenant tripwire violations found:")
        for v in violations:
            print(v)
        return 1
    print("PASS: Tenant tripwires — no violations (Section scoped, no rogue required=False)")
    return 0


if __name__ == "__main__":
    if "--tenant-checks-only" in sys.argv:
        repo_root = Path(__file__).resolve().parents[1]
        raise SystemExit(run_tenant_checks(repo_root / "backend"))
    raise SystemExit(main())
