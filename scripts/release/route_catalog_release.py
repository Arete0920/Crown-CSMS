from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT_JSON = ROOT / "audit-artifacts" / "release-manifest" / "release_route_catalog.json"
OUT_MD = ROOT / "audit-artifacts" / "release-manifest" / "release_route_catalog.md"

ROUTES = [
    r"api/v1/release-closeout/[^\"]+",
    r"api/v1/reports/[^\"]+",
    r"api/schema/",
    r"api/docs/",
]


def main() -> None:
    hits = []
    for path in ROOT.rglob("*.py"):
        if ".venv" in path.parts or "node_modules" in path.parts:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in ROUTES:
            for match in re.findall(pattern, text):
                hits.append({
                    "file": str(path.relative_to(ROOT)).replace("\\", "/"),
                    "route": match,
                })

    dedup = []
    seen = set()
    for item in hits:
        key = (item["file"], item["route"])
        if key in seen:
            continue
        seen.add(key)
        dedup.append(item)

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(dedup, indent=2), encoding="utf-8")

    md = ["# Release Route Catalog", ""]
    for item in dedup:
        md.append(f"- `{item['route']}` :: `{item['file']}`")
    OUT_MD.write_text("\n".join(md) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()