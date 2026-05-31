#!/usr/bin/env python3
"""CROWN release hygiene audit guard.

This script performs static checks that should be run before promoting a release
or merging broad sandbox/demo changes. It does not replace runtime proof.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

FAIL = "FAIL"
PASS = "PASS"
WARN = "WARN"


def read(path: str) -> str:
    p = ROOT / path
    if not p.exists():
        return ""
    return p.read_text(encoding="utf-8", errors="replace")


def result(level: str, code: str, message: str, path: str = "") -> dict:
    return {"level": level, "code": code, "message": message, "path": path}


def check_canonical_release_status() -> list[dict]:
    out = []
    status = read("docs/CURRENT_RELEASE_STATUS.md")
    scorecard = read("docs/release/CURRENT_RELEASE_SCORECARD_20260528.md")
    board = read("docs/release/P0_EXECUTION_BOARD_20260528.md")

    if not status:
        return [result(FAIL, "missing_current_release_status", "docs/CURRENT_RELEASE_STATUS.md is missing", "docs/CURRENT_RELEASE_STATUS.md")]

    if "Repository-wide decision: CONDITIONAL GO" in status:
        out.append(result(PASS, "canonical_decision_present", "Canonical release authority states CONDITIONAL GO", "docs/CURRENT_RELEASE_STATUS.md"))
    elif "Repository-wide decision:" in status:
        out.append(result(WARN, "canonical_decision_changed", "Canonical release decision changed; verify scorecard and P0 board match", "docs/CURRENT_RELEASE_STATUS.md"))
    else:
        out.append(result(FAIL, "canonical_decision_missing", "Canonical release decision line missing", "docs/CURRENT_RELEASE_STATUS.md"))

    if scorecard and "Current decision: CONDITIONAL GO" in scorecard and "Repository-wide decision: CONDITIONAL GO" in status:
        out.append(result(PASS, "scorecard_decision_matches", "Scorecard and canonical status both state CONDITIONAL GO", "docs/release/CURRENT_RELEASE_SCORECARD_20260528.md"))
    elif scorecard:
        out.append(result(FAIL, "scorecard_decision_mismatch", "Scorecard decision does not clearly match canonical release authority", "docs/release/CURRENT_RELEASE_SCORECARD_20260528.md"))
    else:
        out.append(result(FAIL, "scorecard_missing", "Current release scorecard is missing", "docs/release/CURRENT_RELEASE_SCORECARD_20260528.md"))

    if "Deploy SHA parity status: PARTIAL" in status and "P0-1" in board and "COMPLETE" in board:
        out.append(result(WARN, "p0_board_parity_conflict", "P0 board appears to mark parity complete while canonical authority says partial", "docs/release/P0_EXECUTION_BOARD_20260528.md"))

    if "Protected-spine runtime/policy gate status: PARTIAL" in status and "P0-3" in board and "COMPLETE" in board:
        out.append(result(WARN, "p0_board_protected_spine_conflict", "P0 board appears to mark protected spine complete while canonical authority says partial", "docs/release/P0_EXECUTION_BOARD_20260528.md"))

    return out


def check_dashboard_registry() -> list[dict]:
    out = []
    text = read("frontend/dashboards/src/config/dashboardRegistry.js")
    if not text:
        return [result(FAIL, "dashboard_registry_missing", "Dashboard registry not found", "frontend/dashboards/src/config/dashboardRegistry.js")]

    dashboard_count = len(re.findall(r"createDashboard\s*\(", text))
    release_state_count = len(re.findall(r"releaseState\s*:", text))
    out.append(result(PASS, "dashboard_registry_present", f"Dashboard registry contains {dashboard_count} dashboard declarations", "frontend/dashboards/src/config/dashboardRegistry.js"))

    if dashboard_count and release_state_count < dashboard_count:
        out.append(result(WARN, "implicit_dashboard_release_state", f"Only {release_state_count}/{dashboard_count} dashboards declare releaseState explicitly; missing values default to ready", "frontend/dashboards/src/config/dashboardRegistry.js"))
    else:
        out.append(result(PASS, "explicit_dashboard_release_state", "All dashboards declare releaseState explicitly", "frontend/dashboards/src/config/dashboardRegistry.js"))
    return out


def check_sandbox_branch_hygiene() -> list[dict]:
    out = []
    views = read("backend/sandbox_demo/views.py")
    settings = read("backend/crown_api/settings.py")
    urls = read("backend/sandbox_demo/urls.py")

    if views:
        required = ["SandboxInviteCreateView", "SandboxInviteResolveView", "SandboxInviteRevokeView", "SandboxFeedbackView", "SandboxEventView", "_validate_invite"]
        missing = [name for name in required if name not in views]
        if missing:
            out.append(result(FAIL, "sandbox_views_incomplete", f"Missing sandbox view handlers: {', '.join(missing)}", "backend/sandbox_demo/views.py"))
        else:
            out.append(result(PASS, "sandbox_views_hardened", "Sandbox invite/session/event/feedback handlers are present", "backend/sandbox_demo/views.py"))
    else:
        out.append(result(WARN, "sandbox_views_absent", "sandbox_demo views not present on this branch", "backend/sandbox_demo/views.py"))

    if "CROWN_SANDBOX_FALLBACK_PASSWORD = os.getenv(\"CROWN_SANDBOX_FALLBACK_PASSWORD\", os.getenv(\"CROWN_PASSWORD\"" in settings:
        out.append(result(FAIL, "sandbox_shared_password_fallback", "Sandbox fallback password inherits CROWN_PASSWORD; use sandbox-only env or unusable passwords", "backend/crown_api/settings.py"))
    elif "CROWN_SANDBOX_FALLBACK_PASSWORD" in settings:
        out.append(result(PASS, "sandbox_password_isolated", "Sandbox fallback password does not inherit shared CROWN_PASSWORD", "backend/crown_api/settings.py"))

    if urls and all(name in urls for name in ["feedback/", "events/", "invites/"]):
        out.append(result(PASS, "sandbox_urls_complete", "Sandbox invite/event/feedback routes are exposed", "backend/sandbox_demo/urls.py"))
    elif urls:
        out.append(result(FAIL, "sandbox_urls_incomplete", "Sandbox URL module lacks invite/event/feedback endpoints", "backend/sandbox_demo/urls.py"))
    return out


def main() -> int:
    findings = []
    findings.extend(check_canonical_release_status())
    findings.extend(check_dashboard_registry())
    findings.extend(check_sandbox_branch_hygiene())

    fail_count = sum(1 for item in findings if item["level"] == FAIL)
    warn_count = sum(1 for item in findings if item["level"] == WARN)
    pass_count = sum(1 for item in findings if item["level"] == PASS)

    print(json.dumps({"pass": pass_count, "warn": warn_count, "fail": fail_count, "findings": findings}, indent=2))
    return 1 if fail_count else 0


if __name__ == "__main__":
    raise SystemExit(main())
