#!/usr/bin/env python3
from __future__ import annotations

import json
import pathlib
import re
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parents[1]
WF_DIR = ROOT / ".github" / "workflows"

SECRET_REF_RE = re.compile(
    r"\$\{\{\s*secrets(?:\.([A-Za-z0-9_]+)|\[['\"]([A-Za-z0-9_]+)['\"]\])\s*}}"
)
EXPRESSION_REF_RE = re.compile(r"\$\{\{\s*(?:secrets|vars|inputs)\s*(?:\.|\[)")
ENV_ASSIGN_RE = re.compile(r"^\s*([A-Z0-9_]+)\s*:\s*(.+?)\s*$")

PRODUCTION_SECRET_KEYS = {
    "AZURE_CREDENTIALS",
    "AZURE_CREDENTIALS_FOR_LOGIN",
    "AZURE_CLIENT_ID",
    "AZURE_TENANT_ID",
    "AZURE_SUBSCRIPTION_ID",
    "SLACK_WEBHOOK_URL",
    "RC_DEMO_KEY",
    "CI_SMOKE_USERNAME",
    "CI_SMOKE_PASSWORD",
    "DEV_OPS_SECRET",
    "CROWN_OPS_SECRET",
    "OPS_SECRET",
}


def is_placeholder_reference(value: str) -> bool:
    compact = value.strip()
    return (
        bool(EXPRESSION_REF_RE.search(compact))
        or compact == '""'
        or compact == "''"
    )


def find_secret_refs(text: str) -> list[str]:
    refs: set[str] = set()
    for dot_name, bracket_name in SECRET_REF_RE.findall(text):
        name = dot_name or bracket_name
        if name:
            refs.add(name)
    return sorted(refs)


def find_inline_production_secret_values(text: str) -> list[dict]:
    violations: list[dict] = []
    for idx, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        match = ENV_ASSIGN_RE.match(raw_line)
        if not match:
            continue

        key, value = match.group(1), match.group(2)
        if key not in PRODUCTION_SECRET_KEYS:
            continue

        if not is_placeholder_reference(value):
            violations.append({"line": idx, "key": key})

    return violations


def collect(path: pathlib.Path) -> dict:
    text = path.read_text(encoding="utf-8", errors="replace")
    refs = find_secret_refs(text)
    inline_violations = find_inline_production_secret_values(text)
    return {
        "file": str(path.relative_to(ROOT)).replace('\\', '/'),
        "secret_refs": refs,
        "secret_ref_count": len(refs),
        "inline_production_secret_violations": inline_violations,
    }


def main() -> int:
    records = [collect(p) for p in sorted(WF_DIR.glob("*.yml"))]
    secret_to_files: dict[str, list[str]] = {}
    violations: list[dict] = []
    for rec in records:
        for ref in rec["secret_refs"]:
            secret_to_files.setdefault(ref, []).append(rec["file"])
        for violation in rec["inline_production_secret_violations"]:
            violations.append(
                {
                    "file": rec["file"],
                    "line": violation["line"],
                    "key": violation["key"],
                }
            )

    out = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "workflow_count": len(records),
        "unique_secret_refs": sorted(secret_to_files.keys()),
        "secret_reference_map": secret_to_files,
        "production_secret_guardrail_keys": sorted(PRODUCTION_SECRET_KEYS),
        "inline_production_secret_violations": violations,
        "records": records,
    }

    out_file = ROOT / "workflow-secrets-inventory.json"
    out_file.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"Wrote {out_file}")
    if violations:
        print("ERROR: inline production secret values detected in workflows")
        for item in violations:
            print(f"- {item['file']}:{item['line']} key={item['key']} value=<redacted>")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
