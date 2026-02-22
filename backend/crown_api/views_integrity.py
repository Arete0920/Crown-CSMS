import os

from django.http import JsonResponse
from django.utils import timezone

# Required checks as configured in branch protection (enforce_admins=true, strict=true).
# Source of truth: .github/branch_protection.json / GitHub API.
REQUIRED_CHECKS = [
    "changes",
    "demo-proof-static",
    "demo-surface-static-gate",
    "lockdown-gate",
    "meta-check-job-if",
    "phase1-contract",
    "phase3-runtime-proof",
    "proof-ceremony",
    "pytest",
    "rc-promotion-gate",
    "spine-audit",
    "test",
    "verify-immutable-tags",
]

# Authoring meta-gates that enforce structural CI invariants.
META_GATES = [
    {
        "id": "no-job-level-pr-if",
        "description": (
            "No job-level if: condition referencing PR head ref. "
            "Prevents SKIPPED → neutral required-check landmines."
        ),
        "added_pr": 327,
        "checker": "tools/ci/check_no_pr_job_if.py",
        "incident_ref": "PR #323: rc-promotion-gate stuck at neutral",
    },
    {
        "id": "no-unquoted-step-name-colon",
        "description": (
            "No unquoted step/job/workflow names containing ': '. "
            "Prevents go-yaml v3 parse failure (GitHub 'workflow file issue')."
        ),
        "added_pr": 329,
        "checker": "tools/ci/check_workflow_step_names.py",
        "incident_ref": "PR #328: all prod deploys failed silently since PR #317",
    },
]

GITHUB_REPO = "tcmegahan/Crown2026"

# Last known successful prod deploy tag — overwritten each deploy via PROD_DEPLOY_TAG app setting.
_FALLBACK_DEPLOY_TAG = "prod-deploy-2026-02-22-1315"


def integrity(request):
    build_sha = os.getenv("BUILD_SHA") or os.getenv("GITHUB_SHA") or "local-dev"
    env_name = os.getenv("CROWN_ENV", "dev")
    version = os.getenv("APP_VERSION", "crown-0.3.0")
    prod_deploy_tag = os.getenv("PROD_DEPLOY_TAG") or _FALLBACK_DEPLOY_TAG

    is_real_sha = build_sha not in ("local-dev", "unknown")
    github_commit_url = (
        f"https://github.com/{GITHUB_REPO}/commit/{build_sha}"
        if is_real_sha
        else None
    )
    github_tag_url = (
        f"https://github.com/{GITHUB_REPO}/releases/tag/{prod_deploy_tag}"
        if prod_deploy_tag
        else None
    )

    return JsonResponse(
        {
            "ok": True,
            "build_sha": build_sha,
            "github_commit_url": github_commit_url,
            "github_repo": GITHUB_REPO,
            "env": env_name,
            "version": version,
            "prod_deploy_tag": prod_deploy_tag,
            "github_tag_url": github_tag_url,
            "timestamp": timezone.now().isoformat(),
            "required_checks": REQUIRED_CHECKS,
            "meta_gates": META_GATES,
        }
    )
