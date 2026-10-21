#!/usr/bin/env bash
# Read-only audit of a currently open CROWN PR against live main protection.
# Legacy versions unconditionally overwrote branch protection with stale checks.
set -euo pipefail

REPO="Arete0920/Crown-CSMS"
BRANCH="main"

usage() {
  cat <<'USAGE'
Usage: scripts/admin/setup_branch_protection.sh --audit-pr <PR_NUMBER>

Read live main branch protection and the check runs on the current exact PR
head. Re-read PR/main identity before reporting to reject moving references.
Requires read access to authoritative branch protection, including app IDs.
This script cannot change GitHub settings. --apply is unsupported.
USAGE
}

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  usage
  exit 0
fi
if [[ "${1:-}" == "--apply" ]]; then
  echo "REFUSED: legacy branch protection writes are disabled." >&2
  exit 3
fi
if [[ "$#" -ne 2 || "$1" != "--audit-pr" || ! "$2" =~ ^[1-9][0-9]*$ ]]; then
  usage >&2
  exit 2
fi
pr_number="$2"
if ! command -v gh >/dev/null 2>&1 || ! command -v python3 >/dev/null 2>&1; then
  echo "REFUSED: gh and python3 are required for the read-only audit." >&2
  exit 2
fi

scratch="$(mktemp -d)"
trap 'rm -rf -- "$scratch"' EXIT
branch_before="$scratch/branch-before.json"
pr_before="$scratch/pr-before.json"
checks="$scratch/checks.json"
pr_after="$scratch/pr-after.json"
branch_after="$scratch/branch-after.json"
policy_before="$scratch/policy-before.json"
policy_after="$scratch/policy-after.json"

if ! gh api --method GET "/repos/${REPO}/branches/${BRANCH}/protection" > "$policy_before" ||
   ! gh api --method GET "/repos/${REPO}/branches/${BRANCH}" > "$branch_before" ||
   ! gh api --method GET "/repos/${REPO}/pulls/${pr_number}" > "$pr_before"; then
  echo "REFUSED: cannot read current branch/PR authority from GitHub." >&2
  exit 2
fi

if ! head_sha="$(python3 - "$pr_before" "$pr_number" <<'PY'
import json
import re
import sys

with open(sys.argv[1], encoding="utf-8") as stream:
    pr = json.load(stream)
sha = pr.get("head", {}).get("sha", "")
if (pr.get("number") != int(sys.argv[2]) or pr.get("state") != "open"
        or pr.get("base", {}).get("ref") != "main"
        or not re.fullmatch(r"[0-9a-fA-F]{40}", sha)):
    raise SystemExit(2)
print(sha)
PY
)"; then
  echo "REFUSED: PR is not an open main-targeting PR with a verifiable head." >&2
  exit 2
fi

if ! gh api --method GET "/repos/${REPO}/commits/${head_sha}/check-runs?per_page=100" > "$checks" ||
   ! gh api --method GET "/repos/${REPO}/pulls/${pr_number}" > "$pr_after" ||
   ! gh api --method GET "/repos/${REPO}/branches/${BRANCH}" > "$branch_after" ||
   ! gh api --method GET "/repos/${REPO}/branches/${BRANCH}/protection" > "$policy_after"; then
  echo "REFUSED: exact-head checks or final identity confirmation unavailable." >&2
  exit 2
fi

python3 - "$branch_before" "$pr_before" "$checks" "$pr_after" "$branch_after" "$pr_number" "$head_sha" "$policy_before" "$policy_after" <<'PY'
import json
import sys

