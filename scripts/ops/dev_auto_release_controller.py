#!/usr/bin/env python3
"""Bounded, opt-in, code-only CROWN Azure DEV release coordinator.

No Azure credentials; dispatches only existing manual-only GitHub workflows.
The checked-in release policy defaults to OFF, so this code cannot deploy until
source governance and repository activation are separately authorized.
"""
from __future__ import annotations

import argparse
from contextlib import redirect_stdout
from io import StringIO
import json
import os
import re
import sys
import time
from urllib import error, request

import dev_auto_release_eligibility as eligibility
import verify_dev_owner_runtime as runtime

REPO = "Arete0920/Crown-CSMS"
ROOT = "https://api.github.com/repos/" + REPO
SHA = re.compile(r"[0-9a-f]{40}\Z")
BACKEND = "deploy-dev.yml"
FRONTEND = "deploy-dashboard.yml"
RUN_BASE = ".github/workflows/"
MAX_BYTES = 2_000_000
BACKEND_SECONDS = 35 * 60
FRONTEND_SECONDS = 50 * 60
POLL_SECONDS = 20


class Blocked(RuntimeError):
    """A recorded, fail-closed release decision, not permission to retry."""


class NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class GithubClient:
    def __init__(self, token):
        if not token:
            raise Blocked("github_credential_unavailable")
        self.token = token
        self.opener = request.build_opener(NoRedirect())

    def api(self, method, path, data=None):
        if not path.startswith("/") or ".." in path or "//" in path:
            raise Blocked("untrusted_api_path")
        if method not in ("GET", "POST"):
            raise Blocked("untrusted_api_method")
        if method == "POST" and data is None:
            raise Blocked("missing_dispatch_payload")
        url = ROOT + path
        raw = None if data is None else json.dumps(data, separators=(",", ":")).encode()
        headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": "Bearer " + self.token,
            "X-GitHub-Api-Version": "2026-03-10",
        }
        if raw is not None:
            headers["Content-Type"] = "application/json"
        try:
            req = request.Request(url, data=raw, headers=headers, method=method)
            with self.opener.open(req, timeout=20) as response:
                if response.status != 200 or response.geturl() != url:
                    raise Blocked("github_api_did_not_return_200")
                body = response.read(MAX_BYTES + 1)
                if len(body) > MAX_BYTES:
                    raise Blocked("github_api_response_too_large")
                return json.loads(body)
        except (error.URLError, ValueError, TypeError, OSError) as exc:
            raise Blocked("github_api_unavailable_or_invalid") from exc


def assert_event(expected_sha, environ):
    if not isinstance(expected_sha, str) or not SHA.fullmatch(expected_sha):
        raise Blocked("invalid_exact_source")
    if (environ.get("GITHUB_REPOSITORY") != REPO
            or environ.get("GITHUB_REF") != "refs/heads/main"
            or environ.get("GITHUB_SHA") != expected_sha
            or environ.get("GITHUB_EVENT_NAME") not in ("push", "schedule")
            or environ.get("GITHUB_RUN_ATTEMPT") != "1"):
        raise Blocked("untrusted_auto_release_execution")
    if environ.get("CROWN_AUTO_DEV_CD_ENABLED") != "true":
        raise Blocked("repository_activation_disabled")
    policy = json.loads(eligibility.POLICY.read_text(encoding="utf-8"))
    if (not isinstance(policy, dict) or policy.get("enabled") is not True
            or policy.get("target") != "dev"
            or policy.get("automatic_schema_changes") is not False):
        raise Blocked("source_activation_disabled")


def require_eligible(expected_sha):
    """Use the exact independently tested read-only Stage B GitHub authority."""
    output = StringIO()
    with redirect_stdout(output):
        result = eligibility.main(["--expected-sha", expected_sha])
    try:
        receipt = json.loads(output.getvalue())
    except (ValueError, TypeError):
        raise Blocked("eligibility_receipt_unavailable")
    if (result != 0 or receipt.get("status") != "ELIGIBLE"
            or receipt.get("expected_sha") != expected_sha
            or type(receipt.get("required_checks")) is not int
            or receipt["required_checks"] < 17):
        raise Blocked("source_or_checks_no_longer_eligible")


