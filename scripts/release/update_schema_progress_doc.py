from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SUMMARY = ROOT / "audit-artifacts" / "release-verify" / "schema_w002_summary.json"
DOC = ROOT / "docs" / "release" / "SCHEMA_W002_PROGRESS.md"


def main() -> None:
    payload = json.loads(SUMMARY.read_text(encoding="utf-8"))

    lines = [
        "# OPENAPI SCHEMA ERROR PROGRESS",
        "",
        f"- Metric: {payload['metric']}",
        f"- Unique schema errors: {payload['unique_schema_errors']}",
        f"- Total schema errors: {payload['total_schema_errors']}",
        f"- Unique schema warnings: {payload['unique_schema_warnings']}",
        f"- Budget Current Max: {payload['budget_current_max']}",
        f"- Budget Pass: {payload['budget_pass']}",
        f"- Next Target: {payload['budget_next_target']}",
        f"- Production Ready: {payload['production_ready']}",
        "",
        "Production readiness requires zero schema-generation errors. The ratchet may only move downward.",
        "",
        "## Top Offenders",
        "",
        "| File | Unique Error Count |",
        "|---|---:|",
    ]
    for item in payload.get("top_files", [])[:25]:
        lines.append(f"| `{item['file']}` | {item['count']} |")

    DOC.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
