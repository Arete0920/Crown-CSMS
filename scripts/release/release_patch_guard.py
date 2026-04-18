from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "audit-artifacts" / "release-verify" / "release_patch_guard.json"

SETTINGS_BLOCKS = [
    "INSTALLED_APPS += ['drf_spectacular', 'drf_spectacular_sidecar']",
    "REST_FRAMEWORK = globals().get('REST_FRAMEWORK', {})",
    "REST_FRAMEWORK['DEFAULT_SCHEMA_CLASS'] = 'drf_spectacular.openapi.AutoSchema'",
    "'TITLE': 'Crown API'",
    "if \"release_closeout\" not in INSTALLED_APPS:",
    "INSTALLED_APPS.append(\"release_closeout\")",
]

URL_BLOCKS = [
    "from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView",
    "path('api/schema/', SpectacularAPIView.as_view(), name='api-schema')",
    "path('api/docs/', SpectacularSwaggerView.as_view(url_name='api-schema'), name='api-docs')",
    "path(\"\", include(\"release_closeout.urls\"))",
]


def dedupe_lines(text: str, patterns: list[str]) -> tuple[str, int]:
    lines = text.splitlines()
    seen = set()
    out = []
    removed = 0
    for line in lines:
        stripped = line.strip()
        matched = next((p for p in patterns if stripped == p.strip()), None)
        if matched:
            if matched in seen:
                removed += 1
                continue
            seen.add(matched)
        out.append(line)
    return "\n".join(out).rstrip() + "\n", removed


def main() -> None:
    results = []
    files = []
    files.extend(ROOT.rglob("settings.py"))
    files.extend(ROOT.rglob("urls.py"))

    for path in files:
        if ".venv" in path.parts or "node_modules" in path.parts:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        patterns = SETTINGS_BLOCKS if path.name == "settings.py" else URL_BLOCKS
        new_text, removed = dedupe_lines(text, patterns)
        if new_text != text:
            path.write_text(new_text, encoding="utf-8")
        results.append({
            "file": str(path.relative_to(ROOT)),
            "removed_duplicate_lines": removed,
            "changed": new_text != text,
        })

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(results, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()