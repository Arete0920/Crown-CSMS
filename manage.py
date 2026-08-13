#!/usr/bin/env python
"""Repo-root shim to forward Django commands to backend/manage.py.

This eliminates working-directory assumptions:
- From the repository root: python manage.py migrate
- From anywhere: python C:/path/to/Crown-CSMS/manage.py migrate

The Django entry point lives at backend/manage.py.
"""

from __future__ import annotations

import os
import runpy
import sys
from pathlib import Path


def main() -> None:
    repo_root = Path(__file__).resolve().parent
    backend_manage = repo_root / "backend" / "manage.py"
    backend_dir = repo_root / "backend"

    if not backend_manage.exists():
        raise SystemExit(f"ERROR: expected backend/manage.py at: {backend_manage}")

    sys.path.insert(0, str(backend_dir))
    os.chdir(str(repo_root))
    runpy.run_path(str(backend_manage), run_name="__main__")


if __name__ == "__main__":
    main()
