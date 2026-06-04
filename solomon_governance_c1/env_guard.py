#!/usr/bin/env python3
"""Environment guard: validate repo state before governance operations.

Purpose:
    Prevent silent environment drift by validating:
    - Repository root location
    - Required directory structure
    - Git branch state
    - Python environment

Fail-fast principle:
    If ANY validation fails, exit with error before proceeding.
    This prevents governance operations in wrong environments.
"""

from __future__ import annotations

import importlib
import subprocess
import sys
from pathlib import Path


def run_cmd(args: list[str], cwd: Path | None = None) -> tuple[int, str, str]:
    """Run command and return exit code, stdout, stderr."""
    proc = subprocess.run(
        args,
        cwd=cwd or Path.cwd(),
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()


def find_repo_root() -> Path | None:
    """Find Crown2026 repository root by walking up directory tree."""
    current = Path.cwd()
    while current != current.parent:
        if (current / ".git").exists() and (current / "README.md").exists():
            git_remote_output = subprocess.run(
                ["git", "remote", "-v"],
                cwd=current,
                capture_output=True,
                text=True,
                encoding="utf-8",
            ).stdout
            if "Crown2026" in git_remote_output or "tcmegahan" in git_remote_output:
                return current
        current = current.parent
    return None


def validate_repo_root() -> Path:
    """Validate we are in Crown2026 repository root."""
    root = find_repo_root()
    if not root:
        print("FAILED: Crown2026 repository root not found")
        print("This script must be run from within the Crown2026 repository")
        sys.exit(1)

    return root


def validate_required_directories(root: Path) -> None:
    """Validate required directories exist."""
    required_dirs = [
        "solomon_governance_c1",
        "solomon_governance_c1/governance/c1/runtime/audit_pack",
        ".github/workflows",
        "backend",
        "frontend",
    ]

    missing = []
    for dir_name in required_dirs:
        dir_path = root / dir_name
        if not dir_path.exists() or not dir_path.is_dir():
            missing.append(dir_name)

    if missing:
        print("FAILED: Required directories not found:")
        for dir_name in missing:
            print(f"  - {root / dir_name}")
        sys.exit(1)


def validate_git_state(root: Path) -> None:
    """Validate git repository state."""
    # Check if we're in a valid git repo
    rc, _, _ = run_cmd(["git", "rev-parse", "--git-dir"], cwd=root)
    if rc != 0:
        print("FAILED: Not a valid git repository")
        sys.exit(1)

    # Get current branch
    rc_branch, branch, _ = run_cmd(["git", "branch", "--show-current"], cwd=root)
    if rc_branch != 0 or not branch:
        print("FAILED: Cannot determine git branch")
        sys.exit(1)

    # Get current commit
    rc_head, head, _ = run_cmd(["git", "rev-parse", "HEAD"], cwd=root)
    if rc_head != 0 or not head:
        print("FAILED: Cannot determine git HEAD")
        sys.exit(1)

    # Ensure we're on solomon/start or main
    if branch not in ["solomon/start", "main", "master"]:
        print(f"WARN: Current branch '{branch}' is not standard (solomon/start, main, master)")
        # Don't exit - warn but continue

    return branch, head


def validate_python_environment() -> None:
    """Validate Python version and basic imports."""
    if sys.version_info < (3, 10):
        print(f"FAILED: Python 3.10+ required (found {sys.version_info.major}.{sys.version_info.minor})")
        sys.exit(1)

    # Try importing required stdlib modules
    required_modules = ["json", "subprocess", "pathlib", "hashlib", "argparse"]
    for module_name in required_modules:
        try:
            importlib.import_module(module_name)
        except ImportError:
            print(f"FAILED: Required Python module not available: {module_name}")
            sys.exit(1)


def validate_environment() -> dict[str, str | Path]:
    """Run all validations and return environment context."""
    # Validate repo root
    root = validate_repo_root()

    # Validate directories
    validate_required_directories(root)

    # Validate git state
    branch, head = validate_git_state(root)

    # Validate Python
    validate_python_environment()

    # Return context for scripts
    return {
        "root": root,
        "branch": branch,
        "head": head,
        "solomon_dir": root / "solomon_governance_c1",
        "runtime_pack": root / "solomon_governance_c1" / "governance" / "c1" / "runtime" / "audit_pack",
    }


def guard(func):
    """Decorator to add environment validation to a function."""
    def wrapper(*args, **kwargs):
        env = validate_environment()
        return func(env, *args, **kwargs)
    return wrapper


if __name__ == "__main__":
    print("Validating environment...")
    env = validate_environment()
    print("✓ Environment valid")
    print(f"  Repository: {env['root']}")
    print(f"  Branch: {env['branch']}")
    print(f"  HEAD: {env['head'][:12]}...")
