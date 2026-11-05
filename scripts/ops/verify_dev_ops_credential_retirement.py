#!/usr/bin/env python3
"""Bounded DEV schoolless credential probe; never a secret-retirement certificate.

Only approved operator facilities may inject the two credential environment
variables. No credential generation, store update, school selector, reset,
database diagnostic, redirect, or production target is supported.
"""

import argparse
from datetime import datetime, timezone
import hmac
import json
import os
import re
import sys
import urllib.error
import urllib.request


API = "https://crown-api-dev.azurewebsites.net"
RESET_PATH = "/api/v1/system/demo-reset/"
HEALTH_PATH = "/api/health/"
RETIRED_ENV = "CROWN_RETIRED_OPS_SECRET"
REPLACEMENT_ENV = "CROWN_REPLACEMENT_OPS_SECRET"
MISSING_SCHOOL = {"detail": "Missing school_id (send X-School-Id or ?school_id=...)"}
FULL_SHA = re.compile(r"[0-9a-f]{40}\Z")
MAX_BYTES = 2048


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, message, headers, new_url):
        return None


class SafeParser(argparse.ArgumentParser):
    def error(self, message):
        # argparse's default error can echo unrecognized arguments, including a
        # credential accidentally supplied on the command line.
        self.exit(2, "Invalid arguments; use --help. Never pass credentials on the command line.\n")


def _valid_secret(value, minimum):
    return (isinstance(value, str) and minimum <= len(value) <= 1024
            and all(33 <= ord(character) <= 126 for character in value))


def _request(opener, *, credential=None):
    path = HEALTH_PATH if credential is None else RESET_PATH
    headers = {"Accept": "application/json"}
    if credential is not None:
        headers.update({"X-Admin-Ops-Secret": credential, "Content-Type": "application/json"})
    request = urllib.request.Request(
        API + path, headers=headers, method="GET" if credential is None else "POST",
        data=None if credential is None else b"{}",
    )
    try:
        response = opener.open(request, timeout=12)
    except urllib.error.HTTPError as exc:
        response = exc
    except (OSError, ValueError, urllib.error.URLError):
        return None, None
    status = response.code
    try:
        # Never read a successful reset response or any unexpected error body.
        allowed = (200,) if credential is None else (400, 403)
        if status not in allowed:
            return status, None
        body = response.read(MAX_BYTES + 1)
        if len(body) > MAX_BYTES:
            return status, None
        try:
            data = json.loads(body)
        except (ValueError, UnicodeDecodeError):
            return status, None
        return status, data
    except OSError:
        return status, None
    finally:
        response.close()


def _healthy_runtime(status, data, expected_sha):
    return (status == 200 and isinstance(data, dict) and data.get("env") == "dev"
            and data.get("db") == "ok" and data.get("ok") is True
            and data.get("build_sha") == data.get("artifact_build_sha") == expected_sha)


def probe(expected_sha, retired, replacement, *, opener=None):
    if (not isinstance(expected_sha, str) or not FULL_SHA.fullmatch(expected_sha)
            or not _valid_secret(retired, 1) or not _valid_secret(replacement, 32)
            or hmac.compare_digest(retired, replacement)):
        raise ValueError("Full reviewed runtime SHA and distinct securely injected credentials required.")
    opener = opener or urllib.request.build_opener(NoRedirect())
    report = {
        "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        "expected_runtime_sha": expected_sha,
        "target": API,
        "checks": {name: "NOT_TESTED" for name in (
            "initial_runtime", "replacement_reset", "historical_reset", "final_runtime")},
        "http_statuses": {},
        "reset_credential_probe": "BLOCKED",
        "diagnostic_authorization": "NOT_TESTED",
        "secret_store_and_consumer_retirement": "NOT_VERIFIED",
        "issue_269_closure": "NOT_CERTIFIED",
        "limitations": "Schoolless reset validation only; no diagnostic, secret-store or consumer certification.",
    }
    checks = report["checks"]
    statuses = report["http_statuses"]
    status, data = _request(opener)
    statuses["initial_health"] = status
    if not _healthy_runtime(status, data, expected_sha):
        checks["initial_runtime"] = "NOT_VERIFIED"
        return report
    checks["initial_runtime"] = "HEALTHY_PINNED_DEV"

    # Establish the actual enabled handler gate before sending the retired value.
    status, data = _request(opener, credential=replacement)
    statuses["replacement_reset"] = status
    if status != 400 or data != MISSING_SCHOOL:
        checks["replacement_reset"] = "NOT_VERIFIED"
        return report
    checks["replacement_reset"] = "MISSING_SCHOOL_VALIDATION"

    status, data = _request(opener, credential=retired)
    statuses["historical_reset"] = status
    checks["historical_reset"] = (
        "CREDENTIAL_DENIED" if status == 403 and data == {"detail": "Forbidden"}
        else "NOT_VERIFIED"
    )
    status, data = _request(opener)
    statuses["final_health"] = status
    checks["final_runtime"] = (
        "HEALTHY_PINNED_DEV" if _healthy_runtime(status, data, expected_sha) else "NOT_VERIFIED"
    )
    if (checks["historical_reset"] == "CREDENTIAL_DENIED"
            and checks["final_runtime"] == "HEALTHY_PINNED_DEV"):
        report["reset_credential_probe"] = "PASS"
    return report


def main(argv=None):
    parser = SafeParser(description=__doc__)
    parser.add_argument("--expected-runtime-sha", required=True,
                        help="Full SHA of the actual deployed, reviewed DEV runtime (not an assumed main SHA).")
    args = parser.parse_args(argv)
    try:
        report = probe(args.expected_runtime_sha, os.environ.get(RETIRED_ENV),
                       os.environ.get(REPLACEMENT_ENV))
    except ValueError:
        print("BLOCKED: valid reviewed runtime SHA and distinct securely injected operator credentials required.",
              file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["reset_credential_probe"] == "PASS" else 2


if __name__ == "__main__":
    sys.exit(main())