def observe(expected_sha):
    try:
        report = runtime.probe(expected_sha)
    except (ValueError, OSError):
        raise Blocked("dev_runtime_probe_unavailable")
    if (not isinstance(report, dict)
            or report.get("expected_main_sha") != expected_sha
            or not isinstance(report.get("checks"), dict)):
        raise Blocked("dev_runtime_evidence_invalid")
    return report


def assert_safe_dev(report):
    c = report["checks"]
    must = {"backend_environment": "DEV", "backend_database": "READY",
            "anonymous_overview": "DENIED",
            "anonymous_school_directory": "DENIED",
            "dev_preview_cors": "READY"}
    if report.get("api_health_http_status") != 200 or any(c.get(k) != v for k, v in must.items()):
        raise Blocked("existing_dev_runtime_safety_unverified")


def assert_backend_exact(report):
    c = report["checks"]
    if c.get("backend_build_sha") != "MATCH" or c.get("backend_artifact_sha") != "MATCH":
        raise Blocked("backend_source_not_confirmed")
    assert_safe_dev(report)


def existing_run(client, workflow, expected_sha):
    path = f"/actions/workflows/{workflow}/runs?event=workflow_dispatch&head_sha={expected_sha}&per_page=100"
    result = client.api("GET", path)
    runs = result.get("workflow_runs") if isinstance(result, dict) else None
    total = result.get("total_count") if isinstance(result, dict) else None
    if (type(total) is not int or total > 100 or not isinstance(runs, list)
            or len(runs) != total or any(not isinstance(r, dict) for r in runs)):
        raise Blocked("prior_workflow_run_history_incomplete")
    matching = [r for r in runs if r.get("event") == "workflow_dispatch"
                and r.get("head_sha") == expected_sha
                and r.get("path") == RUN_BASE + workflow]
    if len(matching) > 1:
        raise Blocked("ambiguous_prior_workflow_attempts")
    if len(matching) == 1:
        run = matching[0]
        if (run.get("head_branch") != "main"
                or not isinstance(run.get("repository"), dict)
                or run["repository"].get("full_name") != REPO
                or run.get("run_attempt") != 1):
            raise Blocked("prior_workflow_identity_unverified")
        if run.get("status") != "completed" or run.get("conclusion") != "success":
            raise Blocked("prior_workflow_incomplete_or_failed")
        return run
    return None


def assert_no_concurrent_manual(client, workflow):
    """Do not race an operator's in-flight run on either existing DEV workflow."""
    for status in ("queued", "in_progress", "waiting", "pending", "requested"):
        query = f"/actions/workflows/{workflow}/runs?status={status}&per_page=100"
        payload = client.api("GET", query)
        total = payload.get("total_count") if isinstance(payload, dict) else None
        if type(total) is not int or total > 100:
            raise Blocked("unbounded_active_release_inventory")
        if total > 0:
            raise Blocked("another_dev_workflow_is_active")


def dispatch(client, workflow, sha):
    if workflow == BACKEND:
        inputs = {
            "ref": sha,
            "confirm_dev_reviewed24": "auto-code-only",
            "apply_reviewed_heritage24": "false",
            "apply_finance_setup_0003": "false",
            "synthetic_dev_confirmed": "false",
            "backup_recovery_verified": "false",
            "maintenance_window_confirmed": "false",
        }
    elif workflow == FRONTEND:
        inputs = {
            "dev_certification_preview": "true", "dev_deploy_only": "true",
            "dev_hosted_jireh_preview": "false", "dev_source_sha": sha,
            "deploy_label": "auto-dev-" + sha[:12],
        }
    else:
        raise Blocked("unexpected_workflow_target")
    result = client.api("POST", f"/actions/workflows/{workflow}/dispatches",
                        {"ref": "main", "inputs": inputs, "return_run_details": True})
    run_id = result.get("workflow_run_id") if isinstance(result, dict) else None
    if (type(run_id) is not int or run_id <= 0
            or result.get("run_url") != ROOT + "/actions/runs/" + str(run_id)
            or result.get("html_url") !=
            f"https://github.com/{REPO}/actions/runs/{run_id}"):
        raise Blocked("dispatch_run_id_not_returned_no_retry")
    return run_id


