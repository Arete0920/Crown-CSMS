from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPORT_JSON = ROOT / "audit-artifacts" / "release-manifest" / "route_catalog.json"
REPORT_MD = ROOT / "audit-artifacts" / "release-manifest" / "route_catalog.md"

PATTERNS = [
    r"api/v1/release-closeout/[^\"]+",
    r"api/v1/reports/[^\"]+",
    r"api/v1/notifications/sms/status/",
    r"api/health/",
    r"api/integrity/",
]


def main() -> None:
    hits = []
    for path in ROOT.rglob("*.py"):
        if ".venv" in path.parts or "node_modules" in path.parts:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in PATTERNS:
            for match in re.findall(pattern, text):
                hits.append({
                    "file": str(path.relative_to(ROOT)),
                    "route": match,
                })

    deduped = []
    seen = set()
    for item in hits:
        key = (item["file"], item["route"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)

    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(deduped, indent=2), encoding="utf-8")

    md = ["# Route Catalog", ""]
    for item in deduped:
        md.append(f"- `{item['route']}` :: `{item['file']}`")
    REPORT_MD.write_text("\n".join(md) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()