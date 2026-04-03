#!/usr/bin/env bash

set -euo pipefail

REPO="tcmegahan/Crown2026"
BRANCH="main"
EXPORT_PATH="docs/release/branch-protection-export.json"

echo "==> Applying branch protection rules to ${REPO}/${BRANCH}..."

gh api --method PUT \
  "/repos/${REPO}/branches/${BRANCH}/protection" \
  --field required_status_checks='{
    "strict": true,
    "contexts": [
      "Analyze (python)",
      "Analyze (javascript)",
      "Backend Python Dependency Audit",
      "Frontend Node Dependency Audit",
      "backend-gate",
      "frontend-gate",
      "contract-gate",
      "secret-scan"
    ]
  }' \
  --field enforce_admins=true \
  --field required_pull_request_reviews='{
    "required_approving_review_count": 1,
    "dismiss_stale_reviews": true,
    "require_code_owner_reviews": true,
    "require_last_push_approval": true
  }' \
  --field allow_force_pushes=false \
  --field allow_deletions=false \
  --field required_linear_history=true \
  --field required_conversation_resolution=true

echo "==> Branch protection applied."

mkdir -p "$(dirname "$EXPORT_PATH")"
gh api "/repos/${REPO}/branches/${BRANCH}/protection" > "$EXPORT_PATH"

echo "==> Export saved to ${EXPORT_PATH}"