def wait_run(client, workflow, sha, run_id, *, max_seconds, sleep=time.sleep):
    for index in range(max_seconds // POLL_SECONDS + 1):
        run = client.api("GET", f"/actions/runs/{run_id}")
        if (not isinstance(run, dict) or run.get("id") != run_id
                or run.get("path") != RUN_BASE + workflow
                or run.get("head_sha") != sha
                or run.get("head_branch") != "main"
                or run.get("event") != "workflow_dispatch"
                or run.get("run_attempt") != 1
                or not isinstance(run.get("repository"), dict)
                or run["repository"].get("full_name") != REPO):
            raise Blocked("dispatched_run_identity_mismatch")
        if run.get("status") == "completed":
            if run.get("conclusion") != "success":
                raise Blocked("dispatched_workflow_did_not_pass")
            return
        if run.get("status") not in ("queued", "in_progress", "pending", "requested", "waiting"):
            raise Blocked("unknown_dispatched_run_status")
        if index < max_seconds // POLL_SECONDS:
            sleep(POLL_SECONDS)
    raise Blocked("bounded_release_wait_expired")


def run_controller(expected_sha, *, client, eligibility_check=require_eligible,
                   probe=observe, sleep=time.sleep):
    eligibility_check(expected_sha)
    report = probe(expected_sha)
    assert_safe_dev(report)
    if report.get("precheck") == "PASS":
        return "ALREADY_CURRENT"

    backend_exact = (report["checks"].get("backend_build_sha") == "MATCH"
                     and report["checks"].get("backend_artifact_sha") == "MATCH")
    if not backend_exact:
        if existing_run(client, BACKEND, expected_sha):
            raise Blocked("backend_prior_success_but_runtime_not_current")
        assert_no_concurrent_manual(client, BACKEND)
        assert_no_concurrent_manual(client, FRONTEND)
        eligibility_check(expected_sha)
        backend_run = dispatch(client, BACKEND, expected_sha)
        wait_run(client, BACKEND, expected_sha, backend_run,
                 max_seconds=BACKEND_SECONDS, sleep=sleep)
        report = probe(expected_sha)
        assert_backend_exact(report)

    eligibility_check(expected_sha)
    if report.get("precheck") == "PASS":
        return "RELEASED_AND_VERIFIED"
    if report["checks"].get("dev_preview_build_sha") == "MATCH":
        raise Blocked("matching_preview_but_incomplete_parity")
    if existing_run(client, FRONTEND, expected_sha):
        raise Blocked("frontend_prior_success_but_runtime_not_current")
    assert_no_concurrent_manual(client, FRONTEND)
    frontend_run = dispatch(client, FRONTEND, expected_sha)
    wait_run(client, FRONTEND, expected_sha, frontend_run,
             max_seconds=FRONTEND_SECONDS, sleep=sleep)
    final = probe(expected_sha)
    if final.get("precheck") != "PASS":
        raise Blocked("post_release_parity_not_verified")
    eligibility_check(expected_sha)
    return "RELEASED_AND_VERIFIED"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expected-sha", required=True)
    args = parser.parse_args(argv)
    try:
        assert_event(args.expected_sha, os.environ)
        client = GithubClient(os.environ.get("GITHUB_TOKEN"))
        result = run_controller(args.expected_sha, client=client)
        print(json.dumps({"status": result, "source_sha": args.expected_sha}, sort_keys=True))
        return 0
    except (Blocked, OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
        reason = str(exc) if isinstance(exc, Blocked) else "unverified_controller_state"
        print(json.dumps({"status": "BLOCKED", "reason": reason,
                          "source_sha": args.expected_sha}, sort_keys=True))
        return 2


if __name__ == "__main__":
    sys.exit(main())
