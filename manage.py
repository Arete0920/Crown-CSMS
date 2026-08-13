#!/usr/bin/env python
"""Repo-root shim to forward Django commands to backend/manage.py.

This eliminates working-directory assumptions:
- From repo root:  python manage.py migrate
- From anywhere:   python C:/path/to/Crown-CSMS/manage.py migrate

The real Django entrypoint in this repo lives at backend/manage.py.
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

    # Prepend backend/ so `import crown_api.settings` resolves to backend/crown_api
    # (and not the similarly-named repo-root `crown_api/` package).
    sys.path.insert(0, str(backend_dir))

    # Ensure relative paths behave as if launched from repo root.
    os.chdir(str(repo_root))

    # Execute backend/manage.py as __main__ (preserves sys.argv).
    runpy.run_path(str(backend_manage), run_name="__main__")


if __name__ == "__main__":
    main()
