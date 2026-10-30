#!/usr/bin/env python3
"""Fail-closed authority gate for reviewed, destructive DEV demo resets.

Only validates dispatch provenance, exact current protected source, explicit
operator confirmation and an administrator-controlled synthetic-school allowlist.
It has no access to operations secrets or the target API. Run at the start of
an approved workflow and immediately before each authenticated request.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
from uuid import UUID

FULL_SHA = re.compile(r"[0-9a-f]{40}\Z")
CANONICAL_UUID = re.compile(r"[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12}\Z")
REPOSITORY = "Arete0920/Crown-CSMS"
MAX_ALLOWED_IDS = 50


def canonical_school_id(value: str) -> bool:
    """Require an unambiguous canonical, non-nil UUID (no name or URL selectors)."""
    return bool(
        CANONICAL_UUID.fullmatch(value)
        and UUID(value).int != 0
        and str(UUID(value)) == value
    )


def validate_reset_request(environ: dict[str, str]) -> None:
    """Reject any malformed, stale, unprotected or unapproved reset request."""
    if environ.get("GITHUB_REPOSITORY") != REPOSITORY:
        raise ValueError("unexpected GitHub repository")
    if environ.get("GITHUB_EVENT_NAME") != "workflow_dispatch":
        raise ValueError("reset must be manually dispatched")
    if environ.get("GITHUB_REF") != "refs/heads/main":
        raise ValueError("reset requires protected main")
    if environ.get("GITHUB_REF_PROTECTED") != "true":
        raise ValueError("main branch protection was not confirmed")
    if environ.get("GITHUB_RUN_ATTEMPT") != "1":
        raise ValueError("historic workflow reruns are not authorized")
    source_sha = environ.get("GITHUB_SHA", "")
    if not FULL_SHA.fullmatch(source_sha):
        raise ValueError("dispatch SHA must be an exact 40-character source")

    school_id = environ.get("SCHOOL_ID", "")
    confirmed = environ.get("CONFIRM_SCHOOL_ID", "")
    if not canonical_school_id(school_id) or confirmed != school_id:
        raise ValueError("school selection or explicit confirmation is invalid")
    raw_allowed = environ.get("DEV_RESET_ALLOWED_SCHOOL_IDS", "")
    if not raw_allowed or len(raw_allowed) > MAX_ALLOWED_IDS * 40:
        raise ValueError("reviewed DEV school allowlist is missing or invalid")
    ids = [item.strip() for item in raw_allowed.split(",")]
    if (
        not ids
        or len(ids) > MAX_ALLOWED_IDS
        or any(not canonical_school_id(item) for item in ids)
        or len(set(ids)) != len(ids)
        or school_id not in ids
    ):
        raise ValueError("school is not on a valid, explicitly reviewed allowlist")

    # GitHub reruns retain the original GITHUB_SHA. Git fetch refreshes main,
    # so a stale queued job cannot authorize a newer or older source.
    subprocess.run(
        ["git", "fetch", "--no-tags", "origin", "refs/heads/main:refs/remotes/origin/main"],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=30,
    )
    checkout_sha = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        check=True, capture_output=True, text=True, timeout=10,
    ).stdout.strip()
    current_main_sha = subprocess.run(
        ["git", "rev-parse", "refs/remotes/origin/main"],
        check=True, capture_output=True, text=True, timeout=10,
    ).stdout.strip()
    if checkout_sha != source_sha or current_main_sha != source_sha:
        raise ValueError("dispatch source no longer matches current protected main")


def main() -> int:
    try:
        validate_reset_request(os.environ)
    except (ValueError, OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        # Never print config or credentials, even on failure.
        print("BLOCKED: DEV reset authority not verified; no API request issued.", file=sys.stderr)
        return 1
    print("PASS: Current protected-main source and reviewed DEV reset school confirmed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
