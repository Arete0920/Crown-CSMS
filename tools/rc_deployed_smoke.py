#!/usr/bin/env python3
"""
tools/rc_deployed_smoke.py
Phase 6 Move #5: Tier-1 Deployed Smoke Gate

Runs probes from tools/rc_endpoint_probes.json against a live deployed environment.
Designed for the JSON format already established by rc_endpoint_probes.json:
  - "expect":          list[int]   -- accepted HTTP status codes
  - "requiresAuth":    bool        -- send Authorization: Bearer header
  - "requiresSchoolId": bool       -- send X-School-Id header
  - "tier":            "T1"|"T2"  -- filter by RC_TIER env (default: T1)

Required env vars:
  RC_BASE_URL    base URL of deployed API, e.g. http://127.0.0.1:8000
  RC_TOKEN       JWT access token (without "Bearer " prefix)
  RC_SCHOOL_ID   tenant UUID for X-School-Id header

Optional env vars:
  RC_DEMO_KEY    value for X-Demo-Key header (if deployment requires it)
  RC_TIER        which tier to run: T1 (default), T2, ALL
  RC_TIMEOUT     per-request timeout in seconds (default: 20)

Exit codes:
  0  all selected probes passed
  1  one or more probes failed
  2  configuration error (missing env var, missing file, bad JSON)
  3  no probes selected after tier filter

Usage:
  python tools/rc_deployed_smoke.py
"""

import json
import os
import sys
import time
from urllib.parse import urljoin


# ---------------------------------------------------------------------------
# Optional: prefer requests; fall back gracefully with an explicit message
# ---------------------------------------------------------------------------
try:
    import requests as _requests_lib
    _USE_REQUESTS = True
except ImportError:
    _USE_REQUESTS = False
    import urllib.request
    import urllib.error


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def fail_config(msg: str) -> None:
    print(f"\nRC DEPLOYED SMOKE CONFIG ERROR: {msg}", file=sys.stderr)
    sys.exit(2)


def env_required(name: str) -> str:
    v = os.getenv(name, "").strip()
    if not v:
        fail_config(
            f"missing required env var: {name}\n"
            f"  Set {name} before running this script.\n"
            f"  See tools/run_rc_live_probes.ps1 for a convenient wrapper."
        )
    return v


def normalize_base(base: str) -> str:
    return base.rstrip("/")


def load_contract(path: str) -> list[dict]:
    if not os.path.exists(path):
        fail_config(f"probe contract not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            fail_config(f"invalid JSON in {path}: {e}")
    if isinstance(data, dict):
        if "probes" not in data:
            fail_config(f"{path}: missing top-level 'probes' key")
        return list(data["probes"])
    if isinstance(data, list):
        return data
    fail_config(f"{path}: must be a JSON object with 'probes' key or a JSON array")


def build_headers(
    token: str,
    school_id: str,
    demo_key: str | None,
    requires_auth: bool,
    requires_school_id: bool,
) -> dict:
    h: dict[str, str] = {"Accept": "application/json"}
    if requires_auth and token:
        h["Authorization"] = f"Bearer {token}"
    if requires_school_id and school_id:
        h["X-School-Id"] = school_id
    if demo_key:
        h["X-Demo-Key"] = demo_key
    return h


# ---------------------------------------------------------------------------
# HTTP dispatch (requests preferred; stdlib fallback)
# ---------------------------------------------------------------------------

def http_request(
    method: str,
    url: str,
    headers: dict,
    timeout: int,
) -> tuple[int, str]:
    """Returns (status_code, body_snippet)."""
    if _USE_REQUESTS:
        resp = _requests_lib.request(method, url, headers=headers, timeout=timeout)
        body = resp.text or ""
        return resp.status_code, body

    # stdlib fallback (GET/HEAD only for simplicity)
    req = urllib.request.Request(url, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = r.read().decode("utf-8", errors="replace")
            return r.status, body
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        return e.code, body


# ---------------------------------------------------------------------------
# Single probe runner
# ---------------------------------------------------------------------------

def run_probe(
    base_url: str,
    token: str,
    school_id: str,
    demo_key: str | None,
    probe: dict,
    timeout: int,
) -> tuple[bool, str]:
    name        = str(probe.get("name", "unnamed")).strip()
    tier        = str(probe.get("tier", "T1")).strip().upper()
    method      = str(probe.get("method", "GET")).strip().upper()
    path        = str(probe.get("path", "/")).strip()
    expects_raw = probe.get("expect", [200])
    req_auth    = bool(probe.get("requiresAuth", True))
    req_school  = bool(probe.get("requiresSchoolId", False))

    # Normalise expect to list[int]
    if isinstance(expects_raw, (int, float)):
        expect_codes = [int(expects_raw)]
    elif isinstance(expects_raw, list):
        expect_codes = [int(x) for x in expects_raw]
    else:
        expect_codes = [200]

    if not path.startswith("/"):
        path = "/" + path

    url = f"{base_url}{path}"
    headers = build_headers(token, school_id, demo_key, req_auth, req_school)

    t0 = time.monotonic()
    try:
        status, body = http_request(method, url, headers, timeout)
    except Exception as exc:
        elapsed = int((time.monotonic() - t0) * 1000)
        return False, f"{name} [{tier}] {method} {path} -> EXCEPTION ({elapsed}ms): {exc}"

    elapsed = int((time.monotonic() - t0) * 1000)
    passed  = status in expect_codes
    detail  = (
        f"{name} [{tier}] {method} {path}"
        f" -> {status} (expect {expect_codes}) {elapsed}ms"
    )

    if not passed:
        snippet = (body or "").replace("\r", " ").replace("\n", " ").strip()
        if len(snippet) > 220:
            snippet = snippet[:220] + "..."
        detail += f"  |  body: {snippet}"

    return passed, detail


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    contract_path = os.path.join("tools", "rc_endpoint_probes.json")

    base_url  = normalize_base(env_required("RC_BASE_URL"))
    token     = env_required("RC_TOKEN")
    school_id = env_required("RC_SCHOOL_ID")
    demo_key  = os.getenv("RC_DEMO_KEY", "").strip() or None
    tier_filter = os.getenv("RC_TIER", "T1").strip().upper()
    timeout   = int(os.getenv("RC_TIMEOUT", "20"))

    probes = load_contract(contract_path)

    # Apply tier filter
    if tier_filter == "ALL":
        selected = probes
    else:
        selected = [p for p in probes if str(p.get("tier", "T1")).upper() == tier_filter]

    if not selected:
        print(
            f"RC DEPLOYED SMOKE: no probes selected (tier={tier_filter}).\n"
            f"  Check tools/rc_endpoint_probes.json. Available tiers: "
            + str(list({str(p.get('tier', '?')).upper() for p in probes})),
            file=sys.stderr,
        )
        return 3

    print(
        f"RC Deployed Smoke  base={base_url}  tier={tier_filter}"
        f"  probes={len(selected)}  timeout={timeout}s\n"
        + ("-" * 80)
    )

    failures = 0
    for probe in selected:
        passed, detail = run_probe(base_url, token, school_id, demo_key, probe, timeout)
        label = "PASS" if passed else "FAIL"
        print(f"{label}: {detail}")
        if not passed:
            failures += 1

    print("-" * 80)
    if failures:
        print(
            f"\nRC DEPLOYED SMOKE FAILED  ({failures}/{len(selected)} probes failed)\n"
            "  Fix the listed probes before promoting to RC.",
            file=sys.stderr,
        )
        return 1

    print(f"\nRC DEPLOYED SMOKE PASSED  ({len(selected)}/{len(selected)} probes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
