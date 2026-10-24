#!/usr/bin/env python3
"""Read-only Azure DEV owner-console prerequisite probe, not release certification.

All network targets are pinned to existing CROWN DEV hosts. No credentials,
state-changing requests, Azure administration, school provisioning, or source
commits are performed. Raw HTTP bodies and headers are never written to logs.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import re
import sys
import urllib.error
import urllib.request


API = "https://crown-api-dev.azurewebsites.net"
PREVIEW = "https://yellow-forest-0eecc8b0f-devcertification.eastus2.7.azurestaticapps.net"
FULL_SHA = re.compile(r"[0-9a-f]{40}\Z")
MAX_BYTES = 8192
TIMEOUT_SECONDS = 12


class NoRedirect(urllib.request.HTTPRedirectHandler):
    """Treat cross-host and same-host redirects as unverified responses."""

    def redirect_request(self, request, fp, code, message, headers, new_url):
        return None


def _open_request(opener, url: str, *, method: str = "GET", headers=None):
    """Return a status and bounded response, without exposing response data."""
    request = urllib.request.Request(
        url, method=method, headers=headers or {"Accept": "application/json"}
    )
    try:
        with opener.open(request, timeout=TIMEOUT_SECONDS) as response:
            status = response.status
            response_headers = response.headers
            if method == "OPTIONS":
                return status, response_headers, None
            body = response.read(MAX_BYTES + 1)
            if len(body) > MAX_BYTES:
                return status, response_headers, None
            try:
                data = json.loads(body)
            except (ValueError, UnicodeDecodeError):
                data = None
            return status, response_headers, data
    except urllib.error.HTTPError as exc:
        # Includes blocked 3xx redirects. Never follow or read error bodies.
        status = exc.code
        exc.close()
        return status, {}, None
    except (OSError, TimeoutError, ValueError, urllib.error.URLError):
        return None, {}, None


def _identity(value, expected_sha: str) -> str:
    if isinstance(value, str) and FULL_SHA.fullmatch(value):
        return "MATCH" if value == expected_sha else "MISMATCH"
    return "UNAVAILABLE"


def probe(expected_sha: str, *, opener=None) -> dict:
    """Evaluate public preconditions only. A pass never proves operator access."""
    if not FULL_SHA.fullmatch(expected_sha):
        raise ValueError("Expected source must be a full lowercase SHA-1 commit ID.")
    opener = opener or urllib.request.build_opener(NoRedirect())
    health_status, _, health = _open_request(opener, API + "/api/health/")
    health = health if health_status == 200 and isinstance(health, dict) else {}
    backend = _identity(health.get("build_sha"), expected_sha)
    artifact = _identity(health.get("artifact_build_sha"), expected_sha)
    environment = "DEV" if health.get("env") == "dev" else "NOT_VERIFIED"
    database = "READY" if health.get("db") == "ok" and health.get("ok") is True else "NOT_VERIFIED"

    frontend_status, _, frontend = _open_request(opener, PREVIEW + "/build.json")
    frontend = frontend if frontend_status == 200 and isinstance(frontend, dict) else {}
    preview = _identity(frontend.get("build_sha"), expected_sha)

    anon = {}
    for label, path in (
        ("overview", "/api/platform/overview"),
        ("school_directory", "/api/platform/schools/list"),
    ):
        response_status, _, _ = _open_request(opener, API + path)
        anon[label] = (
            "DENIED" if response_status in (401, 403)
            else "EXPOSED" if response_status == 200
            else "NOT_VERIFIED"
        )

    cors_status, cors_headers, _ = _open_request(
        opener, API + "/api/platform/overview", method="OPTIONS",
        headers={
            "Origin": PREVIEW,
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "authorization",
        },
    )
    cors_ok = (
        cors_status in (200, 204)
        and cors_headers.get("Access-Control-Allow-Origin") == PREVIEW
        and cors_headers.get("Access-Control-Allow-Credentials", "").lower() == "true"
        and "authorization" in {
            item.strip().lower()
            for item in cors_headers.get("Access-Control-Allow-Headers", "").split(",")
        }
    )
    checks = {
        "backend_build_sha": backend,
        "backend_artifact_sha": artifact,
        "backend_environment": environment,
        "backend_database": database,
        "dev_preview_build_sha": preview,
        "anonymous_overview": anon["overview"],
        "anonymous_school_directory": anon["school_directory"],
        "dev_preview_cors": "READY" if cors_ok else "NOT_VERIFIED",
    }
    precheck_pass = checks == {
        "backend_build_sha": "MATCH",
        "backend_artifact_sha": "MATCH",
        "backend_environment": "DEV",
        "backend_database": "READY",
        "dev_preview_build_sha": "MATCH",
        "anonymous_overview": "DENIED",
        "anonymous_school_directory": "DENIED",
        "dev_preview_cors": "READY",
    }
    return {
        "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        "expected_main_sha": expected_sha,
        "api_health_http_status": health_status,
        "dev_preview_build_http_status": frontend_status,
        "checks": checks,
        "precheck": "PASS" if precheck_pass else "BLOCKED",
        "owner_console_authenticated_acceptance": "NOT_TESTED",
        "school_provisioning_execution": "NOT_TESTED",
        "backup_restore_evidence": "NOT_TESTED",
        "overall_release_certification": "NOT_VERIFIED",
        "limitations": (
            "HTTP GET/OPTIONS only; does not authenticate an owner, certify the "
            "SPA route or its API binding, authorize a DEV deployment, verify migrations, or execute "
            "provisioning. No bearer tokens, cookies, or Azure credentials used."
        ),
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expected-sha", required=True)
    args = parser.parse_args(argv)
    try:
        report = probe(args.expected_sha)
    except ValueError as exc:
        parser.error(str(exc))
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["precheck"] == "PASS" else 2


if __name__ == "__main__":
    sys.exit(main())
