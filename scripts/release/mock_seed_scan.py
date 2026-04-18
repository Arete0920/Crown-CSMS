from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TARGET_DIRS = [ROOT / "backend", ROOT / "frontend", ROOT / "docs"]
TOKENS = [
    "mock",
    "seed-backed",
    "seed backed",
    "placeholder",
    "todo live data",
    "fake data",
    "stub",
]


def main() -> None:
    hits: list[dict] = []
    for base in TARGET_DIRS:
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if not path.is_file():
                continue
            if path.suffix.lower() not in {".py", ".ts", ".tsx", ".js", ".jsx", ".md", ".json"}:
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            lowered = text.lower()
            for token in TOKENS:
                if token in lowered:
                    hits.append({"file": str(path.relative_to(ROOT)), "token": token})
                    break

    out_dir = ROOT / "audit-artifacts" / "release-verify"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "mock_seed_scan.json").write_text(json.dumps(hits, indent=2), encoding="utf-8")
    md = ["# Mock/Seed Scan", "", f"Hit count: {len(hits)}", ""]
    for hit in hits:
        md.append(f"- {hit['file']} :: {hit['token']}")
    (out_dir / "mock_seed_scan.md").write_text("\n".join(md) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()