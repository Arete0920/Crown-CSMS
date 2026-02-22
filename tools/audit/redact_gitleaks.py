#!/usr/bin/env python3
"""
redact_gitleaks.py

Reads gitleaks JSON from stdin and writes a safe, metadata-only report to stdout.
Never prints secret values, match strings, or raw line content.

Expected gitleaks formats:
- JSON array of findings (typical with `--report-format json`)
- Or an object with a key holding findings (we handle common patterns)
"""

import json
import sys
from typing import Any, Dict, List


def _as_findings(data: Any) -> List[Dict[str, Any]]:
    if isinstance(data, list):
        return [x for x in data if isinstance(x, dict)]
    if isinstance(data, dict):
        for key in ("findings", "Leaks", "leaks", "results", "Results"):
            v = data.get(key)
            if isinstance(v, list):
                return [x for x in v if isinstance(x, dict)]
        return []
    return []


def main() -> int:
    raw = sys.stdin.read().strip()
    if not raw:
        print("0 findings (empty gitleaks input)")
        return 0

    try:
        data = json.loads(raw)
    except Exception as e:
        print(f"gitleaks-json-parse-failed: {type(e).__name__}: {e}")
        return 2

    findings = _as_findings(data)

    out = []
    for f in findings:
        file   = f.get("File")      or f.get("file")      or f.get("Path")      or f.get("path")      or "?"
        line   = f.get("Line")      or f.get("line")      or f.get("StartLine") or f.get("startLine") or "?"
        rule   = f.get("RuleID")    or f.get("ruleID")    or f.get("Rule")      or f.get("rule")      or "?"
        commit = f.get("Commit")    or f.get("commit")    or ""
        # NEVER include: f.get("Match"), f.get("Secret"), f.get("LineContent"), etc.
        meta = {"file": file, "line": line, "rule": rule}
        if commit:
            meta["commit"] = commit
        out.append(meta)

    if not out:
        print("0 findings")
        return 0

    print(f"{len(out)} findings (metadata only)")
    for m in out:
        c = f" commit={m['commit']}" if "commit" in m else ""
        print(f"- {m['file']}:{m['line']} rule={m['rule']}{c}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
