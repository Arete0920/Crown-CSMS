#!/usr/bin/env python3
"""
Phase 6 M6 — Build-SHA / Health Proof

Asserts that a running Crown API service returns the expected build_sha from
GET /api/health/, proving the deployed code matches a known commit.

Environment variables:
  BUILD_SHA_PROOF_URL       Base URL of the service to probe (required)
                            e.g. http://127.0.0.1:8001  or  https://demo.crown.app
  BUILD_SHA_PROOF_EXPECTED  The exact 40-char hex SHA the response must match (required)
  BUILD_SHA_PROOF_TIMEOUT   HTTP timeout in seconds (default: 20)

Exit codes:
  0 — PASSED: build_sha matches expected
  1 — FAILED: build_sha mismatch, missing field, or non-200 response
  2 — CONFIG ERROR: missing env vars or service unreachable
"""

import json
import os
import sys

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

BASE_URL = os.environ.get("BUILD_SHA_PROOF_URL", "").rstrip("/")
EXPECTED_SHA = os.environ.get("BUILD_SHA_PROOF_EXPECTED", "")
TIMEOUT = int(os.environ.get("BUILD_SHA_PROOF_TIMEOUT", "20"))
HEALTH_PATH = "/api/health/"


def die(code: int, msg: str) -> None:
    label = {0: "PASS", 1: "FAIL", 2: "CONFIG ERROR"}.get(code, "ERROR")
    print(f"BUILD-SHA PROOF {label}: {msg}", file=sys.stderr if code else sys.stdout)
    sys.exit(code)


def http_get(url: str, timeout: int):
    """Try requests first, fall back to urllib."""
    try:
        import requests  # type: ignore
        r = requests.get(url, timeout=timeout)
        return r.status_code, r.text
    except ImportError:
        pass

    import urllib.request
    import urllib.error
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return resp.status, resp.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()
    except Exception as e:
        raise ConnectionError(str(e)) from e


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    # Validate config
    if not BASE_URL:
        die(2, "missing required env var: BUILD_SHA_PROOF_URL")
    if not EXPECTED_SHA:
        die(2, "missing required env var: BUILD_SHA_PROOF_EXPECTED")
    if len(EXPECTED_SHA) != 40 or not all(c in "0123456789abcdefABCDEF" for c in EXPECTED_SHA):
        die(2, f"BUILD_SHA_PROOF_EXPECTED must be a 40-char hex SHA (got: {EXPECTED_SHA!r})")

    url = BASE_URL + HEALTH_PATH
    print(f"BUILD-SHA PROOF: probing {url}")
    print(f"BUILD-SHA PROOF: expecting build_sha={EXPECTED_SHA}")

    # Fire request
    try:
        status_code, body = http_get(url, TIMEOUT)
    except ConnectionError as e:
        die(2, f"connection failed: {e}")
    except Exception as e:
        die(2, f"unexpected error during HTTP request: {type(e).__name__}: {e}")

    print(f"BUILD-SHA PROOF: HTTP {status_code}")

    # Parse response
    if status_code != 200:
        die(1, f"health endpoint returned HTTP {status_code} (expected 200)")

    try:
        data = json.loads(body)
    except json.JSONDecodeError as e:
        die(1, f"health response is not valid JSON: {e}")

    # Assert build_sha present
    if "build_sha" not in data:
        die(1, f"health response missing 'build_sha' field. Keys present: {list(data.keys())}")

    actual_sha = data["build_sha"]
    print(f"BUILD-SHA PROOF: response build_sha={actual_sha!r}")

    # Guard against fallback value
    if actual_sha == "local-dev":
        die(1, (
            "build_sha is 'local-dev' — service was not started with BUILD_SHA or GITHUB_SHA env var. "
            "Ensure the deployed process has BUILD_SHA set to the deployed commit SHA."
        ))

    # Assert match
    if actual_sha.lower() != EXPECTED_SHA.lower():
        die(1, (
            f"build_sha MISMATCH:\n"
            f"  expected: {EXPECTED_SHA}\n"
            f"  actual:   {actual_sha}\n"
            f"This means the deployed service is running a DIFFERENT commit than expected."
        ))

    # Also validate format
    if len(actual_sha) != 40 or not all(c in "0123456789abcdefABCDEF" for c in actual_sha):
        die(1, f"build_sha has unexpected format: {actual_sha!r} (must be 40-char hex)")

    die(0, f"build_sha={actual_sha} matches expected commit. Deployed commit is correct.")


if __name__ == "__main__":
    main()
