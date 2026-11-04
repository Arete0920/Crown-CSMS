#!/usr/bin/env python3
"""Read-only public precheck for the EXISTING CROWN Azure buyer-preview hosts.

This checks deployment identity, the Heritage-only catalog, SPA reachability,
invitation metadata (optionally), and preview-to-API CORS. It does NOT create
sandbox sessions, provision tenants, authenticate a buyer, test module writes,
or authorize emailing a full five-module demo. No secrets or response bodies
from authenticated endpoints are collected. No Azure resources are changed.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.request

import verify_dev_owner_runtime as existing

INVITE_ID = re.compile(r"sbx_inv_[A-Za-z0-9]{24}\Z")
EXPECTED_ROLES = frozenset({
    "school_admin", "admissions_director", "finance_director", "teacher",
    "parent", "student", "board",
})
FIVE_MODULES = (
    "diadem_daycare", "extended_care_am_pm", "summer_camp",
    "jireh_financial_aid", "jireh_sgo_partner_processing",
)


def _cors_allows(headers, *, origin, method, required_headers):
    tokens = lambda name: {
        part.strip().lower() for part in headers.get(name, "").split(",")
        if part.strip()
    }
    return (
        headers.get("Access-Control-Allow-Origin") == origin
        and headers.get("Access-Control-Allow-Credentials", "").lower() == "true"
        and method.lower() in tokens("Access-Control-Allow-Methods")
        and required_headers.issubset(tokens("Access-Control-Allow-Headers"))
    )


def _catalog_is_heritage_only(payload):
    """Use the live public catalog response; do not infer schools from UI cards."""
    if not isinstance(payload, dict):
        return False
    schools = payload.get("schools")
    tracks = payload.get("tracks")
    personas = payload.get("personas")
    return bool(
        isinstance(schools, list) and len(schools) == 1
        and isinstance(schools[0], dict)
        and schools[0].get("key") == "heritage-core"
        and schools[0].get("track") == "school"
        and isinstance(tracks, list) and len(tracks) == 1
        and isinstance(tracks[0], dict)
        and tracks[0].get("key") == "school"
        and isinstance(personas, list)
        and {x.get("key") for x in personas if isinstance(x, dict)} == EXPECTED_ROLES
        and len(personas) == len(EXPECTED_ROLES)
    )


def _invite_is_bounded(payload, invite_id):
    """A valid-looking invite is still not evidence that a session can be issued."""
    if not isinstance(payload, dict) or payload.get("invite_id") != invite_id:
        return False
    roles = payload.get("allowed_roles")
    packs = payload.get("allowed_seed_packs")
    return bool(
        payload.get("usable") is True
        and payload.get("track") == "school"
        and isinstance(roles, list) and bool(roles)
        and all(isinstance(x, str) and x in EXPECTED_ROLES for x in roles)
        and isinstance(packs, list) and packs == ["heritage-core"]
        and payload.get("revoked_at") is None
    )


def probe(expected_sha: str, *, invite_id=None, opener=None, identity_probe=None):
    """Run only public GET/OPTIONS. A clean result means PRECHECK, never GO."""
    if not existing.FULL_SHA.fullmatch(expected_sha):
        raise ValueError("Expected source must be one full lowercase SHA-1 commit ID.")
    if invite_id is not None and not INVITE_ID.fullmatch(invite_id):
        raise ValueError("Invalid invite identifier format; no network call made.")
    opener = opener or urllib.request.build_opener(existing.NoRedirect())
    identity_probe = identity_probe or existing.probe
    identity = identity_probe(expected_sha, opener=opener)
    if not isinstance(identity, dict):
        raise ValueError("The established DEV identity probe returned invalid evidence.")

    status_catalog, _, catalog = existing._open_request(
        opener, existing.API + "/api/v1/sandbox/catalog/", read_json=True,
    )
    status_page, _, _ = existing._open_request(
        opener, existing.PREVIEW + "/sandbox", read_json=False,
    )
    status_options, headers, _ = existing._open_request(
        opener, existing.API + "/api/v1/sandbox/session/",
        method="OPTIONS",
        headers={
            "Origin": existing.PREVIEW,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    checks = {
        "existing_dev_source_and_unauthorized_denial": (
            "PASS" if identity.get("precheck") == "PASS" else "BLOCKED"
        ),
        "public_sandbox_catalog_heritage_only": (
            "PASS" if status_catalog == 200 and _catalog_is_heritage_only(catalog) else "BLOCKED"
        ),
        "public_sandbox_page_http": "PASS" if status_page == 200 else "BLOCKED",
        "preview_can_post_sandbox_session_cors": (
            "PASS" if status_options in (200, 204) and _cors_allows(
                headers, origin=existing.PREVIEW, method="POST",
                required_headers={"content-type"},
            ) else "BLOCKED"
        ),
    }
    if invite_id is not None:
        status_invite, _, data = existing._open_request(
            opener, existing.API + "/api/v1/sandbox/invites/" + invite_id + "/",
            read_json=True,
        )
        checks["provided_invite_active_and_heritage_scoped"] = (
            "PASS" if status_invite == 200 and _invite_is_bounded(data, invite_id)
            else "BLOCKED"
        )
    else:
        checks["provided_invite_active_and_heritage_scoped"] = "NOT_TESTED"

    public_pass = all(x == "PASS" for k, x in checks.items()
                      if k != "provided_invite_active_and_heritage_scoped")
    invite_pass = checks["provided_invite_active_and_heritage_scoped"] == "PASS"
    return {
        "expected_source_sha": expected_sha,
        "existing_dev_public_precheck": identity.get("precheck", "BLOCKED"),
        "public_checks": checks,
        "public_precheck": "PASS" if public_pass else "BLOCKED",
        "invite_precheck": "PASS" if invite_pass else "BLOCKED",
        "authorized_role_session_and_navigation": "NOT_TESTED",
        "signed_5_module_write_get_reload_and_negative_tests": {
            module: "NOT_TESTED" for module in FIVE_MODULES
        },
        "hosted_module_entitlement_and_synthetic_provisioning": "NOT_TESTED",
        "hosted_custody_and_partner_authorization": "NOT_TESTED",
        "release_certified": False,
        "email_full_demo_link": "NO_GO",
        "limitations": (
            "Public GET/OPTIONS and sanitized metadata only. No school/parent/SGO "
            "session issuance, POST writes, live browser workflow, invite creation, "
            "migrations, tenant provisioning, deployment, payments or cloud changes. "
            "Public precheck PASS is never five-module certification."
        ),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expected-sha", required=True)
    parser.add_argument(
        "--invite-stdin", action="store_true",
        help="Read an optional existing invite ID from stdin; never pass the ID in CLI args or logs.",
    )
    args = parser.parse_args(argv)
    invite = None
    if args.invite_stdin:
        invite = sys.stdin.readline(100).strip()
        if not invite or len(invite) > 40:
            parser.error("Invite input is missing or invalid.")
    try:
        report = probe(args.expected_sha, invite_id=invite)
    except ValueError as exc:
        parser.error(str(exc))
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["public_precheck"] == "PASS" and (
        not args.invite_stdin or report["invite_precheck"] == "PASS"
    ) else 2


if __name__ == "__main__":
    sys.exit(main())
