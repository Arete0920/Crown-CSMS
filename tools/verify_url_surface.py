"""
CROWN URL resolver manifest and collision detector.

This tool walks Django's effective resolver tree in declaration order. It records
full mounted patterns, route names, namespaces, callbacks, and precedence. It
also retains the existing exact-pattern collision gate.

Exit codes:
  0 - clean (no exact duplicate registrations)
  2 - collisions found
  1 - unexpected error

Usage (from repo root):
  python tools/verify_url_surface.py
  python tools/verify_url_surface.py --json-out resolver-manifest.json
  python tools/verify_url_surface.py --probe /api/v1/academics/sections/<uuid>/roster/
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import defaultdict
from pathlib import Path
from typing import Iterable


def _backend_on_path() -> None:
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    backend_path = os.path.join(repo_root, "backend")
    if backend_path not in sys.path:
        sys.path.insert(0, backend_path)


def _setup_django() -> None:
    _backend_on_path()
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "crown_api.settings")

    import django  # noqa: PLC0415

    django.setup()


def _callback_identity(callback) -> tuple[str, str]:
    view_class = getattr(callback, "cls", None) or getattr(callback, "view_class", None)
    target = view_class or callback
    module = getattr(target, "__module__", "?")
    qualname = getattr(target, "__qualname__", None) or getattr(
        target, "__name__", repr(target)
    )
    return module, qualname


def _walk(
    urlpatterns,
    *,
    prefix: str = "",
    namespaces: tuple[str, ...] = (),
    order_start: int = 0,
):
    from django.urls import URLPattern, URLResolver  # noqa: PLC0415

    order = order_start
    for pattern in urlpatterns:
        mounted_pattern = prefix + str(pattern.pattern)
        if isinstance(pattern, URLPattern):
            module, qualname = _callback_identity(pattern.callback)
            full_name_parts = (*namespaces, pattern.name) if pattern.name else namespaces
            yield {
                "order": order,
                "pattern": mounted_pattern,
                "name": pattern.name,
                "namespace": ":".join(namespaces) or None,
                "qualified_name": ":".join(full_name_parts) or None,
                "callback_module": module,
                "callback_name": qualname,
                "callback": f"{module}.{qualname}",
            }
            order += 1
        elif isinstance(pattern, URLResolver):
            child_namespaces = namespaces
            if pattern.namespace:
                child_namespaces = (*namespaces, pattern.namespace)
            child_records = list(
                _walk(
                    pattern.url_patterns,
                    prefix=mounted_pattern,
                    namespaces=child_namespaces,
                    order_start=order,
                )
            )
            yield from child_records
            order += len(child_records)


def build_manifest() -> dict:
    _setup_django()
    from django.urls import get_resolver  # noqa: PLC0415

    records = list(_walk(get_resolver().url_patterns))
    return {
        "schema_version": 1,
        "mode": "read_only_django_resolver_manifest",
        "record_count": len(records),
        "records": records,
    }


def exact_collisions(records: Iterable[dict]) -> dict[str, list[dict]]:
    seen: dict[str, list[dict]] = defaultdict(list)
    for record in records:
        seen[record["pattern"].strip()].append(record)
    return {pattern: rows for pattern, rows in seen.items() if len(rows) > 1}


def resolve_probe(path: str) -> dict:
    _setup_django()
    from django.urls import resolve  # noqa: PLC0415

    match = resolve(path)
    module, qualname = _callback_identity(match.func)
    return {
        "path": path,
        "route": match.route,
        "url_name": match.url_name,
        "view_name": match.view_name,
        "namespaces": list(match.namespaces),
        "callback_module": module,
        "callback_name": qualname,
        "callback": f"{module}.{qualname}",
        "kwargs": {key: str(value) for key, value in sorted(match.kwargs.items())},
    }


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--json-out",
        type=Path,
        help="Write the deterministic resolver manifest and optional probes to JSON.",
    )
    parser.add_argument(
        "--probe",
        action="append",
        default=[],
        help="Resolve an exact concrete path and include the winning callback.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    manifest = build_manifest()
    collisions = exact_collisions(manifest["records"])
    probes = [resolve_probe(path) for path in args.probe]

    output = {
        **manifest,
        "exact_collision_count": len(collisions),
        "exact_collisions": collisions,
        "probes": probes,
    }

    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(
            json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )

    print(
        f"Scanned {manifest['record_count']} effective route registrations "
        "in resolver precedence order."
    )
    for probe in probes:
        print(
            f"PROBE {probe['path']} -> {probe['callback']} "
            f"(name={probe['view_name']!r}, route={probe['route']!r})"
        )

    if collisions:
        print(f"\nFAIL: {len(collisions)} exact URL collision(s) detected:\n")
        for pattern, rows in sorted(collisions.items()):
            print(f"  {pattern!r}")
            for row in rows:
                print(
                    f"    - order={row['order']} callback={row['callback']} "
                    f"name={row['qualified_name']!r}"
                )
        return 2

    print("PASS: URL surface has no exact duplicate registrations.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