branch_before_path, pr_before_path, checks_path, pr_after_path, branch_after_path, num, sha, policy_before_path, policy_after_path = sys.argv[1:]
try:
    with open(branch_before_path, encoding="utf-8") as stream:
        branch_before = json.load(stream)
    with open(pr_before_path, encoding="utf-8") as stream:
        pr_before = json.load(stream)
    with open(checks_path, encoding="utf-8") as stream:
        observed = json.load(stream)
    with open(pr_after_path, encoding="utf-8") as stream:
        pr_after = json.load(stream)
    with open(branch_after_path, encoding="utf-8") as stream:
        branch_after = json.load(stream)

    with open(policy_before_path, encoding="utf-8") as stream:
        protection_before = json.load(stream)
    with open(policy_after_path, encoding="utf-8") as stream:
        protection_after = json.load(stream)
    if protection_before != protection_after:
        raise ValueError("authoritative branch protection changed while auditing")

    for branch in (branch_before, branch_after):
        if branch.get("name") != "main" or not branch.get("protected"):
            raise ValueError("main protection was not verified")
    before_main = branch_before["commit"]["sha"]
    after_main = branch_after["commit"]["sha"]
    if before_main != after_main:
        raise ValueError("main moved while auditing; rerun against current state")
    if branch_before.get("protection") != branch_after.get("protection"):
        raise ValueError("branch protection changed while auditing")
    for pr in (pr_before, pr_after):
        if (pr.get("number") != int(num) or pr.get("state") != "open"
                or pr.get("base", {}).get("ref") != "main"
                or pr.get("base", {}).get("sha") != before_main
                or pr.get("head", {}).get("sha") != sha):
            raise ValueError("PR head/base changed or is not current with main")

    policy = protection_before["required_status_checks"]
    required = policy["checks"]
    contexts = policy["contexts"]
    if not isinstance(required, list) or not required:
        raise ValueError("authoritative required-check inventory missing")
    names = []
    for check in required:
        if (not isinstance(check, dict) or not isinstance(check.get("context"), str)
                or not check["context"].strip() or "app_id" not in check):
            raise ValueError("required-check context or application identity missing")
        app_id = check["app_id"]
        if app_id is not None and (type(app_id) is not int or (app_id != -1 and app_id <= 0)):
            raise ValueError("invalid required-check application identity")
        names.append(check["context"])
    if (not isinstance(contexts, list) or any(not isinstance(n, str) for n in contexts)
            or len(set(names)) != len(names) or len(set(contexts)) != len(contexts)
            or set(names) != set(contexts)):
        raise ValueError("required-check contexts/checks inventory inconsistent")
    # A branch summary is supplementary: it must never override authoritative app IDs.
    for branch in (branch_before, branch_after):
        summary = branch["protection"]["required_status_checks"]
        if sorted(summary["contexts"]) != sorted(contexts):
            raise ValueError("branch summary differs from authoritative required checks")
        if "checks" in summary and summary["checks"] != required:
            raise ValueError("branch summary differs from authoritative application identities")
    runs = observed["check_runs"]
    total = observed["total_count"]
    if not isinstance(required, list) or not required:
        raise ValueError("live required-check inventory missing")
    if not isinstance(runs, list) or type(total) is not int or total < 0 or total != len(runs):
        raise ValueError("check-run result is incomplete (pagination required)")

    if any(not isinstance(run, dict) or run.get("head_sha") != sha for run in runs):
        raise ValueError("check-run head does not match verified PR head")

    print(f"CROWN live main required-check audit: PR #{num}, head {sha}, main {before_main}")
    print(f"Required check contexts: {len(required)}")
    failures = []
    for check in required:
        name, app_id = check["context"], check.get("app_id")
        same_name = [r for r in runs if r.get("name") == name]
        matches = [r for r in same_name if app_id in (None, -1)
                   or r.get("app", {}).get("id") == app_id]
        if not same_name:
            state = "MISSING"
        elif not matches:
            state = "WRONG_APP"
        elif len(matches) > 1:
            state = "AMBIGUOUS_DUPLICATE"
        elif matches[0].get("status") == "completed" and matches[0].get("conclusion") == "success":
            state = "SUCCESS"
        else:
            state = "NOT_SUCCESS"
        print(f"{state:23} {name} [app_id={app_id}]")
        if state != "SUCCESS":
            failures.append(name)
    if failures:
        print(f"BLOCKED: {len(failures)} required check contexts not fully accepted.")
        sys.exit(1)
    print("REQUIRED_CHECKS_PRESENT: checked on the verified current PR head.")
    print("NOTE: this is not final GitHub merge authorization; other rules still apply.")
except (OSError, KeyError, TypeError, ValueError, AttributeError, json.JSONDecodeError) as exc:
    print(f"REFUSED: cannot verify live required checks: {exc}", file=sys.stderr)
    sys.exit(2)
PY
