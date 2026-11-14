#!/usr/bin/env python3
"""Fail-closed, read-only eligibility proof for future CROWN automatic DEV delivery.

No Azure connection, deployment dispatch, database operation, or credential write.
Intended to run before any credential-bearing deployment job. Not wired to CI yet.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import sys
import urllib.error
import urllib.request

REPO = "Arete0920/Crown-CSMS"
BRANCH = "refs/heads/main"
SHA = re.compile(r"[0-9a-f]{40}\Z")
GITHUB_ACTIONS_APP_ID = 15368
BASELINE = frozenset((
    "Analyze (javascript-typescript)", "Analyze (python)",
    "Release authority gates", "contract-gate", "backend-gate",
    "backend-pip-audit", "gitleaks", "dashboards-build-gate",
    "dependency-review", "frontend-npm-audit", "schema-governance",
    "pytest-gate", "release-verify", "repository-policy",
    "wallet-npm-audit", "test", "pytest-internal",
))
POLICY = Path(__file__).with_name("dev_auto_release_policy.json")
MAX_RESPONSE_BYTES = 2_000_000


def assess(*, expected_sha, event_name, ref, repository, source_policy,
           repository_opt_in, branch_data, check_data):
    """Pure decision; every missing, stale or ambiguous signal BLOCKS."""
    def blocked(reason):
        return {"status": "BLOCKED", "reason": reason,
                "expected_sha": expected_sha if isinstance(expected_sha, str) else None}

    if not isinstance(expected_sha, str) or not SHA.fullmatch(expected_sha):
        return blocked("invalid_source_sha")
    if repository != REPO or ref != BRANCH or event_name not in ("push", "schedule"):
        return blocked("untrusted_event_or_repository")
    if (not isinstance(source_policy, dict)
            or set(source_policy) != {"schema_version", "enabled", "target", "automatic_schema_changes"}
            or source_policy["schema_version"] != 1
            or source_policy["enabled"] is not True
            or source_policy["target"] != "dev"
            or source_policy["automatic_schema_changes"] is not False
            or repository_opt_in is not True):
        return blocked("auto_delivery_not_authorized")

    if not isinstance(branch_data, dict) or branch_data.get("protected") is not True:
        return blocked("main_not_protected")
    if (not isinstance(branch_data.get("commit"), dict)
            or branch_data["commit"].get("sha") != expected_sha):
        return blocked("main_moved_or_identity_unknown")

    protection = branch_data.get("protection")
    required = protection.get("required_status_checks") if isinstance(protection, dict) else None
    if not isinstance(required, dict) or required.get("enforcement_level") != "everyone":
        return blocked("required_check_enforcement_unverified")
    names = required.get("contexts")
    bound = required.get("checks")
    if (not isinstance(names, list) or not names
            or any(not isinstance(n, str) or not n for n in names)
            or len(names) != len(set(names))
            or not BASELINE.issubset(names)
            or not isinstance(bound, list)):
        return blocked("required_contexts_missing_or_weakened")
    binding = {}
    for item in bound:
        if (not isinstance(item, dict) or not isinstance(item.get("context"), str)
                or type(item.get("app_id")) is not int):
            return blocked("required_check_app_binding_invalid")
        binding[item["context"]] = item["app_id"]
    if (set(binding) != set(names)
            or any(binding[n] != GITHUB_ACTIONS_APP_ID for n in names)):
        return blocked("required_check_app_binding_changed")

    if not isinstance(check_data, dict):
        return blocked("check_run_response_invalid")
    runs = check_data.get("check_runs")
    total = check_data.get("total_count")
    if (type(total) is not int or not isinstance(runs, list)
            or total < len(names) or total > 100 or len(runs) != total):
        return blocked("check_run_list_incomplete")
    latest = {}
    for item in runs:
        if not isinstance(item, dict):
            return blocked("check_run_record_invalid")
        name, ident = item.get("name"), item.get("id")
        if not isinstance(name, str) or type(ident) is not int or ident <= 0:
            return blocked("check_run_record_invalid")
        if item.get("head_sha") != expected_sha:
            return blocked("foreign_check_run_source")
        if name in names and (name not in latest or ident > latest[name]["id"]):
            latest[name] = item

    if set(names) - set(latest):
        return blocked("required_checks_missing")
    for name in names:
        item = latest[name]
        app = item.get("app")
        if (not isinstance(app, dict) or app.get("id") != binding[name]
                or item.get("status") != "completed"
                or item.get("conclusion") != "success"):
            return blocked("required_checks_not_green")
    return {"status": "ELIGIBLE", "reason": "protected_source_and_checks_green",
            "expected_sha": expected_sha, "required_checks": len(names)}


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, message, headers, newurl):
        return None


def github_json(url, token):
    """GitHub-only fixed endpoints. Never log the token or untrusted response."""
    opener = urllib.request.build_opener(NoRedirect())
    req = urllib.request.Request(url, headers={
        "Authorization": "Bearer " + token,
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    })
    with opener.open(req, timeout=15) as response:
        if response.status != 200 or response.geturl() != url:
            raise ValueError("unexpected_github_api_response")
        raw = response.read(MAX_RESPONSE_BYTES + 1)
        if len(raw) > MAX_RESPONSE_BYTES:
            raise ValueError("github_api_response_too_large")
        return json.loads(raw)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expected-sha", required=True)
    args = parser.parse_args(argv)
    report = {"status": "BLOCKED", "reason": "external_evidence_unavailable",
              "expected_sha": args.expected_sha}
    try:
        policy = json.loads(POLICY.read_text(encoding="utf-8"))
        token = os.environ.get("GITHUB_TOKEN", "")
        repository_opt_in = os.environ.get("CROWN_AUTO_DEV_CD_ENABLED") == "true"
        if (policy.get("enabled") is True and repository_opt_in and token
                and os.environ.get("GITHUB_REPOSITORY") == REPO):
            base = "https://api.github.com/repos/" + REPO
            branch = github_json(base + "/branches/main", token)
            checks = github_json(
                base + "/commits/" + args.expected_sha + "/check-runs?per_page=100",
                token,
            )
            report = assess(
                expected_sha=args.expected_sha,
                event_name=os.environ.get("GITHUB_EVENT_NAME"),
                ref=os.environ.get("GITHUB_REF"),
                repository=os.environ.get("GITHUB_REPOSITORY"),
                source_policy=policy,
                repository_opt_in=True,
                branch_data=branch,
                check_data=checks,
            )
        else:
            report["reason"] = "auto_delivery_not_authorized"
    except (ValueError, OSError, TypeError, KeyError, json.JSONDecodeError,
            urllib.error.URLError):
        report["reason"] = "external_evidence_unavailable"
    print(json.dumps(report, sort_keys=True))
    return 0 if report["status"] == "ELIGIBLE" else 2


if __name__ == "__main__":
    sys.exit(main())
