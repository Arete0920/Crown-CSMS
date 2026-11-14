#!/usr/bin/env python3
"""Fail-closed code-only DEV image capture/rollback.

Only existing crown-rg/crown-api-dev and crownregistry/crown2026 are permitted.
Never handles database backups or schema migration. No secrets enter receipts.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request

RG, APP, REGISTRY, REPO = "crown-rg", "crown-api-dev", "crownregistry", "crown2026"
IMAGE_PREFIX = f"{REGISTRY}.azurecr.io/{REPO}"
API = "https://crown-api-dev.azurewebsites.net/api/health/"
SHA = re.compile(r"[0-9a-f]{40}\Z")
DIGEST = re.compile(r"sha256:[0-9a-f]{64}\Z")
RECEIPT = frozenset(("status", "prior_sha", "prior_image", "prior_digest",
                     "prior_run_id", "prior_workflow", "captured_at_utc"))


class Unsafe(RuntimeError):
    pass


def az(*args, json_mode=True):
    # Never write raw Azure stdout/stderr to the Actions log (even on failures).
    cmd = ["az", *args, "--output", "json" if json_mode else "none", "--only-show-errors"]
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=120, check=True)
        return json.loads(p.stdout) if json_mode else None
    except (OSError, subprocess.TimeoutExpired, subprocess.CalledProcessError, ValueError) as exc:
        raise Unsafe("azure_command_unavailable_or_failed") from exc


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, message, headers, newurl):
        return None


def health():
    opener = urllib.request.build_opener(NoRedirect())
    try:
        with opener.open(urllib.request.Request(API, headers={"Accept": "application/json"}),
                         timeout=15) as response:
            if response.status != 200 or response.geturl() != API:
                raise Unsafe("dev_health_response_unverified")
            raw = response.read(8193)
            if len(raw) > 8192:
                raise Unsafe("dev_health_response_too_large")
            return json.loads(raw)
    except (urllib.error.URLError, OSError, ValueError) as exc:
        raise Unsafe("dev_health_unavailable") from exc


def assert_health(sha, data):
    if (not isinstance(data, dict) or data.get("ok") is not True
            or data.get("env") != "dev" or data.get("db") != "ok"
            or data.get("build_sha") != sha
            or data.get("artifact_build_sha") != sha):
        raise Unsafe("prior_dev_runtime_not_healthy")


def check_receipt(data):
    if not isinstance(data, dict) or set(data) != RECEIPT:
        raise Unsafe("rollback_receipt_shape_invalid")
    sha, digest = data.get("prior_sha"), data.get("prior_digest")
    if not isinstance(sha, str) or not SHA.fullmatch(sha):
        raise Unsafe("rollback_prior_sha_invalid")
    if not isinstance(digest, str) or not DIGEST.fullmatch(digest):
        raise Unsafe("rollback_prior_digest_invalid")
    if data.get("prior_image") != IMAGE_PREFIX + ":dev-" + sha:
        raise Unsafe("rollback_prior_image_invalid")
    if data.get("status") != "CAPTURED":
        raise Unsafe("rollback_receipt_not_captured")
    if not isinstance(data.get("captured_at_utc"), str) or not data["captured_at_utc"]:
        raise Unsafe("rollback_receipt_timestamp_missing")
    if (not isinstance(data.get("prior_run_id"), str)
            or not re.fullmatch(r"[1-9][0-9]*", data["prior_run_id"])):
        raise Unsafe("rollback_prior_deploy_run_invalid")
    if (not isinstance(data.get("prior_workflow"), str)
            or data["prior_workflow"] != "DEV Deploy (protected main)"):
        raise Unsafe("rollback_prior_workflow_invalid")
    return data


def acr_digest(image):
    record = az("acr", "repository", "show", "--name", REGISTRY,
                "--image", image, "--query", "{digest:digest}")
    digest = record.get("digest") if isinstance(record, dict) else None
    if not isinstance(digest, str) or not DIGEST.fullmatch(digest):
        raise Unsafe("existing_acr_image_digest_not_verified")
    return digest


def capture(path):
    rows = az("webapp", "config", "appsettings", "list",
              "--resource-group", RG, "--name", APP)
    if not isinstance(rows, list):
        raise Unsafe("prior_appsettings_unavailable")
    values = {}
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get("name"), str):
            raise Unsafe("prior_appsettings_invalid")
        key = row["name"]
        if key in ("BUILD_SHA", "DEPLOY_RUN_ID", "DEPLOY_WORKFLOW"):
            if key in values:
                raise Unsafe("duplicate_prior_app_identity")
            values[key] = row.get("value")
    # The DEV workflow also overwrites these four non-secret runtime markers.
    # If they are absent or differ, rollback of three identity keys alone
    # could not re-create the previous configuration. Fail before any write.
    fixed_dev = {"WEBSITES_PORT": "8000", "CROWN_ENV": "dev",
                 "DJANGO_ENV": "development", "ENVIRONMENT": "dev"}
    observed_fixed = {row["name"]: row.get("value") for row in rows
                      if isinstance(row, dict) and row.get("name") in fixed_dev}
    if observed_fixed != fixed_dev:
        raise Unsafe("prior_runtime_settings_not_rollback_compatible")
    sha = values.get("BUILD_SHA")
    if not isinstance(sha, str) or not SHA.fullmatch(sha):
        raise Unsafe("prior_build_sha_unavailable")
    config = az("webapp", "config", "show", "--resource-group", RG, "--name", APP)
    image = IMAGE_PREFIX + ":dev-" + sha
    if not isinstance(config, dict) or config.get("linuxFxVersion") != "DOCKER|" + image:
        raise Unsafe("prior_immutable_app_image_unverified")
    digest = acr_digest(REPO + ":dev-" + sha)
    assert_health(sha, health())
    record = check_receipt({
        "status": "CAPTURED", "prior_sha": sha, "prior_image": image,
        "prior_digest": digest,
        "prior_run_id": values.get("DEPLOY_RUN_ID"),
        "prior_workflow": values.get("DEPLOY_WORKFLOW"),
        "captured_at_utc": datetime.now(timezone.utc).isoformat(),
    })
    target = Path(path)
    fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as out:
        json.dump(record, out, sort_keys=True)
        out.write("\n")
    return record


def restore(path, *, sleep=time.sleep):
    try:
        receipt = check_receipt(json.loads(Path(path).read_text(encoding="utf-8")))
    except (ValueError, OSError, TypeError) as exc:
        raise Unsafe("rollback_receipt_missing_or_invalid") from exc
    prior = receipt["prior_sha"]
    if acr_digest(REPO + ":dev-" + prior) != receipt["prior_digest"]:
        raise Unsafe("prior_image_digest_changed_or_unavailable")
    # Restore the exact immutable digest and the original public identity,
    # never an unpinned latest tag or a new resource.
    az("webapp", "config", "container", "set", "--resource-group", RG, "--name", APP,
       "--docker-registry-server-url", "https://" + REGISTRY + ".azurecr.io",
       "--docker-custom-image-name", IMAGE_PREFIX + "@" + receipt["prior_digest"],
       json_mode=False)
    az("webapp", "config", "appsettings", "set", "--resource-group", RG, "--name", APP,
       "--settings", "BUILD_SHA=" + prior,
       "DEPLOY_RUN_ID=" + receipt["prior_run_id"],
       "DEPLOY_WORKFLOW=" + receipt["prior_workflow"], json_mode=False)
    az("webapp", "restart", "--resource-group", RG, "--name", APP, json_mode=False)
    for attempt in range(36):
        try:
            assert_health(prior, health())
            return prior
        except Unsafe:
            if attempt < 35:
                sleep(10)
    raise Unsafe("prior_runtime_did_not_recover_after_rollback")


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("operation", choices=("capture", "restore"))
    p.add_argument("--receipt", required=True)
    args = p.parse_args(argv)
    try:
        result = capture(args.receipt) if args.operation == "capture" else restore(args.receipt)
        sha = result["prior_sha"] if isinstance(result, dict) else result
        print(json.dumps({"status": "CAPTURED" if args.operation == "capture"
                          else "ROLLBACK_VERIFIED", "prior_sha": sha}, sort_keys=True))
        return 0
    except (Unsafe, OSError, ValueError, TypeError) as exc:
        reason = str(exc) if isinstance(exc, Unsafe) else "rollback_evidence_unavailable"
        print(json.dumps({"status": "BLOCKED", "reason": reason}, sort_keys=True))
        return 2


if __name__ == "__main__":
    sys.exit(main())
