#!/usr/bin/env bash
# Safe, read-only audit of CROWN's live main-branch required checks.
# Retain this legacy script path as a fail-closed diagnostic, not a mutation tool.
set -euo pipefail

REPO="Arete0920/Crown-CSMS"
BRANCH="main"

usage() {
  cat <<'USAGE'
Usage: scripts/admin/setup_branch_protection.sh --audit <40-character-PR-head-SHA>
Read live main branch protection and check runs for one exact PR head.
This script never updates repository settings. --apply is unsupported.
USAGE
}

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  usage
  exit 0
fi
if [[ "${1:-}" == "--apply" ]]; then
  echo "REFUSED: this legacy script cannot update branch protection." >&2
  exit 3
fi
if [[ "$#" -ne 2 || "$1" != "--audit" || ! "$2" =~ ^[0-9a-fA-F]{40}$ ]]; then
  usage >&2
  exit 2
fi
commit_sha="$2"

if ! command -v gh >/dev/null 2>&1 || ! command -v python3 >/dev/null 2>&1; then
  echo "REFUSED: gh and python3 are required." >&2
  exit 2
fi

scratch="$(mktemp -d)"
trap 'rm -rf -- "$scratch"' EXIT
required="$scratch/required.json"
observed="$scratch/observed.json"

if ! gh api --method GET "/repos/${REPO}/branches/${BRANCH}" > "$required"; then
  echo "REFUSED: live branch metadata read failed; historical policy is not a fallback." >&2
  exit 2
fi
if ! gh api --method GET "/repos/${REPO}/commits/${commit_sha}/check-runs?per_page=100" > "$observed"; then
  echo "REFUSED: exact-head check-run inventory failed." >&2
  exit 2
fi

python3 - "$required" "$observed" "$commit_sha" <<'PY'
import json
import sys

required_path, observed_path, sha = sys.argv[1:]
try:
    with open(required_path, encoding="utf-8") as stream:
        configured = json.load(stream)
    with open(observed_path, encoding="utf-8") as stream:
        result = json.load(stream)
    if configured.get("name") != "main" or not configured.get("protected"):
        raise ValueError("main protection not confirmed by live branch response")
    policy = configured["protection"]["required_status_checks"]
    configured_checks = policy.get("checks")
    if configured_checks is None:
        configured_checks = [
            {"context": name, "app_id": None}
            for name in policy.get("contexts", [])
        ]
    runs = result["check_runs"]
    count = result["total_count"]
    if not isinstance(configured_checks, list) or not configured_checks:
        raise ValueError("no usable required status-check inventory")
    if not isinstance(runs, list) or not isinstance(count, int) or count > len(runs):
        raise ValueError("check-run inventory incomplete; pagination required")

    print(f"CROWN main protection audit; exact head: {sha}")
    print(f"Required contexts: {len(configured_checks)}; retrieved check runs: {len(runs)}")
    failures = []
    for check in configured_checks:
        name, app_id = check["context"], check.get("app_id")
        all_named = [run for run in runs if run.get("name") == name]
        matches = [run for run in all_named if app_id in (None, -1) or
                   run.get("app", {}).get("id") == app_id]
        if not all_named:
            state = "MISSING"
        elif not matches:
            state = "WRONG_APP"
        elif len(matches) > 1:
            state = "AMBIGUOUS_DUPLICATE"
        elif matches[0].get("status") == "completed" and matches[0].get("conclusion") == "success":
            state = "SUCCESS"
        else:
            outcomes = sorted({str(run.get("conclusion") or run.get("status")) for run in matches})
            state = "NOT_SUCCESS(" + ",".join(outcomes) + ")"
        print(f"{state:26} {name} [app_id={app_id}]")
        if state != "SUCCESS":
            failures.append(name)
    if failures:
        print(f"BLOCKED: {len(failures)} required checks are not proven successful.")
        sys.exit(1)
    print("REQUIRED_CHECKS_PRESENT: configured check runs succeeded on this exact head.")
    print("NOTE: merge eligibility also depends on PR freshness, review, threads and all other rules.")
except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
    print(f"REFUSED: cannot evaluate complete live checks: {exc}", file=sys.stderr)
    sys.exit(2)
PY
