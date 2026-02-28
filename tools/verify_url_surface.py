"""
Crown2026 — URL surface collision / shadow detector.

Walks the full Django URL tree and identifies any path strings that are
registered by more than one view. These are "shadow" routes — earlier
entries silently win and the later view is never called.

Exit codes:
  0 — clean (no collisions)
  2 — collisions found (fail CI)
  1 — unexpected error

Usage (from repo root):
  .venv\\Scripts\\python.exe tools\\verify_url_surface.py
"""
from __future__ import annotations

import os
import sys
from collections import defaultdict


def _backend_on_path() -> None:
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    backend_path = os.path.join(repo_root, "backend")
    if backend_path not in sys.path:
        sys.path.insert(0, backend_path)


def _walk(urlpatterns, prefix: str = ""):
    from django.urls import URLPattern, URLResolver  # noqa: PLC0415
    for p in urlpatterns:
        if isinstance(p, URLPattern):
            yield (prefix + str(p.pattern), p.callback)
        elif isinstance(p, URLResolver):
            yield from _walk(p.url_patterns, prefix + str(p.pattern))


def main() -> int:
    _backend_on_path()
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "crown_api.settings")

    import django  # noqa: PLC0415
    django.setup()

    from django.urls import get_resolver  # noqa: PLC0415

    seen: dict[str, list] = defaultdict(list)
    for path, cb in _walk(get_resolver().url_patterns):
        seen[path.strip()].append(cb)

    collisions = {k: v for k, v in seen.items() if len(v) > 1}

    total = sum(len(v) for v in seen.values())
    print(f"Scanned {len(seen)} unique route patterns ({total} total registrations).")

    if collisions:
        print(f"\nFAIL: {len(collisions)} URL collision(s) detected:\n")
        for k, v in sorted(collisions.items()):
            print(f"  {k!r}")
            for cb in v:
                mod = getattr(cb, "__module__", "?")
                name = getattr(cb, "__name__", repr(cb))
                print(f"    - {mod}.{name}")
        return 2

    print("PASS: URL surface has no collisions / shadow duplicates.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
